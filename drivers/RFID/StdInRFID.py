from drivers.RFID.RFID import RFID
import sys
import logging
import os
import time

class StdInRFID(RFID):
	def setup(self):
		self.log = self.getDriver('log')
		return True

	def run(self):

		while True:
			try:

				rfid_code = ""
				rfid_code = input("Awaiting Code")
				logging.info("Code Received: %s"% str(rfid_code))

				if len(rfid_code) != 10:
					print("Input: ",rfid_code)
				else:
					self.notifyScanObservers(rfid_code)

			except	OSError as e:
				logging.debug("OS Error caught in StdInRFID: %s" % str(e), exc_info=1)
				time.sleep (10)
				logging.debug("restarting after sleep")
				dev = InputDevice(self.config['device'])
				dev.grab()


			except Exception as e:
				logging.error("Exception: %s" % str(e), exc_info=1)
				os._exit(42) # Make sure entire application exits

