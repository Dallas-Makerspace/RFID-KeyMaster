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
	
	# Some applications run contunously making current sensing of no value
	# If no current sense driver is specified then is it assumed to be disabled

		if 'currentsense' in self.config:
			self.currentsense = self.getDriver('currentsense')
			self.current_sensor_state = 'enabled'
		else:
			self.current_sensor_state = 'disabled'
		
		self.lightdriver = self.getDriver('light')
		#self.buzzer = self.getDriver('buzzer')
		self.relay = self.getDriver('relay')
		self.log = self.getDriver('log')

		self.timer = None

		self.rise_time = 0.3
		if 'rise_time' in self.config:
			self.rise_time = int(self.config['rise_time'])
		
		self.timeout_time = 5 * 60		
		if 'timeout_time' in self.config:
			self.timeout_time = int(self.config['timeout_time'])
#########################################################################################################################################################
	
		# Some applications have a startup current surge that fools the power on check and never allows the 
		# machine to be turned on. These applications have no need for this power on check 
		
		self.start_current_check = 'enabled'

		if 'start_current_check' in self.config:
			self.start_current_check = (self.config['start_current_check']).lower

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
		logging.debug("Starting LargeMachineController")

		try:
			self.queue = queue.Queue()

			self.auth.observeAuth(self.authEvent)
			self.auth.observeAuthProcessing(self.authProcessingEvent)
			self.currentsense.observeCurrentChange(self.currentChangeEvent)

			state = self.STATE_IDLE
			self.light(self.LIGHT_IDLE)
			authId = None

			while True:					
				
				event_type, message = self.queue.get()

				#logging.debug("Event type: "+str(event_type)+", "+str(message))
#######################################################################################
# STATE IDLE
#######################################################################################

				if state == self.STATE_IDLE:
					# machine not in use
					if event_type == self.EVENT_AUTH:
						self.light(self.LIGHT_IDLE)
						logging.info("User: %s" % message)
						
						if message['authorized']:
							authId = message['id']
############################################################################################################################################################################################################
							# This current check is being performed BEFORE the power is aplied.  
							#   It's checking for an error state.
							if self.currentsense.getValue() and current_sensor  == 'enabled':
								# error -- relay isn't supposed to be on - stuck on?
								
								self.relay.off()

								# red LED blinking
								self.light(self.LIGHT_ERROR)
							else:
								# wait to give the current time to rise if switch left on
############################################################################################################################################################################################################								
								self.relay.on()

								# green LED on
								self.light(self.LIGHT_ENERGIZED)
								
								if start_current_check  == 'enabled':
									# start current rise time timer
									self.start_timeout(self.rise_time)
									state = self.STATE_CHECKING_FOR_STARTUP_CURRENT
								else:
									state = self.STATE_AWAITING_TIMEOUT
									# start automatic logoff timeout timer
									self.start_timeout(self.timeout_time)

						else:
							# not an authorized member
							# blink red LED a few times
							self.light(self.LIGHT_NOT_AUTHORIZED)

					elif event_type == self.EVENT_AUTH_PROCESSING:
						self.light(self.LIGHT_AUTH_PROCESSING)

					# not sure what this is doing yet.  -ozindfw
					elif event_type == self.EVENT_CURRENT_SENSE:
						if not message:
							self.light(self.LIGHT_IDLE)
#######################################################################################
# STATE CHECKING_FOR_STARTUP_CURRENT
#######################################################################################

				elif state == self.STATE_CHECKING_FOR_STARTUP_CURRENT:
					self.light(self.LIGHT_ENERGIZED)
					
					# checking for machine left turned on at badge-in
					# give current time to rise
					if event_type == self.EVENT_CURRENT_SENSE and start_current_check  == 'enabled':
						# machine switch left on
						# logout
						state = self.STATE_IDLE
						
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

					elif event_type == self.EVENT_AUTH_PROCESSING:
						self.light(self.LIGHT_AUTH_PROCESSING)
	
					elif event_type == self.EVENT_AUTH:
############################################################################################################################################################################################################
						self.relay.off()
						state = self.STATE_IDLE

						if message['authorized'] and authId == message['id']:
							# user immediately badged back out
							# yellow LED on
							self.light(self.LIGHT_IDLE)
						else:
							# not a member or same member
							# blink red LED a few times
							self.light(self.LIGHT_NOT_AUTHORIZED)
#######################################################################################
# STATE ON
#######################################################################################
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
#######################################################################################
# STATE AWAITING_TIMEOUT
#######################################################################################
				elif state == self.STATE_AWAITING_TIMEOUT:
					self.light(self.LIGHT_ENERGIZED)

					# user turned machine off but did not badge out
					if event_type == self.EVENT_TIMEOUT:
						# log user out
						state = self.STATE_IDLE

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
							self.relay.off()

							# red LED blinking
							self.light(self.LIGHT_ERROR)

					elif event_type == self.EVENT_AUTH_PROCESSING:
						self.light(self.LIGHT_AUTH_PROCESSING)
	
					elif event_type == self.EVENT_AUTH:
						# some badge badged out
						state = self.STATE_IDLE

						# relay off
						self.relay.off()

						self.light(self.LIGHT_IDLE)
#######################################################################################
# STATE AWAITING_OFF
#######################################################################################
				elif state == self.STATE_AWAITING_OFF:
					self.light(self.LIGHT_AWATING_TURN_OFF)

					# attempt to badge out while machine is on
					# wait until machine is turned off
					if event_type == self.EVENT_CURRENT_SENSE and current_sensor  == 'enabled':  :
						if not message:
							# machine turned off, log user out
							state = self.STATE_IDLE

							# relay off
							self.relay.off()

							# yellow LED on
							self.light(self.LIGHT_IDLE)

		
		except Exception as e:
			logging.error("Exception: %s" % str(e), exc_info=1)
			os._exit(42) # Make sure entire application exits

