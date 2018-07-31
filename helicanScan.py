import PyTango
#import sys
#import serial
#import serial.tools.list_ports
#from PyQt4 import QtGui
from PyQt4.QtCore import QThread, SIGNAL
import time
import numpy as np
from scipy import interpolate

x = [0.0, 100.0]   
y = [0.0, 100.0]
z = [0.0, 100.0]


class continuousFocus(QThread):
    def __init__(self, motorX, motorY, motorZ, xp, yp, zp):
        QThread.__init__(self)
        self.motorX = motorX
        self.motorX = motorY
        self.motorX = motorZ
        self.xp = xp
        self.yp = yp
        self.zp = zp
        self.type = type
        self.f1 = None
        self.f2 = None
        self.calculation()
        self.running = True
    def calculation(self):
        self.f1 = interpolate.interp1d(self.xp, self.yp, kind = 'linear')
        self.f2 = interpolate.interp1d(self.xp, self.zp, kind = 'linear')
    def run(self):
        print "Starting Thread"
        while self.running:
            x = self.motorX.Position
            y = self.f1(x)
            z = self.f2(y)
            self.motorY.Position = y
            self.motorZ.Position = z
            time.sleep(0.01)
    def stop(self):
        self.running = False
        print "Stop Thread"
    

motorX = PyTango.DeviceProxy('p11/motor/mexp3.06')
motorY = PyTango.DeviceProxy('p11/motor/mexp3.07')
motorZ = PyTango.DeviceProxy('p11/motor/mexp3.08')
motorGonio = PyTango.DeviceProxy('p11/motor/mexp3.09')

motorX.Position = x[0]
motorY.Position = y[0]
motorZ.Position = z[0]

t = abs(x[0] - x[1]) / motorX.Velocity
rotations = 20

timeRotation = t / rotations
motorGonio.Velocity = 360 / timeRotation

myThread = continuousFocus(motorX, motorY, motorZ, xp, yp, zp)
myThread.start()

motorGonio.Position = motorGonio.Position + 360 * rotations
motorX.Position = x[1]
while motorX.state() == PyTango.DevState.MOVING:
    time.sleep(0.01)
motorGonio.Stop()
myThread.stop()