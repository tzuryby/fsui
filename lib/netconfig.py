#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
from conf import appconfig


def configure():
    net_conf = appconfig.get()['net']
    for iface, settings in net_conf.iteritems():
        os.system("ifconfig %s up" % iface)
        os.system("ip addr add %s brd + dev %s" % (settings['addr'], iface))
        if settings.get("gw", None):            
            os.system("route add default gw %s dev %s" % (settings['gw'], iface))