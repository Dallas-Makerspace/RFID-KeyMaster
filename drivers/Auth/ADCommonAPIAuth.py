#
# Modified from ADApiAuth class
#
#   By Rich Osman, 13 April 2023
#   Untested, and the coder is uninformed. 
#
#   Editing from the original is not complete. 
#

from drivers.Auth.Auth import Auth
import requests
from utils.Observer import Observer
from utils.Synchronization import synchronize
import threading
import logging

#
#       This AD lookup is based on the nicely simplified CommonApi
#       See https://github.com/Dallas-Makerspace/CommonApi/tree/master
#

class ADCommonAPIAuth(Auth):
	def __init__(self, config, loader):
		self.mutex = threading.RLock()
		super().__init__(config, loader)
		
	def setup(self):
		self.rfid = self.getDriver('rfid')
		self.log = self.getDriver('log')

		logging.debug("Setup ADCommonAPIAuth")

		self.group_allowed = self.config['group_allowed']
		logging.debug("group_allowed: %s" % self.group_allowed)

		self.processing = False
		
		self.rfid.observeScan(self.auth_scan)
		self.rfid.observeScan(self.lookup_rfid)

		# do not run as thread
		return False

	def auth_scan(self, id_number):
		logging.debug("RFID scan")
		self.notifyAuthProcessingObservers()
	

	def lookup_rfid(self, id_number):
    
		url = self.config['url']
		data = '{"badge": ",'.format(id_number),'"group": "',self.config['group_allowed']}'
		headers = {'content-type': "Content-Type: application/json"}
        
        print("\n\n",URL,"\n",data,"\n",headers,"\n\n")
		response = requests.request("GET" url, data=data, headers=headers)

		json = response.json()
#
#       Response should be in the form:
#       {"inGroup":true,"activeMember":true}
#       or false as the case may be.  "activeMember" means the badge ID is found.
#       "inGroup" means it is found in the group specified in the request.
# 
		if "inGroup" not in json:
			return
        
        user = {
			"authorized": json["inGroup"],
			"id": id_number
		}
        
        print ("\n\nUesr: ", user,"\n\n")
        
        logging.debug(str(datetime.datetime.now()) + " ---- " + "Badge Number is ".format(id_number)," Permitted:", json["inGroup"]," Active Member: ",json(activeMember))


		self.notifyAuthObservers(user)


synchronize(ADCommonAPIAuth, "auth_scan, lookup_rfid")
		