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
import cryptsetup
from losetup import LoopDevice

import mounts
from executil import system, getoutput, ExecError

class Error(Exception):
    pass

class InvalidKey(Error):
    pass

def _init_module():
    if os.system("lsmod | grep -q dm_crypt"):
        os.system("modprobe -q dm-crypt")
_init_module()

def mount(device, mountpath, key=None):
    try:
        mounted = Mounted.init_from_device(device)
    except Error:
        mounted = None

    if mounted:
        raise Error("device (%s) is already mounted" % device)

    lodev = None
    if isfile(device):
        lodev = LoopDevice.losetup(device)
        device = lodev.path_device

    try:
        try:
            opened = cryptsetup.luksOpen(device, key)
        except:
            if lodev:
                lodev.detach()

            raise
    except cryptsetup.InvalidKey, e:
        raise InvalidKey(e)

    except cryptsetup.Error, e:
        raise Error(e)

    if not exists(mountpath):
        os.makedirs(mountpath)

    system("mount", opened.map, mountpath)
    
def umount(arg):
    mounted = Mounted.init_from_any(arg)

    system("umount", mounted.map)
    cryptsetup.luksClose(mounted.map)
    if mounted.loopdevice:
        LoopDevice(mounted.loopdevice).detach()

def create_keyfile(path):
    key = file("/dev/random").read(cryptsetup.KEYSIZE_BITS / 8)
    file(path, "w").write(key)
    os.chmod(path, 400)

class Mkfs:
    @staticmethod
    def is_fs_supported(filesystem):
        mkfs_util = "mkfs." + filesystem
        try:
            getoutput("which " + mkfs_util)
            return True
        except ExecError:
            return False

    @staticmethod
    def mkfs(device, key, filesystem="ext3", cipher="aes-cbc-essiv:sha256"):
        lodev = None
        if isfile(device):
            lodev = LoopDevice.losetup(device)
            device = lodev.path_device

        opened = None
        try:
            cryptsetup.luksFormat(device, key, cipher)
            opened = cryptsetup.luksOpen(device, key)
            system("mkfs." + filesystem, "-q", opened.map)

        finally:
            if opened:
                cryptsetup.luksClose(opened.map)

            if lodev:
                lodev.detach()

# for convenience
mkfs = Mkfs.mkfs

class FilesystemStats:
    def __init__(self, mountpath):
        self.mountpath = mountpath
        
        self.size = None
        self.avail = None
        self.used = None
        self.percent = None
        
        self.st = os.statvfs(self.mountpath)
        if self.st.f_blocks != long(0):
            st = self.st
            self.size = self._fmt_bytes(st.f_bsize * st.f_blocks)
            self.avail = self._fmt_bytes(st.f_bsize * st.f_bavail)

            used = st.f_blocks - st.f_bavail
            self.used = self._fmt_bytes(st.f_bsize * used)
            self.percent = "%s%%" % (used*100 / st.f_blocks)
    
    @staticmethod
    def _fmt_bytes(bytes):
        G = (1024 * 1024 * 1024)
        M = (1024 * 1024)
        K = (1024)
        if bytes > G:
            return str(bytes/G) + "G"
        elif bytes > M:
            return str(bytes/M) + "M"
        else:
            return str(bytes/K) + "K"

class Mounted(dict):
    """Representation of mounted LUKS filesystem"""
    def __setattr__(self, name, val):
        self[name] = val

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError, e:
            raise AttributeError(e)

    def __init__(self, map):
        try:
            cryptstatus = cryptsetup.Status(map)
            mount = mounts.Mounts()[cryptstatus.map]
        except (KeyError, cryptsetup.Error), e:
            raise Error(e)

        self.map = cryptstatus.map
        self.cipher = cryptstatus.cipher
        self.keysize = cryptstatus.keysize
        self.mountpath = mount.mountpath
        self.stats = FilesystemStats(self.mountpath)

        self.device = cryptstatus.device
        self.loopdevice = None
        if cryptstatus.is_loopback:
            self.device = LoopDevice(cryptstatus.device).path_file
            self.loopdevice = cryptstatus.device

    @classmethod
    def init_from_map(cls, map):
        return cls(map)

    @classmethod
    def init_from_mountpath(cls, mountpath):
        try:
            mount = mounts.Mounts()[realpath(mountpath)]
            status = cryptsetup.Status(mount.device)
        except (KeyError, cryptsetup.Error), e:
            raise Error(e)

        return cls(status.map)

    @classmethod
    def init_from_device(cls, device):
        device = realpath(device)
        for mount in mounts.Mounts():
            try:
                status = cryptsetup.Status(mount.device)
            except cryptsetup.Error:
                continue

            if device == realpath(status.device):
                return cls(status.map)

            if status.is_loopback:
               if device == LoopDevice(status.device).path_file:
                    return cls(status.map)

        raise Error("can't find mounted luks device (%s)" % device)

    @classmethod
    def init_from_any(cls, arg):
        """initialize Mounted from any type (device or mountpath or map)"""

        if isinstance(arg, cls):
            return arg

        try:
            return cls(arg)
        except Error:
            pass

        try:
            return cls.init_from_mountpath(arg)
        except Error:
            pass

        try:
            return cls.init_from_device(arg)
        except Error:
            pass

        raise Error("no matching luks mount for " + arg)

def list_mounts():
    arr = []
    for mount in mounts.Mounts():
        try:
            status = cryptsetup.Status(mount.device)
        except cryptsetup.Error:
            continue

        
        arr.append(Mounted(status.map))

    return arr

class KeyAdmin:
    """Class for administration of luks device keys"""

    MAX_SLOTS = 8

    def __init__(self, device):
        self.lodev = None

        if isfile(device):
            self.lodev = LoopDevice.losetup(device)
            self.device = self.lodev.path_device
        else:
            self.device = device

    def __del__(self):
        if self.lodev:
            self.lodev.detach()

    def _setup(method):
        def wrapper(*args, **kws):
            try:
                retval = method(*args, **kws)
            except cryptsetup.InvalidKey, e:
                raise InvalidKey(e)

            return retval

        return wrapper

    @_setup
    def get_slot(self, key):
        opened = None
        try:
            opened = cryptsetup.luksOpen(self.device, key)

        finally:
            if opened:
                cryptsetup.luksClose(opened.map)

        return opened.keyslot

    @_setup
    def add(self, cur_key, new_key):
        cryptsetup.luksAddKey(self.device, cur_key, new_key)

    @_setup
    def delete(self, key, keyslot):
        cryptsetup.luksDelKey(self.device, key, keyslot)

    @_setup
    def list_slots(self):
        output = cryptsetup.luksDump(self.device)
        return map(int, re.findall(r'Key Slot (\d+): ENABLED', output))

