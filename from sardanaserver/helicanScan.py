"""Macro which does helican scan."""

from sardana.macroserver.macro import Macro, Type
import PyTango
import os
from scipy import interpolate
import time

__all__ = ["helicanscan"]

class helicanscan(Macro):
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

		self.smpx = PyTango.DeviceProxy("exp_dmy01")
		self.velGlobSmpx = self.smpx.Velocity
		self.accGlobSmpx = self.smpx.Acceleration
		self.smpy = PyTango.DeviceProxy("exp_dmy02")
		self.velGlobSmpy = self.smpy.Velocity
		self.accGlobSmpy = self.smpy.Acceleration
		self.phiy = PyTango.DeviceProxy("exp_dmy04")
		self.velGlobPhiy = self.phiy.Velocity
		self.accGlobPhiy = self.phiy.Acceleration
		self.phi = PyTango.DeviceProxy("exp_dmy05")
		self.velGlobPhi = self.phi.Velocity
		self.accGlobPhi = self.phi.Acceleration
		self.phi.Velocity = velPhi

		"""only for sardana pseudo motors"""
		self.accGlobSarSmpx = self.velGlobSmpx / self.accGlobSmpx
		self.accGlobSarSmpy = self.velGlobSmpy / self.accGlobSmpy
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
		f1 = interpolate.interp1d(positionsPhiy, positionsSmpx, kind = 'linear') #find equation posSmpx = f1(posPhiy)
		f2 = interpolate.interp1d(positionsPhiy, positionsSmpy, kind = 'linear') #find equation posSmpy = f2(posPhiy)

		if typeOfMotor == 1:
			disAccPhiy = (self.velGlobPhiy ** 2) / (2 * self.accGlobSarPhiy)
		else:
			disAccPhiy = (self.velGlobPhiy ** 2) / (2 * self.accGlobPhiy)
		disPhiy = abs(startPosPhiy - endPosPhiy) - 2 * disAccPhiy
		if (disPhiy <= 0):
			raise Exception("Can not reach Velocity, try to decrease Velocity or increase Acceleration")
		timePhiy = disPhiy / self.velGlobPhiy

		velSmpx, accSmpx = self.calcAccAndVeloc(startPosPhiy, endPosPhiy, disAccPhiy, timePhiy, f1, startPosSmpx, endPosSmpx, typeOfMotor)
		if (velSmpx > self.velGlobSmpx) or (accSmpx > self.accGlobSmpx):
			raise Exception("Velocity or Acceleration for motor smpx is exceeded, try to decrease Velocity or Acceleration for motor phiy")
		self.smpx.Velocity = velSmpx
		self.smpx.Acceleration = accSmpx
		self.smpx.Deceleration = accSmpx

		velSmpy, accSmpy = self.calcAccAndVeloc(startPosPhiy, endPosPhiy, disAccPhiy, timePhiy, f2, startPosSmpy, endPosSmpy, typeOfMotor)
		if (velSmpy > self.velGlobSmpy) or (accSmpy > self.accGlobSmpy):
			raise Exception("Velocity or Acceleration for motor smpy is exceeded, try to decrease Velocity or Acceleration for motor phiy")
		self.smpy.Velocity = velSmpy
		self.smpy.Acceleration = accSmpy
		self.smpy.Deceleration = accSmpy
		
		if typeOfMotor == 1:
			moveTime = ((self.velGlobPhiy ** 2) + self.accGlobSarPhiy * abs(startPosPhiy - endPosPhiy)) / (self.accGlobSarPhiy * self.velGlobPhiy)
			self.disPhi =  (self.accGlobSarPhi * moveTime * velPhi - (velPhi ** 2)) / self.accGlobSarPhi
		else:
			moveTime = ((self.velGlobPhiy ** 2) + self.accGlobPhiy * abs(startPosPhiy - endPosPhiy)) / (self.accGlobPhiy * self.velGlobPhiy)
			self.disPhi =  (self.accGlobPhi * moveTime * velPhi - (velPhi ** 2)) / self.accGlobPhi

	def calcAccAndVeloc(self, startPosPhiy, endPosPhiy, disAccPhiy, timePhiy, f, startPosSmp, endPosSmp, typeOfMotor):
		"""calculate accelerations and velocities for sample motors"""
		if startPosPhiy < endPosPhiy:
			disAccSmp = abs(startPosSmp - f(startPosPhiy + disAccPhiy))
		else:
			disAccSmp = abs(startPosSmp - f(startPosPhiy - disAccPhiy))
		disSmp = abs(startPosSmp - endPosSmp) - 2 * disAccSmp
		velSmp = disSmp / timePhiy
		accSmp = (velSmp ** 2) / (2 * disAccSmp)
		if typeOfMotor == 1:
			accSmp = velSmp / accSmp
		return velSmp, accSmp

	def run(self, startPosSmpx, endPosSmpx, startPosSmpy, endPosSmpy, startPosPhiy, endPosPhiy, expTime, velPhi, typeOfMotor):
		"""move all motors to their end positions"""
		self.output("Moving motors to their end positions...")
		start = time.time()
		self.smpx.Position = endPosSmpx
		self.smpy.Position = endPosSmpy
		self.phiy.Position = endPosPhiy
		self.phi.Position = self.phi.Position + self.disPhi
		while self.smpx.state() == PyTango.DevState.MOVING:
			time.sleep(0.01)
		while self.smpy.state() == PyTango.DevState.MOVING:
			time.sleep(0.01)
		while self.phiy.state() == PyTango.DevState.MOVING:
			time.sleep(0.01)
		while self.phi.state() == PyTango.DevState.MOVING:
			time.sleep(0.01)
		
		self.smpx.Velocity = self.velGlobSmpx
		self.smpx.Acceleration = self.accGlobSmpx
		self.smpy.Velocity = self.velGlobSmpy
		self.smpy.Acceleration = self.accGlobSmpy
		self.phi.Velocity = self.velGlobPhi
		self.output("Finished")
