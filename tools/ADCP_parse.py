#!/usr/bin/env python
# ADCP_Parse.py
#
# Copyright (C) 2008 - Samuel J. Cubbage
#
# This program is part of the Autonomous Model Software Tools Package
#
# A simple tool to remove the duplicate ensembles from a PD0 ADCP file
#
# 1/3/2008
import os

def parseAdcp(fname):
    if not os.path.isfile(fname):
        print 'No File Found', fname
        return
    
    bytes = open(fname, 'rb').read()
    outfile = open(fname+'x', 'wb')
    
    ensemble = ''                                       # Initialize ensemble counter
    while bytes:
        bytes, chunk = bytes[213:], bytes[:213]         # break into frames
        newensemble = chunk[72] + chunk[73]
        if ensemble != newensemble:
            ensemble = newensemble
#            print hex(ord(ensemble[0])), hex(ord(ensemble[1]))
            outfile.write(chunk)
    outfile.close()

    


if __name__ == '__main__':
    import sys
    errmsg = 'Required argument missing: [filename]'
    assert (len(sys.argv) == 2), errmsg
    parseAdcp(sys.argv[1])
    print 'Parse Complete'
