# -*- coding: utf-8 -*-

import os
import sqlite3
import logging
import datetime
import pytz
import utils.tools as tool
from abc import ABCMeta, abstractmethod
from utils import ResourceLoader as rl
from Mail import MailMessage

logger = logging.getLogger(__name__)


class AlertsStorage(object):
    __metaclass__ = ABCMeta

    def __init__(self, *args):
        pass

    @abstractmethod
    def init(self):
        pass

    @abstractmethod
    def open_session(self, session_date, session_key):
        pass

    @abstractmethod
    def close_session(self, session_date, session_key):
        pass


class LiteStorage(AlertsStorage):
    def __init__(self, storage_file):
        super(LiteStorage, self).__init__()

        self._storage_file = storage_file
        self._res_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'schemas'))
        self._connection = None

    def __del__(self):
        if self._connection is not None:
            try:
                self._connection.close()
            except Exception:
                pass

    def init(self):
        self._connection = sqlite3.connect(self._storage_file)

        self._schema_init()

    def _schema_init(self, autocommit=True):
        is_successfully = True

        try:
            self._connection.executescript(rl.load_script(self._res_dir, 'schema_init.sql'))

            if autocommit:
                self._connection.commit()
        except Exception as e:
            logger.error(u'Exception was raised on db-schema init: {}'.format(e.message))

            self._connection.rollback()
            is_successfully = False

        return is_successfully

    def last_opened_session_date_as_tz(self, session_pair, timezone='UTC'):
        utc_session_date = session_pair[0].astimezone(pytz.timezone('UTC')).strftime('%Y-%m-%d %H:%M:%S')

        opened_session_date = None

        try:
            cursored = self._connection.execute(
                rl.load_script(self._res_dir, 'last_opened_session.sql'),
                {u'session_date': utc_session_date, u'session': session_pair[1]}
            )

            if cursored:
                for entry in cursored:
                    opened_session_date = entry[0]
                    break
        except Exception as e:
            logger.error(
                u'Exception was raised on select a last session date at {:%Y-%m-%d} {}: {}'.format(
                    session_pair[0],
                    session_pair[1],
                    e.message
                )
            )

        if opened_session_date is not None:
            opened_session_date = datetime.datetime.strptime(opened_session_date, '%Y-%m-%d %H:%M:%S')
            opened_session_date = pytz.timezone('UTC').localize(opened_session_date, is_dst=None)
            opened_session_date = opened_session_date.astimezone(pytz.timezone(timezone))

        return opened_session_date

    def close_session(self, session_pair, autocommit=True):
        utc_session_date = session_pair[0].astimezone(pytz.timezone('UTC')).strftime('%Y-%m-%d %H:%M:%S')
        utc_now = tool.today('UTC').strftime('%Y-%m-%d %H:%M:%S')

        is_successfully = True

        try:
            self._connection.execute(
                u'''INSERT OR REPLACE INTO Sessions (Session, Opened, Closed) VALUES (:session, :opened, :closed)''',
                {u'session': session_pair[1], u'opened': utc_session_date, u'closed': u''}
            )
        except Exception as e:
            logger.error(
                u'Exception was raised on close a session at {:%Y-%m-%d} {} #1: {}'.format(
                    session_pair[0],
                    session_pair[1],
                    e.message
                )
            )

            self._connection.rollback()
            is_successfully = False

        try:
            self._connection.execute(
                u'''
                UPDATE Sessions SET Closed = :closed
                WHERE
                    Session = :session
                    AND Opened <= :opened
                    AND Closed = ""
                ''',
                {u'session': session_pair[1], u'opened': utc_session_date, u'closed': utc_now}
            )
        except Exception as e:
            logger.error(
                u'Exception was raised on close a session at {:%Y-%m-%d} {} #2: {}'.format(
                    session_pair[0],
                    session_pair[1],
                    e.message
                )
            )

            self._connection.rollback()
            is_successfully = False

        if is_successfully and autocommit:
            self._connection.commit()

        return is_successfully

    def open_session(self, session_pair, autocommit=True):
        utc_session_date = session_pair[0].astimezone(pytz.timezone('UTC')).strftime('%Y-%m-%d %H:%M:%S')

        is_successfully = True

        try:
            self._connection.execute(
                u'''INSERT OR REPLACE INTO Sessions (Session, Opened, Closed) VALUES (:session, :opened, :closed)''',
                {u'session': session_pair[1], u'opened': utc_session_date, u'closed': u''}
            )

            if autocommit:
                self._connection.commit()
        except Exception as e:
            logger.error(u'Exception was raised on open a session at {:%Y-%m-%d}: {}'.format(session_pair[0], e.message))

            self._connection.rollback()
            is_successfully = False

        return is_successfully

    def rollback(self):
        try:
            self._connection.rollback()
        except:
            pass

    def commit(self):
        self._connection.commit()

    def store_messages(self, session_pair, msgs, autocommit=True):
        is_successfully = True

        msgs_pack = [(msg.id, msg.datetime.astimezone(pytz.timezone('UTC')).strftime('%Y-%m-%d %H:%M:%S'), msg.subject, msg.sender) for _, msg in msgs]

        try:
            self._connection.executemany('''INSERT INTO Mails (ID, ReceiveDate, Subject, Sender) VALUES (?, ?, ?, ?)''', msgs_pack)

            if autocommit:
                self._connection.commit()
        except Exception as e:
            logger.error(u'Exception was raised on store a messages at {:%Y-%m-%d} {}: {}'.format(session_pair[0], session_pair[1], e.message))

            self._connection.rollback()
            is_successfully = False

        return is_successfully

    def get_stored_messages(self, session_pair, timezone):
        session_start, session_end = tool.get_session_period(session_pair, timezone)

        utc_session_start = session_start.astimezone(pytz.timezone('UTC')).strftime('%Y-%m-%d %H:%M:%S')
        utc_session_end = session_end.astimezone(pytz.timezone('UTC')).strftime('%Y-%m-%d %H:%M:%S')

        stored_messages = []

        try:
            cursored = self._connection.execute(
                rl.load_script(self._res_dir, 'get_stored_mails.sql'),
                {u'session_start': utc_session_start, u'session_end': utc_session_end}
            )

            if cursored:
                for entry in cursored:
                    msg = MailMessage(
                        id=entry[0],
                        msg_datetime=datetime.datetime.strptime(entry[1], '%Y-%m-%d %H:%M:%S'),
                        subject=entry[2],
                        sender=entry[3],
                        timezone='UTC'
                    )

                    stored_messages.append(msg)
        except Exception as e:
            logger.error(
                u'Exception was raised on select a stored messages at {:%Y-%m-%d} {}: {}'.format(
                    session_pair[0],
                    session_pair[1],
                    e.message
                )
            )

        return stored_messages
