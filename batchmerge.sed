# This is a simple sed script to create the input file for the batch merge
# It takes the output of the Find command: $find -L . -iname '*.obc'
# and adds the paths for the merge output and input file.  Edit as needed
# 
# SJC 9/2013
#
s|\./|/frmg/Autonomous_Model/Test_Data/VIRGINIA/VPM_Surfaced_97ft-201410/|g 
s|obc|obc /disk2/home/samc/rcmdata/NSSN_VA/dnssni-n31r-dg-vpm97ft-surfaced-1410|
s|-1410|-1410 /frmg/Autonomous_Model/Test_Data/Merge_Files/CB10/MERGE_VA_VPM97ft_Lake-Depth3.INP |

