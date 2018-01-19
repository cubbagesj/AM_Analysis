# search_file.py
#
# Copyright (C) 2006-2007 - Samuel J. Cubbage
#
# This program is part of the Autonomous Model Software Tools Package
#
"""
    search_file.py - Provides 2 search methods to find RCM and AM data files
    search_file - searches a list directories provided in a search_path
    search_file_walk - Can search a list of directories and their subdirectories
"""

import os

def find_file(filename, search_path):
    """ Use the linux find command to locate the file
        Much simpler than the other way
    """
    findtext = os.popen('find -L %s -name %s -print'%(search_path, filename)).read().split('\n')
    
    return findtext[0]

def search_file(filename, search_path, pathsep=os.pathsep):
    """ Given a search path, find a file with requested name
        Returns the complete path and filename found, or None if not found
    """
    for path in search_path.split(pathsep):
        candidate = os.path.join(path, filename)
        if os.path.isfile(candidate):
            return os.path.abspath(candidate)
    return None

def search_file_walk(filename, search_path, pathsep=os.pathsep):
    """ Given a search path, find a file with requested name in the path
        or in any of the subdirectories in the path.  Returns complete
        path and filename or None if not found
    """

    # For some reason, this takes a very long time when searching the alpha, so
    # only use this for the obc files

    for path in search_path.split(pathsep):
        for root, dirs, files in os.walk(path):
            candidate = os.path.join(root, filename)
            if os.path.isfile(candidate):
                return candidate
    return None

if __name__ == '__main__':
    
    # Just a little test code
    f = search_file_walk('run-2287.obc', r"\\skipjack\share1\autonomous_model\test_data")
    print(f)

