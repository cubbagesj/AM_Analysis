# turnstats.py
#
# Copyright (C) 2014 - Samuel J. Cubbage
#
# This program is part of the Autonomous Model Software Tools Package
#
# A utility routine to compute the advance and transfer for turn maneuvers
# 
# 

# 10/24/2014 - sjc

#import libraries to use

import numpy as np
import matplotlib.pyplot as plt
from filetypes import STDFile

runlist = []
for i in range(7244,7256):
    runlist.append('10-'+str(i))

runpath = '/disk2/home/samc/rcmdata/NSSN_VA/dnssni-n31r-g-vpm62ft-surfaced-1411/'
outfile = open('turnstats.txt', 'w')
outfile.write( 'run, advance, transfer, tactdiam, time90, time180\n')

for runname in runlist:
    rundata = STDFile(runpath+runname+'.std', 'known')
    rundata.turnstats()

    outfile.write(rundata.filename)
    outfile.write(', %f' % rundata.advance)
    outfile.write(', %f' % rundata.transfer)
    outfile.write(', %f' % rundata.tactdiam)
    outfile.write(', %f' % rundata.time90)
    outfile.write(', %f' % rundata.time180)
    outfile.write('\n')
