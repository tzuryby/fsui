#!/usr/bin/env python
# -*- coding: UTF-8 -*-

__author__ = "Tzury Bar Yochay <tzury.by@reguluslabs.com>"
__version__ = "0.1"

import subprocess
import tornado.web
from lib.utils import common

global_client_params = {}
def init_global_client_params():
    global_client_params['hostname'] = common.get_hostname()

init_global_client_params()

class FSUIHandler(tornado.web.RequestHandler):
    pass

class DashboardHandler(FSUIHandler):
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
        command = "/usr/local/freeswitch/bin/fs_cli -x '%s'" % (command)
        print command
        output = common.shell(command)
        self.write("<pre>")
        self.write(output)
        self.write("</pre>")
        
        
