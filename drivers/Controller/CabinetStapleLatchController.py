from drivers.Controller.Controller import Controller
import queue
import time
import threading
import logging
import os

class CabinetStapleLatchController(Controller):
	STATE_LOCKED = 10			#Door closed, latch closed
	STATE_AUTH = 20				#Authorization is complete
	STATE_AUTH_PROCESSING = 30	#Authorization in progress
	STATE_UNLOCKED = 40	 #Door closed, Latch Open
	STATE_READY_TO_LOCK = 50	#Door Open, Latch Open
	STATE_LATCH_FAULT = 60		#Door Open, Latch Closed
	STATE_FAILED = 70			#Door Open, Latch Closed, n failed attemps to clear

	EVENT_AUTH = 10
	EVENT_AUTH_PROCESSING = 20
	EVENT_TIMEOUT = 30
	EVENT_CABINET_SENSE = 40
	EVENT_IDLE = 50

	def setup(self):
		self.auth = self.getDriver('auth')
		self.lightdriver = self.getDriver('light')
		self.interface = self.getDriver('controller_io_interface')
		self.cabinetsense = self.getDriver('cabinet_sense')
		#self.buzzer = self.getDriver('buzzer')
		self.log = self.getDriver('log')

		self.rise_time = 0.3
		self.unlock_pulse = 0.1		#Unlock pulse duration to latch
		self.relock_time = 30
		self.timeout_time = 5 * 60
		self.timer = None
		self.clear_retries = 3
		self.clear_retry_delay = 2	# delay between latch clearance attempts

		if 'rise_time' in self.config:
			self.rise_time = int(self.config['rise_time'])

		if 'unlock_pulse' in self.config:
			self.unlock_pulse = int(self.config['unlock_pulse'])

		if 'relock_time' in self.config:
			self.relock_time = int(self.config['relock_time'])

		if 'timeout_time' in self.config:
			self.timeout_time = int(self.config['timeout_time'])

		if 'clear_retries' in self.config:
			self.clear_retries = int(self.config['clear_retries'])
			
		self.retry_count = self.clear_retries

		if 'latch_control_interface' in self.config:
			self.latch_control_interface = (self.config['latch_control_interface'])
		else:
			log.debug("latch_control_interface not specified, aborting")


		# Defaults
		# [Intensity/Color, Blink, Blink Count]
		self.LIGHT_LOCKED = self.getColorFromConfig('light_locked',
												  [self.lightdriver.COLOR_RED, False, None])

		self.LIGHT_UNLOCKED = self.getColorFromConfig('light_unlocked',
															  [self.lightdriver.COLOR_GREEN, True, -1]) #Blink Forever

		self.LIGHT_READY_TO_LOCK = self.getColorFromConfig('ready_to_lock',
													   [self.lightdriver.COLOR_GREEN, False, None])

		self.LIGHT_FAILED  = self.getColorFromConfig('light_failed',
												   [self.lightdriver.COLOR_RED, True, -1]) #Blink Forever

		self.LIGHT_AUTH_PROCESSING = self.getColorFromConfig('light_auth_processing',
															  [self.lightdriver.COLOR_YELLOW, False, None])

		self.LIGHT_NOT_AUTHORIZED = self.getColorFromConfig('light_not_authorized',
															[self.lightdriver.COLOR_YELLOW, True, 5])

		self.LIGHT_LATCH_FAULT = self.getColorFromConfig('light_latch_fault',
															[self.lightdriver.COLOR_RED, True, -1]) #Blink Forever

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
		
	def cabinetChangeEvent(self, value):
		self.queue.put([self.EVENT_CABINET_SENSE, value])
		
	def changeState(self,new_state):
		match new_state:
			case CabinetStapleLatchController.STATE_LOCKED:
				self.state = self.STATE_LOCKED
				self.light(self.LIGHT_LOCKED)
				logging.debug("Cabinet state changed to LOCKED")
			case CabinetStapleLatchController.STATE_AUTH_PROCESSING:
				self.state = self.STATE_AUTH_PROCESSING
				self.light(self.LIGHT_AUTH_PROCESSING)
				logging.debug("Cabinet state changed to AUTH_PROCESSING")
			case CabinetStapleLatchController.STATE_AUTH:
				self.state = self.STATE_AUTH
				self.light(self.LIGHT_AUTH_PROCESSING)
				logging.debug("Cabinet state changed to AUTH")
			case CabinetStapleLatchController.STATE_UNLOCKED:
				self.state = self.STATE_UNLOCKED
				self.light(self.LIGHT_UNLOCKED)
				logging.debug("Cabinet state changed to UNLOCKED")
			case CabinetStapleLatchController.STATE_READY_TO_LOCK:
				self.state = self.STATE_READY_TO_LOCK
				self.light(self.LIGHT_READY_TO_LOCK)
				logging.debug("Cabinet state changed to READY TO LOCK")
			case CabinetStapleLatchController.STATE_LATCH_FAULT:
				self.state = self.STATE_LATCH_FAULT
				self.retry_count = self.clear_retries
				self.light(self.LIGHT_LATCH_FAULT)
				logging.debug("Cabinet state changed to LATCH FAULT")
			case CabinetStapleLatchController.STATE_FAILED:
				self.state = self.STATE_FAILED
				self.light(self.LIGHT_LATCH_FAULT)
				logging.error("Cabinet state changed to FAILED")

#
#	Pulse latch 'unlock_pulse' seconds on to unlock
#		--- usually 100 or so milliseconds
#

	def unlock(self):
		self.interface.output(self.config['latch_control_interface'],1)
		time.sleep(self.unlock_pulse)
		self.interface.output(self.config['latch_control_interface'],0)

################################################################################
#
#					Main Loop
#
################################################################################

	def run(self):
		logging.info("Starting CabinetStapleLatchController")
		print("\nStarting CabinetStapleLatchController\n")
		
		self.interface.output(self.config['latch_control_interface'],0)

		try:
			self.queue = queue.Queue()

			self.auth.observeAuth(self.authEvent)
			self.auth.observeAuthProcessing(self.authProcessingEvent)
			self.cabinetsense.observeCabinetChange(self.cabinetChangeEvent)
			
			self.retry_count = self.clear_retries  # set up for fault clearance 
			
##################################################################################
# Get initial door state to set system state
##################################################################################
			match self.cabinetsense.getValue():
				case "closed":
					logging.info("Startup state LOCKED")
#					print("\nStartup state LOCKED")
					self.changeState(self.STATE_LOCKED)
				case "fault":
					logmsg = "Startup Latch Fault Detected, attempting to clear"
					logging.debug(logmsg)
#					print("\n",logmsg)
					self.changeState(self.STATE_LATCH_FAULT)
					self.unlock()
			# Need to start timer to kick off event loop so we can try to clear
					self.start_timeout(self.clear_retry_delay)
				case "unlocked":
					logging.info("Startup state UNlocked")
#					print("\nStartup state UNlocked")
					self.changeState(self.STATE_UNLOCKED)
				case "open":
					logging.info("Startup state OPEN")
#					print("\nStartup state OPEN")
					self.changeState(self.STATE_READY_TO_LOCK)

			authId = None
			message = ""
			event_type = self.EVENT_IDLE

###############################################################################
#
#			EVENT LOOP
#					only exectuted when an event is triggered
#
###############################################################################

			while True:

				event_type, message = self.queue.get()
				
				logging.debug ("Event: %s, Message: %s, State: %s",event_type, message, self.state )
#				print ("\nLoop Top Event: ",event_type," Message: ", message, "State: ",self.state )
 

###############################################################################
#
#			STATE_LOCKED
#					Door closed, latch closed
#
###############################################################################

				if self.state == self.STATE_LOCKED:
					if event_type == self.EVENT_AUTH_PROCESSING:
						self.changeState(self.STATE_AUTH_PROCESSING)
					elif event_type == self.EVENT_AUTH:
						logging.debug("User: %s" % message)
						if message['authorized']:
							authId = message['id']
							self.unlock()
							self.changeState(self.STATE_UNLOCKED)
						else:
							# not an authorized member
							self.light(self.LIGHT_NOT_AUTHORIZED)
							time.sleep(3)
							self.light(self.LIGHT_LOCKED)
					elif event_type == self.EVENT_CABINET_SENSE:
						match message:
							case "closed":
								pass
							case "fault":
								self.changeState(self.STATE_LATCH_FAULT)
							case "unlocked":
								self.changeState(self.STATE_UNLOCKED)
							case "open":
								self.changeState(self.STATE_READY_TO_LOCK)
					elif event_type == self.EVENT_TIMEOUT:
						pass
						   
			
						
###############################################################################
#
#			STATE_AUTH or STATE_AUTH_PROCESSING
#					Door closed, latch closed
#
###############################################################################

				if self.state == self.STATE_AUTH or self.state == self.STATE_AUTH_PROCESSING:
					if event_type == self.EVENT_AUTH_PROCESSING:
						pass
					elif event_type == self.EVENT_AUTH:
						logging.debug("User: %s" % message)
						if message['authorized']:
							authId = message['id']
							self.unlock()
							self.changeState(self.STATE_UNLOCKED)
						else:
							# not an authorized member
							self.light(self.LIGHT_NOT_AUTHORIZED)
							self.changeState(self.STATE_LOCKED)
							time.sleep(2)
							self.light(self.LIGHT_LOCKED)
					elif event_type == self.EVENT_CABINET_SENSE:
						match message:
							case "closed":
								pass
							case "fault":
								self.changeState(self.STATE_LATCH_FAULT)
							case "unlocked":
								self.changeState(self.STATE_UNLOCKED)
							case "open":
								self.changeState(self.STATE_READY_TO_LOCK)
					elif event_type == self.EVENT_TIMEOUT:
						pass

###############################################################################
#
#				STATE_UNLOCKED
#
#					Cabinet unlocked and ready to open
#  This may not be needed - should be either awaiting timeout or ready to lock
#
###############################################################################

				elif self.state == self.STATE_UNLOCKED:

					if event_type == self.EVENT_CABINET_SENSE:
						match message:
							case "closed":
								self.changeState(self.STATE_LOCKED)
							case "fault":
								self.changeState(self.STATE_LATCH_FAULT)
							case "unlocked":
								pass
							case "open":
								self.changeState(self.STATE_READY_TO_LOCK)
					elif event_type == self.EVENT_AUTH_PROCESSING or self.EVENT_AUTH:
						logging.debug("Already Open")
					elif event_type == self.EVENT_TIMEOUT:
						pass

###############################################################################
#
#				STATE_READY_TO_LOCK
#					door oppen, and latch open
#
###############################################################################

				elif self.state == self.STATE_READY_TO_LOCK:
					if event_type == self.EVENT_CABINET_SENSE:
						match message:
							case "closed":
								self.changeState(self.STATE_LOCKED)
							case "fault":
								self.changeState(self.STATE_LATCH_FAULT)
							case "unlocked":
								self.changeState(self.STATE_UNLOCKED)
							case "open":
								pass
					elif event_type == self.EVENT_AUTH_PROCESSING or self.EVENT_AUTH:
						logging.debug("Already ready to lock")
					elif event_type == self.EVENT_TIMEOUT:
						pass

###############################################################################
#
#				STATE_LATCH_FAULT
#
#				If the latch is closed, but the door is open, any attempt to close
#				door will not latch it.	 Make 'clear_retries' attempts to unlatch
#				it.
#
###############################################################################

				if self.state == self.STATE_LATCH_FAULT:
					if self.retry_count == self.clear_retries :
						logging.debug("		LATCH FAULT")
						self.unlock()
						self.retry_count -= 1
						self.start_timeout(self.clear_retry_delay)

					elif event_type == self.EVENT_TIMEOUT:
						self.unlock()
						self.retry_count -= 1
						self.start_timeout(self.clear_retry_delay)
					
					elif event_type == self.EVENT_CABINET_SENSE:
						match message:
							case "closed":
								self.retry_count = self.clear_retries
								self.changeState(self.STATE_LOCKED)
							case "unlocked":
								self.retry_count = self.clear_retries
								self.changeState(self.STATE_UNLOCKED)
							case "open":
								self.retry_count = self.clear_retries
								self.changeState(self.STATE_READY_TO_LOCK)
								
					elif event_type == self.EVENT_AUTH_PROCESSING or self.EVENT_AUTH:
						print("\nLatch Fault Auth Event: ",event_type)
						logging.debug("Attempting to clear fault, ignnored")

					if self.retry_count <= 0 :
						self.changeState(self.STATE_FAILED)
						self.cancel_timeout()
						logmsg="Latch in failed self.state after "+str(self.clear_retries)+" attempts to clear"
						logging.error(logmsg)
						self.start_timeout(.2)


					# lock up
				if self.state == self.STATE_FAILED:
					while True:
						self.light(self.LIGHT_LATCH_FAULT)




###############################################################################
#
#
#		Blow Up on Fail (and cleanly exit)
#
#
###############################################################################

		except Exception as e:
			logging.error("Exception: %s" % str(e), exc_info=1)
			os._exit(42) # Make sure entire application exits cleanly

