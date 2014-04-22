#!/usr/bin/python
# Copyright (c) 2014 TurnKey Linux - http://www.turnkeylinux.org
# 
# This file is part of LUKS.
# 
# LUKS is open source software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.
# 

"""
Mount filesystem

If --keyfile is not specified, ask for a passphrase.
"""
import os
from os.path import *

import sys
import getopt

import luks
import help

import getpass

class Error(Exception):
    pass

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [ --keyfile=PATH ] [ /dev/device | path/to/loopfile ] <mountpath>" % sys.argv[0]

def fatal(s):
    print >> sys.stderr, "error: " + str(s)
    sys.exit(1)

def mount(device, mountpath, keyfile=None):
    """mount <device> at <mountpath>. 
    
    If no <keyfile> is provided, get a passphrase from the user and use
    that as the key"""

    key = keyfile
    interactive = os.isatty(sys.stdin.fileno())

    while True:
        if not keyfile:
            if interactive:
                key = getpass.getpass("Enter passphrase: ")
            else:
                key = raw_input()

        try:
            luks.mount(device, mountpath, key)
            return
        except luks.InvalidKey:
            if not keyfile and interactive:
                print >> sys.stderr, "Incorrect passphrase"
                continue
            raise

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "",
                                       ['keyfile='])

    except getopt.GetoptError, e:
        usage(e)

    if not args:
        usage()

    if len(args) != 2:
        usage("bad number of arguments")

    device, mountpath = args

    try:
        mounted = luks.Mounted.init_from_mountpath(mountpath)
    except luks.Error:
        mounted = None

    if mounted:
        fatal("%s already mounted" % mountpath)
    
    keyfile = None

    for opt, val in opts:
        if opt == '--keyfile':
            keyfile = val

            if not isfile(keyfile):
                fatal("no such file (%s)" % val)

    try:
        mount(device, mountpath, keyfile)
    except luks.Error, e:
        fatal(e)

if __name__ == "__main__":
    main()
