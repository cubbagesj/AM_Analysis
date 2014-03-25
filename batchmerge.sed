# This is a simple sed script to create the input file for the batch merge
# It takes the output of the Find command: $find -L . -iname '*.obc'
# and adds the paths for the merge output and input file.  Edit as needed
# 
# SJC 9/2013
#
s|\./|/frmg/Autonomous_Model/Test_Data/VIRGINIA/BLOCK_III_Surfaced-201309/|g 
s|obc|obc /disk2/home/samc/rcmdata/DNSSNI-N31R-DG-BLK3-SURFACED-1309|
s|-1309|-1309 /frmg/Autonomous_Model/Test_Data/Merge_Files/CB10/MERGE_VA_BLOCK3-MASK.INP |

