import NatNet
import time
import threading, Queue
from asynch_dispatch import *


class OptitrakStream(threading.Thread):
	def __init__(self, sinks=None, autoStart=True):
		threading.Thread.__init__(self)
		self.daemon = True
    
		self.c = NatNet.NatNetClient(1)
		print self.c.NatNetVersion()

		self.c.SetVerbosityLevel(NatNet.Verbosity_Info)

		self.c.Initialize("127.0.0.1", "127.0.0.1")
		
		self.new_data = threading.Condition()
    
		self.dispatcher=AsynchDispatch(sinks=sinks)
		
		self.recieve_queue = Queue.Queue()
		
		self.c.SetDataCallback(self.get_Net_Callback)
		
		if autoStart:
			self.start()
		
	def run(self):
		while (True):
			self.time.sleep(20)
			pass

	def get(self):
		if not self.recieve_queue.empty():
			return self.recieve_queue.get()
		else:
			return None
      
	def put(self, data):
		self.dispatcher.put(message)

	def add_sinks(self,sinks):
		self.dispatcher.add_sinks(sinks)
	
	def update(self, array):
		input_data = "x %.2f  y %.2f  z %.2f  qx %.4f  qy %.4f  qz %.4f qw %.4f" % (
								 array.data.x, array.data.y, array.data.z, array.data.qx, array.data.qy, array.data.qz, array.data.qw)
		pos = "x %.2f y%.2f z %.2f" % (array.data.x, array.data.y, array.data.z)

		print input_data
		
	def get_Net_Callback(self, dataFrame):
		body = dataFrame.RigidBodies[0]
		self.dispatcher.dispatch(Message('optitrak_data', body))