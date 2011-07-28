#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import subprocess, os

class Storage(dict):
    def __new__(cls, *args, **kwargs):
        self = dict.__new__(cls, *args, **kwargs)
        self.__dict__ = self
        return self
        
def printargs(fn, *args, **kwargs):
    def wrapper(*args, **kwargs):
        print 'function name:', fn.__name__
        print 'args:', args
        print 'kwargs:', kwargs        
        return fn(*args, **kwargs)
    
    return wrapper

def restore_cwd(fn, *args, **kwargs):
    def wrapper(*args, **kwargs):
        olddir = os.getcwd()
        results = fn(*args, **kwargs)        
        os.chdir(olddir)
        return results
    
    return wrapper

class postexec(object):
    def __init__(self, *commands):
        self.commands = commands

    def __call__(self, f):
        def wrapper(*args, **kwargs):
            results = f(*args, **kwargs)
            
            for command in self.commands:
                os.system(command)
            
            return results
            
        return wrapper
        
def fork_shell(args, shell=True):
    return subprocess.Popen(args, shell=shell, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    
def xshell(args, shell=True):
    '''returns an iterator for output lines'''
    return (line for line in fork_shell(args, shell=shell).stdout)
       
def shell(args, shell=True):
    '''execute a command and returns the output in a block mode'''    
    return ''.join(line for line in xshell(args, shell))
        
def get_dev_addr(dev='eth0'):
    '''returns the first ip address of a given ethernet device'''
    ip_addr = shell("ip addr show %s | grep 'inet .*%s$'" % (dev, dev)).strip().split(" ")
    return ip_addr[0] and ip_addr[1] or None
    
def gen_dev_addresses(dev='eth0'):
    '''returns the first ip address of a given ethernet device'''
    for line in shell("ip addr show %s | grep 'inet .*%s$'" % (dev, dev)).split("\n"):
        addr = line.strip().split(" ")
        if addr[0]:
            yield addr[1]
        
def reboot_device(*args):    
    os.system("sleep 4s && reboot")

def get_hostname(execute="cat /etc/hostname"):
    return shell(execute).strip()

    


if __name__ == '__main__':
    @postexec("touch /tmp/a.proove.this.shit.works")
    def foo(*args):
        print args
        
    foo(1,2,3,4)
        