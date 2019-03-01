# -*- coding: utf-8 -*-

import imaplib
import email
import email.message
import email.utils
import email.header
import logging
import datetime
import utils.tools as tool
import socket
import string
import pytz

logger = logging.getLogger(__name__)


class MailAgent(object):
    def __init__(self, config):
        self._config = config
        self._imap = None
        self._timezone = self._config['timezone'] or 'UTC'

    def __del__(self):
        self.drop_connection()

    def drop_connection(self):
        if self._imap is None:
            return

        try:
            self._imap.close()
        except Exception as e:
            logger.error(u'Exception was raised on drop a mail-agent connection (close): {}'.format(e.message))

        try:
            self._imap.logout()
        except Exception as e:
            logger.error(u'Exception was raised on drop a mail-agent connection (logout): {}'.format(e.message))

    def connect(self):
        self.drop_connection()

        self._imap = imaplib.IMAP4_SSL(host=self._config['host'], port=self._config['port'])
        self._imap.login(self._config['username'], self._config['password'])

    def _select_mailbox(self, mailbox='INBOX'):
        status = 'BAD'
        select_data = None

        counter = 20
        while counter > 0:
            counter = counter - 1

            try:
                status, select_data = self._imap.select(mailbox)

                if status == 'OK':
                    break
            except socket.error as e:
                logger.error(u'Exception was raised on select a mailbox (#1). There are re-connect is needed: {}'.format(e.message))

                self.connect()

                return (False, None)
            except imaplib.IMAP4.error as e:
                logger.error(u'Exception was raised on select a mailbox (#2). There are re-connect is needed: {}'.format(e.message))

                self.connect()

                return (False, None)

        return (True, select_data[0]) if status == 'OK' else (False, None)

    def get_messages(self, session_pair, chunk_size=10):
        selected, count_messages = self._select_mailbox('INBOX')

        if not selected:
            return False

        logger.info(u'AlertsDog daemon sniffed {} messages on processing a mail session at {:%Y-%m-%d} {}'.format(count_messages, session_pair[0], session_pair[1]))

        status, search_data = self._imap.search(None, 'ALL')

        if status != 'OK':
            return False

        msgs = []
        for msg_id_chunk in tool.chunker(search_data[0].split(), chunk_size):
            chunked_msgs = self._fetch(msg_id_chunk)

            msgs.extend(chunked_msgs)

        session_day_msgs = [(seq_num, msg) for seq_num, msg in msgs if msg.datetime.date() == session_pair[0].date()]

        return session_day_msgs

    def open_session(self, session_pair, chunk_size=10):
        selected, count_messages = self._select_mailbox('INBOX')

        if not selected:
            return False

        logger.info(u'AlertsDog daemon sniffed {} messages on opening a mail session at {:%Y-%m-%d} {}'.format(count_messages, session_pair[0], session_pair[1]))

        status, search_data = self._imap.search(None, 'ALL')

        if status != 'OK':
            return False

        msgs = []
        for msg_id_chunk in tool.chunker(search_data[0].split(), chunk_size):
            chunked_msgs = self._fetch(msg_id_chunk)

            msgs.extend(chunked_msgs)

        self._drop_outdated_messages(session_pair, msgs, chunk_size)

        return True

    def _drop_outdated_messages(self, session_pair, msgs, chunk_size=10):
        outdated_msgs = [(seq_num, msg) for seq_num, msg in msgs if msg.datetime.date() < session_pair[0].date()]

        if not outdated_msgs:
            return

        status, response = self._drop(outdated_msgs, chunk_size)

        if status == 'OK':
            logger.info(u'AlertsDog daemon drops {} out-of-date messages on opening a mail session at {:%Y-%m-%d} {}'.format(len(outdated_msgs), session_pair[0], session_pair[1]))

    def drop_messages(self, session_pair, msgs, chunk_size=10):
        if not msgs:
            return

        status, response = self._drop(msgs, chunk_size)

        if status == 'OK':
            logger.info(u'AlertsDog daemon drops {} messages on processing a mail sessions at {:%Y-%m-%d} {}'.format(len(msgs), session_pair[0], session_pair[1]))

    def _drop(self, msgs, chunk_size=10):
        for msg_seq_num_chunk in tool.chunker([string.strip(msg[0]) for msg in msgs], chunk_size):
            if self._config['debug']:
                status, response = self._imap.copy(','.join(msg_seq_num_chunk), r'debug')
                if status != 'OK':
                    raise RuntimeError('Messages copying error')

            status, response = self._imap.store(','.join(msg_seq_num_chunk), '+FLAGS', r'(\Deleted)')
            if status != 'OK':
                raise RuntimeError('Messages dropping error')

        return self._imap.expunge()

    def _fetch(self, ids_list, message_parts='(RFC822.HEADER)'):
        fetched_msgs = []

        if not ids_list:
            return fetched_msgs

        status, msg_data = self._imap.fetch(','.join(ids_list), message_parts)

        if status != 'OK':
            raise RuntimeError('Messages fetching error')

        if not isinstance(msg_data, list):
            raise RuntimeError('Messages fetching error (non-list structure)')

        for msg_raw in msg_data:
            if not isinstance(msg_raw, tuple):
                continue

            msg = email.message_from_string(msg_raw[1])

            if 'Date' not in msg:
                raise RuntimeError('Messages fetching error (no Date field)')

            if 'Message-ID' not in msg:
                raise RuntimeError('Messages fetching error (no Message-ID field)')

            if 'Subject' not in msg:
                raise RuntimeError('Messages fetching error (no Subject field)')

            if 'From' not in msg:
                raise RuntimeError('Messages fetching error (no From field)')

            msg_timestamp = email.utils.mktime_tz(email.utils.parsedate_tz(msg['Date']))

            message = MailMessage(id=msg['Message-ID'], msg_datetime=datetime.datetime.fromtimestamp(msg_timestamp), timezone=self._timezone)
            message.subject = u''.join(word.decode(encoding or 'utf8') if isinstance(word, bytes) else word for word, encoding in email.header.decode_header(msg['Subject']))

            sender = email.utils.parseaddr(msg['From'])[1]
            message.sender = sender.decode('utf-8', 'ignore') if type(sender) != unicode else sender

            fetched_msgs.append((msg_raw[0].split('(')[0], message))

        return fetched_msgs


class MailMessage(object):
    def __init__(self, id, msg_datetime, subject=u'', sender=u'', timezone='UTC'):
        self.id = id
        self.subject = subject
        self.sender = sender

        if msg_datetime.tzinfo is None:
            self.datetime = pytz.timezone(timezone).localize(msg_datetime, is_dst=None)

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__
