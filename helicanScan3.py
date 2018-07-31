import PyTango
#import os
from scipy import interpolate
import time
#import numpy as np
import threading
#import signal
#signal.signal(signal.SIGINT, signal.SIG_DFL)

class continuousFocus(threading.Thread):
	def __init__(self, smpx, smpy, phiy, phi, f1, f2, f3):
		threading.Thread.__init__(self)
		self.smpx = smpx
		self.smpy = smpy
		self.phiy = phiy
		self.phi = phi
		self.f1 = f1
		self.f2 = f2
		self.f3 = f3
		self.running = True
	def run(self):
		#self.output("Starting continuous Thread")
		while self.running:
			currPosPhiy = self.phiy.Position
			currPosSmpx = self.f1(currPosPhiy)
			currPosSmpy = self.f2(currPosPhiy)
			currPosPhi = self.f3(currPosPhiy)
			if self.smpx.state() != PyTango.DevState.MOVING:
				self.smpx.Position = currPosSmpx
			if self.smpy.state() != PyTango.DevState.MOVING:
				self.smpy.Position = currPosSmpy
			#if self.phi.state() != PyTango.DevState.MOVING:
				#self.phi.Position = currPosPhi
			#time.sleep(0.01)
	def stop(self):
		self.running = False
		#self.output("Stop continuous Thread")

positionsSmpx = [-166, -138]
positionsSmpy = [850, 916]
positionsPhiy = [2281, 2586]

endPosPhiy = 2586

startPosSmpx = -166
startPosSmpy = 850
startPosPhiy = 2281

smpx = PyTango.DeviceProxy("p11/piezomotor/eh.4.02")
smpy = PyTango.DeviceProxy("p11/piezomotor/eh.4.01")
phiy = PyTango.DeviceProxy("p11/motor/eh.3.12")
phi = PyTango.DeviceProxy("p11/servomotor/eh.1.01")

#print smpx.Position
#print smpy.Position
#print phiy.Position
#print phi.Position

print "Moving motors to their start positions..."
smpx.Position = startPosSmpx
smpy.Position = startPosSmpy
phiy.Position = startPosPhiy
phi.Position = 0
while smpx.state() == PyTango.DevState.MOVING:
    time.sleep(0.01)
while smpy.state() == PyTango.DevState.MOVING:
	time.sleep(0.01)
while phiy.state() == PyTango.DevState.MOVING:
	time.sleep(0.01)
while phi.state() == PyTango.DevState.MOVING:
	time.sleep(0.01)
print "Motors on the start positions"

phiy.SlewRate = 50

f1 = interpolate.interp1d(positionsPhiy, positionsSmpx, kind = 'linear') #find equation posSmpx = f1(posPhiy)
f2 = interpolate.interp1d(positionsPhiy, positionsSmpy, kind = 'linear') #find equation posSmpy = f2(posPhiy)
#f3 = interpolate.interp1d(positionsPhiy, positionsPhi, kind = 'linear') #find equation posPhi = f3(posPhiy)
f3 = f2

"""move all motors to their end positions"""
print "Moving motors to their end positions..."
myThread = continuousFocus(smpx, smpy, phiy, phi, f1, f2, f3)
myThread.start()
phi.Position = 6000
phiy.Position = endPosPhiy
while phiy.state() == PyTango.DevState.MOVING:
	time.sleep(0.01)
phi.AbortMove()
myThread.stop()
phiy.SlewRate = 5000
print "Finished"
