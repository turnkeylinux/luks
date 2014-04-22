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

"""Print key slot

Prints the key slot of the specified key, unless user asks for --all
slots.

A key can either be a passphrase or a keyfile. If you don't specify a
keyfile, then we ask for a passphrase.

Arguments:
  <device> := /dev/path | path/to/loopfile 

Options:

  --all         Print the slots of all keys
  --keyfile=    Path to the keyfile

"""

import os
from os.path import *
import sys

import getopt

import luks
import help

from cli_common import get_valid_key

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [ -options ] <device>" % sys.argv[0]

def fatal(s):
    print >> sys.stderr, "error: " + str(s)
    sys.exit(1)

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "",
                                       ["keyfile=", "all"])
    except getopt.GetoptError, e:
        usage(e)

    keyfile = None
    all = False
    for opt, val in opts:
        if opt == "--keyfile":
            if not isfile(val):
                fatal("no such file (%s)" % val)
            keyfile = val

        if opt == "--all":
            all = True

    if not args:
        usage()

    if len(args) > 1:
        usage("too many arguments")

    device = args[0]
    keyadm = luks.KeyAdmin(device)

    if all:
        for slot in keyadm.list_slots():
            print slot

    else:
        try:
            key, keyslot = get_valid_key(keyadm, keyfile, retry=False)
            print keyslot

        except luks.InvalidKey:

            if keyfile:
                fatal("no key slot for specified keyfile (%s)" % keyfile)
            else:
                fatal("no key slot for specified passphrase")

if __name__ == "__main__":
    main()
