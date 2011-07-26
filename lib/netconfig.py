#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
from conf import appconfig


def configure():
    conf_tree = appconfig.get()
    for iface in conf_tree["net"]:
        os.system("ifconfig %s up" % (iface['name'])
        os.system("ip addr add %(addr)s brd + dev %(name)s" % iface)
        if iface.get("gw", None):
            os.system("route add default gw %(gw)s dev %(name)s" % iface)
            
    