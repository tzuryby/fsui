#!/usr/bin/env python
# -*- coding: UTF-8 -*-

__author__ = "Tzury Bar Yochay <tzury.by@reguluslabs.com>"
__version__ = "0.1"

import os, os.path, re

import tornado, tornado.httpserver, tornado.ioloop, tornado.options, tornado.web
from tornado.options import define, options

from httphandlers import *
from uimodules import *
from lib import conf, netconfig
from conf import appconfig

lan_host = appconfig.get()['net']['eth0']['addr'].split("/")[0]

define("port", default=5678, help="fsui port 5678", type=int)

class Application(tornado.web.Application):
    def __init__(self):
        
        settings = dict(
            app_title=u"FSUI - FREESWITCH HTML5 INTERFACE",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            ui_modules = {
                "Header": HeaderModule, 
                "Footer": FooterModule, 
                "Title": TitleModule,
            },
            autoescape = None
        )
        
        tornado.web.Application.__init__(self, HTTP_HANDLERS, **settings)

def main():
    # SET IP ADDRESSES FOR WAN/LAN INTERFACES
    netconfig.configure()
    os.system("/usr/local/bin/freeswitchd restart")
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port, lan_host)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
