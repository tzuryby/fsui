#!/usr/bin/env python
# -*- coding: UTF-8 -*-

__author__ = "Tzury Bar Yochay <tzury.by@reguluslabs.com>"
__version__ = "0.1"

import os, json
from lxml import etree
from utils import common

FS_ROOT_DIR         = "/usr/local/freeswitch" 
FS_DIR_PATH         = os.path.join(FS_ROOT_DIR, "conf", "directory", "default")
DIALPLAN_PATH       = os.path.join(FS_ROOT_DIR, "conf", "dialplan", "snoip.xml")
CONF_PROFILES_PATH  = os.path.join(FS_ROOT_DIR, "conf", "autoload_configs", "conference.conf.xml")
FS_CLI_COMMAND      = os.path.join(FS_ROOT_DIR, "bin", "fs_cli") + " -x '%s'"
FSUI_CONF_PATH      = "/opt/snoip/fsui/app.json"


class XMLHandler(object):
    filename = None
    _api = {}
    
    def __init__(self):
        self.et = etree.parse(self.filename)
        
    def api(self):
        return self._api
        
    def setAttr(self, xpath, **kwargs):
        for node in self.et.xpath(xpath):
            for k,v in kwargs.iteritems():
                node.attrib[k] = v
                
    def getAttr(self, xpath):
        node = self.et.xpath(xpath)
        return node and node[0].attrib or {}        
        
    def get_all(self):
        _api = self.api()
        ret = []
        for k, (_xpath, name,) in _api.iteritems():
            ret.append([node.attrib for node in self.et.xpath(_xpath)])
            
        return ret
        
    def write(self):
        self.et.write(self.filename)
        
    def set(self, **kwargs):
        _api = self.api()
        for k,v in kwargs.iteritems():
            if k in _api:
                (_xpath, name) = _api[k]
                self.setAttr(_xpath, **{name: v})
                
        self.write()
        
    def get(self):
        _api = self.api()
        ret = {}
        for k, (_xpath, name,) in _api.iteritems():
            attr = self.getAttr(_xpath)
            ret[k] = 'value' in attr and attr['value'] or attr[k]
            
        return ret
        
class ExtensionFileHandler(XMLHandler):
    _api = {
        "id": ("/include/user[@id]", "id"),
        "password": ("/include/user/params/param[@name='password']", "value"),
        "vm-password": ("/include/user/params/param[@name='vm-password']", "value")
    }
    
    def __init__(self, xt_number):
        self.filename = os.path.join(FS_DIR_PATH, "%s.xml" % (xt_number))
        XMLHandler.__init__(self)
        

class ConferenceProfilesHandler(XMLHandler):
    filename = CONF_PROFILES_PATH
    _api = {"name": ("/configuration/profiles/profile[@name]", "name")}

class ConferencePINHandler(XMLHandler):
    filename = CONF_PROFILES_PATH
    
    def __init__(self, profile):
        self.profile = profile
        self._api = {"pin": 
            ("/configuration/profiles/profile[@name='%s']/param[@name='pin']" 
                % (self.profile) , "value")}
                
        XMLHandler.__init__(self)
        
class DialplanContextRegexpHandler(XMLHandler):
    filename = DIALPLAN_PATH    

class DialplanInternalContextRegexpHandler(DialplanContextRegexpHandler):
    _api = {
        "expression":
        ("//context[@name='from-pstn']"
            "/extension[@name='to-sip']"
                "/condition[@field='destination_number']", 
            "expression")
    }

class DialplanExternalContextRegexpHandler(DialplanContextRegexpHandler):
    _api = {
        "expression":
        ("//context[@name='core']"
            "/extension[@name='to-pstn']"
                "/condition[@field='destination_number']", 
            "expression")
    }






XTN_TEMPLATE = '''<include>
  <user id="%(xtn)s">
    <params>
      <param name="password" value="%(xtn)s"/>
      <param name="vm-password" value="%(xtn)s"/>
    </params>
    <variables>
      <variable name="user_context" value="from-sip"/>
    </variables>
  </user>
</include>
'''

def directory_reset(start=1000):    
    olddir = os.getcwd()
    os.chdir(FS_DIR_PATH)
    os.system("rm -f *.xml")
    
    for xtn in range(start, start+30):
        with open("%d.xml" % (xtn), "wb") as xtn_file:
            xtn_file.write(XTN_TEMPLATE % ({"xtn": xtn}))
            
    os.system(FS_CLI_COMMAND % ("sofia profile internal flush_inbound_reg"))
    os.system(FS_CLI_COMMAND % ("sofia profile internal rescan"))
    os.chdir(olddir)

def fs_directory_range():
    xtns = (xtn.strip().replace(".xml", "") for xtn in common.shell("ls -m %s" % FS_DIR_PATH).strip().split(","))
    return map(int, (xtn for xtn in xtns if xtn.isdigit()))
    


class JSONConfHandler(object):
    def __init__(self, path):
        assert path
        self.path = path
        
    def reader(self):
        try:
            return open(self.path , 'rb')
            
        except IOError, msg:
            print msg
        
    def writer(self):
        try:
            return open(self.path , 'wb')
            
        except IOError, msg:
            print msg
    
    def get(self):
        return json.load(self.reader())
        
    def set(self, tree):
        json.dump(tree, self.writer(), indent=2)
        
appconfig = JSONConfHandler(FSUI_CONF_PATH)
