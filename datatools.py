# datatools.py
#
# Copyright (C) 2017 - Samuel J. Cubbage
#
# This program is part of the Autonomous Model Software Tools Package
#
# These are some useful tools for the data consistency checkers
# To use import with: from datatools import *
#
#
import numpy as np
from scipy.signal import butter, lfilter, lfilter_zi


def butter_lowpass(cutoff, fs, order=5):
    nyq = .5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    # Use the initial points to initialize filter
    zi = lfilter_zi(b,a)
    y, _ =lfilter(b,a,data, zi=zi*data[0])
    return y



def spikeFilter(rawdata, limit):
    """ Parse an array and filter out spikes with delta > limit
    """
    lastvalue = rawdata[0]
    filterdata = []
    for n in range (len(rawdata)):
        if np.abs(rawdata[n] - lastvalue) > limit:
            filterdata.append(lastvalue)
        else:
            filterdata.append(rawdata[n])
            lastvalue = rawdata[n]

    return np.array(filterdata)

def yawFilter(rawdata):
    """ Takes out 360 deg yaw spikes when heading flips
    """
    step = 0.0
    filterdata = []
    for n in range(len(rawdata)):
        if n == 0:
            filterdata.append(rawdata[n])
        else:
            delta = rawdata[n] - rawdata[n-1]
            if abs(delta) > 180:
                step = delta
            filterdata.append(rawdata[n] - step)

    return np.array(filterdata)

def compTrajectory(x0, y0, z0, theta0, phi0, psi0, u, v, w, p, q, r, dt):
    """ This routine computes the model trajectory, it assumes
    that p,q,r are valid as well as u,v,w. It then starts
    from an initial state defines by x0,y0,z0 and theta0, phi0, psi0
    to compute the trajectory
    """

    # We will process this point by point so setup some containers for
    # the data
    phidot = []
    psidot = []
    thetadot = []
    phi= []
    psi = []
    theta = []
    xpos = []
    ypos = []
    zpos = []

    # Initialize the starting point
    phi.append(phi0)
    psi.append(psi0)
    theta.append(theta0)
    xpos.append(x0)
    ypos.append(y0)
    zpos.append(z0)

    # Now loop for each point
    for n in range(len(u)):
        thetadot.append(q[n]*np.cos(phi[n]) - r[n]*np.sin(phi[n]))
        phidot.append(p[n] + np.tan(theta[n])*(r[n]*np.cos(phi[n])+q[n]*np.sin(phi[n])))
        psidot.append((r[n]*np.cos(phi[n])+q[n]*np.sin(phi[n]))/np.cos(theta[n]))

        phi.append(phi[n] + phidot[n]*dt)
        theta.append(theta[n] + thetadot[n]*dt)
        psi.append(psi[n] + psidot[n]* dt)

        # Generate direction cosines
        a1 = np.cos(psi[n]) * np.cos(theta[n])
        a2 = (np.cos(psi[n])*np.sin(phi[n]*np.sin(theta[n])) - (np.sin(psi[n])*np.cos(phi[n])))
        a3 = (np.cos(phi[n])*np.cos(psi[n])*np.sin(theta[n])) + (np.sin(phi[n])*np.sin(psi[n]))
        b1 = np.sin(psi[n]) * np.cos(theta[n])
        b2 = (np.sin(phi[n])*np.sin(psi[n])*np.sin(theta[n])) + (np.cos(psi[n])*np.cos(phi[n]))
        b3 = (np.sin(psi[n])*np.sin(theta[n])*np.cos(phi[n])) - (np.sin(phi[n])* np.cos(psi[n]))
        c1 = -np.sin(theta[n])
        c2 = np.cos(theta[n]) * np.sin(phi[n])
        c3 = np.cos(theta[n]) * np.cos(phi[n])

        dx = a1*u[n] + a2*v[n] + a3*w[n]
        dy = b1*u[n] + b2*v[n] + b3*w[n]
        dz = c1*u[n] + c2*v[n] + c3*w[n]

        xpos.append(xpos[n] + dx*dt)
        ypos.append(ypos[n] + dy*dt)
        zpos.append(zpos[n] + dz*dt)

    return [xpos, ypos, zpos, phi, theta, psi]


def doTransform(u, v, w, phi, theta, psi, direction='toInertial'):
    """ Do coordinate transformation using direction cosines
    """

    unew = []
    vnew = []
    wnew = []

    for n in range(len(u)):
        a1 = np.cos(psi[n]) * np.cos(theta[n])
        a2 = (np.cos(psi[n])*np.sin(phi[n]*np.sin(theta[n])) - (np.sin(psi[n])*np.cos(phi[n])))
        a3 = (np.cos(phi[n])*np.cos(psi[n])*np.sin(theta[n])) + (np.sin(phi[n])*np.sin(psi[n]))
        b1 = np.sin(psi[n]) * np.cos(theta[n])
        b2 = (np.sin(phi[n])*np.sin(psi[n])*np.sin(theta[n])) + (np.cos(psi[n])*np.cos(phi[n]))
        b3 = (np.sin(psi[n])*np.sin(theta[n])*np.cos(phi[n])) - (np.sin(phi[n])* np.cos(psi[n]))
        c1 = -np.sin(theta[n])
        c2 = np.cos(theta[n]) * np.sin(phi[n])
        c3 = np.cos(theta[n]) * np.cos(phi[n])

        if direction == 'toInertial':
            unew.append(a1*u[n] + a2*v[n] + a3*w[n])
            vnew.append(b1*u[n] + b2*v[n] + b3*w[n])
            wnew.append(c1*u[n] + c2*v[n] + c3*w[n])
        elif direction == 'toBody':
            unew.append(a1*u[n] + b1*v[n] + c1*w[n])
            vnew.append(a2*u[n] + b2*v[n] + c2*w[n])
            wnew.append(a3*u[n] + b3*v[n] + c3*w[n])
        else:
            unew.append(u[n])
            vnew.append(v[n])
            wnew.append(w[n])

    return [np.array(unew), np.array(vnew), np.array(wnew)]


