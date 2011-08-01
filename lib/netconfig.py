#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
from conf import appconfig

net_conf = appconfig.get()['net']

def _assign_addr():
    for iface, settings in net_conf.iteritems():
        os.system("ifconfig %s up" % iface)
        os.system("ip addr add %s brd + dev %s" % (settings['addr'], iface))
        if settings.get("gw", None):            
            os.system("route add default gw %s dev %s" % (settings['gw'], iface))
            
def _setup_firewall():
    
    closeall_lines = (        
        # CLEAR / FLUSH TABLE
        "iptables -F", 
        
        # SRTP PORT RANGE
        "iptables -A INPUT -p udp --dport 16384:32768 -j ACCEPT",
        
        # TLS
        "iptables -A INPUT -p tcp --dport 5061 -j ACCEPT",
        
        # SSH
        "iptables -A INPUT -p tcp --dport 2211 -j ACCEPT",
        
        # FSUI
        "iptables -A INPUT -p tcp --dport 5678 -j ACCEPT",
        
        #"iptables -A INPUT -p udp --dport 5060 -j DROP",
        #"iptables -A INPUT -p tcp --dport 5060 -j DROP"
        
        # DROP THE REST
        "iptables -A INPUT -j DROP"        
        )

    tmp_lines = (
        "iptables -F", 
        "iptables -A INPUT -p tcp --dport 5060 -j DROP",
        "iptables -A INPUT -p udp --dort 5060 -j DROP"
    )
    
    os.system(';'.join(tmp_lines))
    
def configure():
    _assign_addr()
    _setup_firewall()