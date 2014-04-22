# Copyright (c) 2014 TurnKey Linux - http://www.turnkeylinux.org
# 
# This file is part of LUKS.
# 
# LUKS is open source software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.
# 

import os
from os.path import *

import re

from executil import system, getoutput, ExecError
import stdtrap

import luks

DEV_MAPPER_PATH = "/dev/mapper"
KEYSIZE_BITS = 256

class Error(Exception):
    pass

class InvalidKey(Error):
    pass

class Status(dict):
    Error = Error

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError, e:
            raise AttributeError(e)

    def is_loopback(self):
        if "/dev/loop" in self['device']:
            return True
        return False
    is_loopback = property(is_loopback)

    def __init__(self, map):
        """<map> is either relative to /dev/mapper or a full absolute
        path (e.g., /dev/mapper/foo)  """
        if not map.startswith("/"):
            map = join(DEV_MAPPER_PATH, map)

        if not map.startswith(DEV_MAPPER_PATH) or not exists(map):
            raise Error("invalid map (%s)" % map)

        self.map = map

        try:
            output = getoutput("cryptsetup status " + map)
        except ExecError, e:
            if "You have to be root" in e.output:
                raise

            raise Error(e)

        for line in output.split("\n"):
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip()

            if not v:
                continue

            self[k] = v

        if self.is_loopback:
            # /dev/.static/dev/loop1 -> /dev/loop1
            self['device'] = join("/dev", basename(self["device"]))
        else:
            # /dev/mapper/volgrp-area51 -> /dev/volgroup/area51
            try:
                output = getoutput("lvdisplay -c %s 2>&1" % self['device'])
                self['device'] = output.strip().split(':')[0]
            except ExecError:
                pass

def luksClose(map):
    system("cryptsetup luksClose", map)

LUKS_EXITCODE_INVALID_KEY = 255

def _cryptsetup(cmd, key1=None, key2=None):
    trap = stdtrap.UnitedStdTrap()

    try:
        fh = os.popen("cryptsetup " + cmd, "w")
        if key1 and not isfile(key1):
            fh.write(key1 + "\n")

        if key2 and not isfile(key2):
            fh.write(key2 + "\n")

        fh.flush()
        error = fh.close()
    finally:
        trap.close()

    output = trap.std.read()

    if error:
        error_msg = cmd + "\n" + output

        exitcode = os.WEXITSTATUS(error)
        if exitcode == LUKS_EXITCODE_INVALID_KEY:
            raise InvalidKey(error_msg)

        raise Error(error_msg)

    return output

def luksFormat(device, key, cipher):
    cmd = "--batch-mode --cipher=%s --key-size=%d luksFormat %s" % \
           (cipher, KEYSIZE_BITS, device)

    if isfile(key):
        cmd += " " + key

    _cryptsetup(cmd, key)

def luksOpen(device, key):
    """open a luks encrypted <device> using <key> -> _LuksOpened(map, keyslot)
    
    <key> can be either a filename or a passphrase
    """

    try:
        system("cryptsetup isLuks", device)
    except ExecError, e:
        raise Error(e)

    def get_free_dev_mapper_path(device):
        prefix = "luks:" + basename(realpath(device))
        index = 1
        while True:
            mapper_path = join(DEV_MAPPER_PATH, prefix)
            if index != 1:
                mapper_path += ":%d" % index

            if not exists(mapper_path):
                return mapper_path

            index += 1

    newmap = get_free_dev_mapper_path(device)

    cmd = "luksOpen %s %s" % (device, basename(newmap))
    if isfile(key):
        cmd += " --key-file=" + key

    output = _cryptsetup(cmd, key)
    if 'slot' in output:
        keyslot = int(re.search(r'slot (\d+)', output).group(1))
    else:
        keyadm = luks.KeyAdmin(device)
        keyslot = keyadm.list_slots()[0]

    class LuksOpened:
        def __init__(self, map, keyslot):
            self.map = map
            self.keyslot = keyslot

    return LuksOpened(newmap, keyslot)

def luksAddKey(device, cur_key, new_key):
    cmd = "luksAddKey " + device
    if isfile(new_key):
        cmd += " " + new_key

    if isfile(cur_key):
        cmd += " --key-file=" + cur_key

    _cryptsetup(cmd, cur_key, new_key)

def luksDelKey(device, key, keyslot):
    cmd = "luksDelKey %s %s" % (device, keyslot)

    if isfile(key):
        cmd += " --key-file=" + key

    _cryptsetup(cmd, key)

def luksDump(device):
    cmd = "luksDump " + device
    return _cryptsetup(cmd)
