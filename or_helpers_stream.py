import glob
import time
import sys
from lib import command
from callback_stream import CallbackStream
import datetime
import serial
import shared
from struct import pack
from xbee import XBee
from math import ceil,floor
import numpy as np
from asynch_dispatch import *

## Constants
###
MOVE_SEG_CONSTANT = 0
MOVE_SEG_RAMP = 1
MOVE_SEG_SIN = 2
MOVE_SEG_TRI = 3
MOVE_SEG_SAW = 4
MOVE_SEG_IDLE = 5
MOVE_SEG_LOOP_DECL = 6
MOVE_SEG_LOOP_CLEAR = 7
MOVE_SEG_QFLUSH = 8

##
STEER_MODE_DECREASE = 0
STEER_MODE_INCREASE = 1
STEER_MODE_SPLIT = 2

class HelpersStream(threading.Thread):
	def __init__(self, sinks = None, callbacks = None):
		threading.Thread.__init__(self)
		self.daemon = True

		self.dispatcher = AsynchDispatch(sinks=sinks, callbacks = callbacks)

		self.start()

	def run(self):
		while True:
			pass

	def put(self, data):
		self.dispatcher.put(message)
  
	def add_sinks(self,sinks):
		self.dispatcher.add_sinks(sinks)
########## Helper functions #################
	def xb_send(self, DEST_ADDR, status, type, data):
		payload = chr(status) + chr(type) + ''.join(data)
		data = [DEST_ADDR, payload]
		self.dispatcher.dispatch(Message('xb_send', data))

	def xb_safe_exit(self):
		print "Halting xb"
		shared.xb.halt()
		print "Closing serial"
		shared.ser.close()
		print "Exiting..."
		sys.exit(1)

	def resetRobot(self, DEST_ADDR):
		print "Resetting robot..."
		self.xb_send(DEST_ADDR, 0, command.SOFTWARE_RESET, pack('h',1))

	def findFileName(self):
		filenames = glob.glob("*imudata*.txt");
		# Explicitly remove "imudata.txt", since that can mess up the pattern
		if 'imudata.txt' in filenames:
				filenames.remove('imudata.txt')

		if filenames == []:
				dataFileName = "imudata1.txt"
		else:
				filenames.sort()
				filenum = [int(fn[7:-4]) for fn in filenames]
				filenum.sort()
				filenum = filenum[-1] + 1
				dataFileName = "imudata" + str(filenum) + ".txt"
		return dataFileName

	def writeFileHeader(self, dataFileName):
		now = datetime.datetime.now()

		fileout = open(dataFileName,'w')
		#write out parameters
		fileout.write('% ' + now.strftime("%m/%d/%Y %H:%M") + '\n')
		fileout.write('%  Comments: \n')
		fileout.write('%  angrate (deg) = ' + str(shared.angRateDeg) + '\n')
		fileout.write('%  angrate (raw) = ' + str(shared.angRate) + '\n')
		fileout.write('%  motorgains    = ' + repr(shared.motorGains) + '\n')
		fileout.write('%  steeringGains = ' + repr(shared.steeringGains) + '\n')
		fileout.write('%  runtime       = ' + repr(shared.runtime) + '\n')
		fileout.write('%  numSamples    = ' + repr(shared.numSamples) + '\n')
		fileout.write('%  moveq         = ' + repr(shared.moveq) + '\n')
		fileout.write('% Columns: \n')
		fileout.write('% time | Llegs | Rlegs | DCL | DCR | GyroX | GyroY | GyroZ | GryoZAvg | AccelX | AccelY |AccelZ | LBEMF | RBEMF | SteerOut | Vbatt | SteerAngle\n')
		fileout.close()

	def dlProgress(self, current, total):
		percent = int(100.0*current/total)
		dashes = int(floor(percent/100.0 * 45))
		stars = 45 - dashes - 1
		barstring = '|' + '-'*dashes + '>' + '*'*stars + '|'
		#sys.stdout.write("\r" + "Downloading ...%d%%   " % percent)
		sys.stdout.write("\r" + str(current).rjust(5) +"/"+ str(total).ljust(5) + "   ")
		sys.stdout.write(barstring)
		sys.stdout.flush()

	def sendEcho(self, msg):
		self.xb_send(DEST_ADDR, 0, command.ECHO, msg)

	def downloadTelemetry(self, numSamples):
		#Wait for run length before starting download
		time.sleep((shared.runtime + shared.leadinTime + shared.leadoutTime)/1000.0 + 1)

		print "started readback"
		self.xb_send(DEST_ADDR, 0, command.FLASH_READBACK, pack('=L',numSamples))
	 
		dlStart = time.time()
		shared.last_packet_time = dlStart
		shared.bytesIn = 0
		while shared.imudata.count([]) > 0:
			time.sleep(0.1)
			#print "Downloading ...",(n-shared.imudata.count([])),"/",n
			dlProgress(numSamples -shared.imudata.count([]) , numSamples)
			if (time.time() - shared.last_packet_time) > shared.readback_timeout:
				print "\nReadback timeout exceeded, restarting."
				raw_input("Press Enter to start readback ...")
				shared.imudata = [ [] ] * numSamples
				print "started readback"
				dlStart = time.time()
				shared.last_packet_time = dlStart
				self.xb_send(DEST_ADDR, \
								0, command.FLASH_READBACK, pack('=L',numSamples))

		dlEnd = time.time()
		#Final update to download progress bar to make it show 100%
		dlProgress(numSamples-shared.imudata.count([]) , numSamples)
		print "\nTime: %.2f s ,  %.3f KBps" % ( (dlEnd - dlStart), \
												shared.bytesIn / (1000*(dlEnd - dlStart)))

		print "readback done"
		fileout = open(shared.dataFileName, 'a')
		np.savetxt(fileout , np.array(shared.imudata), '%d', delimiter = ' ')

		print "data saved to ",shared.dataFileName
		#Done with flash download and save

	def wakeRobot(self):
		shared.awake = 0;
		while not(shared.awake):
			print "Waking robot ... "
			self.xb_send(DEST_ADDR, 0, command.SLEEP, pack('b',0))
			time.sleep(0.2)

	def sleepRobot(self):
		print "Sleeping robot ... "
		self.xb_send(DEST_ADDR, 0, command.SLEEP, pack('b',1))

	def setSteeringRate(self, rate):
		count = 1
		deg2count = 14.375
		count2deg = 1/deg2count
		angRate = round(angRateDeg / count2deg)
#		while not(shared.steering_rate_set):
		print "Setting steering rate...   ",count,"/8"
		count = count + 1
		self.xb_send(DEST_ADDR, 0, command.SET_CTRLD_TURN_RATE, pack('h',shared.angRate))
		time.sleep(0.3)
#			if count > 8:
#				print "Unable to set steering rate, exiting."
#				xb_safe_exit()

	def setMotorGains(self, DEST_ADDR, gains):
		count = 1
		self.motorGains = gains
#		while not(shared.motor_gains_set):
		print "Setting motor gains...   ",count,"/8"
		self.xb_send(DEST_ADDR, \
						0, command.SET_PID_GAINS, pack('10h',*gains))
		time.sleep(0.3)
#			if count > 8:
#				print "Unable to set motor gains, exiting."
#				xb_safe_exit()

	def setSteeringGains(self, DEST_ADDR, gains):
		count = 1
		steeringGains = gains
#		while not (shared.steering_gains_set):
		print "Setting steering gains...   ",count,"/8"
		self.xb_send(DEST_ADDR, \
						0, command.SET_STEERING_GAINS, pack('6h',*gains))
		time.sleep(0.3)
#			if count > 8:
#				print "Unable to set steering gains, exiting."
#				xb_safe_exit()

	def eraseFlashMem(self, DEST_ADDR, numSamples):
		eraseStartTime = time.time()
		self.xb_send(DEST_ADDR, \
						0, command.ERASE_SECTORS, pack('L',numSamples))
		print "started flash erase ...",
		while not (shared.flash_erased):
			time.sleep(0.25)
			sys.stdout.write('.')
			if (time.time() - eraseStartTime) > 8:
				print"\nFlash erase timeout, retrying;"
				self.xb_send(DEST_ADDR,0, command.ERASE_SECTORS, pack('L',numSamples))
				eraseStartTime = time.time()
		print "\nFlash erase done."

	def startTelemetrySave(self, DEST_ADDR, numSamples):
		shared.numSamples = numSamples
		print "started save"
		self.xb_send(DEST_ADDR, \
						0, command.SPECIAL_TELEMETRY, pack('L',numSamples))

	def sendMoveQueue(self, DEST_ADDR, moveq):
		shared.moveq = moveq
		nummoves = moveq[0]
		self.xb_send(DEST_ADDR, \
						0, command.SET_MOVE_QUEUE, pack('=h'+nummoves*'hhLhhhh', *moveq))

	def setMotorSpeeds(self, DEST_ADDR, spleft, spright):
		thrust = [spleft, 0, spright, 0, 0]
		self.xb_send(DEST_ADDR, \
						0, command.SET_THRUST_CLOSED_LOOP, pack('5h',*thrust))

	def calcNumSamples(self, moveq):
		leadinTime = 500
		leadoutTime = 500
		#Calculates the total movement time from the move queue above
		runtime = sum([moveq[i] for i in [ind*7+3 for ind in range(0,moveq[0])]])
	 
		#calculate the number of telemetry packets we expect
		n = int(ceil(150 * (runtime + leadinTime + leadoutTime) / 1000.0))
		#allocate an array to write the downloaded telemetry data into
		shared.imudata = [ [] ] * n
		print "Samples: ",n
		return n

	def startTelemetryStream(self, DEST_ADDR, numSamples):
		self.xb_send(DEST_ADDR, \
						0, command.STREAM_TELEMETRY, pack('L',numSamples))
