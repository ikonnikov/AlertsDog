# -*- coding: utf-8 -*-

import ConfigParser
import codecs
import logging
import os.path
import Broker
import json
from tornado import ioloop, web, httpserver, gen
from tornado.options import define, options, parse_command_line
from SinksFiller import fill_task_broker


define('config', default=u'TaskMan.cfg', help=u'absolute path to config file')
define('logto', default=u'TaskManLog.txt', help=u'absolute path to log file')
parse_command_line()

# logging.basicConfig(filename=options.logto, filemode='a', level=logging.INFO)
logger = logging.getLogger(__name__)


class RootHandler(web.RequestHandler):
    @gen.coroutine
    def get(self):
        self.render('index.html')


class MessageUpdatesHandler(web.RequestHandler):
    @gen.coroutine
    def get(self):
        sinks = self.application.sink_callback()

        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(sinks))

    @gen.coroutine
    def post(self):
        # cursor = self.get_argument("cursor", None)
        # self.future = global_message_buffer.wait_for_messages(cursor=cursor)
        # messages = yield self.future

        if self.request.connection.stream.closed():
            return

        self.write({'messages': self.application.sink_callback()})

    def on_connection_close(self):
        # global_message_buffer.cancel_wait(self.future)
        pass


class Application(web.Application):
    def __init__(self, callback):
        self.sink_callback = callback

        settings = {
            'template_path': os.path.join(os.path.dirname(__file__), 'templates'),
            'static_path': os.path.join(os.path.dirname(__file__), 'static'),
            'xsrf_cookies': True,
            'cookie_secret': '6666666666',  # todo: insert a secret
            'debug': False
        }

        handlers = [
            (r'/?', RootHandler),
            (r'/message/updates', MessageUpdatesHandler),
        ]

        super(Application, self).__init__(handlers, **settings)


def read_config():
    config = ConfigParser.ConfigParser()
    config.readfp(codecs.open(options.config, 'r', 'utf-8-sig'))

    daemon_config = Broker.BrokerConfig()
    daemon_config.common = {
        'host': config.get('common', 'host'),
        'port': config.getint('common', 'port'),
        'storage_dir': config.get('common', 'storage_dir')
    }
    daemon_config.mail = {
        'host': config.get('mail', 'host'),
        'port': config.getint('mail', 'port'),
        'username': config.get('mail', 'username'),
        'password': config.get('mail', 'password'),
        'interval': config.getint('mail', 'interval'),
        'timezone': config.get('mail', 'timezone'),
        'debug': config.getboolean('mail', 'debug')
    }
    daemon_config.session = {
        'begin': config.get('session', 'begin'),
        'end': config.get('session', 'end'),
        'timezone': config.get('session', 'timezone')
    }

    return daemon_config


def main():
    config = read_config()

    logger.info(u'Starting AlertsDog daemon on: {}:{}'.format(config.common['host'], config.common['port']))

    task_broker = Broker.TaskBroker(config)
    task_broker.init()

    fill_task_broker(task_broker)  # todo: rewrite it to fill from json-file

    server = httpserver.HTTPServer(Application(task_broker.fetch_sinks))
    server.listen(config.common['port'], config.common['host'])

    pc = ioloop.PeriodicCallback(task_broker.shedule, 1000 * config.mail['interval'])
    pc.start()

    ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main()
