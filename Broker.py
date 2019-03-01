# -*- coding: utf-8 -*-

import logging
import os
import time
import utils.tools as tool

from tornado import gen
from utils import Storage as st
from utils import Mail as mail
from utils import Sinks as sinks

logger = logging.getLogger(__name__)


class BrokerConfig(object):
    def __init__(self):
        self.common = {}
        self.mail = {}
        self.session = {}


class TaskBroker(object):
    def __init__(self, config):
        self._sinks = []
        self._events = []

        self._config = config
        self._storage = None
        self._mail_agent = None
        self._timezone = 'UTC'
        self._opened_session_date = None
        self._session_period = None

    def init(self):
        self._timezone = self._config.session['timezone']
        self._session_period = {
            'begin': time.strptime(self._config.session['begin'], '%H:%M'),
            'end': time.strptime(self._config.session['end'], '%H:%M')
        }

        self._storage = st.LiteStorage(os.path.join(self._config.common['storage_dir'], u'common-storage.db'))
        self._storage.init()

        self._mail_agent = mail.MailAgent(self._config.mail)
        self._mail_agent.connect()

    def fetch_sinks(self):
        now = tool.today(self._timezone)

        fetch_array = []
        for sink_item in self._sinks:
            array_item = {'measure': sink_item.name, 'data': []}

            if isinstance(sink_item, (sinks.TaskSinkGroup, sinks.TaskSinkChain, sinks.TaskSinkIndividual)):
                array_item['data'].extend(sink_item.get_data_sequence(now, self._timezone))
            else:
                continue

            fetch_array.append(array_item)


        return fetch_array

    @gen.coroutine
    def shedule(self):
        now = tool.today(self._timezone)
        session_key = tool.session_key(self._session_period)

        try:
            yield self._inspect_session_date((now, session_key))
        except Exception as e:
            logger.error(u'Exception was raised on session inspection: {}'.format(e.message), exc_info=1)
            return

        yield self._process_session((now, session_key))
        yield self._process_sinks((now, session_key))

    @gen.coroutine
    def _process_sinks(self, session_pair):
        for sink in self._sinks:
            if not isinstance(sink, (sinks.TaskSinkGroup, sinks.TaskSinkChain, sinks.TaskSinkIndividual)):
                continue

            sink.process(self._events, session_pair, self._timezone)

    @gen.coroutine
    def _process_session(self, session_pair):
        is_successfully = True

        msgs = None

        try:
            msgs = self._mail_agent.get_messages(session_pair)
        except Exception as e:
            logger.error(u'Exception was raised on session processing (get messages): {}'.format(e.message), exc_info=1)
            is_successfully = False

        if not is_successfully:
            raise gen.Return(False)

        if not msgs:
            raise gen.Return(True)

        try:
            is_successfully = self._storage.store_messages(session_pair, msgs, False)
        except Exception as e:
            logger.error(u'Exception was raised on session processing (store messages): {}'.format(e.message), exc_info=1)
            is_successfully = False

        if not is_successfully:
            self._storage.rollback()
            raise gen.Return(False)

        try:
            self._mail_agent.drop_messages(session_pair, msgs)
        except Exception as e:
            logger.error(u'Exception was raised on session processing (drop messages): {}'.format(e.message), exc_info=1)
            is_successfully = False

        if not is_successfully:
            self._storage.rollback()
            raise gen.Return(False)

        self._storage.commit()

        # todo: завернуть в локи
        new_msgs = [msg[1] for msg in msgs if msg[1].id not in [sink_event.event.id for sink_event in self._events]]
        self._events.extend([sinks.SinkedEvent(new_msg) for new_msg in new_msgs])
        # todo: завернуть в локи

        raise gen.Return(True)

    @gen.coroutine
    def _inspect_session_date(self, session_pair):
        need_open_session_new = False
        need_close_session_last = False

        is_session_period_timed = tool.in_session_period(session_pair, self._timezone)
        last_opened_date = None

        if is_session_period_timed:
            if self._opened_session_date is None:
                self._events = [sinks.SinkedEvent(stored_message) for stored_message in self._storage.get_stored_messages(session_pair, self._timezone)]

                last_opened_date = self._storage.last_opened_session_date_as_tz(session_pair, self._timezone)

                if last_opened_date is None:
                    need_open_session_new = True
                elif last_opened_date < tool.session_datetime(session_pair, 0, self._timezone):
                    need_close_session_last = True  # идет период сессии, но висит незакрытой прошлая сессия - нужно закрыть!
                    need_open_session_new = True  # идет период сессии, но текущая сессия не открыта - нужно открыть!
                else:
                    self._opened_session_date = last_opened_date
        else:
            self._events = []

            if self._opened_session_date is not None:
                last_opened_date = self._storage.last_opened_session_date_as_tz(session_pair, self._timezone)

                if last_opened_date is None:
                    self._opened_session_date = None
                else:
                    need_close_session_last = True

        if need_close_session_last:
            self._opened_session_date = None

            if last_opened_date is not None:
                self._close_session((last_opened_date, session_pair[1]))

        if need_open_session_new:
            self._opened_session_date = self._open_session(session_pair)

    def _close_session(self, session_pair):
        logger.info(u'AlertsDog daemon closes a session at {:%Y-%m-%d} {}'.format(session_pair[0], session_pair[1]))

        is_successfully = True

        for sink in self._sinks:
            sink.reset_events()

        try:
            self._storage.close_session(session_pair)
        except Exception as e:
            logger.error(u'Exception was raised on session closing (db): {}'.format(e.message), exc_info=1)

            is_successfully = False

        return is_successfully

    def _open_session(self, session_pair):
        logger.info(u'AlertsDog daemon opens a session at {:%Y-%m-%d} {}'.format(session_pair[0], session_pair[1]))

        is_successfully = True

        try:
            self._storage.open_session(session_pair, False)
        except Exception as e:
            logger.error(u'Exception was raised on session opening (db): {}'.format(e.message), exc_info=1)
            is_successfully = False

        if is_successfully:
            try:
                is_successfully = self._mail_agent.open_session(session_pair)
            except Exception as e:
                logger.error(u'Exception was raised on session opening (mail): {}'.format(e.message), exc_info=1)
                is_successfully = False

        if is_successfully:
            self._storage.commit()
        else:
            self._storage.rollback()

        return session_pair[0] if is_successfully else None

    def append_sink(self, sink):
        if not isinstance(sink, (sinks.TaskSinkGroup, sinks.TaskSinkChain, sinks.TaskSinkIndividual)):
            raise RuntimeError(u'Illegal data type is appended to sink collection!')

        self._sinks.append(sink)
