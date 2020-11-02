# cal_patch.py
"""
    cal_patch.py - This program is designed to change the calfile
    entries for a given channel
    
    06/28/2010 - sjc
    03/12/2013 - sjc - updated to generalize
    10/21/2020 - sjc - small tweaks for easier use in single mode
"""

import glob, sys, cfgparse
from optparse import OptionParser


def CalPatcher(patches, filelist):
    """ CalPatcher applies a series of patches to the cal files
        for a list of runs.
        
        args: patches - list of patches, each in the form: [section, entry, value]
            filelist - list of runs to apply the patch to: [run1, run2....]
    """
    # We apply all of the patches to the each file in list
    # so we loop on the files first
    
    for calfile in filelist:       
        
        print("Processing file: %s " % calfile) 
        
        # create a parser object
        c = cfgparse.ConfigParser()
        f = c.add_file(calfile)

        
        # Then we loop through the patches
        for patch in patches:
            [section, entry, value] = patch
                          
            # Then update the keys in the cal file
            f.set_option(entry.strip(), value.strip(), keys=section.strip())
        
        f.write(calfile)
    

if __name__ == "__main__":
    # If we are running as a stand alone, get the inputs from cmdline
    # You can run on a single file with:
    #        cal_patch.py file section entry value
    #
    # Or you use -f, -p to specify files containing patches and files to patch
    
    # Set up the command line parser
    parser = OptionParser()
    parser.add_option("-p", "--patchfile", dest="patchfile",
                      help="file containing patches")
    parser.add_option("-f","--filelist", dest="filelist",
                      help="file containing list of files to patch")
    
        
    # Parse the arguments
    (options, args) = parser.parse_args()
    
    # Now we need to check whether we are in single or batch mode
    if (options.patchfile and options.filelist):
        # We are in batch mode
        
        # First get the file list
        #filelist = file(options.filelist).read().split()
        filelist = glob.glob(options.filelist)
        
        # Then the patches
        # patch file format is: section entry value
        patches = []
        for line in open(options.patchfile):
            if (line.strip() != '' and line.strip().startswith('#') == False):
                patches.append(line.strip().split(','))
        
        CalPatcher(patches, filelist)
        
    else:
        # Single mode
        filename = args[0]
        patch = args[1:]
        
        for name in glob.glob(filename):
            
            # Apply patch
            CalPatcher([patch], [name])
        
    

