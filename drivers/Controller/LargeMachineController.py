from drivers.Controller.Controller import Controller
import queue
import time
import threading
import logging
import os

class LargeMachineController(Controller):
	STATE_IDLE = 10
	STATE_ON = 20
	STATE_AWAITING_TIMEOUT = 30
	STATE_AWAITING_OFF = 40
	STATE_CHECKING_FOR_STARTUP_CURRENT = 50

	EVENT_AUTH = 10
	EVENT_AUTH_PROCESSING = 15
	EVENT_CURRENT_SENSE = 20
	EVENT_TIMEOUT = 30

	def setup(self):
		self.auth = self.getDriver('auth')
		self.currentsense = self.getDriver('currentsense')
		self.lightdriver = self.getDriver('light')
		#self.buzzer = self.getDriver('buzzer')
		self.relay = self.getDriver('relay')
		self.authlog = self.getDriver('authlog')

		self.rise_time = 0.3
		self.timeout_time = 5 * 60
		self.timer = None

		if 'rise_time' in self.config:
			self.rise_time = self.config['rise_time']
		if 'timeout_time' in self.config:
			self.timeout_time = self.config['timeout_time']

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

		self.LIGHT_SWITCH_LEFT_ON = self.getColorFromConfig('light_switch_left_on',
															[self.lightdriver.COLOR_YELLOW, False, None])

		self.LIGHT_AWATING_TURN_OFF = self.getColorFromConfig('light_awating_turn_off',
															  [self.lightdriver.COLOR_GREEN, True, None])

		self.LIGHT_AUTH_PROCESSING = self.getColorFromConfig('light_auth_processing',
															  [self.lightdriver.COLOR_YELLOW, True, None])

		self.queue = queue.Queue()

		self.auth.bind(auth=self.authEvent)
		self.auth.bind(auth_processing=self.authProcessingEvent)
		self.currentsense.bind(current_change=self.currentChangeEvent)

		self.user = None
		self.relay_state = False

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

	def currentChangeEvent(self, value):
		self.queue.put([self.EVENT_CURRENT_SENSE, value])

	def logEvent(self, event, state):
		pass

	def setRelay(self, state):
		if state != self.relay_state:
			if state:
				self.relay.on()
			else:
				self.relay.off()
			self.logEvent(self.authlog.LOG_RELAY_CHANGE, state)
			self.relay_state = state

	def loop(self):
		if self.startup:
			logging.debug("Starting LargeMachineController")
			self.state = self.STATE_IDLE
			self.light(self.LIGHT_IDLE)
			self.authId = None
			self.user = None
	
		event_type, message = self.queue.get()

		if event_type == self.EVENT_AUTH:
			self.logEvent(self.LOG_AUTH, message)
		elif event_type == self.EVENT_CURRENT_SENSE:
			self.logEvent(self.LOG_CURRENT_SENSE, message)

		if self.state == self.STATE_IDLE:
			# machine not in use
			if event_type == self.EVENT_AUTH:
				self.user = message

				self.light(self.LIGHT_IDLE)

				logging.debug("User: %s" % message)

				if message['authorized']:
					self.authId = message['id']

					if self.currentsense.getValue():
						# error -- relay isn't supposed to be on - stuck on?

						# relay off
						self.setRelay(False)

						# red LED blinking
						self.light(self.LIGHT_ERROR)

						self.logEvent(self.authlog.LOG_STUCK_ON, self.user)
					else:
						# wait to give the current time to rise if switch left on
						self.state = self.STATE_CHECKING_FOR_STARTUP_CURRENT

						# relay on
						self.setRelay(True)

						# green LED on
						self.light(self.LIGHT_ENERGIZED)

						# start current rise time timer
						self.start_timeout(self.rise_time)
				else:
					# not an authorized member
					# blink red LED a few times
					self.light(self.LIGHT_NOT_AUTHORIZED)

					self.logEvent(self.authlog.LOG_NOT_AUTHORIZED, self.user)

			elif event_type == self.EVENT_AUTH_PROCESSING:
				self.light(self.LIGHT_AUTH_PROCESSING)

			elif event_type == self.EVENT_CURRENT_SENSE:
				if not message:
					self.light(self.LIGHT_IDLE)

		elif self.state == self.STATE_CHECKING_FOR_STARTUP_CURRENT:
			self.light(self.LIGHT_ENERGIZED)
			
			# checking for machine left turned on at badge-in
			# give current time to rise
			if event_type == self.EVENT_CURRENT_SENSE:
				# machine switch left on
				# logout
				self.state = self.STATE_IDLE

				# relay off
				self.setRelay(False)

				# blink all LEDs
				self.light(self.LIGHT_SWITCH_LEFT_ON)

				self.logEvent(self.authlog.LOG_SWITCH_LEFT_ON, self.user)

			elif event_type == self.EVENT_TIMEOUT:
				# machine was off, everything normal
				self.state = self.STATE_AWAITING_TIMEOUT

				# green LED on
				self.light(self.LIGHT_ENERGIZED)
				
				# start automatic logoff timeout timer
				self.start_timeout(self.timeout_time)

				self.logEvent(self.authlog.LOG_AUTH, self.user)

			elif event_type == self.EVENT_AUTH_PROCESSING:
				self.light(self.LIGHT_AUTH_PROCESSING)

			elif event_type == self.EVENT_AUTH:
				if message['authorized'] and self.authId == message['id']:
					# user immediately badged back out
					self.state = self.STATE_IDLE

					# relay off
					self.setRelay(False)

					# idle
					self.light(self.LIGHT_IDLE)

					self.logEvent(self.authlog.LOG_DEAUTH, self.user)
					self.user = None

				else:
					# not a member or same member

					# blink red LED a few times
					self.light(self.LIGHT_NOT_AUTHORIZED)

		elif self.state == self.STATE_ON:
			self.light(self.LIGHT_ENERGIZED)

			# machine enabled and ready for use
			if event_type == self.EVENT_AUTH:
				if message['authorized'] and self.authId == message['id']:
					if self.currentsense.getValue():
						# machine not switched off first, wait until it is
						self.state = self.STATE_AWAITING_OFF

						# green LED blinking
						self.light(self.LIGHT_AWATING_TURN_OFF)

						self.logEvent(self.authlog.LOG_AWATING_TURN_OFF, self.user)
						
					else:
						# user badged out
						self.state = self.STATE_IDLE

						# relay off
						self.setRelay(False)

						# Idle
						self.light(self.LIGHT_IDLE)
	
						self.logEvent(self.authlog.DEAUTH, self.user)
						self.user = None
				else:
					# ignore nonmember or different member

					# blink red LED a few times
					self.light(self.LIGHT_NOT_AUTHORIZED)

			elif event_type == self.EVENT_AUTH_PROCESSING:
				self.light(self.LIGHT_AUTH_PROCESSING)

			elif event_type == self.EVENT_CURRENT_SENSE:
				if not message:
					# machine turned off
					self.state = self.STATE_AWAITING_TIMEOUT

					# start automatic logoff timeout timer
					self.start_timeout(self.timeout_time)
				else:
					# machine turned on
					pass

		elif self.state == self.STATE_AWAITING_TIMEOUT:
			self.light(self.LIGHT_ENERGIZED)

			# user turned machine off but did not badge out
			if event_type == self.EVENT_TIMEOUT:
				# log user out
				self.state = self.STATE_IDLE

				# relay off
				self.setRelay(False)

				# yellow LED on
				self.light(self.LIGHT_IDLE)

			elif event_type == self.EVENT_CURRENT_SENSE:
				if message:
					# user stopped for awhile, but turned machine back on
					self.state = self.STATE_ON

					# timer off
					self.cancel_timeout()
				else:
					# error state

					# relay off
					self.setRelay(False)

					# red LED blinking
					self.light(self.LIGHT_ERROR)

					self.logEvent(self.authlog.LOG_CURRENT_ALREADY_OFF_ERROR, self.user)
					self.logEvent(self.authlog.LOG_DEAUTH, self.user)
					self.user = None
					self.state = STATE_IDLE

			elif event_type == self.EVENT_AUTH_PROCESSING:
				self.light(self.LIGHT_AUTH_PROCESSING)

			elif event_type == self.EVENT_AUTH:
				# some badge badged out
				self.state = self.STATE_IDLE

				# relay off
				self.setRelay(False)

				self.light(self.LIGHT_IDLE)

				self.logEvent(self.authlog.LOG_OTHER_BADGE_OUT, message)
				self.user = None

		elif self.state == self.STATE_AWAITING_OFF:
			self.light(self.LIGHT_AWATING_TURN_OFF)

			# attempt to badge out while machine is on
			# wait until machine is turned off
			if event_type == self.EVENT_CURRENT_SENSE:
				if not message:
					# machine turned off, log user out
					self.state = self.STATE_IDLE

					# relay off
					self.setRelay(False)

					# yellow LED on
					self.light(self.LIGHT_IDLE)

					self.logEvent(self.authlog.LOG_DEAUTH, self.user)
					self.user = None
