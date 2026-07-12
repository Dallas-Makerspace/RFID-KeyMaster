#
#	This module reads and processes door and latch sense switches into
#	a state change notification
#
#	Rich Osman OZINDFW 4 July 2026
#


from drivers.CabinetSense.CabinetSense import CabinetSense
import time
import logging
import os

class CabinetSwitchSense(CabinetSense):
	def setup(self):
		self.interface = self.getDriver('cabinet_sense_interface')
		self.log = self.getDriver('log')
		state = "closed"
		return True
		
#	Switch State 0 = closed; 1 = open
#			| Latch0	|  Latch1 
#	door0	| CLOSED	| UNLOCKED
#	door1	| FAULT		| OPEN
#
	def getValue(self):
		sense = [0,0]
		state = ""
		
		sense[0] = self.interface.input(self.config['latch_sense_interface'])
		sense[1] = self.interface.input(self.config['door_sense_interface'])
		match sense:
			case [0,0]:
				state = "closed"
			case [0,1]:
				state = "fault"
			case [1,0]:
				state = "unlocked"
			case [1,1]:
				state = "open"
		return state

	def run(self):
		state = self.getValue()
		
		debounce_tries = 4
		if 'debounce_tries' in self.config:
			debounce_tries = self.config['debounce_tries']

		try:
			while(True):
				
#
#	Door switches in some installations need debouncing because the 
#	doors themselves flex when hit and cause effective bouncing of the switches.
#	the switches.
#
				tries = 1
				for loop in range (0,debounce_tries):
					time.sleep(0.1)
					if state != self.getValue():
#						check = self.getValue()
#						logging.debug(f"Switch check state: {check}")
#
#						logging.debug(f"Switch state debounce try: {tries}")
						tries += 1
					else: break
				else:
					state = self.getValue()
					logging.debug(f"Switch state change to: {state}")
					self.notifyCabinetChangeObservers(state)
				
		except Exception as e:
			logging.error("Exception: %s" % str(e), exc_info=1)
			os._exit(42) # Make sure entire application exits
