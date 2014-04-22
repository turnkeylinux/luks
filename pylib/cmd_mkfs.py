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

import os
import re
import sys
import getopt

import luks
import help

from cli_common import get_verified_passphrase

DEFAULT_CIPHER = "aes-cbc-essiv:sha256"
DEFAULT_FILESYSTEM = "ext3"

__doc__ = \
"""
Make filesystem

If no keyfile specified, we ask for a passphrase and use that as a key
instead.

Options:
  --fs=        Filesystem (default: %s)
               ext3 or reiserfs are recommended - can be extended on the fly

               Note: reiserfs default journal size is ~33MB

  --keyfile=   Path to keyfile
               If keyfile does not already exist, a new keyfile is created.
  --cipher=    The cipher specification string (default: %s)

  -f --force   Don't confirm destructive creation of filesystem 

               By default, if the command is run interactively (I.e.,
               from a tty), we ask the user to confirm the operation to
               prevent catastrophic loss of data.

""" % (DEFAULT_FILESYSTEM, DEFAULT_CIPHER)

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [-options] ( /dev/path | path/to/loopfile ) " % sys.argv[0]

def fatal(s):
    print >> sys.stderr, "error: " + str(s)
    sys.exit(1)

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "f",
                                       ['force', 
                                        'keyfile=',
                                        'fs=', 'cipher=' ])
    except getopt.GetoptError, e:
        usage(e)

    force = False

    keyfile = None
    filesystem = DEFAULT_FILESYSTEM
    cipher = DEFAULT_CIPHER

    for opt, val in opts:
        if opt == '--keyfile':
            keyfile = val
        elif opt == '--fs':
            filesystem = val
            if not luks.Mkfs.is_fs_supported(filesystem):
                fatal("filesystem (%s) is not supported" % filesystem)

        elif opt == '--cipher':
            cipher = val
        elif opt in ('-f', '--force'):
            force = True
            
    if not args:
        usage()

    if len(args) != 1:
        usage("bad number of arguments")

    device = args[0]
    if not os.path.exists(device):
        fatal("no such device (%s)" % device)

    if not force and os.isatty(sys.stderr.fileno()):
        print >> sys.stderr, "WARNING: this operation will destroy any data on " + device
        print >> sys.stderr, "Are you sure you want to continue (y/n): ",
        if raw_input() not in ("y", "yes"):
            sys.exit(1)

    if keyfile and not os.path.exists(keyfile):
        luks.create_keyfile(keyfile)

    key = keyfile 
    if not keyfile:
        key = get_verified_passphrase()
    try:
        luks.mkfs(device, key, filesystem, cipher)
    except luks.Error, e:
        fatal(e)
    
if __name__ == "__main__":
    main()
