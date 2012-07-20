from optitrak_stream import OptitrakStream
from asynch_dispatch import AsynchDispatch
from file_stream import FileStream
from RobotGUI import GUIStream
from basestation_stream import BasestationStream
from callback_stream import CallbackStream
from struct import pack, unpack
from lib import command
from or_helpers_stream import HelpersStream
from run_commands import RunCommands

import GUI_helpers as gh

import sys, glob
import time

imudata = []

def xb_send(val):
	outgoing = ('packet',val.data[0], val.data [1])
	b.put(outgoing)

def OptitrakUpdate(val):
	o.update(val)

def imudataUpdate(val):
	h.setImuData(val.data[0], val.data[1])

def setupFile(val):
	file = h.findFileName()
	h.setFileName(file)
	gh.setDataFileName(file)

def getnumSamples(val):
	samples = h.calcNumSamples(val.data)

def setMotor_Gains(val):
	h.setMotorGainsSet()

def setSteer_Gains(val):
	h.setSteeringGainsSet()

def setSteer_Rate(val):
	h.setSteeringRateSet()

def setNumSamples(val):
	t.setNumSamples(val.data)

def setCount2Deg(val):
	h.setCount2Deg(val.data)

def setBytesIn(val):
	h.setBytesIn()

def setFlashErased(val):
	h.setFlashErase()

def runRobot(val):
	t.setAddr(val.data[0])
	t.setMove(val.data[1])
	t.runCommands()

def basestationReset(val):
	h.resetRobot(val.data)

def basestationMotor(val):
	print 'call motor'
	h.setMotorGains(val.data[0], val.data[1])

def basestationThrot(val):
	print 'call throt'
	h.setMotorSpeeds(val.data[0], val.data[1], val.data[2])

def basestationSteer(val):
	print 'call gains'
	h.put([val.type, val.data[0], val.data[1]])

def basestationTurning(val):
	print 'call turning'
	h.put([val.type, val.data[0], val.data[1]])

def basestationMove(val):
	print 'call move'
	h.put([val.type,val.data[0], val.data[1]])

def basestationQuit(val):
	input_data = ('quit','quit')
	b.put(input_data)

def stream_telemetry(val):
	numSamples = 100
	h.startTelemetryStream(val.data)

def robotData(val):
	cal.xbee_received(val.data[2])

def callback_stream(val):
	f = open('streaming_data.txt', 'a')
	f.write(val.data + '\n')
	f.close()

def eraseFlashMemory(val):
	print ('erase flash called')
	h.put([val.type, val.data[0], val.data[1]])

def saveTelemetry(val):
	print ('save telemetry called')
	h.put([val.type, val.data[0], val.data[1]])

def readTelemetry(val):
	h.put([val.type, val.data[0], val.data[1]])

g = GUIStream(sinks = {'reset':[basestationReset], 'quit':[basestationQuit],
						 'motor':[basestationMotor], 'throt_speed':[basestationThrot],
						 'file':[setupFile], 'stream_telem':[stream_telemetry], 'imu_samples':[getnumSamples], 
						 'run_commands':[runRobot]}, callbacks = None, autoStart = False)

#o = OptitrakStream(sinks = {'optitrak_data':[OptitrakUpdate]}, autoStart = False)

#f = FileStream(sinks = {'file_line':[OptitrakUpdate]}, autoStart = False)

#c = CalcStream(sinks = {'optitrak_euler':[FileUpdate]}, autoStart = False)

b = BasestationStream(sinks = {'robot_data':[robotData]}, callbacks = None)

cal = CallbackStream(sinks = {'streaming_data':[callback_stream], 'special_telem':[imudataUpdate], 
										'steering_rate_set':[setSteer_Rate], 'motor_gains_set':[setMotor_Gains], 
										'steering_gains_set':[setSteer_Gains], 'bytes_in':[setBytesIn], 'flash_erased':[setFlashErased],
										'turning_rate':[setCount2Deg]}, callbacks = None)

h = HelpersStream(sinks = {'xb_send':[xb_send], 'num_samples':[setNumSamples]}, callbacks = None, fileName = None)

t = RunCommands(sinks = {'erase_flash':[eraseFlashMemory], 'save_telem':[saveTelemetry],
							 'steer_gains':[basestationSteer], 'turning_rate':[basestationTurning],
							 'read_telem':[readTelemetry], 'move':[basestationMove]}, callbacks = None, move = None, addr = None)

time.sleep(0.5)

while(True):
  try:
    time.sleep(0.1)
  except KeyboardInterrupt:
    sys.exit()