"""Macro which does helican scan."""

from sardana.macroserver.macro import Macro, Type
import PyTango
#import os
from scipy import interpolate
import time
#import numpy as np
import threading
#import signal
#signal.signal(signal.SIGINT, signal.SIG_DFL)


__all__ = ["helicanscan2"]

class helicanscan2(Macro):
	"""Helican scan."""

	param_def = [["startPosSmpx", Type.Float, None, "start position for motor smpx"], 
                     ["endPosSmpx", Type.Float, None, "end position for motor smpx"],
                     ["startPosSmpy", Type.Float, None, "start position for motor smpy"],
                     ["endPosSmpy", Type.Float, None, "end position for motor smpy"],
                     ["startPosPhiy", Type.Float, None, "start position for motor phiy"],
                     ["endPosPhiy", Type.Float, None, "end position for motor phiy"],
                     ["expTime", Type.Float, None, "exposure time"],
                     ["velPhi", Type.Float, None, "velocity for motor phi"],
		     ["typeOfMotor", Type.Integer, 0, "0 for motor, 1 for sardana pseudo motor"]]

	def prepare(self, startPosSmpx, endPosSmpx, startPosSmpy, endPosSmpy, startPosPhiy, endPosPhiy, expTime, velPhi, typeOfMotor):
		"""move all motors to their start positions, calculate accelerations and velocities for motors"""
		if expTime <= 0 :
			raise Exception("Exposure time is not correct")

		#self.smpx = PyTango.DeviceProxy("exp_dmy01")
		self.smpx = PyTango.DeviceProxy("motor/galil_dmc_eh4/2")
		#self.smpy = PyTango.DeviceProxy("exp_dmy02")
		self.smpy = PyTango.DeviceProxy("motor/galil_dmc_eh4/1")
		#self.phiy = PyTango.DeviceProxy("exp_dmy04")
		self.phiy = PyTango.DeviceProxy("motor/omsvme58_eh3/12")
		self.velGlobPhiy = self.phiy.Velocity
		self.accGlobPhiy = self.phiy.Acceleration
		self.phi = PyTango.DeviceProxy("exp_dmy05")
		self.velGlobPhi = self.phi.Velocity
		self.accGlobPhi = self.phi.Acceleration
		self.phi.Velocity = velPhi

		"""only for sardana pseudo motors"""
		self.accGlobSarPhiy = self.velGlobPhiy / self.accGlobPhiy
		self.accGlobSarPhi = velPhi / self.accGlobPhi

		self.output("Moving motors to their start positions...")
		self.smpx.Position = startPosSmpx
		self.smpy.Position = startPosSmpy
		self.phiy.Position = startPosPhiy
		while self.smpx.state() == PyTango.DevState.MOVING:
			time.sleep(0.01)
		while self.smpy.state() == PyTango.DevState.MOVING:
			time.sleep(0.01)
		while self.phiy.state() == PyTango.DevState.MOVING:
			time.sleep(0.01)
		while self.phi.state() == PyTango.DevState.MOVING:
			time.sleep(0.01)
		self.output("Motors on the start positions")

		positionsSmpx = [startPosSmpx, endPosSmpx]
		positionsSmpy = [startPosSmpy, endPosSmpy]
		positionsPhiy = [startPosPhiy, endPosPhiy]

		if typeOfMotor == 1:
			moveTime = ((self.velGlobPhiy ** 2) + self.accGlobSarPhiy * abs(startPosPhiy - endPosPhiy)) / (self.accGlobSarPhiy * self.velGlobPhiy)
			self.disPhi =  (self.accGlobSarPhi * moveTime * velPhi - (velPhi ** 2)) / self.accGlobSarPhi
		else:
			moveTime = ((self.velGlobPhiy ** 2) + self.accGlobPhiy * abs(startPosPhiy - endPosPhiy)) / (self.accGlobPhiy * self.velGlobPhiy)
			self.disPhi =  (self.accGlobPhi * moveTime * velPhi - (velPhi ** 2)) / self.accGlobPhi
		positionsPhi = [self.phi.Position, self.phi.Position + self.disPhi]
		self.f1 = interpolate.interp1d(positionsPhiy, positionsSmpx, kind = 'linear') #find equation posSmpx = f1(posPhiy)
		self.f2 = interpolate.interp1d(positionsPhiy, positionsSmpy, kind = 'linear') #find equation posSmpy = f2(posPhiy)
		self.f3 = interpolate.interp1d(positionsPhiy, positionsPhi, kind = 'linear') #find equation posPhi = f3(posPhiy)

	def run(self, startPosSmpx, endPosSmpx, startPosSmpy, endPosSmpy, startPosPhiy, endPosPhiy, expTime, velPhi, typeOfMotor):
		"""move all motors to their end positions"""
		self.output("Moving motors to their end positions...")
		myThread = continuousFocus(self.smpx, self.smpy, self.phiy, self.phi, self.f1, self.f2, self.f3)
		myThread.start()
		self.phiy.Position = endPosPhiy
		while self.phiy.state() == PyTango.DevState.MOVING:
			time.sleep(0.01)
			"""currPosPhiy = self.phiy.Position
			currPosSmpx = self.f1(currPosPhiy)
			currPosSmpy = self.f2(currPosPhiy)
			currPosPhi = self.f3(currPosPhiy)
			if self.smpx.state() != PyTango.DevState.MOVING:
				self.smpx.Position = currPosSmpx
			if self.smpy.state() != PyTango.DevState.MOVING:
				self.smpy.Position = currPosSmpy
			if self.phi.state() != PyTango.DevState.MOVING:
				self.phi.Position = currPosPhi"""
		myThread.stop()
		self.phi.Velocity = self.velGlobPhi
		self.output("Finished")

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
			if self.phi.state() != PyTango.DevState.MOVING:
				self.phi.Position = currPosPhi
			#time.sleep(0.01)
	def stop(self):
		self.running = False
		#self.output("Stop continuous Thread")
