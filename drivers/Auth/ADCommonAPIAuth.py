#
# Modified from ADApiAuth class
#
#   By Rich Osman, 7 December 2023
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

        self.group = self.config['group']
        logging.debug("group: %s" % self.group)

        self.processing = False
        
        self.rfid.observeScan(self.auth_scan)
        self.rfid.observeScan(self.lookup_rfid)
        #
        # do not run as thread
        #
        return False

    def auth_scan(self, id_number):
        logging.debug("RFID scan")
        self.notifyAuthProcessingObservers()
    

    def lookup_rfid(self, id_number):
    
        url = self.config['url']
        data = {"badge":id_number,"group":self.config['group']}
        headers = {'content-type' : 'application/json'}
        
        response = requests.get(url, json=data, headers=headers)
        
        if response.status_code != requests.codes.ok:
        
            logmsg = "RFID scan result response "+str(response.status_code)
            logging.debug(logmsg)

            return
        
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
                
        logmsg = "Badge Number is "+str(id_number)+" Permitted: "+str(json["inGroup"])+" Active Member: "+str(json["activeMember"])        
        logging.debug(logmsg)

        self.notifyAuthObservers(user)


synchronize(ADCommonAPIAuth, "auth_scan, lookup_rfid")
        
