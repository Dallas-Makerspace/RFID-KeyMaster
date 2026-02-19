#
#       Large Machine Controller with updated logging
#
#               OZINDFW 
#               29 Jan 2026
#               14 Feb 2026 Added logging for more states
#


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
		self.log = self.getDriver('log')

		self.rise_time = 0.3
		self.timeout_time = 5 * 60
		self.timer = None

		if 'rise_time' in self.config:
			self.rise_time = int(self.config['rise_time'])
		if 'timeout_time' in self.config:
			self.timeout_time = int(self.config['timeout_time'])

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

	def run(self):
		logging.info("Starting LargeMachineController")

		try:
			self.queue = queue.Queue()

			self.auth.observeAuth(self.authEvent)
			self.auth.observeAuthProcessing(self.authProcessingEvent)
			self.currentsense.observeCurrentChange(self.currentChangeEvent)

			state = self.STATE_IDLE
			self.light(self.LIGHT_IDLE)
			authId = None

			while True:
				#if state == self.STATE_IDLE:
				#	 print("State Idle")
				#elif state == self.STATE_CHECKING_FOR_STARTUP_CURRENT:
				#	 print("State checking for startup current")
				#elif state == self.STATE_AWAITING_TIMEOUT:
				#	 print("State Awating timeout")
				#elif state == self.STATE_AWAITING_OFF:
				#	 print("State Awating off")
				#elif state == self.STATE_ON:
				#	 print("State On")
				#else:
				#	 print("State Unknown")
					
				
				event_type, message = self.queue.get()

				#if event_type == self.EVENT_AUTH:
				#	 print("EVENT_AUTH")
				#elif event_type == self.EVENT_AUTH_PROCESSING:
				#	 print("EVENT_AUTH_PROCESSING")
				#elif event_type == self.EVENT_CURRENT_SENSE:
				#	 print("EVENT_CURRENT_SENSE")
				#elif event_type == self.EVENT_TIMEOUT:
				#	 print("EVENT_TIMEOUT")
				#else:
				#	 print("Unknown EVENT")

				#logging.debug("Event type: "+str(event_type)+", "+str(message))

				if state == self.STATE_IDLE:
					# machine not in use
					if event_type == self.EVENT_AUTH:
						self.light(self.LIGHT_IDLE)

						logging.debug("User: %s" % message)
						
						if message['authorized']:
							authId = message['id']
							if self.currentsense.getValue():
								# error -- relay isn't supposed to be on - stuck on?

								# relay off
								self.relay.off()
								
								logging.notice("Initial Startup Current Detected, shutting off")

								# red LED blinking
								self.light(self.LIGHT_ERROR)
							else:
								# wait to give the current time to rise if switch left on
								state = self.STATE_CHECKING_FOR_STARTUP_CURRENT

								# relay on
								self.relay.on()

								# green LED on
								self.light(self.LIGHT_ENERGIZED)

								# start current rise time timer
								self.start_timeout(self.rise_time)
						else:
							# not an authorized member
							# blink red LED a few times
							self.light(self.LIGHT_NOT_AUTHORIZED)

					elif event_type == self.EVENT_AUTH_PROCESSING:
						self.light(self.LIGHT_AUTH_PROCESSING)

					elif event_type == self.EVENT_CURRENT_SENSE:
						if not message:
							self.light(self.LIGHT_IDLE)

				elif state == self.STATE_CHECKING_FOR_STARTUP_CURRENT:
					self.light(self.LIGHT_ENERGIZED)
					
					# checking for machine left turned on at badge-in
					# give current time to rise
					if event_type == self.EVENT_CURRENT_SENSE:
						# machine switch left on
						# logout
						state = self.STATE_IDLE
						
						logging.info("Startup Current Detected, shutting off")

						# relay off
						self.relay.off()

						# blink all LEDs
						self.light(self.LIGHT_SWITCH_LEFT_ON)

					elif event_type == self.EVENT_TIMEOUT:
						# machine was off, everything normal
						state = self.STATE_AWAITING_TIMEOUT

						# green LED on
						self.light(self.LIGHT_ENERGIZED)
						
						# start automatic logoff timeout timer
						self.start_timeout(self.timeout_time)
						
						logging.info("Normal Startup, system on")


					elif event_type == self.EVENT_AUTH_PROCESSING:
						self.light(self.LIGHT_AUTH_PROCESSING)
	
					elif event_type == self.EVENT_AUTH:
						if message['authorized'] and authId == message['id']:
							# user immediately badged back out
							state = self.STATE_IDLE
							
							logging.info("Badged out, shutting off")

							# relay off
							self.relay.off()

							# yellow LED on
							self.light(self.LIGHT_IDLE)
						else:
							# not a member or same member

							# blink red LED a few times
							self.light(self.LIGHT_NOT_AUTHORIZED)

				elif state == self.STATE_ON:
					self.light(self.LIGHT_ENERGIZED)

					# machine enabled and ready for use
					if event_type == self.EVENT_AUTH:
						if message['authorized'] and authId == message['id']:
							if self.currentsense.getValue():
								# machine not switched off first, wait until it is
								state = self.STATE_AWAITING_OFF

								# green LED blinking
								self.light(self.LIGHT_AWATING_TURN_OFF)

							else:
								# user badged out
								state = self.STATE_IDLE
								
								logging.info("Badged out, System off")

								# relay off
								self.relay.off()

								# yellow LED on
								self.light(self.LIGHT_IDLE)
						else:
							# ignore nonmember or different member

							# blink red LED a few times
							self.light(self.LIGHT_NOT_AUTHORIZED)

					elif event_type == self.EVENT_AUTH_PROCESSING:
						self.light(self.LIGHT_AUTH_PROCESSING)
	
					elif event_type == self.EVENT_CURRENT_SENSE:
						if not message:
							# machine turned off
							state = self.STATE_AWAITING_TIMEOUT

							# start automatic logoff timeout timer
							self.start_timeout(self.timeout_time)
						else:
							# machine turned on
							pass

				elif state == self.STATE_AWAITING_TIMEOUT:
					self.light(self.LIGHT_ENERGIZED)

					# user turned machine off but did not badge out
					if event_type == self.EVENT_TIMEOUT:
						# log user out
						
						logging.info("Idle timeout, shutting off")

						state = self.STATE_IDLE

						# relay off
						self.relay.off()

						# yellow LED on
						self.light(self.LIGHT_IDLE)

					elif event_type == self.EVENT_CURRENT_SENSE:
						if message:
							# user stopped for awhile, but turned machine back on
							state = self.STATE_ON

							# timer off
							self.cancel_timeout()
						else:
							# error state

							# relay off
							self.relay.off()

							# red LED blinking
							self.light(self.LIGHT_ERROR)

					elif event_type == self.EVENT_AUTH_PROCESSING:
						self.light(self.LIGHT_AUTH_PROCESSING)
	
					elif event_type == self.EVENT_AUTH:
						# some badge badged out
						state = self.STATE_IDLE
						
						logging.info("Badged out while awaiting timeout, System off")

						# relay off
						self.relay.off()

						self.light(self.LIGHT_IDLE)

				elif state == self.STATE_AWAITING_OFF:
					self.light(self.LIGHT_AWATING_TURN_OFF)

					# attempt to badge out while machine is on
					# wait until machine is turned off
					if event_type == self.EVENT_CURRENT_SENSE:
						if not message:
							# machine turned off, log user out
							state = self.STATE_IDLE

							# relay off
							self.relay.off()
							logging.info("Badged out and machine turned off, System off")

							# yellow LED on
							self.light(self.LIGHT_IDLE)
		except Exception as e:
			logging.error("Exception: %s" % str(e), exc_info=1)
			os._exit(42) # Make sure entire application exits

