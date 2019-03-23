import threading
from exceptions.RequiredDriverException import RequiredDriverException
import logging
import os
import time
from pydispatch import Dispatcher

class Loadable(threading.Thread, Dispatcher):
	def __init__(self, config, loader, id):
		self.config = config
		self.loader = loader
		self.id = id
		super().__init__()

	def setup(self):
		return False

	def getDriver(self, driver_name, controller=None):
		driver = self.loader.getDriver(driver_name, controller)
		if driver == None:
			raise RequiredDriverException(driver_name)  
		return driver  

	def run(self):
		self.startup = True
		try:
			while self.loop() != False:
				self.startup = False
		except Exception as e:
			logging.error("Exception: %s" % str(e), exc_info=1)
			os._exit(42) # Make sure entire application exits

	def loop(self):
		return False

