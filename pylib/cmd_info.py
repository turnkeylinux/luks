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

"""Show mapped filesystems

By default, unless an argument is provided, all mapped luks filesystems
will be displayed.

"""

import os
import sys

import luks
import help

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [ /dev/path | path/to/loopfile | path/to/mountpoint ]" % sys.argv[0]

def fatal(s):
    print >> sys.stderr, "error: " + str(s)
    sys.exit(1)

def fmt_luks_mount(mount):
    fields = ('device', 'map', 'cipher', 'keysize', 'mountpath')
    fields = dict([ (field, mount[field]) for field in fields])

    column_len = max([ len(field) + 1 for field in fields ])

    lines = []

    # calculate fields
    for key, val in fields.items():
        if not val:
            continue
        line = "%s %s" % (key.ljust(column_len), val)
        lines.append(line)

    summary = "%s %s, used: %s (%s), avail: %s" % ('capacity'.ljust(column_len),
                                                   mount.stats.size,
                                                   mount.stats.used,
                                                   mount.stats.percent,
                                                   mount.stats.avail)
    lines.append(summary)
    return "\n".join(lines)

def main():
    args = sys.argv[1:]

    if len(args) > 1:
        usage("too many arguments")

    if not args:
        mounts = luks.list_mounts()
        for mount in mounts:
            print fmt_luks_mount(mount)
            print

    else:
        arg = args[0]
        try:
            mounted = luks.Mounted.init_from_any(arg)
        except luks.Error, e:
            fatal(e)

        print fmt_luks_mount(mounted)

if __name__ == "__main__":
    main()
