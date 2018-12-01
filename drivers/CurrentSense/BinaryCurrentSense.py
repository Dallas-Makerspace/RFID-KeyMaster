from drivers.CurrentSense.CurrentSense import CurrentSense
import time
import logging
import os

class BinaryCurrentSense(CurrentSense):
	def setup(self):
		self.interface = self.getDriver('currentsense_interface')
		self.threshold = int(self.config['threshold'])
		return True

	def getValue(self):
		return self.interface.input(self.config['interface_position']) >= self.threshold

	def run(self):
		current_value = self.getValue()

		try:
			while(True):
				time.sleep(0.1)
				new_value = self.getValue()
				if current_value != new_value:
					current_value = new_value
					self.notifyCurrentChangeObservers(new_value)
		except Exception as e:
			logging.error("Exception: %s" % str(e), exc_info=1)
			os._exit(42) # Make sure entire application exits

