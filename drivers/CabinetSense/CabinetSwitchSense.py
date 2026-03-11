from drivers.CabinetSense.CabinetSense import CabinetSense
import time
import logging
import os

class CabinetSwitchSense(CabinetSense):
	def setup(self):
		self.interface = self.getDriver('cabinet_sense_interface')
		self.log = self.getDriver('log')
		old_state = "closed"
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
		old_state = self.getValue()

		try:
			while(True):
				time.sleep(0.1)
				new_state = self.getValue()
				if old_state != new_state:
					logging.debug(f"Switch state change to: {new_state}")
					old_state = new_state
					self.notifyCabinetChangeObservers(new_state)
					
		except Exception as e:
			logging.error("Exception: %s" % str(e), exc_info=1)
			os._exit(42) # Make sure entire application exits
