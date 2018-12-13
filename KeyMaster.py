import configparser
from importlib import import_module
from utils.Observer import Observer
import sys
import os
from utils.Loader import Loader
import logging
import time
from io import StringIO
import traceback

class KeyMaster(object):

	def __init__(self, config_filename):
		try:
			# insert all driver paths
			for x in os.walk('drivers'):
				if "__pycache__" not in x[0]:
					sys.path.insert(0, x[0])

			config = configparser.ConfigParser()
			config.read(config_filename)

			loader = Loader(config)

			for driver in config.items('Drivers'):
				loader.loadDriver(driver[0], driver[1])
		except Exception as e:
			print("Exception: %s" % str(e))
			sys.exit(1)

		self.log = loader.getDriver('log')

		logging.info("KeyMaster %s Starting ---" % VERSION)

		try:	
			startable = dict()
			for driver_instance in loader.getDrivers():
				startable[driver_instance] = driver_instance.setup()

			for driver_instance in loader.getDrivers():
				if driver_instance in startable:
					driver_instance.start()

			# Watch Dog
			if config.has_option('General', 'watchdog'):
				logging.debug("Starting watchdog")
				watchdog = int(config.get('General', 'logging'))
				while True:
					self.touch("KeyMaster-watchdog")
					time.sleep(watchdog)

		except Exception as e:
			logging.error("Exception: %s" % str(e), exc_info=1)
			sys.exit(1)

	def touch(self, fname, times=None):
		with open(fname, 'a'):
			os.utime(fname, times)
			

def add_custom_print_exception():
	old_print_exception = traceback.print_exception
	def custom_print_exception(etype, value, tb, limit=None, file=None):
		tb_output = StringIO()
		traceback.print_tb(tb, limit, tb_output)
		logger = logging.getLogger('customLogger')
		logger.error(tb_output.getvalue())
		tb_output.close()
		old_print_exception(etype, value, tb, limit=None, file=None)
	traceback.print_exception = custom_print_exception

if __name__ == '__main__':
	VERSION = 1.0
	add_custom_print_exception()
	KeyMaster("KeyMaster.ini")
