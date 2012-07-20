import glob
import time
import sys
from lib import command
from callback_stream import CallbackStream
import datetime
import serial
from struct import pack
from xbee import XBee
from math import ceil,floor
import numpy as np
from asynch_dispatch import *
import threading, Queue
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
	def __init__(self, sinks = None, callbacks = None, fileName = ''):
		threading.Thread.__init__(self)
		self.daemon = True

		self.dispatcher = AsynchDispatch(sinks=sinks, callbacks = callbacks)
		self.fileName = fileName

		self.imudata = []
		self.fileName = ''
		self.steering_rate_set = False
		self.motor_gains_set = False
		self.steering_rate_set = False
		self.flash_erased = False
		self.leadinTime = 0
		self.leadoutTime = 0
		self.angRateDeg = 0
		self.deg2count = 0
		self.count2deg = 0
		self.angRate = 0

		self.command_queue = Queue.Queue()

		self.start()

	def setFileName(self, fileName):
		self.fileName = fileName
		print self.fileName

	def put(self, data):
		self.command_queue.put(data)
  
	def add_sinks(self,sinks):
		self.dispatcher.add_sinks(sinks)

	def setImuData(self, telem_index, data):
		self.imudata[telem_index] = data

	def setMotorGainsSet(self):
		self.motor_gains_set = True
	
	def setSteeringGainsSet(self):
		self.steering_gains_set = True

	def setSteeringRateSet(self):
		self.steering_rate_set = True

	def setBytesIn(self):
		self.bytesIn = self.bytesIn + (2*4 + 15*2)

	def setCount2Deg(self, rate):
		self.Count2Deg = self.Count2Deg * rate
		print "degrees: ", self.Count2Deg
		print "counts: ", rate

	def setFlashErase(self):
		self.flash_erased = True

	def run(self):
		while True:

			if not self.command_queue.empty():
				data = self.command_queue.get()

				if data[0] == 'turning_rate':
					self.setSteeringrate(data[1], data[2])
				elif data[0] == 'steer_gains':
					self.setSteeringGains(data[1], data[2])
				elif data[0] == 'erase_flash':
					self.eraseFlashMem(data[1], data[2])
				elif data[0] == 'save_telem':
					self.startTelemetrySave(data[1], data[2])
				elif data[0] == 'stream_telem':
					self.startTelemetryStream(data[1], data[2])
				elif data[0] == 'move':
					self.sendMoveQueue(data[1], data[2])
				elif data[0] == 'read_telem':
					self.downloadTelemetry(data[1], data[2])

				time.sleep(0.25)
			else:
				pass


########## Helper functions #################
	def xb_send(self, DEST_ADDR, status, type, data):
		payload = chr(status) + chr(type) + ''.join(data)
		data = [DEST_ADDR, payload]
		self.dispatcher.dispatch(Message('xb_send', data))

	def xb_safe_exit(self):
		print "Halting xb"
		self.xb.halt()
		print "Closing serial"
		self.ser.close()
		print "Exiting..."

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
		fileout.write('# ' + now.strftime("%m/%d/%Y %H:%M") + '\n')
		fileout.write('#  Comments: \n')
		fileout.write('#  angrate (deg) = ' + str(self.angRateDeg) + '\n')
		fileout.write('#  angrate (raw) = ' + str(self.angRate) + '\n')
		fileout.write('#  motorgains    = ' + repr(self.motorGains) + '\n')
		fileout.write('#  steeringGains = ' + repr(self.steeringGains) + '\n')
		fileout.write('#  runtime       = ' + repr(self.runtime) + '\n')
		fileout.write('#  numSamples    = ' + repr(self.numSamples) + '\n')
		fileout.write('#  moveq         = ' + repr(self.moveq) + '\n')
		fileout.write('# Columns: \n')
		fileout.write('# time | Llegs | Rlegs | DCL | DCR | GyroX | GyroY | GyroZ | GryoZAvg | AccelX | AccelY |AccelZ | LBEMF | RBEMF | SteerOut | Vbatt | SteerAngle\n')
		fileout.close()

	def dlProgress(self, current, total):
		percent = int(100.0*current/total)
		dashes = int(floor(percent/100.0 * 45))
		stars = 45 - dashes - 1
		barstring = '|' + '-'*dashes + '>' + '*'*stars + '|'
		#sys.stdout.write("\r" + "Downloading ...%d%%   " % percent)
		sys.stdout.write("\r" + str(current).rjust(5) +"/"+ str(total).ljust(5) + "   ")
		sys.stdout.write(barstring)
#		sys.stdout.flush()

	def sendEcho(self, msg):
		self.xb_send(DEST_ADDR, 0, command.ECHO, msg)

	def downloadTelemetry(self, DEST_ADDR, numSamples):
		#Wait for run length before starting download
		time.sleep((self.runtime + self.leadinTime + self.leadoutTime)/1000.0 + 1)

		print "started readback"
		self.xb_send(DEST_ADDR, 0, command.FLASH_READBACK, pack('=L',numSamples))
	 
		# While downloading via callbackfunc, write parameters to start of file
		self.writeFileHeader(self.fileName)

		dlStart = time.time()
		self.last_packet_time = dlStart
		self.bytesIn = 0
		while self.imudata.count([]) > 0:
			time.sleep(0.1)
			#print "Downloading ...",(n-self.imudata.count([])),"/",n
			self.dlProgress(numSamples -self.imudata.count([]) , numSamples)
#			if (time.time() - self.last_packet_time) > self.readback_timeout:
#				print "\nReadback timeout exceeded, restarting."
#				self.imudata = [ [] ] * numSamples
#				print "started readback"
#				dlStart = time.time()
#				self.last_packet_time = dlStart
#				self.xb_send(DEST_ADDR, 0, command.FLASH_READBACK, pack('=L',numSamples))

		dlEnd = time.time()
		#Final update to download progress bar to make it show 100%
		self.dlProgress(numSamples-self.imudata.count([]) , numSamples)
		print "\nTime: %.2f s ,  %.3f KBps" % ( (dlEnd - dlStart), \
												self.bytesIn / (1000*(dlEnd - dlStart)))

		print "readback done"
		fileout = open(self.fileName, 'a')
		np.savetxt(fileout , np.array(self.imudata), '%d', delimiter = ' ')

		print "data saved to ",self.fileName
		#Done with flash download and save

	def wakeRobot(self):
		self.awake = 0;
		while not(self.awake):
			print "Waking robot ... "
			self.xb_send(DEST_ADDR, 0, command.SLEEP, pack('b',0))
			time.sleep(0.2)

	def sleepRobot(self):
		print "Sleeping robot ... "
		self.xb_send(DEST_ADDR, 0, command.SLEEP, pack('b',1))

	def setSteeringRate(self, rate):
		count = 1
		self.angRateDeg = rate
		self.deg2count = 14.375
		self.count2deg = 1/self.deg2count
		self.angRate = round( self.angRateDeg / self.count2deg)
#		while not(self.steering_rate_set):
		print "Setting steering rate...   ",count,"/8"
		count = count + 1
		self.xb_send(DEST_ADDR, 0, command.SET_CTRLD_TURN_RATE, pack('h',self.angRate))
		time.sleep(0.3)
#			if count > 8:
#				print "Unable to set steering rate, exiting."
	#			xb_safe_exit()

	def setMotorGains(self, DEST_ADDR, gains):
		count = 1
		self.motorGains = gains
#		while not(self.motor_gains_set):
		print "Setting motor gains...   ",count,"/8"
		self.xb_send(DEST_ADDR, \
						0, command.SET_PID_GAINS, pack('10h',*gains))
		time.sleep(0.3)
#			if count > 8:
#				print "Unable to set motor gains, exiting."
#				xb_safe_exit()

	def setSteeringGains(self, DEST_ADDR, gains):
		count = 1
		self.steeringGains = gains
#		while not (self.steering_gains_set):
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
		while not (self.flash_erased):
			time.sleep(0.25)
			sys.stdout.write('.')
			if (time.time() - eraseStartTime) > 8:
				print"\nFlash erase timeout, retrying;"
				self.xb_send(DEST_ADDR,0, command.ERASE_SECTORS, pack('L',numSamples))
				eraseStartTime = time.time()
		print "\nFlash erase done."

	def startTelemetrySave(self, DEST_ADDR, numSamples):
		self.numSamples = numSamples
		print "started save"
		self.xb_send(DEST_ADDR, \
						0, command.SPECIAL_TELEMETRY, pack('L',numSamples))

	def sendMoveQueue(self, DEST_ADDR, moveq):
		self.moveq = moveq
		nummoves = moveq[0]
		self.xb_send(DEST_ADDR, \
						0, command.SET_MOVE_QUEUE, pack('=h'+nummoves*'hhLhhhh', *moveq))

	def setMotorSpeeds(self, DEST_ADDR, spleft, spright):
		thrust = [spleft, 0, spright, 0, 0]
		self.xb_send(DEST_ADDR, \
						0, command.SET_THRUST_CLOSED_LOOP, pack('5h',*thrust))

	def calcNumSamples(self, moveq):
		self.leadinTime = 500
		self.leadoutTime = 500
		#Calculates the total movement time from the move queue above
		self.runtime = sum([moveq[i] for i in [ind*7+3 for ind in range(0,moveq[0])]])
	 
		#calculate the number of telemetry packets we expect
		n = int(ceil(150 * (self.runtime + self.leadinTime + self.leadoutTime) / 1000.0))
		#allocate an array to write the downloaded telemetry data into
		self.imudata = [ [] ] * n
		print "Samples: ",n
		self.dispatcher.dispatch(Message('num_samples',n))