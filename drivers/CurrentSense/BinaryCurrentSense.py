from drivers.CurrentSense.CurrentSense import CurrentSense
import time
import logging
import os

class BinaryCurrentSense(CurrentSense):
	def setup(self):
		self.interface = self.getDriver('currentsense_interface')
		self.threshold = int(self.config['threshold'])
		self.startup = True
		return True

	def getValue(self):
		return self.interface.input(self.config['interface_position']) >= self.threshold

	def	loop(self):
		if self.startup:
			current_value = self.getValue()
			self.startup = False

		time.sleep(0.1)
		new_value = self.getValue()
		if current_value != new_value:
			current_value = new_value
			self.notifyCurrentChangeObservers(new_value)

