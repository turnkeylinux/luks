#!/usr/bin/python
from os.path import *
import pyproject

class CliWrapper(pyproject.CliWrapper):
    DESCRIPTION = __doc__
    
    INSTALL_PATH = dirname(__file__)

    COMMANDS_USAGE_ORDER = ['mount', 'umount', 'mkfs', 'info',
                           '',
                           'key-replace', 'key-add', 'key-delete', 'key-slot']
    
if __name__ == '__main__':
    CliWrapper.main()
