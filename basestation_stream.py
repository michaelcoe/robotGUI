from xbee import XBee
from lib import command
import threading
import Queue
import time
import serial
import sys
from packet import Packet
from struct import pack, unpack
from asynch_dispatch import *
from callback_stream import CallbackStream

class BasestationStream(threading.Thread):
	def __init__(self, sinks = None, callbacks = None, port='COM5', baudrate=57600, addr='\x30\x02', timeout=-1, 
							timeoutFunction = None):
		threading.Thread.__init__(self)
		self.daemon = True

		try:
			self.ser = serial.Serial(port, baudrate, timeout=3, rtscts=0)
			print "Serial Port Set Up"
		except serial.serialutil.SerialException:
			print "Could not open serial port:%d"

		self.addr = addr
		self.dispatcher = AsynchDispatch(sinks=sinks, callbacks = callbacks)
		self.timeout = timeout
		self.last_time = -1
		self.timeoutFunction = timeoutFunction
		self.xb = XBee(self.ser, callback = self.receiveCallback)
		self.send_queue = Queue.Queue()
		self.receive_queue = Queue.Queue()
		self.start()
    
	def run(self):
		while True:
			if self.last_time != -1 and self.timeout != -1 \
				and self.timeoutFunction is not None \
				and (time.time() - self.last_time) > self.timeout:
				self.timeoutFunction()

			if not self.send_queue.empty():
				entry = self.send_queue.get()

				if entry[0] == 'packet':
					self.addr = entry[1]
					pkt = entry[2]
#					pkt = Packet(dest_addr = self.addr, payload = entry[2])
					self.xb.tx(dest_addr = self.addr, data = pkt)
					#self.xb.tx(dest_addr = pack('>h',pkt.dest_addr), data = (chr(0) + chr(0x88) + ''.join(pack('h',0))))
				elif entry[0] == 'quit':
					self.xb.halt()
					self.ser.close()

				time.sleep(0.25)

	def get(self):
		if not self.receive_queue.empty():
			return self.receive_queue.get()
		else:
			return None

	def put(self,entry):
		self.send_queue.put(entry)

	def receiveCallback(self,xbee_data):
		self.last_time = time.time()
#		pkt = Packet(dest_addr=self.addr, time=self.last_time,
#								payload=xbee_data.get('rf_data'))
#		self.receive_queue.put(('packet',pkt))
		pkt = (self.addr, self.last_time, xbee_data.get('rf_data'))
		self.dispatcher.dispatch(Message('robot_data',pkt))
  
	def sendPacket(self,pkt):
		self.send_queue.put(('packet',pkt))