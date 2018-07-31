"""Macro which do helican scan."""

from sardana.macroserver.macro import Macro, Type
import PyTango
import os
from scipy import interpolate

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
                     ["velPhi", Type.Float, None, "velocity for motor phi"]]

	self.smpx = self.getMotor("sampx")
    self.smpy = self.getMotor("sampy")
    self.phiy = self.getMotor("phiy")
    self.phi = self.getMotor("phi")
    self.phi.set_velocity(velPhi)

	def def prepare(self, startPosSmpx, endPosSmpx, startPosSmpy, endPosSmpy, startPosPhiy, endPosPhiy, expTime, velPhi):
        self.smpx.move(startPosSmpx)
        self.smpy.move(startPosSmpy)
        self.phiy.move(startPosPhiy)

        positionsSmpx = [startPosSmpx, endPosSmpx]
        positionsSmpy = [startPosSmpy, endPosSmpy]
        positionsPhiy = [startPosPhiy, endPosPhiy]
        f1 = interpolate.interp1d(positionsPhiy, positionsSmpx, kind = 'linear') #find equation posSmpx = f1(posPhiy)
        f2 = interpolate.interp1d(positionsPhiy, positionsSmpy, kind = 'linear') #find equation posSmpy = f2(posPhiy)

        accPhiy = self.phiy.read_acceleration()
        velPhiy = self.phiy.set_velocity(abs(startPosPhiy - endPosPhiy) / expTime)
        disAccPhiy = (velPhiy ** 2) / (2 * accPhiy)
        disPhiy = abs(startPosPhiy - endPosPhiy) - 2 * disAccPhiy
        timePhiy = disPhiy / velPhiy

        if startPosPhiy < endPosPhiy:
            disAccSmpx = abs(startPosSmpx - f1(startPosPhiy + disAccPhiy))
        else:
            disAccSmpx = abs(startPosSmpx - f1(startPosPhiy - disAccPhiy))
        disSmpx = abs(startPosSmpx - endPosSmpx) - 2 * disAccSmpx
        velSmpx = disSmpx / timePhiy
        accSmpx = (velSmpx ** 2) / (2 * disAccSmpx)
        self.smpx.set_velocity(velSmpx)
        self.smpx.set_acceleration(accSmpx)
        self.smpx.set_deceleration(accSmpx)

        if startPosPhiy < endPosPhiy:
            disAccSmpy = abs(startPosSmpy - f2(startPosPhiy + disAccPhiy))
        else:
            disAccSmpy = abs(startPosSmpy - f2(startPosPhiy - disAccPhiy))
        disSmpy = abs(startPosSmpy - endPosSmpy) - 2 * disAccSmpy
        velSmpy = disSmpy / timePhiy
        accSmpy = (velSmpy ** 2) / (2 * disAccSmpy)
        self.smpy.set_velocity(velSmpy)
        self.smpy.set_acceleration(accSmpy)
        self.smpy.set_deceleration(accSmpy)

    def run(self, startPosSmpx, endPosSmpx, startPosSmpy, endPosSmpy, startPosPhiy, endPosPhiy, expTime, velPhi):
        self.smpx.move(endPosSmpx)
        self.smpy.move(endPosSmpy)
        self.phiy.move(endPosPhiy)
        self.phi.move(velPhi * expTime)


