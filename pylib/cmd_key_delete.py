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

"""Delete filesystem key

A key can either be a passphrase or a keyfile. If you don't specify a
keyfile, then we ask for a passphrase.

Arguments:

    <device> := /dev/path | path/to/loopfile
    <keyslot> := [0-7]
"""

import os
from os.path import *
import sys

import getopt
from cli_common import get_valid_key

import luks
import help

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: [ --keyfile=PATH ] %s <device> <keyslot>" % sys.argv[0]

def fatal(s):
    print >> sys.stderr, "error: " + str(s)
    sys.exit(1)

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "",
                                       ["keyfile="])
    except getopt.GetoptError, e:
        usage(e)

    keyfile = None

    for opt, val in opts:
        if opt == "--keyfile":
            if not isfile(val):
                fatal("no such file (%s)" % val)
            keyfile = val

    if not args:
        usage()

    if len(args) != 2:
        usage("bad number of arguments")

    device = args[0]
    delete_keyslot = int(args[1])

    keyadm = luks.KeyAdmin(device)

    if delete_keyslot not in keyadm.list_slots():
        fatal("keyslot %d is not active" % delete_keyslot)

    key, keyslot = get_valid_key(keyadm, keyfile)

    if keyslot == delete_keyslot:
        fatal("can't delete the same key used to access the filesystem")

    keyadm.delete(key, delete_keyslot)

if __name__ == "__main__":
    main()
