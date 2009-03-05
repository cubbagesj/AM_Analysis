#!/usr/bin/env python
# cal_patch.py
#
# Copyright (C) 2008 - Samuel J. Cubbage
# 
#  This program is part of the Autonomous Model Software Tools Package
# 
"""
This utility automates the process of patching
the calibration file for the Autonomous Model

"""
import difflib

# Start with some quick code just to try out the basic logic

# Begin with two cal files, the original and a modified one with the new cals

org_cal = open('cal.org', 'r').readlines()
new_cal = open('cal.new', 'r').readlines()

# Cycle through and generate differences
#d = difflib.Differ()
diffs = difflib.unified_diff(org_cal, new_cal)

print "".join(diffs)
