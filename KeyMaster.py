#import configparser
import json
from importlib import import_module
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

			#config = configparser.ConfigParser()
			#config.read(config_filename)
			with open(config_filename) as config_file:  
				config = json.load(config_file)

			loader = Loader(config)

			# Load Common Drivers
			for driver in config['common']:
				loader.loadDriver(driver[0], driver[1])

			# Load Controller Drivers
			for controller in config['controllers']:
				for driver in controller[1]:
					loader.loadDriver(driver[0], driver[1], controller[0]) 

		except Exception as e:
			print("Exception: %s" % str(e))
			sys.exit(1)

		self.log = loader.getDriver('log')

		logging.info("KeyMaster %s Starting ---" % VERSION)

		try:	
			startable = {
				'common' : [],
				'controllers' : []
			}

			# Setup Common Drivers
			for driver_instance in loader.getCommonDrivers():
				if driver_instance.setup():
					startable['common'].append(driver_instance)

			# Setup Controller Drivers
			for controller in config['controllers']:
				for driver_instance in loader.getControllerDrivers(controller[0]):
					if driver_instance.setup():
						startable['controllers'].append(driver_instance) 

			# Start common
			for driver_instance in startable['common']:
				driver_instance.start()

			# Start Controllers
			for driver_instance in startable['controllers']:
				driver_instance.start()

			# Start Watch Dog
			if 'watchdog' in config['general']:
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
			
if __name__ == '__main__':
	VERSION = 1.0
	KeyMaster("KeyMaster.ini")
