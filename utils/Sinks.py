# -*- coding: utf-8 -*-

import logging
import datetime
import pytz
import utils.tools as tool
import string
from abc import ABCMeta, abstractmethod

logger = logging.getLogger(__name__)


class SinkColors:
    default = 0  # grey (session outtimed)
    ok = 1  # green (in-time and no one errors)
    belated = 2  # yellowed-green 1 (late arrival)
    warning = 3  # yellow 2 (warning status)
    fail = 4  # red (fail status)
    processing = 5  # grayed-green (probably execution)


class SinkedEvent(object):
    def __init__(self, event, is_trapped=False):
        self.event = event
        self.is_trapped = is_trapped

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class TaskSink(object):
    __metaclass__ = ABCMeta

    def __init__(self, data):
        if not isinstance(data, dict):
            raise TypeError(u'Illegal data type')

        self.name = data['name']
        self.color_status = SinkColors.default
        self.is_trapped = False  # The event had trapped or not
        self.trapped_events = []
        self.trapped_datetime = None

        self._id = data['id']
        self._phrase = data['phrase'] if 'phrase' in data else None
        self._has_status = data['has_status'] if 'has_status' in data else True
        self._duration_s = data['duration_s'] if 'duration_s' in data else None

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    @property
    def phrase(self):
        return self._phrase

    @property
    def duration(self):
        return self._duration_s

    def is_phrase_fitted(self, test_phrase):
        return string.lower(self._phrase) in string.lower(test_phrase)

    def identify_status(self, start_datetime, end_datetime, now):
        status = SinkColors.ok

        if self.is_trapped:
            if self.trapped_datetime >= end_datetime:
                status = SinkColors.belated
        else:
            if now > end_datetime:
                status = SinkColors.fail
            elif now < start_datetime:
                status = SinkColors.default
            elif start_datetime <= now < end_datetime:
                status = SinkColors.processing

        return status

    def process_events(self, events, start_datetime, end_datetime, now):
        if self.is_trapped:
            return

        is_failed = False  # todo: rewrite it!
        is_warned = False  # todo: rewrite it!

        # for sink_event in [untrapped_event for untrapped_event in events if not untrapped_event.is_trapped]:
        for sink_event in [untrapped_event for untrapped_event in events]:
            if self.is_phrase_fitted(sink_event.event.subject) and now >= start_datetime:
                self.trapped_events.append(sink_event)
                self.is_trapped = True
                self.trapped_datetime = sink_event.event.datetime if self.trapped_datetime is None else self.trapped_datetime

                sink_event.is_trapped = True

                # todo: to correctfull realize!
                is_failed = True if '{fail}' in string.lower(sink_event.event.subject) else is_failed
                is_warned = True if '{warn}' in string.lower(sink_event.event.subject) else is_failed

        self.color_status = self.identify_status(start_datetime, end_datetime, now)

        if is_warned:
            self.color_status = SinkColors.warning

        if is_failed:
            self.color_status = SinkColors.fail

    def reset_events(self):
        self.is_trapped = False  # The event had trapped or not
        self.trapped_events = []
        self.trapped_datetime = None


class TaskSinkChained(TaskSink):
    def __init__(self, data):
        super(TaskSinkChained, self).__init__(data)

        self._lag_s = data['lag_s']
        self._chain_id = data['chain_id']

    @property
    def lag(self):
        return self._lag_s


class TaskSinkIndividual(TaskSink):
    def __init__(self, data):
        super(TaskSinkIndividual, self).__init__(data)

        self.start = data['start']

    def get_data_sequence(self, now, timezone):
        now = now.astimezone(pytz.timezone(timezone))

        sink_start_datetime = datetime.datetime.strptime(now.strftime('%Y-%m-%d') + u' ' + self.start, '%Y-%m-%d %H:%M:%S')
        sink_start_datetime = pytz.timezone(timezone).localize(sink_start_datetime, is_dst=None)

        sink_end_datetime = sink_start_datetime + datetime.timedelta(seconds=self.duration)

        return [[u'{:%Y-%m-%d %H:%M:%S}'.format(sink_start_datetime), self.color_status, u'{:%Y-%m-%d %H:%M:%S}'.format(sink_end_datetime)]]

    def process(self, events, session_pair, timezone):
        is_session_period_timed = tool.in_session_period(session_pair, timezone)

        if not is_session_period_timed:
            self.color_status = SinkColors.default
            return

        now = session_pair[0].astimezone(pytz.timezone(timezone))

        sink_start_datetime = datetime.datetime.strptime(now.strftime('%Y-%m-%d') + u' ' + self.start, '%Y-%m-%d %H:%M:%S')
        sink_start_datetime = pytz.timezone(timezone).localize(sink_start_datetime, is_dst=None)

        sink_end_datetime = sink_start_datetime + datetime.timedelta(seconds=self.duration)

        self.process_events(events, sink_start_datetime, sink_end_datetime, now)


class TaskSinkGroup(object):
    def __init__(self, group_id, name):
        self._counter = 0
        self._sink_group = []
        self._group_id = group_id

        self.name = name

    @property
    def group_id(self):
        return self._group_id

    @property
    def group(self):
        return self._sink_group

    def reset_events(self):
        for group_item in self._sink_group:
            group_item.reset_events()

    def get_data_sequence(self, now, timezone):
        now = now.astimezone(pytz.timezone(timezone))

        data_sequence = []

        for sink_item in self._sink_group:
            if not isinstance(sink_item, TaskSinkIndividual):
                raise TypeError(u'Illegal data type')

            group_item_start_datetime = datetime.datetime.strptime(now.strftime('%Y-%m-%d') + u' ' + sink_item.start, '%Y-%m-%d %H:%M:%S')
            group_item_start_datetime = pytz.timezone(timezone).localize(group_item_start_datetime, is_dst=None)

            group_item_end_datetime = group_item_start_datetime + datetime.timedelta(seconds=sink_item.duration)

            data_sequence.append([u'{:%Y-%m-%d %H:%M:%S}'.format(group_item_start_datetime), sink_item.color_status, u'{:%Y-%m-%d %H:%M:%S}'.format(group_item_end_datetime)])

        return data_sequence

    def process(self, events, session_pair, timezone):
        is_session_period_timed = tool.in_session_period(session_pair, timezone)
        now = session_pair[0].astimezone(pytz.timezone(timezone))

        for sink_item in self._sink_group:
            if not isinstance(sink_item, TaskSinkIndividual):
                raise TypeError(u'Illegal data type')

            if not is_session_period_timed:
                sink_item.color_status = SinkColors.default
                continue

            group_item_start_datetime = datetime.datetime.strptime(now.strftime('%Y-%m-%d') + u' ' + sink_item.start, '%Y-%m-%d %H:%M:%S')
            group_item_start_datetime = pytz.timezone(timezone).localize(group_item_start_datetime, is_dst=None)

            group_item_end_datetime = group_item_start_datetime + datetime.timedelta(seconds=sink_item.duration)

            sink_item.process_events(events, group_item_start_datetime, group_item_end_datetime, now)

    def push(self, data):
        if not isinstance(data, dict):
            raise TypeError(u'Illegal data type')

        self._counter += 1

        sink_data = {
            'id': u'{}_{}'.format(self._group_id, self._counter),
            'name': data['name'],
            'start': data['start'],
            'duration_s': data['duration_s'],
            'phrase': data['phrase'],
            'group_id': self._group_id
        }

        self._sink_group.append(TaskSinkIndividual(sink_data))

    def clear(self):
        raise NotImplementedError(u'Not implemented "clear" method!')

    def pop(self):
        raise NotImplementedError(u'Not implemented "pop" method!')


class TaskSinkChain(object):
    def __init__(self, chain_id, name, start, end):
        self._counter = 0
        self._sink_chain = []
        self._chain_id = chain_id

        self.name = name
        self.start = start
        self.end = end

    @property
    def chain_id(self):
        return self._chain_id

    @property
    def chain(self):
        return self._sink_chain

    def reset_events(self):
        for chain_item in self._sink_chain:
            chain_item.reset_events()

    def get_data_sequence(self, now, timezone):
        now = now.astimezone(pytz.timezone(timezone))

        chain_start_datetime = datetime.datetime.strptime(now.strftime('%Y-%m-%d') + u' ' + self.start, '%Y-%m-%d %H:%M:%S')
        chain_start_datetime = pytz.timezone(timezone).localize(chain_start_datetime, is_dst=None)

        chain_end_datetime = datetime.datetime.strptime(now.strftime('%Y-%m-%d') + u' ' + self.end, '%Y-%m-%d %H:%M:%S')
        chain_end_datetime = pytz.timezone(timezone).localize(chain_end_datetime, is_dst=None)

        data_sequence = []

        chain_item_start_datetime = chain_start_datetime

        for chain_item in self._sink_chain:
            if not isinstance(chain_item, TaskSinkChained):
                raise TypeError(u'Illegal data type')

            chain_item_end_datetime = chain_item_start_datetime + datetime.timedelta(seconds=chain_item.duration - 1)
            chain_item_end_datetime = chain_item_end_datetime if chain_start_datetime <= chain_item_end_datetime < chain_end_datetime else chain_end_datetime

            data_sequence.append([u'{:%Y-%m-%d %H:%M:%S}'.format(chain_item_start_datetime), chain_item.color_status, u'{:%Y-%m-%d %H:%M:%S}'.format(chain_item_end_datetime)])

            chain_item_start_datetime = chain_item_end_datetime + datetime.timedelta(seconds=1)

        return data_sequence

    def process(self, events, session_pair, timezone):
        is_session_period_timed = tool.in_session_period(session_pair, timezone)

        now = session_pair[0].astimezone(pytz.timezone(timezone))

        chain_start_datetime = datetime.datetime.strptime(now.strftime('%Y-%m-%d') + u' ' + self.start, '%Y-%m-%d %H:%M:%S')
        chain_start_datetime = pytz.timezone(timezone).localize(chain_start_datetime, is_dst=None)

        chain_end_datetime = datetime.datetime.strptime(now.strftime('%Y-%m-%d') + u' ' + self.end, '%Y-%m-%d %H:%M:%S')
        chain_end_datetime = pytz.timezone(timezone).localize(chain_end_datetime, is_dst=None)

        sink_start_datetime = chain_start_datetime

        for sink_item in self._sink_chain:
            if not isinstance(sink_item, TaskSinkChained):
                raise TypeError(u'Illegal data type')

            if not is_session_period_timed:
                sink_item.color_status = SinkColors.default
                continue

            sink_end_datetime = chain_start_datetime + datetime.timedelta(seconds=sink_item.lag)
            sink_end_datetime = sink_end_datetime if chain_start_datetime <= sink_end_datetime < chain_end_datetime else chain_end_datetime

            sink_item.process_events(events, sink_start_datetime, sink_end_datetime, now)

            sink_start_datetime = sink_end_datetime

    def push(self, data):
        if not isinstance(data, dict):
            raise TypeError(u'Illegal data type')

        self._counter += 1

        sink_data = {
            'id': u'{}_{}'.format(self._chain_id, self._counter),
            'name': data['name'],
            'lag_s': data['lag_s'],
            'duration_s': data['duration_s'],
            'phrase': data['phrase'],
            'chain_id': self._chain_id
        }

        self._sink_chain.append(TaskSinkChained(sink_data))

    def clear(self):
        raise NotImplementedError(u'Not implemented "clear" method!')

    def pop(self):
        raise NotImplementedError(u'Not implemented "pop" method!')
