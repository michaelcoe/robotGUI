#Helps with GUI Elements
from or_helpers_stream import HelpersStream
import wx.grid as gridlib
import time
import threading
import shared

import numpy as np

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.backends.backend_wx import NavigationToolbar2Wx

from matplotlib.figure import Figure

## Constants
###
MOVE_SEG_CONSTANT = 0
MOVE_SEG_RAMP = 1
MOVE_SEG_SIN = 2
MOVE_SEG_TRI = 3
MOVE_SEG_SAW = 4
MOVE_SEG_IDLE = 5

##
STEER_MODE_DECREASE = 0
STEER_MODE_INCREASE = 1
STEER_MODE_SPLIT = 2

global dataFileName

def setDataFileName(file):
	dataFileName = file

def getDataFileName():
	return dataFileName

	#grabs and sets up a move q from the grid on the main UI
def setupMoveq (inputGrid):
	r = inputGrid.GetNumberRows()
	a = []
	for i in range(0,r):
		for j in range(0,7):
			a.append(inputGrid.GetCellValue(i,j))
	a = [int(i) for i in a]
	b = [inputGrid.GetNumberRows()]
	move = b + a
		
	return move

	#sets the presets for the grid on the main UI   
def gridPreset(inputGrid, select):
	r = inputGrid.GetNumberRows()
	s = 0
	inputGrid.ClearGrid()
	constant = ["0", "0", "1000", "0", "0", "0", "0",
	 					 "100", "100", "5000", "0", "0", "0",
						 "0", "50", "50", "1000", "0", "0", "0", "0"]
	ramp = ["0", "0", "500", "1", "300", "300", "0",
				 "150", "150", "3000", "0", "0", "0", "0",
				 "150", "150", "500", "1", "-300",  "-300", "0"]
	sine = ["76", "76", "2000", "2", "75", "1000", "1.45",
				 "75", "75", "2000", "0", "0", "0", "0"]
	if select == 0:
		for i in range(0,r):
			for j in range(0,7):
				if(s < 21):
					inputGrid.SetCellValue(i,j, constant[s])
					s += 1
	elif select == 1:
			for i in range(0,r):
				for j in range(0,7):
					if(s < 21):
						inputGrid.SetCellValue(i,j, ramp[s])
						s += 1
	elif select == 2:
			for i in range(0,r):
				for j in range(0,7):
					if(s < 14):
						inputGrid.SetCellValue(i,j, sine[s])
						s += 1
	s = 0
	
def plotGraph(figure):

	dataFileName = getDataFileName()

	axes1 = figure.add_subplot(221)
	axes2 = figure.add_subplot(222)
	axes3 = figure.add_subplot(223)		
	axes4 = figure.add_subplot(224)
	
	axes1.set_autoscale_on(True)
	axes2.set_autoscale_on(True)
	axes3.set_autoscale_on(True)
	axes3.set_autoscale_on(True)
	
	axes1.set_ylabel("Back EMF (V)")
	axes1.set_xlabel("time(s)")
	axes3.set_ylabel("Accelerator")
	axes3.set_xlabel("time(s)")
	axes4.set_ylabel("Gyro")
	axes4.set_xlabel("time(s)")
	
	time = np.loadtxt(dataFileName, unpack=True, usecols=[0])
	Gyrox, Gyroy, Gyroz = np.loadtxt(dataFileName,unpack=True, usecols=[5,6,7])
	XLx, XLy, XLz = np.loadtxt(dataFileName, unpack=True, usecols=[8,9,10])
	LBemf, RBemf = np.loadtxt(dataFileName, unpack=True, usecols=[11,12])
	x = 0
	for x in range(len(time)):
		time[x] = (time[x] / 1000000)
	
		axes1.plot(time,LBemf, color='blue')
		axes1.plot(time,RBemf, color='red')
		axes2.plot(t,s)
		axes3.plot(time,XLx,color='blue')
		axes3.plot(time,XLy,color='yellow')
		axes3.plot(time,XLz,color='red')
		axes4.plot(time,Gyrox,color='blue')
		axes4.plot(time,Gyroy,color='yellow')
		axes4.plot(time,Gyroz,color='red')
		
	return figure