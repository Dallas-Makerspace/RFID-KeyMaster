from drivers.Auth.Auth import Auth
import requests
from utils.Observer import Observer
from utils.Synchronization import synchronize
import threading
import logging

class ADApiAuth(Auth):
	def __init__(self, config, loader):
		self.mutex = threading.RLock()
		super().__init__(config, loader)
		
	def setup(self):
		self.rfid = self.getDriver('rfid')

		logging.debug("Setup ADApiAuth")

		self.groups_allowed = self.config['groups_allowed'].split(',')
		self.groups_denied = self.config['groups_denied'].split(',')
		logging.debug("groups_allowed: %s" % self.groups_allowed)
		logging.debug("groups_denied: %s" % self.groups_denied)

		self.processing = False
		
		self.rfid.observeScan(self.auth_scan)
		self.rfid.observeScan(self.lookup_rfid)

		# do not run as thread
		return False

	def auth_scan(self, id_number):
		logging.debug("RFID scan")
		self.notifyAuthProcessingObservers()
	

	def lookup_rfid(self, id_number):
		user = None
		url = self.config['url']
		payload = "rfid={:}".format(id_number)
		headers = {'content-type': "application/x-www-form-urlencoded", }
		response = requests.request("POST", url, data=payload, headers=headers)
		json = response.json()
		if "result" not in json:
			return
		result = json["result"]

		if "user" in result and "groups" in result["user"]:
			usergroups = result["user"]["groups"]
			access = result["accessGranted"]
			user = result["user"]
		else:
			usergroups = []
			access = False

		#permit = (
		#	all([x in usergroups for x in self.groups_allowed]) and access)
		permit = False
		deny = any([x in usergroups for x in self.groups_denied])
		if not deny:
			permit = any([x in usergroups for x in self.groups_allowed])

		user = {
			"authorized": permit,
			"id": id_number,
			"user": user
		}
		self.notifyAuthObservers(user)


synchronize(ADApiAuth, "auth_scan, lookup_rfid")
		