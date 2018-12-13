from drivers.Indicator.Light import Light
import time
import logging
import os

class RGBLight(Light):
	COLOR_BLACK = [0, 0, 0]
	COLOR_WHITE = [255, 255, 255]
	COLOR_RED = [255, 0, 0]
	COLOR_GREEN = [0, 255, 0]
	COLOR_BLUE = [0, 0, 255]
	COLOR_YELLOW = [255, 255, 0]
	COLOR_CYAN = [0, 255, 255]
	COLOR_MAGENTA = [255, 0, 255]

	def setup(self):
		self.interface = self.getDriver('light_interface')

		self.pin_red = self.config['interface_position_red']
		self.pin_green = self.config['interface_position_green']
		self.pin_blue = self.config['interface_position_blue']
		if 'blink_rate' in self.config:
			self.blink_rate = float(self.config['blink_rate']) / 2 
		else:
			self.blink_rate = 0.5
		self.is_on = False

		self.intensity = self.COLOR_WHITE
		self.blink = False
		self.count = None
		self.current_blink = False
		self.current_count = None

		self.saved = False
		self.saved_intensity = None
		self.saved_blink = False
		self.saved_count = None
		self.saved_current_blink = False
		self.saved_current_count = None

		return True

	def printValues(self):
		print("intensity: ", self.intensity)
		print("blink: ", self.blink)
		print("count: ", self.count)
		print("current_blink: ", self.current_blink)
		print("current_count: ", self.current_count)

	def saveValues(self):
		#print("Saving these values")
		#self.printValues()
		
		self.saved_intensity = self.intensity
		self.saved_blink = self.blink
		self.saved_count = self.count
		self.saved_current_blink = self.current_blink
		self.saved_current_count = self.current_count
		self.saved = True

	def restoreValues(self):
		self.intensity = self.saved_intensity
		self.current_blink = self.saved_current_blink
		self.current_count = self.saved_current_count
		self.blink = self.saved_blink
		self.count = self.saved_count
		self.saved = False

		self.interface.output(self.pin_red, self.intensity[0])
		self.interface.output(self.pin_green, self.intensity[1])
		self.interface.output(self.pin_blue, self.intensity[2])

		#print("Restored these values")
		#self.printValues()

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
		self.interface.output(self.pin_red, self.intensity[0])
		self.interface.output(self.pin_green, self.intensity[1])
		self.interface.output(self.pin_blue, self.intensity[2])

	def off(self):
		""" Turn off light

		:return: None
		"""
		self.current_blink = False
		self.current_count = None
		self.interface.output(self.pin_red, 0)
		self.interface.output(self.pin_green, 0)
		self.interface.output(self.pin_blue, 0)

	def setValue(self, intensity, blink=False, count=None):
		""" Sets up light, does not turn on or off light

		:type intensity: int or list
		:param intensity: Intensity of light, 0 through 255 for each color [red, green, blue]

		:type blink: bool
		:param blink: Blinks light at a 'blink_delay' seconds cycle

		:type count: int or None
		:param count: Blink for count times then turn off

		:raises: Nothing

		:rtype: None
		 """
		if count != None:
			self.saveValues()

		if isinstance(intensity, list):
			# RGB Value
			self.intensity = intensity
		elif isinstance(intensity, str):
			self.intensity = self.stringToColor(intensity)
		else:
			# Monochrome Value
			self.intensity = [intensity, intensity, intensity]

		if count == None:
			self.count = None
		else:
			self.count = int(count) * 2  # Number of off and on cycles
		self.blink = blink

	def stringToColor(self, string):
		string = string.lower()
		if string == 'black':
			return self.COLOR_BLACK
		elif string == 'white':
			return self.COLOR_WHITE
		elif string == 'red':
			return self.COLOR_RED
		elif string == 'green':
			return self.COLOR_GREEN
		elif string == 'blue':
			return self.COLOR_BLUE
		elif string == 'yellow':
			return self.COLOR_YELLOW
		elif string == 'cyan':
			return self.COLOR_CYAN
		elif string == 'magenta' or string == 'purple':
			return self.COLOR_MAGENTA
		else:
			return None

	def loop(self):
		if self.current_count == None:
			pass
		elif self.current_count > 0:
			self.current_count = self.current_count - 1
		elif self.current_count == 0:
			self.current_blink = False
			self.current_count = None
			#print("saved: ", self.saved)
			if self.saved:
				self.restoreValues()
			else:
				self.off()

		time.sleep(self.blink_rate)
		if self.current_blink:
			self.is_on = not self.is_on
			if self.is_on:
				self.interface.output(self.pin_red, self.intensity[0])
				self.interface.output(self.pin_green, self.intensity[1])
				self.interface.output(self.pin_blue, self.intensity[2])
			else:
				self.interface.output(self.pin_red, 0)
				self.interface.output(self.pin_green, 0)
				self.interface.output(self.pin_blue, 0)
		1/0
		