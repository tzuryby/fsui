#!/usr/bin/env python
# -*- coding: UTF-8 -*-

__author__ = "Tzury Bar Yochay <tzury.by@reguluslabs.com>"
__version__ = "0.1"

import tornado.web
from lib.utils import common

global_client_params = {}
def init_global_client_params():
    global_client_params['hostname'] = common.get_hostname()

init_global_client_params()

class DashboardHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html", global_client_params=global_client_params)

class CLIHandler(tornado.web.RequestHandler):
    def get(self):
        self.post()
        
    def post(self):
        command = self.get_argument("x", "sofia status profile internal")
        command = "/usr/local/freeswitch/bin/fs_cli -x '%s'" % (command)
        print command
        output = common.shell(command)
        self.write(output)