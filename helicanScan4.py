from PyTango import *
from scipy import interpolate
import time
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtCore import SIGNAL, QThread


class HelicanScan(QThread):
    # A thread is started by calling QThread.start() never by calling run() directly!
    def __init__(self, motorSmpx, motorSmpy, motorPhiy, motorPhi, numberOfImages, exposureTime, anglePerImage,
		         positionsSmpx, positionsSmpy, positionsPhiy, positionPhi):
        QThread.__init__(self)
		self.motorSmpx = motorSmpx
		self.motorSmpy = motorSmpy
		self.motorPhiy = motorPhiy
		self.motorPhi = motorPhi
		self.mumberOfImages = numberOfImages
		self.exposureTime = exposureTime
		self.anglePerImage = anglePerImage
		self.positionsSmpx = positionsSmpx
		self.positionsSmpy = positionsSmpy
		self.positionsPhiy = positionsPhiy
		self.positionPhi = positionPhi
		self.velocityPhy = self.motorPhiy.SlewRate
		self.f1 = None #equation posSmpx = f1(posPhiy)
		self.f2 = None #equation posSmpy = f2(posPhiy)
		self.f3 = None #equation posPhi = f3(posPhiy)
		self.running = True
		if len(self.positionsSmpx) != len(self.positionsPhiy):
			print "The length of Phiy must be equal to the length of Smpx"
			self.stop()
		if len(self.positionsSmpy) != len(self.positionsPhiy):
			print "The length of Phiy must be equal to the length of Smpy"
			self.stop()
		if self.running:
			self.prepare()
				
	def prepare(self):
        print "Moving motors to their start positions..."
		self.motorSmpx.Position = self.positionsSmpx[0]
		self.motorSmpy.Position = self.positionsSmpy[0]
		self.motorPhiy.Position = self.positionsPhiy[0]
		self.motorPhi = self.positionPhi
		while self.motorSmpx.state() == PyTango.DevState.MOVING:
			time.sleep(0.01)
		while self.motorSmpy.state() == PyTango.DevState.MOVING:
			time.sleep(0.01)
		while self.motorPhiy.state() == PyTango.DevState.MOVING:
			time.sleep(0.01)
		while self.motorPhi.state() == PyTango.DevState.MOVING:
			time.sleep(0.01)
		print "Motors on the start positions"
		
		self.motorPhiy.SlewRate = abs(self.positionsPhiy[0] - self.positionsPhiy[-1]) / (self.numberOfImages * self.exposureTime)
		
		positionsPhiyPhi = [positionsPhiy[0], positionsPhiy[-1]]
		positionsPhi=[self.positionPhi, self.positionPhi + numberOfImages * self.anglePerImage]
		
		self.f1 = interpolate.interp1d(self.positionsPhiy, self.positionsSmpx, kind = 'linear')
		self.f2 = interpolate.interp1d(self.positionsPhiy, self.positionsSmpy, kind = 'linear')
		self.f3 = interpolate.interp1d(self.positionsPhiyPhi, self.positionsPhi, kind = 'linear')
		
	def stop(self):
        print "Motor thread: Stopping thread"
        self.running: = False
        self.wait() # waits until run stops on his own

    def run(self):
    	print "Motor thread: started"
    	while self.running:
    		currPosPhiy = self.motorPhiy.Position
			currPosSmpx = self.f1(currPosPhiy)
			currPosSmpy = self.f2(currPosPhiy)
			currPosPhi = self.f3(currPosPhiy)
			if self.motorSmpx.state() != PyTango.DevState.MOVING:
				self.motorSmpx.Position = currPosSmpx
			if self.motorSmpy.state() != PyTango.DevState.MOVING:
				self.motorSmpy.Position = currPosSmpy
			if self.motorPhi.state() != PyTango.DevState.MOVING:
				self.motorPhi.Position = currPosPhi
		self.motorPhiy.SlewRate = self.velocityPhy


"""example how to use helican scan thread"""
myThread = HelicanScan(motorSmpx, motorSmpy, motorPhiy, motorPhi, numberOfImages, exposureTime, anglePerImage,
				       positionsSmpx, positionsSmpy, positionsPhiy, positionPhi)
myThread.start()
motorPhiy.Position = positionsPhiy[-1]
while motorPhiy.state() == PyTango.DevState.MOVING:
	time.sleep(0.01)
myThread.stop()
