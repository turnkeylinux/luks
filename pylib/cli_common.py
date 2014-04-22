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

import sys
import getpass
import luks

def get_valid_key(keyadm, keyfile=None, retry=True):
    """Get valid key in <keyadm> -> (key, keyslot)
    
    If <keyfile> is None, get a passphrase from the user.
    
    If we're on a tty, retry if the passphrase is a bad key.

    Raise exception: if keyfile is not valid, or if passphrase is not
    valid and not an interactive tty.

    """

    interactive = os.isatty(sys.stdin.fileno())
    key = keyfile

    while True:
        if not keyfile:
            if interactive:
                key = getpass.getpass("Enter passphrase: ")
            else:
                key = raw_input()

        try:
            keyslot = keyadm.get_slot(key)
            return (key, keyslot)

        except luks.InvalidKey:
            if retry and not keyfile and interactive:
                print >> sys.stderr, "Incorrect passphrase"
                continue
            raise

class Error(Exception):
    pass

def get_verified_passphrase():
    if not os.isatty(sys.stdin.fileno()):
        passphrase = raw_input()
        if isfile(passphrase):
            raise Error("You can't choose an existing file as your passphrase")

        return passphrase

    while True:
        p1 = getpass.getpass('Enter new passphrase: ')
        if isfile(p1):
            print "You can't choose an existing filename as your passphrase"
            continue

        p2 = getpass.getpass('Verify new passphrase: ')
        if p1 == p2:
            return p1
        else:
            print "Passphrases do not match, try again..."
            print
