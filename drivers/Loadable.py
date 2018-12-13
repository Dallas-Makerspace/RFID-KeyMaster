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

	def log_traceback(self, ex, ex_traceback=None):
		if ex_traceback is None:
			ex_traceback = ex.__traceback__
		tb_lines = [ line.rstrip('\n') for line in
					traceback.format_exception(ex.__class__, ex, ex_traceback)]
		logging.error(tb_lines)

	def run(self):
		try:
			while self.loop() != False:
				pass
		except Exception as e:
			#logging.error("Exception: %s" % str(e), exc_info=1)
			self.log_traceback(e)
			os._exit(42) # Make sure entire application exits

	def loop(self):
		return False

