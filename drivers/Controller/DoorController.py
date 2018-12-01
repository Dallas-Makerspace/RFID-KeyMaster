from drivers.Controller.Controller import Controller
import queue
import time
import threading
import logging
import os

class DoorController(Controller):
	STATE_IDLE = 10
	STATE_ON = 20
	STATE_AWAITING_TIMEOUT = 30
	STATE_AWAITING_OFF = 40
	STATE_DOOR_ENERGIZED = 50

	EVENT_AUTH = 10
	EVENT_AUTH_PROCESSING = 15
	EVENT_CURRENT_SENSE = 20
	EVENT_TIMEOUT = 30

	def setup(self):
		self.auth = self.getDriver('auth')
		self.lightdriver = self.getDriver('light')
		#self.buzzer = self.getDriver('buzzer')
		self.relay = self.getDriver('relay')
		self.log = self.getDriver('log')

		self.door_time = 3
		self.timer = None

		if 'door_time' in self.config:
			self.door_time = self.config['door_time']

		# Defaults
		# [Intensity/Color, Blink, Blink Count]
		self.LIGHT_IDLE = self.getColorFromConfig('light_idle',
												  [self.lightdriver.COLOR_BLUE, False, None])

		self.LIGHT_ERROR = self.getColorFromConfig('light_error',
												   [self.lightdriver.COLOR_RED, False, None])

		self.LIGHT_ENERGIZED = self.getColorFromConfig('light_energized',
													   [self.lightdriver.COLOR_GREEN, False, None])

		self.LIGHT_NOT_AUTHORIZED = self.getColorFromConfig('light_not_authorized',
															[self.lightdriver.COLOR_RED, True, 3])

		self.LIGHT_AUTH_PROCESSING = self.getColorFromConfig('light_auth_processing',
															  [self.lightdriver.COLOR_YELLOW, True, None])

		return True

	def getColorFromConfig(self, key, default=None):
		if key in self.config:
			color = self.config[key].replace(" ", "").split(",")
			color[0] = color[0].lower()
			color[1] = color[1].lower()
			color[2] = color[2].lower()
			
			if self.lightdriver.stringToColor(color[0]) == None:
				raise Exception("light_idle has invalid color")
			color[1] = color[1] == 'true'
			if color[2] == 'false' or color[2] == 'none':
				color[2] = None
			else:
				color[2] = float(color[2])
			return color
		else:
			return default

	def light(self, color):
		self.lightdriver.on(color[0], color[1], color[2])

	def start_timeout(self, timeout):
		def updatequeue():
			self.queue.put([self.EVENT_TIMEOUT, None])
		self.cancel_timeout()
		self.timer = threading.Timer(timeout, updatequeue)
		self.timer.start()

	def cancel_timeout(self):
		if self.timer != None and self.timer.is_alive():
			self.timer.cancel()

	def authEvent(self, user):
		self.queue.put([self.EVENT_AUTH, user])

	def authProcessingEvent(self, value):
		self.queue.put([self.EVENT_AUTH_PROCESSING, None])

	def run(self):
		logging.debug("Starting DoorController")

		try:

			self.queue = queue.Queue()

			self.auth.observeAuth(self.authEvent)
			self.auth.observeAuthProcessing(self.authProcessingEvent)

			state = self.STATE_IDLE
			self.light(self.LIGHT_IDLE)
			authId = None

			while True:
				event_type, message = self.queue.get()

				if state == self.STATE_IDLE:
					# not in use
					if event_type == self.EVENT_AUTH:
						self.light(self.LIGHT_IDLE)

						logging.debug("User: %s" % message)
						
						if message['authorized']:
							authId = message['id']
							# relay on
							self.relay.on()

							# green LED on
							self.light(self.LIGHT_ENERGIZED)

							# start door time timer
							self.start_timeout(self.door_time)

							state = self.STATE_DOOR_ENERGIZED
						else:
							# not an authorized member
							# blink red LED a few times
							self.light(self.LIGHT_NOT_AUTHORIZED)

					elif event_type == self.EVENT_AUTH_PROCESSING:
						self.light(self.LIGHT_AUTH_PROCESSING)

				elif state == self.STATE_DOOR_ENERGIZED:
					self.light(self.LIGHT_ENERGIZED)
					
					if event_type == self.EVENT_TIMEOUT:
						# turn off and reset
						state = self.STATE_IDLE

						self.light(self.LIGHT_IDLE)
						
						self.relay.off()
						

					elif event_type == self.EVENT_AUTH_PROCESSING:
						self.light(self.LIGHT_AUTH_PROCESSING)
		except Exception as e:
			logging.error("Exception: %s" % str(e), exc_info=1)
			os._exit(42) # Make sure entire application exits
 
