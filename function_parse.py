"""
Created on Mon Jul 26 06:20:39 2010

This class contains the doFunction function, which will evaluate a string 
containing numpy commands as a function and return the result.

@author: C.Michael Pietras
"""

#import everything from numy so the exec function in doFunction will use it
from numpy import *


def doFunction(function, chans, ydata):
    for chan in chans:
        old = '$'+str(chan)
        new = 'ydata['+str(chan)+']'
        function = function.replace(old,new)
    if not function.find('$') == -1:
        return None
    exec('ydata'+function)
    return ydata
    
def makeLabel(function, chans, chan_names):
    for chan in chans:
        old = '$'+str(chan)
        new = chan_names[chan]
        function = function.replace(old,new)
    return function[1:]

def mult(x,y):
    x,y,ans = x.tolist(), y.tolist(), y.tolist()
    for i in range(len(ans)):
        ans[i] = x[i]*y[i]
    return ans
    
def div(x,y):
    x,y,ans = x.tolist(), y.tolist(), y.tolist()
    for i in range(len(ans)):
        ans[i] = x[i]/y[i]
    return ans
    
def diff(x, y):
    x = x.tolist()
    y = y.tolist()
    ans = []
    for i in range(len(x)-1):
        ans.append((x[i+1]-x[i])/(y[i+1]-y[i]))
    ans.append(ans[-1])
    print array(ans)
    return array(ans)
    
def integrate(x, y):
    x = x.tolist()
    y = y.tolist()
    ans = []
    for i in range(len(x)-1):
        interval = y[i+1] - y[i]
        ans.append(x[i]*interval)
    ans.append(x[i+1]*interval)
    return array(ans)
