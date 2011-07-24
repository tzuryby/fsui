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
        online_users = [dict((map(str.strip, entry.split(": ")) for entry in user if entry)) for user in users]
        return online_users
        
    def _get_directory_entries(self):
        return [filename.strip().replace(".xml", "")
            for filename in common.shell("cd %s; ls -m *.xml" % FS_DIR_PATH).split(",")
                if filename]
        
    def get_state(self):
        all_users_ids = [user for user in self._get_directory_entries()]
        online_users_data = self._get_online_users()
        
        online_users = [(user['Auth-User'], 1) for user in online_users_data]
        offline_users = [
            (user['Auth-User'], 0) for 
                user in all_users_ids 
                    if (user['Auth-User'], 1) not in online_users]
                
        all_users = [(user, user in online_users_ids) for user in self._get_directory_entries()]
        
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


'''    HTTPRequest(protocol='http', host='localhost:5678', method='GET', uri='/dashboard', version='HTTP/1.1', remote_ip='127.0.0.1', body='', headers={'Accept-Language': 'en-US,en;q=0.8', 'Accept-Encoding': 'gzip,deflate,sdch', 'Host': 'localhost:5678', 'Accept': 'text/html, */*; q=0.01', 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.124 Safari/534.30', 'Accept-Charset': 'UTF-8,*;q=0.5', 'Connection': 'keep-alive', 'X-Requested-With': 'XMLHttpRequest', 'Referer': 'http://localhost:5678/', 'Cookie': 'ui-tabs-1=0'})
    Traceback (most recent call last):
      File "/usr/local/lib/python2.6/dist-packages/tornado/web.py", line 850, in _execute
        getattr(self, self.request.method.lower())(*args, **kwargs)
      File "/usr/src/snoip/fsui/httphandlers.py", line 132, in get
        self.render("dashboard.html", data=self.get_state())
      File "/usr/src/snoip/fsui/httphandlers.py", line 121, in get_state
        all_users_ids if user not in online_users]
    TypeError: string indices must be integers, not str
