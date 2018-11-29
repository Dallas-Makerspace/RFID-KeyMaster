from drivers.RFID.RFID import RFID
from evdev import InputDevice, ecodes
import sys
import logging
import os

class KeyboardRFID(RFID):
	def setup(self):
		self.log = self.getDriver('log')
		return True

	def run(self):
		try:
			scancodes = {
				0: None, 2: u'1', 3: u'2', 4: u'3', 5: u'4', 6: u'5', 7: u'6', 8: u'7', 9: u'8', 10: u'9', 11: u'0', 28: u'\n'
			}

			# print "scan_daemon: " + str(os.getpid())

			dev = InputDevice(self.config['device'])
			dev.grab()

			logging.debug(dev)


			rfid_code = ""

			for event in dev.read_loop():
				# If key event and key up (0)
				if event.type == ecodes.EV_KEY and event.value == 0:
					key = scancodes.get(event.code)
					if key == u'\n':  # if enter
						self.notifyScanObservers(rfid_code)
						rfid_code = ""
					else:
						rfid_code = rfid_code + key

		except Exception as e:
			logging.error("Exception: %s" % str(e), exc_info=1)
			os._exit(42) # Make sure entire application exits

