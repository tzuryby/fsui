#!/usr/bin/env python
# -*- coding: UTF-8 -*-

__author__ = "Tzury Bar Yochay <tzury.by@reguluslabs.com>"
__version__ = "0.1"

import os, json, re
from lxml import etree
from utils import common

FS_ROOT_DIR         = "/usr/local/freeswitch" 
FS_DIR_PATH         = os.path.join(FS_ROOT_DIR, "conf", "directory", "default")
SNOIP_VARS_PATH     = os.path.join(FS_ROOT_DIR, "conf", "snoip-vars.xml")

DIALPLAN_PATH       = os.path.join(FS_ROOT_DIR, "conf", "dialplan", "snoip.xml")

FS_CLI_COMMAND      = os.path.join(FS_ROOT_DIR, "bin", "fs_cli") + " -x '%s'"
FSUI_CONF_PATH      = "/opt/snoip/fsui/app.json"


class XMLHandler(object):
    filename = None
    _api = {}
    
    def __init__(self, _api = {}):
        self.et = etree.parse(self.filename)
        self._api = _api
        
        
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
        
# user's extensins password (and vm-password) handler
class ExtensionFileHandler(XMLHandler):
    def __init__(self, xt_number):
        _api = {
            "id": ("/include/user[@id]", "id"),
            "password": ("/include/user/params/param[@name='password']", "value"),
            "vm-password": ("/include/user/params/param[@name='vm-password']", "value")
        }
        self.filename = os.path.join(FS_DIR_PATH, "%s.xml" % (xt_number))
        XMLHandler.__init__(self, _api)
        
    def write(self):
        XMLHandler.write(self)
        common.shell("touch " + FS_DIR_PATH)


class SnoipVars(XMLHandler):
    filename = SNOIP_VARS_PATH
    
    def __init__(self, _api):
        XMLHandler.__init__(self, _api)
    

    def write(self):
        XMLHandler.write(self)
        common.shell("touch " + SNOIP_VARS_PATH)


class SnoipVarsXMLHandler(object):
    
    def __init__(self):        
        self.base_path = "/include/X-PRE-PROCESS[starts-with(@data,'%s')]"
        
    def get(self, path):
        return SnoipVars({'data': (self.base_path % path ,'data')}).get()
    
    def set(self, path, value):
        SnoipVars({'data': (self.base_path % path ,'data')}).set(data=path+ value)
        
class SnoipBaseHandler(object):
    xmlhandler = SnoipVarsXMLHandler()
    def get(self):
        ret = {}
        for name, path in self.paths.iteritems():                
            value = self.xmlhandler.get(path)['data']
            ret [name] = value.replace(path, '')
            
        return ret
        
    def set(self, **kwargs):
        for name, value in kwargs.iteritems():
            self.xmlhandler.set(self.paths[name], value)
    
class DialplanInternalContextRegexpHandler(SnoipBaseHandler):
    paths = {'internalDIDregex': 'DID_REGEX='}
        
class ConferenceOneHandler(SnoipBaseHandler):
    paths = {
        'conferenceOneName': 'CONFERENCE_ONE=',
        'conferenceOnePin': 'PIN_CONFERENCE_ONE=',
        'conferenceOneDid': 'DID_CONFERENCE_ONE=',
        'conferenceOneModeratorPin': 'MODERATOR_PIN_CONFERENCE_ONE=',
        'ivrDelay' : 'IVR_INIT_DELAY='
    }

class ConferenceTwoHandler(SnoipBaseHandler):
    paths = {
        'conferenceTwoName': 'CONFERENCE_TWO=',
        'conferenceTwoPin': 'PIN_CONFERENCE_TWO=',
        'conferenceTwoDid': 'DID_CONFERENCE_TWO=',
        'conferenceTwoModeratorPin': 'MODERATOR_PIN_CONFERENCE_TWO='        
    }

    
class ConferenceAdminHandler(SnoipBaseHandler):
    paths = {
        #~ 'pinAdmin': 'PIN_CONFERENCE_ADMIN=',
        #~ 'didAdmin': 'DID_CONFERENCE_ADMIN=',
        'lockRoom': 'LOCK_CONFERENCE_DIGITS=',
        'addMember': 'ADD_MEMBER_DIGITS=',
        'cancelMember': 'CANCEL_MEMBER_DIGITS='
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

def get_online_users():
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

def fs_directory_range():
    xtns = (xtn.strip().replace(".xml", "") for xtn in common.shell("ls -m %s" % FS_DIR_PATH).strip().split(","))
    return map(int, (xtn for xtn in xtns if xtn.isdigit()))
    
def get_conference_state():
    online_users = online_users = [(user.strip(), 1) for user in get_online_users().iterkeys()]
    rooms = {
        ConferenceOneHandler().get()['conferenceOneName']: None,
        ConferenceTwoHandler().get()['conferenceTwoName']: None
    }
    
    for room in rooms:
        users = common.shell("%s | grep %s | head -n 1" % (FS_CLI_COMMAND % 'show calls', room))
        users = users.split(",")
        users = [user for user in users if user in online_users]
        if users:
            rooms[room] = users
            
    for room in rooms.keys():
        if not rooms[room]:
            del rooms[room]
            
    return rooms
        
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
