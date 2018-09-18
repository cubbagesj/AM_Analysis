# dynos.py
#
# Copyright (C) 2006-2007 - Samuel J. Cubbage
#
#  This program is part of the Autonomous Model Software Tools Package
#
"""
    dynos.py - A collection of classes to handle dyno data

    CLASSES:
    RingBuffer - Implements a ring buffer for prop dyno data
    Kistler6 - Class for 4-guage Kistler gauges
    Kistler3 - Class for 3-guage kistler
    Dyno6 - 6 DOF dyno - stationary
    Rot_Dyno6 - Rotating 6 DOF dyno
"""

import numpy as np
import pandas as pd
import datatools as dt

class RingBuffer(object):
    """ class that implements a not-yet-full buffer
    Used for a running average of the prop data"""
    def __init__(self, size_max):
        self.max = size_max
        self.data = []
    def _full_append(self, x):
        """ Append an element overwriting the oldest one"""
        self.data[self.cur] = x
        self.cur = (self.cur+1) % self.max
    def _full_tolist(self):
        """ Return list of elements in correct order"""
        return self.data[self.cur:] + self.data[:self.cur]
    def _full_average(self):
        """ Return the average of the buffer elements"""
        return sum(self.data) / self.max
    def append(self,x):
        """ append an element to the end of the buffer """
        self.data.append(x)
        if len(self.data) == self.max:
            self.cur = 0
            self.append = self._full_append
            self.tolist = self._full_tolist
            self.average =  self._full_average
    def tolist(self):
        """ Return a list of elements from oldest to newest"""
        return self.data
    def average(self):
        """ Return average of the buffer elements """
        return sum(self.data) / len(self.data)


#  Dyno Classes - The following classes are set up to handle the 
#  various types of dynos

class Kistler6:
    """ A class to handle the cals for a Kistler Sail gauge.
        The Kistler is made up of 4 three-DOF gauges that are
        assembled into one 6DOF gauge.  Processing the dyno data requires
        combining the forces and moments to get the overall gauge forces and
        moments.  To combine the forces, we need some geometry info on the
    gauge construction that is provided in the cal.ini file

    These forces and moments are then passed through an interaction matrix
    and orientation matrix to get body forces and moments.  These 
    matrices come from the cal.ini file also.

    CLASS METHODS:

    __init__ - Sets up the instance and retrieves the channel numbers
    the geometry info and the interaction and orientation matrices

    compute() - Computes the body forces for at a time step

    addZero() - Adds a point to the accumulated zeros array

    compZero() - Computes the average zero value for each channel
    """
    def __init__(self, calfile):
        """ The constructor needs the calfile dictionary
            for the dyno
        """

        # First we get the channel assignments - There are 12 channels, 3 per gauge

        self.Fx1_chan = calfile['Fx1']
        self.Fy1_chan = calfile['Fy1']
        self.Fz1_chan = calfile['Fz1']

        self.Fx2_chan = calfile['Fx2']
        self.Fy2_chan = calfile['Fy2']
        self.Fz2_chan = calfile['Fz2']

        self.Fx3_chan = calfile['Fx3']
        self.Fy3_chan = calfile['Fy3']
        self.Fz3_chan = calfile['Fz3']

        self.Fx4_chan = calfile['Fx4']
        self.Fy4_chan = calfile['Fy4']
        self.Fz4_chan = calfile['Fz4']

        # Next comes combined gauge geometry as defined by the Xdist and Ydist
        # These are used when combining the forces

        self.xdist = calfile['xdist']
        self.ydist = calfile['ydist']

        # Now we need to get the info needed to remove the sail weight
        # This is the weight and the moment arms of this weight

        self.weight = calfile['weight']

        self.armx = calfile['armx']
        if self.armx == None:
            self.armx = 0.0
        self.army = calfile['army']
        if self.army == None:
            self.army = 0.0
        self.armz = calfile['armz']
        if self.army == None:
            self.army = 0.0
 
        # Now read the Interaction Matrix and Orientation Matrix

        self.Int_Mat = calfile['Int_Mat']
        self.Orient_Mat = calfile['Orient_Mat']

        # Finally we set the channel zeros to zero
        self.zeros = np.array(([0.0, 0.0, 0.0, 0.0, 0.0, 0.0]), float)

    def compute(self, rawdata, bodyAngles, cb_id=10, doZeros=1.0):
        """ Compute the corrected forces for the current timestep by combining the
        forces from each of the individual gauges and then applying
        the interaction and orientation matricies.  Finally, the sail weight
        is taken out using the body angles"""
        
        phi = bodyAngles[0]
        theta = bodyAngles[1]
        psi = bodyAngles[2]

        # Subtract zeros to get the relative forces
        relForces = np.array([rawdata[rawdata.columns[self.Fx1_chan]],
                           rawdata[rawdata.columns[self.Fy1_chan]],
                           rawdata[rawdata.columns[self.Fz1_chan]],
                           rawdata[rawdata.columns[self.Fx2_chan]],
                           rawdata[rawdata.columns[self.Fy2_chan]],
                           rawdata[rawdata.columns[self.Fz2_chan]],
                           rawdata[rawdata.columns[self.Fx3_chan]],
                           rawdata[rawdata.columns[self.Fy3_chan]],
                           rawdata[rawdata.columns[self.Fz3_chan]],
                           rawdata[rawdata.columns[self.Fx4_chan]],
                           rawdata[rawdata.columns[self.Fy4_chan]],
                           rawdata[rawdata.columns[self.Fz4_chan]]], float).transpose()

        # Now combine these individual gauge forces into total gauge forces
        combFx = relForces[:,0] + relForces[:,3] + relForces[:,6] + relForces[:,9]
        combFy = relForces[:,1] + relForces[:,4] + relForces[:,7] + relForces[:,10]
        combFz = relForces[:,2] + relForces[:,5] + relForces[:,8] + relForces[:,11]
        combMx = self.ydist*(-relForces[:,2] + relForces[:,5] -relForces[:,8] + relForces[:,11])
        combMy = self.xdist*(-relForces[:,2] - relForces[:,5] + relForces[:,8] + relForces[:,11])
        combMz = (self.ydist*(relForces[:,0] - relForces[:,3] + relForces[:,6] - relForces[:,10]) +
                  self.xdist*(relForces[:,1] + relForces[:,4] - relForces[:,7] -relForces[:,10]))

        rawForces = np.array([combFx,
                           combFy,
                           combFz,
                           combMx,
                           combMy,
                           combMz], float).transpose()

        # Apply the Interaction Matrix
        def intMatrix ( a, b):
            return np.dot( a,b)
        intForces = np.apply_along_axis(intMatrix, 1, rawForces, self.Int_Mat)

        # Apply the Orientation Matrix
        def orientMatrix ( a, b):
            return np.dot( a,b)
        compForces = np.apply_along_axis(orientMatrix, 1, intForces, self.Orient_Mat)

        # Now compute the self weight vector in body coords
        Wx, Wy, Wz = dt.doTransform(np.zeros(len(combFx), dtype=float),
                                    np.zeros(len(combFx), dtype=float),
                                    np.ones(len(combFx), dtype=float)*self.weight,
                                    phi,
                                    theta,
                                    psi) 
    
        # And then take out the self weight using the body angles
        self.CFx = compForces[:,0] - Wx 
        self.CFy = compForces[:,1] - Wy
        self.CFz = compForces[:,2] - Wz
        self.CMx = compForces[:,3] - (Wz*self.army - Wy*self.armz)
        self.CMy = compForces[:,4] - (-Wz*self.armx - Wx*self.armz)
        self.CMz = compForces[:,5] - (Wy*self.armx - Wx*self.army)
        
        if doZeros == 1.0:                      #Subtract zeros
            self.CFx = self.CFx - self.CFx_z
            self.CFy = self.CFy - self.CFy_z
            self.CFz = self.CFz - self.CFz_z
            self.CMx = self.CMx - self.CMx_z
            self.CMy = self.CMy - self.CMy_z
            self.CMz = self.CMz - self.CMz_z
        else:                                   #Compute Zeros
            self.CFx_z = self.CFx.mean()
            self.CFy_z = self.CFy.mean()
            self.CFz_z = self.CFz.mean()
            self.CMx_z = self.CMx.mean()
            self.CMy_z = self.CMy.mean()
            self.CMz_z = self.CMz.mean()
            

class Kistler3:
    """ A class to handle the cals for a 3-gauge Kistler.
        The Kistler is made up of 3 three-DOF gauges that are
        assembled into one 6DOF gauge.  Processing the dyno data requires
        combining the forces and moments to get the overall gauge forces and
        moments.  To combine the forces, we need some geometry info on the
        gauge construction that is provided in the cal.ini file

    These forces and moments are then passed through an interaction matrix
    and orientation matrix to get body forces and moments.  These 
    matrices come from the cal.ini file also.

    CLASS METHODS:

    __init__ - Sets up the instance and retrieves the channel numbers
    the geometry info and the interaction and orientation matrices

    compute() - Computes the body forces for at a time step

    addZero() - Adds a point to the accumulated zeros array

    compZero() - Computes the average zero value for each channel
    """
    def __init__(self, calfile):
        """ The constructor needs the calfile dictionary
            for the dyno
        """

        # First we get the channel assignments - There are 12 channels, 3 per gauge

        self.Fx1_chan = calfile['Fx1']
        self.Fy1_chan = calfile['Fy1']
        self.Fz1_chan = calfile['Fz1']

        self.Fx2_chan = calfile['Fx2']
        self.Fy2_chan = calfile['Fy2']
        self.Fz2_chan = calfile['Fz2']

        self.Fx3_chan = calfile['Fx3']
        self.Fy3_chan = calfile['Fy3']
        self.Fz3_chan = calfile['Fz3']

        # Next comes combined gauge geometry as defined by the Xdist and Ydist
        # These are used when combining the forces

        self.xdist = calfile['xdist']
        self.ydist = calfile['ydist']

        # Now we need to get the info needed to remove the sail weight
        # This is the weight and the moment arms of this weight

        self.weight = calfile['weight']

        self.armx = calfile['armx']
        if self.armx == None:
            self.armx = 0.0
        self.army = calfile['army']
        if self.army == None:
            self.army = 0.0
        self.armz = calfile['armz']
        if self.armz == None:
            self.armz = 0.0
 
        # Now read the Interaction Matrix and Orientation Matrix

        self.Int_Mat = calfile['Int_Mat']
        self.Orient_Mat = calfile['Orient_Mat']

        # Finally we set the channel zeros to zero
        self.zeros = np.array(([0.0, 0.0, 0.0, 0.0, 0.0, 0.0]), float)

    def compute(self, rawdata, bodyAngles, cb_id=10, doZeros=1.0):
        """ Compute the corrected forces for the current timestep by combining the
        forces from each of the individual gauges and then applying
        the interaction and orientation matricies.  Finally, the sail weight
        is taken out using the body angles"""

        phi = bodyAngles[0]
        theta = bodyAngles[1]
        psi = bodyAngles[2]

        # Subtract zeros to get the relative forces
        relForces = np.array([rawdata[rawdata.columns[self.Fx1_chan]],
                           rawdata[rawdata.columns[self.Fy1_chan]],
                           rawdata[rawdata.columns[self.Fz1_chan]],
                           rawdata[rawdata.columns[self.Fx2_chan]],
                           rawdata[rawdata.columns[self.Fy2_chan]],
                           rawdata[rawdata.columns[self.Fz2_chan]],
                           rawdata[rawdata.columns[self.Fx3_chan]],
                           rawdata[rawdata.columns[self.Fy3_chan]],
                           rawdata[rawdata.columns[self.Fz3_chan]]], float).transpose()

        # Now combine these individual gauge forces into total gauge forces
        combFx = relForces[:,0] + relForces[:,3] + relForces[:,6]
        combFy = relForces[:,1] + relForces[:,4] + relForces[:,7]
        combFz = relForces[:,2] + relForces[:,5] + relForces[:,8]
        combMx = self.ydist*(relForces[:,2] + relForces[:,5] - relForces[:,8])
        combMy = self.xdist*(relForces[:,2] - relForces[:,5] )
        combMz = (self.ydist*(-relForces[:,0] - relForces[:,3] + relForces[:,6]) +
                  self.xdist*(-relForces[:,1] + relForces[:,4]))

        rawForces = np.array([combFx,
                           combFy,
                           combFz,
                           combMx,
                           combMy,
                           combMz], float).transpose()


        # Apply the Interaction Matrix
        def intMatrix ( a, b):
            return np.dot( a,b)
        intForces = np.apply_along_axis(intMatrix, 1, rawForces, self.Int_Mat)

        # Apply the Orientation Matrix
        def orientMatrix ( a, b):
            return np.dot( a,b)
        compForces = np.apply_along_axis(orientMatrix, 1, intForces, self.Orient_Mat)

        # Now compute the self weight vector in body coords
        Wx, Wy, Wz = dt.doTransform(np.zeros(len(combFx), dtype=float),
                                    np.zeros(len(combFx), dtype=float),
                                    np.ones(len(combFx), dtype=float)*self.weight,
                                    phi,
                                    theta,
                                    psi) 
 
        # And then take out the self weight using the body angles

        self.CFx = compForces[:,0] - Wx 
        self.CFy = compForces[:,1] - Wy
        self.CFz = compForces[:,2] - Wz
        self.CMx = compForces[:,3] - (Wz*self.army - Wy*self.armz)
        self.CMy = compForces[:,4] - (-Wz*self.armx - Wx*self.armz)
        self.CMz = compForces[:,5] - (Wy*self.armx - Wx*self.army)

        if doZeros == 1.0:                      #Subtract zeros
            self.CFx = self.CFx - self.CFx_z
            self.CFy = self.CFy - self.CFy_z
            self.CFz = self.CFz - self.CFz_z
            self.CMx = self.CMx - self.CMx_z
            self.CMy = self.CMy - self.CMy_z
            self.CMz = self.CMz - self.CMz_z
        else:                                   #Compute Zeros
            self.CFx_z = self.CFx.mean()
            self.CFy_z = self.CFy.mean()
            self.CFz_z = self.CFz.mean()
            self.CMx_z = self.CMx.mean()
            self.CMy_z = self.CMy.mean()
            self.CMz_z = self.CMz.mean()
   

class Dyno6:
    """ A class to handle the cals for a standard non-rotating 6DOF dyno.
        This is used for the stator but not for the prop which is special 
    because it rotates

    The forces and moments are passed through an interaction matrix
    and orientation matrix to get body forces and moments.  These 
    matrices come from the cal.ini file also.

    CLASS METHODS:

    __init__ - Sets up the instance and retrieves the channel numbers
    and the interaction and orientation matrices

    compute() - Computes the body forces for at a time step


    """
    def __init__(self, calfile):
        """ The constructor needs the calfile dictionary
            for the dyno

            This routine populates the various variables needed for the class
            from the calfile
        """

        # First we get the channel assignments

        self.Fx_chan = calfile['Fx']
        self.Fy_chan = calfile['Fy']
        self.Fz_chan = calfile['Fz']
        self.Mx_chan = calfile['Mx']
        self.My_chan = calfile['My']
        self.Mz_chan = calfile['Mz']

        # Next comes the weight       
        self.weight = calfile['weight']

        # Older cal files only had one arm term, check for this:
        self.arm = calfile['arm']       
        if self.arm != None and self.arm != 0:
            self.armx = self.arm
            self.army = 0.0
            self.armz = 0.0

        self.armx = calfile['armx']
        if self.armx == None:
            self.armx = 0.0
        self.army = calfile['army']
        if self.army == None:
            self.army = 0.0
        self.armz = calfile['armz']
        if self.armz == None:
            self.armz = 0.0


        # Next comes the rotation angle
        try:
            self.angle = calfile['angle']
        except:
            self.angle = 0.0

        # Now for the interaction Matrix and Orient Matrix
        self.Int_Mat = calfile['Int_Mat']
        self.Orient_Mat = calfile['Orient_Mat']

        # Finally we set the channel zeros to zero
        self.zeros = np.array(([0.0, 0.0, 0.0, 0.0, 0.0, 0.0]), float)

    def compute(self, rawdata, bodyAngles, cb_id=10, doZeros=1.0):
        """ 
        Compute the corrected forces for the current timestep using
        the interaction and orientation matricies
        
        cb_id -flag is not relevant here, only used for rotating 6-DOF
        doZeros -flag to determine if zeros are to be subtracted. 
        """

        # The bodyAngles are in radians
        phi = bodyAngles[0]
        theta = bodyAngles[1]
        psi = bodyAngles[2]
       
        # Set up raw forces
        rawForces = np.array([rawdata[rawdata.columns[self.Fx_chan]],
                           rawdata[rawdata.columns[self.Fy_chan]],
                           rawdata[rawdata.columns[self.Fz_chan]],
                           rawdata[rawdata.columns[self.Mx_chan]],
                           rawdata[rawdata.columns[self.My_chan]],
                           rawdata[rawdata.columns[self.Mz_chan]]], float).transpose()

        # Apply the Interaction Matrix
        def intMatrix ( a, b):
            return np.dot( a,b)
        intForces = np.apply_along_axis(intMatrix, 1, rawForces, self.Int_Mat)

        # Apply the Orientation Matrix
        def orientMatrix ( a, b):
            return np.dot( a,b)
        compForces = np.apply_along_axis(orientMatrix, 1, intForces, self.Orient_Mat)

        # Now compute the self weight vector in body coords
        Wx, Wy, Wz = dt.doTransform(np.zeros(len(rawForces), dtype=float),
                                    np.zeros(len(rawForces), dtype=float),
                                    np.ones(len(rawForces), dtype=float)*self.weight,
                                    phi,
                                    theta,
                                    psi) 
    
        # And then take out the self weight using the body angles
        self.CFx = compForces[:,0] - Wx 
        self.CFy = compForces[:,1] - Wy
        self.CFz = compForces[:,2] - Wz
        self.CMx = compForces[:,3] - (Wz*self.army - Wy*self.armz)
        self.CMy = compForces[:,4] - (-Wz*self.armx - Wx*self.armz)
        self.CMz = compForces[:,5] - (Wy*self.armx - Wx*self.army)
        
        if doZeros == 1.0:                      #Subtract zeros
            self.CFx = self.CFx - self.CFx_z
            self.CFy = self.CFy - self.CFy_z
            self.CFz = self.CFz - self.CFz_z
            self.CMx = self.CMx - self.CMx_z
            self.CMy = self.CMy - self.CMy_z
            self.CMz = self.CMz - self.CMz_z
        else:                                   #Compute Zeros
            self.CFx_z = self.CFx.mean()
            self.CFy_z = self.CFy.mean()
            self.CFz_z = self.CFz.mean()
            self.CMx_z = self.CMx.mean()
            self.CMy_z = self.CMy.mean()
            self.CMz_z = self.CMz.mean()
     
class Rot_Dyno6:
    """ This class is a special case of a 6DOF dyno that rotates.  It
        is used for the propeller dyno.  Unlike the normal 6DOF dyno, we
    need to go from the rotating prop coordinate system into the body
    coordinate system.  This requires knowing the prop position.

    The forces and moments are also passed through an interaction matrix
    and orientation matrix to get body forces and moments.  These 
    matrices come from the cal.ini file also.

    CLASS METHODS:

    __init__ - Sets up the instance and retrieves the channel numbers
    the geometry info and the interaction and orientation matrices

    compute() - Computes the body forces for at a time step

    addZero() - Adds a point to the accumulated zeros array

    compZero() - Computes the average zero value for each channel

    """
    def __init__(self,  calfile):
        """ The constructor needs the calfile dictionary
            for the dyno
        """

        # First we get the channel assignments

        self.Fx_chan = calfile['Fx']
        self.Fy_chan = calfile['Fy']
        self.Fz_chan = calfile['Fz']
        self.Mx_chan = calfile['Mx']
        self.My_chan = calfile['My']
        self.Mz_chan = calfile['Mz']

        # Next comes the weight       
        self.weight = calfile['weight']

        # Older cal files only had one arm term, check for this:
        self.arm = calfile['arm']       
        if self.arm != None and self.arm != 0:
            self.armx = self.arm
            self.army = 0.0
            self.armz = 0.0

        self.armx = calfile['armx']
        if self.armx == None:
            self.armx = 0.0
        self.army = calfile['army']
        if self.army == None:
            self.army = 0.0
        self.armz = calfile['armz']
        if self.armz == None:
            self.armz = 0.0

        # Prop position zero
        try:
            self.PropPosZero = calfile['position']
        except:
            self.PropPosZero = 0
        if self.PropPosZero == None:
            self.PropPosZero = 0

        # Now for the interaction Matrix and Orient Matrix
        self.Int_Mat = calfile['Int_Mat']
        self.Orient_Mat = calfile['Orient_Mat']

        # initialize the rotation sensor
        self.lastpos = 0
        self.rotating = 0

        # Finally we set the channel zeros to zero
        self.zeros = np.array(([0.0, 0.0, 0.0, 0.0, 0.0, 0.0]), float)

    def compute(self, rawdata, bodyAngles, cb_id=10, doZeros=1.0):
        """ Compute the corrected forces for the current timestep using
        the interaction and orientation matricies

        Also do the rotation to model coords and subtract the prop
        weight
        """
        # The bodyAngles are in radians
        phi = bodyAngles[0]
        theta = bodyAngles[1]
        psi = bodyAngles[2]
             
        # Prop position depends on which centerbody it is
        prop_pos = rawdata['prop_position'].copy(deep=True)
         
        if cb_id < 12:
            prop_pos = prop_pos.map(lambda x: x+20000 if (x < 0) else x)
            prop_pos = prop_pos.map(lambda x: x-20000 if (x > 20000) else x)
            rot_angle = (prop_pos * .01800)
        else:
            rot_angle = prop_pos
            
        sinR = np.sin(np.radians(rot_angle))
        cosR = np.cos(np.radians(rot_angle))

        rawForces = np.array([rawdata[rawdata.columns[self.Fx_chan]],
                           rawdata[rawdata.columns[self.Fy_chan]],
                           rawdata[rawdata.columns[self.Fz_chan]],
                           rawdata[rawdata.columns[self.Mx_chan]],
                           rawdata[rawdata.columns[self.My_chan]],
                           rawdata[rawdata.columns[self.Mz_chan]]], float).transpose()

        # Apply the Interaction Matrix
        def intMatrix ( a, b):
            return np.dot( a,b)
        intForces = np.apply_along_axis(intMatrix, 1, rawForces, self.Int_Mat)

        # Apply the Orientation Matrix
        def orientMatrix ( a, b):
            return np.dot( a,b)
        compForces = np.apply_along_axis(orientMatrix, 1, intForces, self.Orient_Mat)

        if doZeros == 0.0:                      #Subtract zeros
            self.CFx_z = compForces[:,0].mean()
            self.CFy_z = compForces[:,1].mean()
            self.CFz_z = compForces[:,2].mean()
            self.CMx_z = compForces[:,3].mean()
            self.CMy_z = compForces[:,4].mean()
            self.CMz_z = compForces[:,5].mean()        

        rawbodyFx = compForces[:,0] - self.CFx_z
        rawbodyFy = compForces[:,1] - self.CFy_z
        rawbodyFz = compForces[:,2] - self.CFz_z
        rawbodyMx = compForces[:,3] - self.CMx_z
        rawbodyMy = compForces[:,4] - self.CMy_z
        rawbodyMz = compForces[:,5] - self.CMz_z

        # Now we need to rotate to the body coordinates
        bodyFx = compForces[:,0]
        bodyFy = cosR * rawbodyFy - sinR * rawbodyFz
        bodyFz = sinR * rawbodyFy + cosR * rawbodyFz
        bodyMx = compForces[:,3]
        bodyMy = cosR * rawbodyMy - sinR * rawbodyMz
        bodyMz = sinR * rawbodyMy + cosR * rawbodyMz

        # Now compute the self weight vector in body coords
        Wx, Wy, Wz = dt.doTransform(np.zeros(len(bodyFx), dtype=float),
                                    np.zeros(len(bodyFx), dtype=float),
                                    np.ones(len(bodyFx), dtype=float)*self.weight,
                                    phi,
                                    theta,
                                    psi) 
    
        # And then take out the self weight using the body angles
        self.CFx = bodyFx - Wx 
        self.CFy = bodyFy - Wy
        self.CFz = bodyFz - Wz
        self.CMx = bodyMx - (Wz*self.army - Wy*self.armz)
        self.CMy = bodyMy - (-Wz*self.armx - Wx*self.armz)
        self.CMz = bodyMz - (Wy*self.armx - Wx*self.army)



class Deck:
    """ A class to handle the cals for a Deck gauge.
        The Deck is made of 2 3-button Kistler gauges that are
        assembled into one 6DOF gauge.  Processing the dyno data requires
        combining the forces and moments to get the overall gauge forces and
        moments.  To combine the forces, we need some geometry info on the
        gauge construction that is provided in the cal.ini file

    These forces and moments are then passed through an interaction matrix
    and orientation matrix to get body forces and moments.  These 
    matrices come from the cal.ini file also.

    CLASS METHODS:

    __init__ - Sets up the instance and retrieves the channel numbers
    the geometry info and the interaction and orientation matrices

    compute() - Computes the body forces for at a time step

    addZero() - Adds a point to the accumulated zeros array

    compZero() - Computes the average zero value for each channel
    """
    def __init__(self, calfile):
        """ The constructor needs the calfile dictionary
            for the dyno
        """

        # First we get the channel assignments - There are 234channels, 3 per gauge, 3 gauges per Kistler

        self.Fx1f_chan = calfile['Fx1f']
        self.Fy1f_chan = calfile['Fy1f']
        self.Fz1f_chan = calfile['Fz1f']

        self.Fx2f_chan = calfile['Fx2f']
        self.Fy2f_chan = calfile['Fy2f']
        self.Fz2f_chan = calfile['Fz2f']

        self.Fx3f_chan = calfile['Fx3f']
        self.Fy3f_chan = calfile['Fy3f']
        self.Fz3f_chan = calfile['Fz3f']

        self.Fx1a_chan = calfile['Fx1a']
        self.Fy1a_chan = calfile['Fy1a']
        self.Fz1a_chan = calfile['Fz1a']

        self.Fx2a_chan = calfile['Fx2a']
        self.Fy2a_chan = calfile['Fy2a']
        self.Fz2a_chan = calfile['Fz2a']

        self.Fx3a_chan = calfile['Fx3a']
        self.Fy3a_chan = calfile['Fy3a']
        self.Fz3a_chan = calfile['Fz3a']


        # Next comes combined gauge geometry as defined by the Xdist and Ydist
        # These are used when combining the forces

        self.xdista = calfile['xdista']
        self.ydista = calfile['ydista']

        self.xdistf = calfile['xdistf']
        self.ydistf = calfile['ydistf']

        # Combined geometry
        self.gagex = calfile['gagex']
        self.gagey = calfile['gagey']
        self.gagez = calfile['gagez']

        # Now we need to get the info needed to remove the sail weight
        # This is the weight and the moment arms of this weight

        self.weight = calfile['weight']
        self.armx = calfile['armx']
        self.army = calfile['army']
        self.armz = calfile['armz']

        # Now read the Interaction Matrix and Orientation Matrix

        self.Int_Matf = calfile['Int_Matf']
        self.Orient_Matf = calfile['Orient_Matf']

        self.Int_Mata = calfile['Int_Mata']
        self.Orient_Mata = calfile['Orient_Mata']

        # Finally we set the channel zeros to zero
        self.zeros = np.array(([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]), float)

    def compute(self, rawdata, gains, bodyAngles,cb_id=10):
        """ Compute the corrected forces for the current timestep by combining the
        forces from each of the individual gauges and then applying
        the interaction and orientation matricies.  Finally, the sail weight
        is taken out using the body angles"""

        sinTH = bodyAngles[0]
        cosTH = bodyAngles[1]
        sinPH = bodyAngles[2]
        cosPH = bodyAngles[3]

        sinTHZ = bodyAngles[4]
        cosTHZ = bodyAngles[5]
        sinPHZ = bodyAngles[6]
        cosPHZ = bodyAngles[7]

        # Subtract zeros to get the relative forces
        relForcesf = np.array([(rawdata[self.Fx1f_chan]-self.zeros[0])*gains[self.Fx1f_chan],
                            (rawdata[self.Fy1f_chan]-self.zeros[1])*gains[self.Fy1f_chan],
                            (rawdata[self.Fz1f_chan]-self.zeros[2])*gains[self.Fz1f_chan],
                            (rawdata[self.Fx2f_chan]-self.zeros[3])*gains[self.Fx2f_chan],
                            (rawdata[self.Fy2f_chan]-self.zeros[4])*gains[self.Fy2f_chan],
                            (rawdata[self.Fz2f_chan]-self.zeros[5])*gains[self.Fz2f_chan],
                            (rawdata[self.Fx3f_chan]-self.zeros[6])*gains[self.Fx3f_chan],
                            (rawdata[self.Fy3f_chan]-self.zeros[7])*gains[self.Fy3f_chan],
                            (rawdata[self.Fz3f_chan]-self.zeros[8])*gains[self.Fz3f_chan]], float)

        relForcesa = np.array([(rawdata[self.Fx1a_chan]-self.zeros[9])*gains[self.Fx1a_chan],
                            (rawdata[self.Fy1a_chan]-self.zeros[10])*gains[self.Fy1a_chan],
                            (rawdata[self.Fz1a_chan]-self.zeros[11])*gains[self.Fz1a_chan],
                            (rawdata[self.Fx2a_chan]-self.zeros[12])*gains[self.Fx2a_chan],
                            (rawdata[self.Fy2a_chan]-self.zeros[13])*gains[self.Fy2a_chan],
                            (rawdata[self.Fz2a_chan]-self.zeros[14])*gains[self.Fz2a_chan],
                            (rawdata[self.Fx3a_chan]-self.zeros[15])*gains[self.Fx3a_chan],
                            (rawdata[self.Fy3a_chan]-self.zeros[16])*gains[self.Fy3a_chan],
                            (rawdata[self.Fz3a_chan]-self.zeros[17])*gains[self.Fz3a_chan]], float)


        # Now combine these individual gauge forces into total gauge forces
        combFxf = relForcesf[0] + relForcesf[3] + relForcesf[6]
        combFyf = relForcesf[1] + relForcesf[4] + relForcesf[7]
        combFzf = relForcesf[2] + relForcesf[5] + relForcesf[8]
        combMxf = self.ydistf*(relForcesf[2] + relForcesf[5] - relForcesf[8])
        combMyf = self.xdistf*(relForcesf[2] - relForcesf[5] )
        combMzf = (self.ydistf*(-relForcesf[0] - relForcesf[3] + relForcesf[6]) +
                   self.xdistf*(-relForcesf[1] + relForcesf[4]))

        rawForcesf = np.array([combFxf,
                            combFyf,
                            combFzf,
                            combMxf,
                            combMyf,
                            combMzf], float)

        # Apply the Interaction Matrix
        intForcesf = np.dot( rawForcesf, self.Int_Matf)
        # Apply the Orientation Matrix
        compForcesf = np.dot(intForcesf, self.Orient_Matf)

        self.compForcesf = compForcesf

        # Now combine these individual gauge forces into total gauge forces
        combFxa = relForcesa[0] + relForcesa[3] + relForcesa[6]
        combFya = relForcesa[1] + relForcesa[4] + relForcesa[7]
        combFza = relForcesa[2] + relForcesa[5] + relForcesa[8]
        combMxa = self.ydista*(relForcesa[2] + relForcesa[5] - relForcesa[8])
        combMya = self.xdista*(relForcesa[2] - relForcesa[5] )
        combMza = (self.ydista*(-relForcesa[0] - relForcesa[3] + relForcesa[6]) +
                   self.xdista*(-relForcesa[1] + relForcesa[4]))

        rawForcesa = np.array([combFxa,
                            combFya,
                            combFza,
                            combMxa,
                            combMya,
                            combMza], float)
        # Apply the Interaction Matrix
        intForcesa = np.dot( rawForcesa, self.Int_Mata)

        # Apply the Orientation Matrix
        compForcesa = np.dot(intForcesa, self.Orient_Mata)

        self.compForcesa = compForcesa


        # Now we need to combine the two gauges into one
        combFx = compForcesa[0] + compForcesf[0]
        combFy = compForcesa[1] + compForcesf[1]
        combFz = compForcesa[2] + compForcesf[2]

        combMx = (compForcesa[3] + compForcesf[3])/12 
        combMy = (compForcesa[2]*self.gagex/2 - compForcesf[2]*self.gagex/2)/12
        combMz = (compForcesf[1]*self.gagex/2 - compForcesa[1]*self.gagex/2)/12

        # And then take out the sail weight using the body angles
        # The values for the sin and cos of pitch and roll were calculated in the
        # main program so just use them here

        self.CFx = combFx - self.weight*(sinTHZ - sinTH)
        self.CFy = combFy - self.weight*(sinPH*cosTH - cosTHZ*sinPHZ)
        self.CFz = combFz - self.weight*(cosPH*cosTH - cosTHZ*cosPHZ)
        self.CMx = combMx + (self.weight*sinPH*cosTH*self.armz +
                             self.weight*self.army*(1-cosTH*cosPH))
        self.CMy = combMy + (self.weight*sinTH*self.armz +
                             self.weight*self.armx*(cosTH*cosPH -1))
        self.CMz = combMz - (self.weight*sinTH*self.army +
                             self.weight*sinPH*cosTH*self.armx)


    def addZero(self, rawdata):
        """ Adds a point to the accumulated zeros
        To account for the zeros not being at zero pitch and roll 
        we need to also compute a zero for the pitch and roll channels"""
        rawForces = np.array([rawdata[self.Fx1f_chan],
                           rawdata[self.Fy1f_chan],
                           rawdata[self.Fz1f_chan],
                           rawdata[self.Fx2f_chan],
                           rawdata[self.Fy2f_chan],
                           rawdata[self.Fz2f_chan],
                           rawdata[self.Fx3f_chan],
                           rawdata[self.Fy3f_chan],
                           rawdata[self.Fz3f_chan],
                           rawdata[self.Fx1a_chan],
                           rawdata[self.Fy1a_chan],
                           rawdata[self.Fz1a_chan],
                           rawdata[self.Fx2a_chan],
                           rawdata[self.Fy2a_chan],
                           rawdata[self.Fz2a_chan],
                           rawdata[self.Fx3a_chan],
                           rawdata[self.Fy3a_chan],
                           rawdata[self.Fz3a_chan]], float)

        self.zeros = self.zeros + rawForces

    def compZero(self, count):
        """ Computes the zero by dividing by the count"""

        self.zeros = self.zeros / count

