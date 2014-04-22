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
Umount filesystem

Options:
  --force      Attempt to force a umount that would otherwise fail by
               brutally killing any processes that are accessing the filesystem
               (use with care)

"""

import sys
import getopt

import help
import luks

import executil

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [ --force ] ( /dev/path | path/to/loopfile | path/to/mount )" % sys.argv[0]

def fatal(e):
    print >> sys.stderr, "error: " + str(e)
    sys.exit(1)

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "",
                                       ['force'])
    except getopt.GetoptError, e:
        usage(e)

    force = False

    for opt, val in opts:
        if opt == '--force':
            force = True

    if not args:
        usage()

    if len(args) != 1:
        usage("too many arguments")

    arg = args[0]
    try:
        mounted = luks.Mounted.init_from_any(arg)
    except luks.Error, e:
        fatal(e)

    if force:
        executil.system("fuser -s -k", mounted.mountpath)

    luks.umount(mounted)

if __name__ == "__main__":
    main()
