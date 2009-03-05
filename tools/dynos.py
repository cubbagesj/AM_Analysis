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
    Kistler6 - Class for Kistler gauges
    Dyno6 - 6 DOF dyno - stationary
    Rot_Dyno6 - Rotating 6 DOF dyno
"""

from math import *
from Numeric import *

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
    def __init__(self, name, calfile):
        """ The constructor needs the calfile parser object and the
            section name for the dyno
        """
        
        # First we get the channel assignments - There are 12 channels, 3 per gauge
        
        self.Fx1_chan = calfile.add_option('Fx1', type='int', keys=name).get()
        self.Fy1_chan = calfile.add_option('Fy1', type='int', keys=name).get()
        self.Fz1_chan = calfile.add_option('Fz1', type='int', keys=name).get()

        self.Fx2_chan = calfile.add_option('Fx2', type='int', keys=name).get()
        self.Fy2_chan = calfile.add_option('Fy2', type='int', keys=name).get()
        self.Fz2_chan = calfile.add_option('Fz2', type='int', keys=name).get()

        self.Fx3_chan = calfile.add_option('Fx3', type='int', keys=name).get()
        self.Fy3_chan = calfile.add_option('Fy3', type='int', keys=name).get()
        self.Fz3_chan = calfile.add_option('Fz3', type='int', keys=name).get()

        self.Fx4_chan = calfile.add_option('Fx4', type='int', keys=name).get()
        self.Fy4_chan = calfile.add_option('Fy4', type='int', keys=name).get()
        self.Fz4_chan = calfile.add_option('Fz4', type='int', keys=name).get()

        # Next comes combined gauge geometry as defined by the Xdist and Ydist
        # These are used when combining the forces
        
        self.xdist = calfile.add_option('xdist', type = 'float', keys=name).get()
        self.ydist = calfile.add_option('ydist', type = 'float', keys=name).get()
        
        # Now we need to get the info needed to remove the sail weight
        # This is the weight and the moment arms of this weight

        self.weight = calfile.add_option('weight', type = 'float', keys=name).get()
        self.armx = calfile.add_option('armx', type = 'float', keys=name).get()
        self.army = calfile.add_option('army', type = 'float', keys=name).get()
        self.armz = calfile.add_option('armz', type = 'float', keys=name).get()
        
                
        # Now read the Interaction Matrix and Orientation Matrix
        rows = []
        for i in range(1,7):
            row = []
            rowstr = calfile.add_option('int_row%d' % i, keys=name).get()
            cols = rowstr.strip().split()
            for col in cols:
                row.append(float(col))
            rows.append(row)
        
        self.Int_Mat = array(rows, Float)

        rows = []
        for i in range(1,7):
            row = []
            rowstr = calfile.add_option('orient_row%d' % i, keys=name).get()
            cols = rowstr.strip().split()
            for col in cols:
                row.append(float(col))
            rows.append(row)
        
        self.Orient_Mat = array(rows, Float)
        
        # Finally we set the channel zeros to zero
        self.zeros = array(([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]), Float)
        
    def compute(self, rawdata, gains, bodyAngles):
        """ Compute the corrected forces for the current timestep by combining the
        forces from each of the individual gauges and then applying
        the interaction and orientation matricies.  Finally, the sail weight
        is taken out using the body angles"""
        
        sinTH = bodyAngles[0]
        cosTH = bodyAngles[1]
        sinPH = bodyAngles[2]
        cosPH = bodyAngles[3]
        
        # Subtract zeros to get the relative forces
        relForces = array([(rawdata[self.Fx1_chan]-self.zeros[0])*gains[self.Fx1_chan],
                           (rawdata[self.Fy1_chan]-self.zeros[1])*gains[self.Fy1_chan],
                           (rawdata[self.Fz1_chan]-self.zeros[2])*gains[self.Fz1_chan],
                           (rawdata[self.Fx2_chan]-self.zeros[3])*gains[self.Fx2_chan],
                           (rawdata[self.Fy2_chan]-self.zeros[4])*gains[self.Fy2_chan],
                           (rawdata[self.Fz2_chan]-self.zeros[5])*gains[self.Fz2_chan],
                           (rawdata[self.Fx3_chan]-self.zeros[6])*gains[self.Fx3_chan],
                           (rawdata[self.Fy3_chan]-self.zeros[7])*gains[self.Fy3_chan],
                           (rawdata[self.Fz3_chan]-self.zeros[8])*gains[self.Fz3_chan],
                           (rawdata[self.Fx4_chan]-self.zeros[9])*gains[self.Fx4_chan],
                           (rawdata[self.Fy4_chan]-self.zeros[10])*gains[self.Fy4_chan],
                           (rawdata[self.Fz4_chan]-self.zeros[11])*gains[self.Fz4_chan]], Float)

        # Now combine these individual gauge forces into total gauge forces
        combFx = relForces[0] + relForces[3] + relForces[6] + relForces[9]
        combFy = relForces[1] + relForces[4] + relForces[7] + relForces[10]
        combFz = relForces[2] + relForces[5] + relForces[8] + relForces[11]
        combMx = self.ydist*(-relForces[2] + relForces[5] -relForces[8] + relForces[11])
        combMy = self.xdist*(-relForces[2] - relForces[5] + relForces[8] + relForces[11])
        combMz = (self.ydist*(relForces[0] - relForces[3] + relForces[6] - relForces[10]) +
                  self.xdist*(relForces[1] + relForces[4] - relForces[7] -relForces[10]))
        
        rawForces = array([combFx,
                           combFy,
                           combFz,
                           combMx,
                           combMy,
                           combMz], Float)

        # Apply the Interaction Matrix
        intForces = matrixmultiply( rawForces, self.Int_Mat)
        
        # Apply the Orientation Matrix
        compForces = matrixmultiply(intForces, self.Orient_Mat)
        
        # And then take out the sail weight using the body angles
        # The values for the sin and cos of pitch and roll were calculated in the
        # main program so just use them here
                       
        self.CFx = compForces[0] + self.weight*sinTH
        self.CFy = compForces[1] - self.weight*sinPH*cosTH
        self.CFz = compForces[2] + self.weight*(1 - cosPH*cosTH)
        self.CMx = compForces[3] + (self.weight*sinPH*cosTH*self.armz +
                                    self.weight*self.army*(1-cosTH*cosPH))
        self.CMy = compForces[4] + (self.weight*sinTH*self.armz +
                                    self.weight*self.armx*(cosTH*cosPH -1))
        self.CMz = compForces[5] - (self.weight*sinTH*self.army +
                                    self.weight*sinPH*cosTH*self.armx)
             
        
    def addZero(self, rawdata):
        """ Adds a point to the accumulated zeros
        """
        rawForces = array([rawdata[self.Fx1_chan],
                           rawdata[self.Fy1_chan],
                           rawdata[self.Fz1_chan],
                           rawdata[self.Fx2_chan],
                           rawdata[self.Fy2_chan],
                           rawdata[self.Fz2_chan],
                           rawdata[self.Fx3_chan],
                           rawdata[self.Fy3_chan],
                           rawdata[self.Fz3_chan],
                           rawdata[self.Fx4_chan],
                           rawdata[self.Fy4_chan],
                           rawdata[self.Fz4_chan]], Float)
        
        self.zeros = self.zeros + rawForces
    
    def compZero(self, count):
        """ Computes the zero by dividing by the count"""
        
        self.zeros = self.zeros / count
        

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

	addZero() - Adds a point to the accumulated zeros array

	compZero() - Computes the average zero value for each channel


    """
    def __init__(self, name, calfile):
        """ The constructor needs the calfile parser object and the
            section name for the dyno
        """
        
        # First we get the channel assignments
        
        self.Fx_chan = calfile.add_option('Fx', type='int', keys=name).get()
        self.Fy_chan = calfile.add_option('Fy', type='int', keys=name).get()
        self.Fz_chan = calfile.add_option('Fz', type='int', keys=name).get()
        self.Mx_chan = calfile.add_option('Mx', type='int', keys=name).get()
        self.My_chan = calfile.add_option('My', type='int', keys=name).get()
        self.Mz_chan = calfile.add_option('Mz', type='int', keys=name).get()

        # Next comes the rotation angle
        
        self.angle = calfile.add_option('angle', type = 'float', keys=name).get()
        
        # Now for the interaction Matrix and Orient Matrix
        rows = []
        for i in range(1,7):
            row = []
            rowstr = calfile.add_option('int_row%d' % i, keys=name).get()
            cols = rowstr.strip().split()
            for col in cols:
                row.append(float(col))
            rows.append(row)
        
        self.Int_Mat = array(rows, Float)

        rows = []
        for i in range(1,7):
            row = []
            rowstr = calfile.add_option('orient_row%d' % i, keys=name).get()
            cols = rowstr.strip().split()
            for col in cols:
                row.append(float(col))
            rows.append(row)
        
        self.Orient_Mat = array(rows, Float)
        
        # Finally we set the channel zeros to zero
        self.zeros = array(([0.0, 0.0, 0.0, 0.0, 0.0, 0.0]), Float)
        
    def compute(self, rawdata, gains, bodyAngles):
        """ Compute the corrected forces for the current timestep using
        the interaction and orientation matricies"""
        
        # Set up raw forces
        rawForces = array([rawdata[self.Fx_chan]-self.zeros[0],
                           rawdata[self.Fy_chan]-self.zeros[1],
                           rawdata[self.Fz_chan]-self.zeros[2],
                           rawdata[self.Mx_chan]-self.zeros[3],
                           rawdata[self.My_chan]-self.zeros[4],
                           rawdata[self.Mz_chan]-self.zeros[5]], Float)

        # Apply the Interaction Matrix
        intForces = matrixmultiply( rawForces, self.Int_Mat)
        
        # Apply the Orientation Matrix
        compForces = matrixmultiply(intForces, self.Orient_Mat)
        
        # And then we map the computed forces
        self.CFx = compForces[0]
        self.CFy = compForces[1]
        self.CFz = compForces[2]
        self.CMx = compForces[3]
        self.CMy = compForces[4]
        self.CMz = compForces[5]
        
    def addZero(self, rawdata):
        """ Adds a point to the accumulated zeros
        """
        rawForces = array([rawdata[self.Fx_chan],
                           rawdata[self.Fy_chan],
                           rawdata[self.Fz_chan],
                           rawdata[self.Mx_chan],
                           rawdata[self.My_chan],
                           rawdata[self.Mz_chan]], Float)
        
        self.zeros = self.zeros + rawForces
    
    def compZero(self, count):
        """ Computes the zero by dividing by the count"""
        
        self.zeros = self.zeros / count
        
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
    def __init__(self, name, calfile):
        """ The constructor needs the calfile parser object and the
            section name for the dyno
        """
        
        # First we get the channel assignments
        
        self.Fx_chan = calfile.add_option('Fx', type='int', keys=name).get()
        self.Fy_chan = calfile.add_option('Fy', type='int', keys=name).get()
        self.Fz_chan = calfile.add_option('Fz', type='int', keys=name).get()
        self.Mx_chan = calfile.add_option('Mx', type='int', keys=name).get()
        self.My_chan = calfile.add_option('My', type='int', keys=name).get()
        self.Mz_chan = calfile.add_option('Mz', type='int', keys=name).get()
        
        # Look for the prop position zero.  Set to zero if key not found
        try:
            self.PropPosZero = calfile.add_option('position', type='int', keys=name).get()
        except:
            self.PropPosZero = 0

        # Next comes the rotation angle
        
        self.weight = calfile.add_option('weight', type = 'float', keys=name).get()
        self.arm = calfile.add_option('arm', type = 'float', keys=name).get()
        
        # Now for the interaction Matrix and Orient Matrix
        rows = []
        for i in range(1,7):
            row = []
            rowstr = calfile.add_option('int_row%d' % i, keys=name).get()
            cols = rowstr.strip().split()
            for col in cols:
                row.append(float(col))
            rows.append(row)
        
        self.Int_Mat = array(rows, Float)    
        
        rows = []
        for i in range(1,7):
            row = []
            rowstr = calfile.add_option('orient_row%d' % i, keys=name).get()
            cols = rowstr.strip().split()
            for col in cols:
                row.append(float(col))
            rows.append(row)
        
        self.Orient_Mat = array(rows, Float)
        
        # For the prop running averages we need to create some ring buffers
        self.runavg = []
        for i in range(4):
            self.runavg.append(RingBuffer(100))
        
        # initialize the rotation sensor
        self.lastpos = 0
        self.rotating = 0
        
        # Finally we set the channel zeros to zero
        self.zeros = array(([0.0, 0.0, 0.0, 0.0, 0.0, 0.0]), Float)
        
    def compute(self, rawdata, gains, bodyAngles):
        """ Compute the corrected forces for the current timestep using
        the interaction and orientation matricies
        
        Also do the rotation to model coords and subtract the prop
        weight
        """
        # Start with getting the prop rotation angle and comparing
        # with the last angle to see if we are rotating
        sinTH = bodyAngles[0]
        cosTH = bodyAngles[1]
        sinPH = bodyAngles[2]
        cosPH = bodyAngles[3]
        
        # Compute prop position.  The encoder has 20000 counts
        # per revolution and the prop position is at data location 184
        prop_pos = rawdata[184] - self.PropPosZero
        if prop_pos < 0:
                prop_pos = prop_pos + 20000
        if prop_pos > 20000:
                prop_pos = prop_pos - 20000
        rot_angle = (prop_pos * .01800)
        sinR = sin(radians(rot_angle))
        cosR = cos(radians(rot_angle))
        
        if rot_angle != self.lastpos:
            self.rotating = 1
        else:
            self.rotating = 0
        self.lastpos = rot_angle
        
        # Add the points to the running averages
        self.runavg[0].append(rawdata[self.Fx_chan])
        self.runavg[1].append(rawdata[self.Fy_chan])
        self.runavg[2].append(rawdata[self.Mx_chan])
        self.runavg[3].append(rawdata[self.My_chan])
        
        # Set up raw forces - Zero subtraction depends on if we are rotating 
        if self.rotating:           # Rotating prop
            rawForces = array([rawdata[self.Fx_chan]-self.runavg[0].average(),
                               rawdata[self.Fy_chan]-self.runavg[1].average(),
                               rawdata[self.Fz_chan]-self.zeros[2],
                               rawdata[self.Mx_chan]-self.runavg[2].average(),
                               rawdata[self.My_chan]-self.runavg[3].average(),
                               rawdata[self.Mz_chan]-self.zeros[5]], Float)
            
        else:                       # static prop
            rawForces = array([rawdata[self.Fx_chan]-self.zeros[0],
                               rawdata[self.Fy_chan]-self.zeros[1],
                               rawdata[self.Fz_chan]-self.zeros[2],
                               rawdata[self.Mx_chan]-self.zeros[3],
                               rawdata[self.My_chan]-self.zeros[4],
                               rawdata[self.Mz_chan]-self.zeros[5]], Float)

        # Apply the Interaction Matrix
        intForces = matrixmultiply( rawForces, self.Int_Mat)
        
        # Apply the Orientation Matrix
        compForces = matrixmultiply(intForces, self.Orient_Mat)
        
        # Now we need to rotate to the body coordinates
        
        
        bodyFx = compForces[0]
        bodyFy = cosR * compForces[1] - sinR * compForces[2]
        bodyFz = sinR * compForces[1] + cosR * compForces[2]
        bodyMx = compForces[3]
        bodyMy = cosR * compForces[4] - sinR * compForces[5]
        bodyMz = sinR * compForces[4] + cosR * compForces[5]
                       
        
        # And then we subtract weight and map the computed forces
        self.CFx = bodyFx + self.weight * sinTH
        self.CFy = bodyFy - self.weight * sinPH * cosTH
        self.CFz = bodyFz - self.weight * cosPH * cosTH
        self.CMx = bodyMx
        self.CMy = bodyMy + self.weight * self.arm * cosPH * cosTH
        self.CMz = bodyMz - self.weight * self.arm * sinPH * cosTH
        
    def addZero(self, rawdata):
        """ Adds a point to the accumulated zeros
        """
        rawForces = array([rawdata[self.Fx_chan],
                           rawdata[self.Fy_chan],
                           rawdata[self.Fz_chan],
                           rawdata[self.Mx_chan],
                           rawdata[self.My_chan],
                           rawdata[self.Mz_chan]], Float)
        
        self.zeros = self.zeros + rawForces
    
    def compZero(self, count):
        """ Computes the zero by dividing by the count"""
        
        # Really need to take the prop weight out of here by using
        # the inverse of the Int matrix.  This only affects the value
        # when the prop is not rotating
        
        self.zeros = self.zeros / count
 
