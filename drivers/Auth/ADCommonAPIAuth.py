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
#       at the time these notes are written, the URL is 
#       http://192.168.203.30:8083/badgeGroupMembership"
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

        # The auth transport must never take the interlock down with it:
        # a failed, slow, or unreachable membership service is a denial,
        # not an exception in the RFID reader thread. (Previously this
        # call had no timeout and no exception handling; a connection
        # error propagated through the Observer notification and the
        # reader's generic handler exited the whole application, and a
        # hung service blocked badge scans indefinitely.)
        try:
            response = requests.get(url, json=data, headers=headers, timeout=5)
        except requests.RequestException as e:
            logging.error("Badge lookup failed for badge %s: %s" % (id_number, e))
            self.notifyAuthObservers({"authorized": False, "id": id_number})
            return

        if response.status_code != requests.codes.ok:

            logmsg = "RFID scan result response "+str(response.status_code)
            logging.debug(logmsg)

            self.notifyAuthObservers({"authorized": False, "id": id_number})
            return

        try:
            payload = response.json()
        except ValueError:
            logging.error("Badge lookup for badge %s returned unparseable JSON" % id_number)
            self.notifyAuthObservers({"authorized": False, "id": id_number})
            return

#
#       Response should be in the form:
#       {"inGroup":true,"activeMember":true}
#       or false as the case may be.  "activeMember" means the badge ID is found.
#       "inGroup" means it is found in the group specified in the request.
#
#       Both must be true to authorize: a badge that is in the group but
#       not an active membership must not energize the machine. Missing
#       keys are treated as a denial rather than raising KeyError.
#
        in_group = payload.get("inGroup") is True
        active_member = payload.get("activeMember") is True

        user = {
            "authorized": in_group and active_member,
            "id": id_number
        }

        logmsg = "Badge Number is "+str(id_number)+" Permitted: "+str(in_group)+" Active Member: "+str(active_member)
        logging.debug(logmsg)

        self.notifyAuthObservers(user)

synchronize(ADCommonAPIAuth, "auth_scan, lookup_rfid")
        
