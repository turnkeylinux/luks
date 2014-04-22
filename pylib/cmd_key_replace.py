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

"""Replace filesystem key

A key can either be a passphrase or a keyfile. If you don't specify a
keyfile, then we ask for a passphrase.

Options:

  --cur-keyfile=    Path to the current keyfile you want to replace
  --new-keyfile=    Path to the new keyfile

"""

import os
from os.path import *
import sys

import getopt

import luks
import help

from cli_common import get_valid_key, get_verified_passphrase

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: [-options] %s ( /dev/path | path/to/loopfile )" % sys.argv[0]

def fatal(s):
    print >> sys.stderr, "error: " + str(s)
    sys.exit(1)

def key_replace(keyadm, cur_keyfile=None, new_keyfile=None):
    cur_key, cur_keyslot = get_valid_key(keyadm, cur_keyfile)

    if new_keyfile:
        new_key = new_keyfile
    else:
        new_key = get_verified_passphrase()

    keyadm.add(cur_key, new_key)
    keyadm.delete(new_key, cur_keyslot)

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "",
                                       ["cur-keyfile=", "new-keyfile="])
    except getopt.GetoptError, e:
        usage(e)

    cur_keyfile = None
    new_keyfile = None

    for opt, val in opts:
        if opt == "--cur-keyfile":
            cur_keyfile = val
        elif opt == "--new-keyfile":
            new_keyfile = val

    for keyfile in (cur_keyfile, new_keyfile):
        if not keyfile:
            continue

        if not isfile(keyfile):
            fatal("no such file (%s)" % keyfile)

    if not args:
        usage()

    if len(args) > 1:
        usage("too many arguments")

    device = args[0]

    keyadm = luks.KeyAdmin(device)
    if not len(keyadm.list_slots()) < keyadm.MAX_SLOTS:
        fatal("no free slots")

    try:
        key_replace(keyadm, cur_keyfile, new_keyfile)
    except luks.InvalidKey:
        fatal("can't access device (%s) with keyfile (%s)" % (device,
                                                              cur_keyfile))

if __name__ == "__main__":
    main()
