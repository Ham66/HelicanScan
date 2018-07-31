from PyTango import *
from scipy import interpolate
import time
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtCore import SIGNAL, QThread


class HelicanScanThread(QThread):
    # A thread is started by calling QThread.start() never by calling run() directly!
    def __init__(self, f1, f2, f3, goniometerThread):
        QThread.__init__(self)
		self.f1 = f1 #equation posSmpx = f1(posPhiy)
		self.f2 = f2 #equation posSmpy = f2(posPhiy)
		self.f3 = f3 #equation posPhi = f3(posPhiy)
        self.goniometerThread = goniometerThread
		self.running = True
			
	def stop(self):
        print "HelicanScanThread: Stopping thread"
        self.running: = False
        self.wait() # waits until run stops on his own

    def run(self):
    	print "HelicanScanThread: started"
    	while self.running:
    		currPosPhiy = self.goniometerThread.currentPositionKohzuGoniometerY
			currPosSmpx = self.f1(currPosPhiy)
			currPosSmpy = self.f2(currPosPhiy)
			currPosPhi = self.f3(currPosPhiy)
            if self.goniometerThread.stateFlexureX != "MOVING":
			    self.goniometerThread.setPositionFlexureX = currPosSmpx
			if self.goniometerThread.stateFlexureY != "MOVING":
			    self.goniometerThread.setPositionFlexureY = currPosSmpy
			if self.goniometerThread.stateGoniometer != "MOVING":
				self.goniometerThread.setAngleNoMod = currPosPhi
