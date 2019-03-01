# -*- coding: utf-8 -*-

import datetime
import pytz
import string


def chunker(seq, size):
    return (seq[pos:pos + size] for pos in xrange(0, len(seq), size))


def today(timezone='UTC'):
    if timezone == 'UTC':
        today = datetime.datetime.utcnow()
    else:
        today = datetime.datetime.now()

    return pytz.timezone(timezone).localize(today, is_dst=None)


def session_key(session_period):
    begin = session_period['begin']
    end = session_period['end']

    return u'{:02d}:{:02d}-{:02d}:{:02d}'.format(begin.tm_hour, begin.tm_min, end.tm_hour, end.tm_min)


def session_datetime(session_pair, part, timezone='UTC'):
    sess_date = session_pair[0].astimezone(pytz.timezone(timezone))
    sess_key = session_pair[1]

    period_list = string.split(sess_key, u'-')

    sess_datetime = u'{} {}:00'.format(sess_date.strftime('%Y-%m-%d'), period_list[part])
    sess_datetime = datetime.datetime.strptime(sess_datetime, '%Y-%m-%d %H:%M:%S')
    sess_datetime = pytz.timezone(timezone).localize(sess_datetime, is_dst=None)

    return sess_datetime


def get_session_period(session_pair, timezone='UTC'):
    sess_date = session_pair[0].astimezone(pytz.timezone(timezone))
    sess_key = session_pair[1]

    period_list = string.split(sess_key, u'-')  # ex. HH:MM-HH:MM

    sess_datetime_l = u'{} {}:00'.format(sess_date.strftime('%Y-%m-%d'), period_list[0])
    sess_datetime_l = datetime.datetime.strptime(sess_datetime_l, '%Y-%m-%d %H:%M:%S')
    sess_datetime_l = pytz.timezone(timezone).localize(sess_datetime_l, is_dst=None)

    sess_datetime_r = u'{} {}:00'.format(sess_date.strftime('%Y-%m-%d'), period_list[1])
    sess_datetime_r = datetime.datetime.strptime(sess_datetime_r, '%Y-%m-%d %H:%M:%S')
    sess_datetime_r = pytz.timezone(timezone).localize(sess_datetime_r, is_dst=None)

    return sess_datetime_l, sess_datetime_r


def in_session_period(session_pair, timezone='UTC'):
    sess_datetime_l, sess_datetime_r = get_session_period(session_pair, timezone)

    sess_date = session_pair[0].astimezone(pytz.timezone(timezone))

    return True if sess_datetime_l <= sess_date < sess_datetime_r else False
