#!/usr/bin/env python
# -*- coding: UTF-8 -*-

__author__ = "Tzury Bar Yochay <tzury.by@reguluslabs.com>"
__version__ = "0.1"

import os

FS_ROOT_DIR = "/usr/local/freeswitch" 
FS_CLI_COMMAND = os.path.join(FS_ROOT_DIR, "bin", "fs_cli") + " -x '%s'"
FS_DIR_PATH = os.path.join(FS_ROOT_DIR, "conf", "directory", "default")