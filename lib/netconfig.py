#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
from conf import appconfig


def configure():
    net_conf = appconfig.get()['net']
    for iface, set in net_conf.iteritems():
        os.system("ifconfig %s up" % iface)
        os.system("ip addr add %s brd + dev %s" % (set['addr'], iface))
        if iface.get("gw", None):
            os.system("route add default gw %(gw)s dev %(name)s" % (set['gw'], iface))