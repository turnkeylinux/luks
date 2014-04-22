# Copyright (c) 2014 TurnKey Linux - http://www.turnkeylinux.org
# 
# This file is part of LUKS.
# 
# LUKS is open source software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.
# 

"""An interface to the losetup program"""

import re
from os.path import *
from executil import system, getoutput

class Error(Exception):
    pass

class LoopDevice:
    @staticmethod
    def _lodev2file(lodev):
        output = getoutput("losetup", lodev)
        m = re.match(r'/.*:.*\((.*)\)$', output)
        if not m:
            raise Error("can't parse losetup output: " + output)

        return m.group(1)

    def __init__(self, path_device):
        self.path_device = realpath(path_device)
        self.path_file = self._lodev2file(path_device)

    def detach(self):
        system("losetup -d", self.path_device)

    @classmethod
    def losetup(cls, path_file):
        """losetup a new loop device for <path_file> -> LoopDevice()"""
        free_device = getoutput("losetup -f")
        system("losetup", free_device, realpath(path_file))

        return cls(free_device)
