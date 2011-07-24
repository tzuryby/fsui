#!/usr/bin/env python
# -*- coding: UTF-8 -*-

__author__ = "Tzury Bar Yochay <tzury.by@reguluslabs.com>"
__version__ = "0.1"

import subprocess, re
import tornado.web
from tornado.escape import xhtml_escape

from lib.conf import *
from lib.utils import common

global_client_params = {}
def init_global_client_params():
    global_client_params['hostname'] = common.get_hostname()

init_global_client_params()

class FSUIHandler(tornado.web.RequestHandler):
    pass

class MainHandler(FSUIHandler):
    def get(self):
        self.render("index.html", global_client_params=global_client_params)


class StreamHandler(FSUIHandler): 
    start_page = "<pre>"        
    end_page = "</pre>"
    
    @tornado.web.asynchronous 
    def get(self):
        self.post()
        
    @tornado.web.asynchronous 
    def post(self):
        self.write(self.start_page) 
        self.ioloop = tornado.ioloop.IOLoop.instance() 
        self.pipe = self.get_pipe()        
        self.ioloop.add_handler(self.pipe.fileno(), self.async_callback (self.on_read), self.ioloop.READ)
        
    def close_pipe(self):
        self.ioloop.remove_handler(self.pipe.fileno())
        self.write(self.end_page)
        self.finish()
        self.pipe.close()
        
        try:
            self.process.kill()
        except:
            pass
        
    def on_read(self, fd, events): 
        buffer = self.pipe.read(90)
        try: 
            assert buffer 
            self.write(buffer)
            self.flush()
        except: 
            self.close_pipe()
            
    def _spawn_process(self, commandline):
        self.process = subprocess.Popen(
            commandline, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stdin=subprocess.PIPE, 
            stderr=subprocess.PIPE)
            
        return self.process
        
    def _get_pipe(self):
        return self._spawn_process('cat /dev/urandom').stdout
            
    def get_pipe(self):
        return self._get_pipe()
        
class FSLogHandler(StreamHandler):
    def _get_pipe(self):
        # dirty way to kill previous tails
        common.shell("killall tail")
        return self._spawn_process("tail -f /usr/local/freeswitch/log/freeswitch.log").stdout

class SyslogHandler(StreamHandler):
    def _get_pipe(self):
        # dirty way to kill previous tails
        common.shell("killall tail")
        return self._spawn_process("tail -f /var/log/syslog").stdout

class CLIHandler(FSUIHandler):
    def get(self):
        self.post()
        
    def post(self):
        command = self.get_argument("x", "sofia status profile internal")
        output = common.shell(FS_CLI_COMMAND % command)
        self.write("<pre>")
        self.write(xhtml_escape(output))
        self.write("</pre>")
        
class DashboardHandler(FSUIHandler):
    def _get_online_users(self):
        output = common.shell(FS_CLI_COMMAND % "sofia status profile internal")
        items = re.findall("Call-ID.*?Auth-Realm:.*?\n", output, re.DOTALL)
        users = (line for line in (item.split("\n") for item in items))
        online_users = (dict((map(str.strip, entry.split(": ")) for entry in user if entry)) for user in users)
        ret = {}
        for user in online_users:
            ret[user["Auth-User"]] = user
            
        print ret
        return ret
        
    def _get_directory_entries(self):
        return [filename.strip().replace(".xml", "")
            for filename in common.shell("cd %s; ls -m *.xml" % FS_DIR_PATH).split(",")
                if filename]
        
    def get_state(self):
        all_users_ids = [user for user in self._get_directory_entries()]
        online_users_data = self._get_online_users()
        
        online_users = [(user['Auth-User'], 1) for user in online_users_data]
        print "online_users", online_users
        
        offline_users = [(user, 0) for user in all_users_ids 
            if (user, 1,) not in online_users]
                
        return {
            "online_users_data": online_users_data,
            "online_users": online_users,
            "offline_users": offline_users
        }
        
    def get(self):
        self.render("dashboard.html", data=self.get_state())
        
        
HANDLERS = [
    (r"/", MainHandler),
    (r"/dashboard", DashboardHandler),
    (r"/cli", CLIHandler),
    (r"/fslog", FSLogHandler),
]
