import threading
from asynch_dispatch import *

class CalcStream(threading.Thread):
  def __init__(self, sinks=None, autoStart=True):

    threading.Thread.__init__(self)
    self.daemon = True

    self.new_data = threading.Condition()

    self.dispatcher=AsynchDispatch(sinks=sinks, callbacks={'optitrak_line':[self.put]})

    if autoStart:
      self.start()
 
	def run(self):
		while(True):
			self.new_data.acquire()
			self.new_data.wait()
			self.put(new_data)
			self.new_data.release()

	def put(self,message):
		self.dispatcher.put(message)
  
	def add_sinks(self,sinks):
		self.dispatcher.add_sinks(sinks)
  
	def qaut_ealer(self, message):
		quat_v = np.array((message.data.qw, message.data.qx, message.data.qy, message.data.qz)).transpose()
		orn_v = np.zeros((quat_v.shape[0], 3))

		orn_v[i,0] = (math.atan2(2.0*(quat_v[i,2] * quat_v[i,3] + \
								 quat_v[i,0] * quat_v[i,1]), \
								 quat_v[i,0]**2 - quat_v[i,1]**2 - \
								 quat_v[i,2]**2 + quat_v[i,3]**2) + \
								 2*math.pi) % (2*math.pi) - math.pi
		orn_v[i,1] = math.asin(-2*(quat_v[i,1] * quat_v[i,3] - \
								 quat_v[i,0] * quat_v[i,2]))
		orn_v[i,2] = math.atan2(2*(quat_v[i,1] * quat_v[i,2] + \
								 quat_v[i,0] * quat_v[i,3]), \
								 quat_v[i,0]**2 + quat_v[i,1]**2 - \
								 quat_v[i,2]**2 - quat_v[i,3]**2)
		self.dispatcher.dispatch(Message('optitrak_euler', orn_v))