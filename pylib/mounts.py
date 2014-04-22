# Copyright (c) 2014 TurnKey Linux - http://www.turnkeylinux.org
# 
# This file is part of LUKS.
# 
# LUKS is open source software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.
# 

from os.path import *

class Mounts(list):
    class Record:
        def __str__(self):
            return " ".join([self.device, self.mountpath,
                             self.filesystem, self.options])

        def __repr__(self):
            return `str(self)`

        def __init__(self, device, mountpath, filesystem, options):
            self.device = device
            self.mountpath = mountpath
            self.filesystem = filesystem
            self.options = options

    @classmethod
    def parse(cls):
        for line in file('/proc/mounts', 'r').readlines():
            device, mountpath, filesystem, options, unused = line.split(None, 4)
            yield cls.Record(device, mountpath, filesystem, options)

    def __init__(self):
        self[:] = list(self.parse())

    def __getitem__(self, key):
        try:
            return list(self)[int(key)]
        except ValueError:
            for k in [key, realpath(key)]:
                for record in self:
                    if key in (record.device, record.mountpath):
                        return record
            raise KeyError("no such mount: " + key)
