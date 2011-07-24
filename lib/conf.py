#!/usr/bin/env python
# -*- coding: UTF-8 -*-

__author__ = "Tzury Bar Yochay <tzury.by@reguluslabs.com>"
__version__ = "0.1"

import os
from lxml import etree

FS_ROOT_DIR = "/usr/local/freeswitch" 
FS_CLI_COMMAND = os.path.join(FS_ROOT_DIR, "bin", "fs_cli") + " -x '%s'"
FS_DIR_PATH = os.path.join(FS_ROOT_DIR, "conf", "directory", "default")

class XMLHandler(object):
    def __init__(self, filename):
        self.filename = filename
        self.et = etree.parse(self.filename)
        
    def setAttr(self, xpath, **kwargs):
        for node in self.et.xpath(xpath):
            for k,v in kwargs.iteritems():
                node.attrib[k] = v
                
    def getAttr(self, xpath):
        node = self.et.xpath(xpath)
        return node and node[0].attrib or {}
        
        
    def write(self):
        self.et.write(self.filename)

class ExtensionFileHandler(XMLHandler):
    def __init__(self, xt_number):
        XMLHandler.__init__(self, os.path.join(FS_DIR_PATH, xt_number + ".xml"))
        
    def api(self):
        _api = {
            "id": ("/include/user[@id]", "id"),
            "password": ("/include/user/params/param[@name='password']", "value"),
            "vm-password": ("/include/user/params/param[@name='vm-password']", "value")
        }
        
        return _api
        
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
