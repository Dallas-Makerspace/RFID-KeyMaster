from drivers.Controller.Controller import Controller
import queue
import time
import threading
import logging
import os

class CabinetController(Controller):
	STATE_OPEN = 10
	STATE_AWAITING_LOCK = 30
	STATE_LOCKED = 40
	STATE_FAULT = 50

	EVENT_AUTH = 10
	EVENT_AUTH_PROCESSING = 15
	EVENT_DOOR_SENSE = 20
	EVENT_TIMEOUT = 30

	def setup(self):
		self.auth = self.getDriver('auth')
		self.doorsense = self.getDriver('doorsense')
		self.lightdriver = self.getDriver('light')
		#self.buzzer = self.getDriver('buzzer')
		self.log = self.getDriver('log')

		self.debounce_time = 0.1  # Door sense switch debounce time (do we really need this or just do in delay time?
		self.door_switch_time = 5
		self.timer = None

		if 'debounce' in self.config:
			self.debounce_time = self.config['debounce_time']
		if 'timeout_time' in self.config:
			self.timeout_time = self.config['timeout_time']
            
        self.lock = self.config['lock']
        self.door_sense = self.config['door_sense']
        

		# Defaults
		# [Intensity/Color, Blink, Blink Count]
		self.LIGHT_OPEN = self.getColorFromConfig('light_idle',
												  [self.lightdriver.COLOR_GREEN, False, None])

		self.LIGHT_FAULT = self.getColorFromConfig('light_fault',
												   [self.lightdriver.COLOR_RED, False, None]) # want flashing red 1 Sec interval

		self.LIGHT_AWAITING_LOCK = self.getColorFromConfig('light_awating_lock',
													   [self.lightdriver.COLOR_GREEN, False, None]) # want flashing green 1 Sec interval

		self.LIGHT_NOT_AUTHORIZED = self.getColorFromConfig('light_not_authorized',
															[self.lightdriver.COLOR_RED, True, 3]) # want flashing red 1/4 Sec interval for 3 sec

		self.LIGHT_LOCKED = self.getColorFromConfig('light_locked',
															[self.lightdriver.COLOR_RED, False, None]) # want solid red


		self.LIGHT_AUTH_PROCESSING = self.getColorFromConfig('light_auth_processing',
															  [self.lightdriver.COLOR_YELLOW, True, None]) # Want green/red alternating until auth or failure

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
		logging.debug("Starting CabinetController")

		try:
			self.queue = queue.Queue()

			self.auth.observeAuth(self.authEvent)
			self.auth.observeAuthProcessing(self.authProcessingEvent)
			self.currentsense.observeCurrentChange(self.currentChangeEvent)

			state = self.AWAITING_LOCK
			self.light(self.AWAITING_LOCK)
			authId = None

			while True:
				
				event_type, message = self.queue.get()
#
#   If in the LOCKED state:
#       1) waiting for AUTH > STATE_OPEN
#       2) checking for door sensor state change > STATE_FAULT
#       3) waiting for timeout > STATE_AWAITING_LOCK
#
				if state == self.STATE_LOCKED:
					# 
					if event_type == self.EVENT_AUTH:
						self.light(self.LIGHT_AUTH_PROCESSING)

						logging.debug("User: %s" % message)
						
						if message['authorized']:

							state = self.STATE_OPEN
                            output(LOCK, off)
                            self.light(self.OPEN)
                           # start time to 	STATE_AWAITING_LOCK 

						else:
							# not an authorized member
							# 
							self.light(self.LIGHT_NOT_AUTHORIZED)

					elif event_type == self.EVENT_AUTH_PROCESSING:
						self.light(self.LIGHT_AUTH_PROCESSING)
                        
                    elif event_type == self.DOOR_SENSE_TIMEOUT:
                         
                        #check for door sense failure
	 
#
#   If in the OPEN state
#       1) waiting for timeout > STATE_AWAITING_LOCK
#       2) waiting for AUTH > STATE_LOCKED
#
				elif state == self.STATE_OPEN:
					self.light(self.LIGHT_OPEN)
					output(LOCK, off)
                
                #wait for timeout to go to STATE_AWAITING_LOCK
	 
#   If in the AWAITING_LOCK state
#   1) waiting for Door sense Timeout
#   2) waiting for AUTH > STATE_LOCKED or Fault depending on door sense state
#
				elif state == self.STATE_AWAITING_LOCK:
					
                #  check for door lock closure for at least debounce time    
                    
                # or if authorized badge is swiped and doorsense is not active, enter fault state    
	 
#
#   If in the FAULT state
#   1) waiting for AUTH > OPEN
#   2) waiting for Door Sense > LOCKED
#

				elif state == self.STATE_FAULT:
					self.light(self.STATE_FAULT)

# if door sense becomes valid, remain locked waiting for unlock

                            
                            
		except Exception as e:
			logging.error("Exception: %s" % str(e), exc_info=1)
			os._exit(42) # Make sure entire application exits

