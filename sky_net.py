from optitrak_stream import OptitrakStream
from asynch_dispatch import AsynchDispatch
from file_stream import FileStream
from RobotGUI import GUIStream
from basestation_stream import BasestationStream
from callback_stream import CallbackStream
from struct import pack, unpack
from lib import command
from or_helpers_stream import HelpersStream

import sys, glob
import time

imudata = []
samples = 0
file = ''

def xb_send(val):
	outgoing = ('packet',val.data[0], val.data [1])
	b.put(outgoing)

def OptitrakUpdate(val):
	o.update(val)

def imudataUpdate(val):
	data = val.data

def setupFile(val):
	file = h.findFileName()
	print file

def getnumSamples(val):
	samples = h.calcNumSamples(val.data)

def basestationReset(val):
	addr = val.data
	h.resetRobot(addr)

def basestationMotor(val):
	h.setMotorGains(val.data[0], val.data[1])

def basestationThrot(val):
	h.setMotorSpeeds(val.data[0], val.data[1], val.data[2])

def basestationSteer(val):
	h.setSteeringGains(val.data[0], val.data[1])

def basestationTurning(val):
	h.setSteeringRate(val.data[0], val.data[1])

def basestationMove(val):
	h.sendMoveQueue(val.data[0], val.data[1])

def basestationQuit(val):
	input_data = ('quit','quit')
	b.put(input_data)

def stream_telemetry(val):
	numSamples = 100
	h.startTelemetryStream(val.data, numSamples)

def robotData(val):
	print val
	cal.xbee_received(val.data[2])

def callback_stream(val):
	f = open('streaming_data.txt', 'a')
	f.write(val.data + '\n')
	f.close()

def flashMemory(val):
	print val.type
	print samples
	self.addr = val.data
	if val.type == 'erase_flash':
		h.eraseFlashMem(self.addr, samples)
	elif val.type == 'save_telem':
		h.startTelemetrySave(self.addr, samples)
	elif val.type == 'read_telem':
		h.downloadTelemetry(self.addr, samples)

g = GUIStream(sinks = {'reset':[basestationReset], 'quit':[basestationQuit],
						 'motor':[basestationMotor], 'throt_speed':[basestationThrot],
						 'move':[basestationMove], 'steer_gains':[basestationSteer],
						 'turning_rate':[basestationTurning], 'file':[setupFile],
						 'stream_telem':[stream_telemetry], 'erase_flash':[flashMemory],
						 'save_telem':[flashMemory], 'read_telem':[flashMemory], 'imusamples':[getnumSamples]}, 
						 callbacks = None, autoStart = False)

#o = OptitrakStream(sinks = {'optitrak_data':[OptitrakUpdate]}, autoStart = False)

#f = FileStream(sinks = {'file_line':[OptitrakUpdate]}, autoStart = False)

#c = CalcStream(sinks = {'optitrak_euler':[FileUpdate]}, autoStart = False)

b = BasestationStream(sinks = {'robot_data':[robotData]}, callbacks = None)

cal = CallbackStream(sinks = {'streaming_data':[callback_stream], 'special_telem':[imudataUpdate]}, callbacks = None)

h = HelpersStream(sinks = {'xb_send':[xb_send]}, callbacks = None)

time.sleep(0.5)

while(True):
  try:
    time.sleep(0.1)
  except KeyboardInterrupt:
    sys.exit()