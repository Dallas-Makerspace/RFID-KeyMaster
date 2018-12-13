from drivers.RFID.RFID import RFID
from evdev import InputDevice, ecodes
import sys
import logging
import os

class KeyboardRFID(RFID):
	def setup(self):
		self.scancodes = {
			0: None, 2: u'1', 3: u'2', 4: u'3', 5: u'4', 6: u'5', 7: u'6', 8: u'7', 9: u'8', 10: u'9', 11: u'0', 28: u'\n'
		}

		return True

	def loop(self):
		if self.startup:
			# print "scan_daemon: " + str(os.getpid())

			self.dev = InputDevice(self.config['device'])
			self.dev.grab()
			logging.debug(self.dev)
			self.rfid_code = ""

		for event in self.dev.read_loop():
			# If key event and key up (0)
			if event.type == ecodes.EV_KEY and event.value == 0:
				key = self.scancodes.get(event.code)
				if key == u'\n':  # if enter
					self.notifyScanObservers(self.rfid_code)
					self.rfid_code = ""
				else:
					self.rfid_code = self.rfid_code + key


