#!/usr/bin/env python
# -*- coding: UTF-8 -*-

__author__ = "Tzury Bar Yochay <tzury.by@reguluslabs.com>"
__version__ = "0.1"

import subprocess, re, time

from tornado import httpclient
import tornado.web
from tornado.escape import xhtml_escape

from lib.conf import *
from lib.utils import common 
from lib.utils.BeautifulSoup import BeautifulSoup

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
    TIMEOUT = 15
    
    @tornado.web.asynchronous 
    def get(self):
        self.post()
        
    @tornado.web.asynchronous 
    def post(self):
        self.write(self.start_page) 
        self.ioloop = tornado.ioloop.IOLoop.instance() 
        self.pipe = self.get_pipe()        
        self.ioloop.add_handler(self.pipe.fileno(), self.async_callback (self.on_read), self.ioloop.READ)
        
        # close pipe after 180 seconds
        self.ioloop.add_timeout(time.time()+self.TIMEOUT, self.close_pipe);
        
    def close_pipe(self):
        print ('self.ioloop.remove_handler(self.pipe.fileno())')
        self.ioloop.remove_handler(self.pipe.fileno())
        print ('self.write(self.end_page)')
        self.write(self.end_page)
        print ('self.finish()')
        self.finish()
        
        try:
            print ('self.process.kill()')
            self.process.kill()
            print ('self.pipe.close()')
            self.pipe.close()    
        
        except Exception, msg:
            print (msg)
            
            
    def on_read(self, fd, events): 
        buffer = self.pipe.read(90)
        try: 
            assert buffer 
            self.write(xhtml_escape(buffer))
            self.flush()
        except: 
            self.close_pipe()
            
    def _spawn_process(self, commandline):
        self.process = subprocess.Popen(
            commandline, shell=True, 
            stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            
        return self.process
        
    def _get_pipe(self):
        return self._spawn_process('cat /dev/urandom').stdout
            
    def get_pipe(self):
        return self._get_pipe()
        

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
            extension = user["Auth-User"]
            ret[extension] = user
            ret[extension]["password"] = ExtensionFileHandler(extension).get()['password']
        
        return ret
        
    def _get_directory_entries(self):
        return [filename.strip().replace(".xml", "")
            for filename in common.shell("cd %s; ls -m *.xml" % FS_DIR_PATH).split(",")
                if filename]
        
    def get_state(self):
        all_users_ids = [user for user in self._get_directory_entries()]
        online_users_data = self._get_online_users()        
        online_users = [(user, 1) for user in online_users_data.iterkeys()]

        offline_users = [
            (user, 0, 
                ExtensionFileHandler(user).get()['password'])
                for user in all_users_ids 
                    if (user, 1,) not in online_users]
                
        return {
            "online_users_data": online_users_data,
            "online_users": online_users,
            "offline_users": offline_users
        }
        
    def get(self):
        self.render("dashboard.html", data=self.get_state())
        
class ExtensionPasswordHandler(FSUIHandler):
    def post(self):
        extension = self.get_argument("extension")
        password = self.get_argument("password")
        
        if extension and password:
            ExtensionFileHandler(extension).set(**{"password": password})
            

class ConferenceHandler(FSUIHandler):
    def _render(self):
        # render response
        data = []
        profiles = ConferenceProfilesHandler().get_all()[0]
        for profile in profiles:
            p = ConferencePINHandler(profile['name']).get()
            p['profile'] = profile['name']
            data.append(p)

        self.render("conferences.html", data=data)

    def get(self):
        self._render()
        
    def post(self):
        profile = self.get_argument("profile", None) 
        pin = self.get_argument("pin", None)
        if profile and pin:
            # save changes
            ConferencePINHandler(profile).set(**{"pin": pin})
        
        # render shit
        self._render()    
        
class FileCatter(FSUIHandler):        
    input_path =  '/tmp/non-exists.log' 
    output_name = 'null'
    header_type = ('Content-type', 'text/plain')
    
    def get(self):
        fd = common.shell('[ -e %s ] && cat %s || echo "file not found"' % (self.input_path, self.input_path))
        self.set_header(*self.header_type);
        self.set_header('Content-disposition', 'attachment;filename=%s'% (self.output_name))
        self.write(fd)

class SyslogCatter(FileCatter):
    input_path =  '/var/log/syslog' 
    output_name = 'syslog'
    
class FSLogCatter(FileCatter):
    input_path =  '/usr/local/freeswitch/log/freeswitch.log'
    output_name = 'switch.log'
    
class PcapFileCatter(FileCatter):
    input_path =  '/tmp/eth1.cap'
    output_name = 'traffic.cap'
    header_type = ('Content-type', 'application/octet-stream')

class TCPDumpHandler(StreamHandler):
    end_page = '''
    </pre><hr/><a href="/dl/pcap">Download PCAP File</a>
    <script>
        window.opener.showTcpdumpDownloadLink();
    </script>
    '''
    def get(self):
        self.post()
        
    def post(self):
        self.TIMEOUT = int(self.get_argument("timeout", 10))
        StreamHandler.post(self)
        
    def _get_pipe(self):
        # dirty way to kill previous tails        
        common.shell("killall tcpdump")
        # write to file and console at the same time 
        return self._spawn_process("tcpdump -s 0 -i eth1 -w - -U | tee /tmp/eth1.cap | tcpdump -xX -n -r -").stdout

class FSRegexpHandler(FSUIHandler):
    def get(self):
        self.post()
        
    def post(self):
        exp = self.get_argument("exp", "false")
        input = self.get_argument("input", '')
        
        self.write(exp and common.shell(FS_CLI_COMMAND % ("regex %s|%s" % (input, exp))).strip())

class DialplanHandler(FSUIHandler):
    def get(self):
        self.post()
        
    def post(self):
        expression = self.get_argument("expression", None)
        if expression:
            DialplanDestRegexpHandler().set(**{'expression': expression})
            
        data = {}
        data.update(DialplanDestRegexpHandler().get())
        dir_range = fs_directory_range()
        data['first-xtn'] = dir_range[0]
        data['last-xtn'] = dir_range[-1:][0]
        
        self.render("directory.html", data=data)


class MonitHandler(FSUIHandler):
    def post(self):
        self.get()
        
    def get(self):        
        # simply read monit
        if self.get_argument("action", None) is None:
            try:
                response = httpclient.HTTPClient().fetch("http://admin:admin@localhost:2812")
                response = BeautifulSoup(response.body)
                response = response('table')[-6:]
                self.render("monit.html", items=response)
            except:    
                self.render("monit.html", items="<error/>")
            
        # reload monit configuration 
        elif self.get_argument("action") == "reload":
            common.shell("monit reload all")
        
        # reboot machine
        elif self.get_argument("action") == "reboot":
            common.shell("reboot")
            
class RecreateDirectoryHandler(FSUIHandler):
    def get(self):
        self.post()
        
    def post(self):
        start_extension = self.get_argument("new-start", 1000)
        directory_reset(int(start_extension))
        
        self.render("directory.html", data=data)

HTTP_HANDLERS = [
    (r"/", MainHandler),
    (r"/dashboard", DashboardHandler),
    (r"/cli", CLIHandler),
    (r"/tcpdump", TCPDumpHandler),
    (r"/dl/syslog", SyslogCatter),
    (r"/dl/switchlog", FSLogCatter),
    (r"/dl/pcap", PcapFileCatter),
    (r"/admin/set/extension/password", ExtensionPasswordHandler),
    (r"/admin/conferences", ConferenceHandler),
    (r"/directory/recreate", RecreateDirectoryHandler),
    (r"/dialplan", DialplanHandler),
    (r"/dialplan/test", FSRegexpHandler),
    (r"/monit/read", MonitHandler),
]
