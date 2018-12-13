import threading
from exceptions.RequiredDriverException import RequiredDriverException
import logging
import os
import time
import traceback

class Loadable(threading.Thread):
	def __init__(self, config, loader):
		self.config = config
		self.loader = loader
		super().__init__()

	def setup(self):
		return False

	def getDriver(self, driver_type):
		driver = self.loader.getDriver(driver_type)
		if driver == None:
			raise RequiredDriverException(driver_type)  
		return driver  

	def run(self):
		try:
			while self.loop() != False:
				pass
		except Exception as e:
			#logging.error("Exception: %s" % str(e), exc_info=1)
			logging.error(traceback.format_exc(10))
			os._exit(42) # Make sure entire application exits

	def loop(self):
		return False

