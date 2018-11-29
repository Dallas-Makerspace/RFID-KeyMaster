from drivers.Loadable import Loadable
import time
import logging
import os

class Light(Loadable):
	"""
	Driver for a single light and also base class for other lights
	"""

	def setup(self):
		"""
		Setup for Light Module

		:return: Returns true to enable threaded run method 
		"""
		self.interface = self.getDriver('light_interface')

		self.pin = self.config['interface_position']
		self.blink_rate = self.config['blink_rate'] / 2 or 0.5
		self.is_on = False

		self.intensity = 255
		self.blink = False
		self.count = None
		self.current_count = False
		self.current_count = None

		self.saved_intensity = None
		self.saved_blink = False
		self.saved_count = None

		return True

	def saveValues(self):
		self.saved_intensity = self.intensity
		self.saved_blink = self.blink
		self.saved_count = self.count

	def restoreValues(self):
		self.intensity = self.saved_intensity
		self.blink = self.saved_blink
		self.count = self.saved_count

	def on(self, intensity=None, blink=False, count=None):
		"""
		Turns on light to current intensity, blink

		For optional parameters see setValue method
		with the exception of count, if count is not None
		it will save the values and restore them after
		the count has expired.  This allows you to blink
		for a certain number of times and then return to
		the previous value

		:return: None
		"""
		if count != None:
			self.saveValues()

		if intensity != None:
			self.setValue(intensity, blink, count)
		self.current_count = self.count
		self.current_blink = self.blink
		self.interface.output(self.pin, self.intensity)

	def off(self):
		""" Turn off light

		:return: None
		"""
		self.current_blink = False
		self.current_count = None
		self.interface.output(self.pin, 0)

	def setValue(self, intensity, blink=False, count=None):
		""" Sets up light, does not turn on or off light

		:type intensity: int
		:param intensity: Intensity of light, 0 through 255

		:type blink: bool
		:param blink: Blinks light at a 'blink_delay' seconds cycle

		:type count: int or None
		:param count: Blink for count times then turn off

		:raises: Nothing

		:rtype: None
		 """
		self.intensity = intensity
		self.count = count * 2  # Number of off and on cycles
		self.blink = blink

	def run(self):
		try:
			while True:
				if self.current_count > 0:
					self.current_count = self.current_count - 1
				elif self.current_count == 0:
					if self.saved_intensity != None:
						self.restoreValues()
						self.saved_intensity = None
					else:
						self.off()

				time.sleep(self.blink_rate)
				if self.current_blink:
					self.is_on = not self.is_on
					if self.is_on:
						self.interface.output(self.pin, self.intensity)
					else:
						self.interface.output(self.pin, 0)
		except Exception as e:
			logging.error("Exception: %s" % str(e), exc_info=1)
			os._exit(42) # Make sure entire application exits
