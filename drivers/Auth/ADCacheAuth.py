from drivers.Auth.Auth import Auth
import requests
import threading
import os
import time
import datetime
import json
import urllib3
import logging
import os

class ADCacheAuth(Auth):
	ad_cache = {}

	def __init__(self, config, loader):
		self.mutex = threading.RLock()
		super().__init__(config, loader)
		
	def setup(self):
		self.rfid = self.getDriver('rfid')

		logging.debug("Setup ADCacheAuth")

		self.groups_allowed = self.config['groups_allowed'].split(',')
		self.groups_denied = self.config['groups_denied'].split(',')
		logging.debug("groups_allowed: %s" % self.groups_allowed)
		logging.debug("groups_denied: %s" % self.groups_denied)

		self.remote_cache_url = self.config['remote_cache_url']
		self.apikey = self.config['apikey']

		self.local_cache_file = "ADCache.json"

		self.sync_delay = 60
		if 'sync_delay' in self.config:
			self.sync_delay = int(self.config['sync_delay'])

		self.syncCheck()
		self.loadCache()

		self.processing = False
		
		self.rfid.bind(swipe=self.lookup_rfid)

		# run as thread
		return True

	def lookup_rfid(self, id_number):
		self.emit('auth_processing', True)

		self.mutex.acquire()

		permit = False
		user = None
		if id_number in self.ad_cache:
			if "user" in self.ad_cache[id_number] and "groups" in self.ad_cache[id_number]["user"]:
				usergroups = self.ad_cache[id_number]["user"]["groups"]
				user = self.ad_cache[id_number]["user"]
			else:
				usergroups = []

			deny = any([x in usergroups for x in self.groups_denied])
			if not deny:
				permit = any([x in usergroups for x in self.groups_allowed])

		self.mutex.release()
		
		user = {
			"authorized": permit,
			"id": id_number,
			"user": user
		}

		self.emit('auth', user)

	def updateCache(self, newcache):
		self.mutex.acquire()
		self.ad_cache = newcache
		self.mutex.release()

	def loadCache(self):
		with open(self.local_cache_file) as f:
			self.ad_cache = json.load(f)

	def syncCheck(self):
		logging.debug("SyncCheck")

		remote_source = self.remote_cache_url
		local_source = self.local_cache_file

		params = {'apikey': self.apikey}

		response = requests.head(remote_source, verify=False, params=params)
		if "last-modified" in response.headers:
			remote_source_last_modified = response.headers["last-modified"]
			remote_source_last_modified = time.mktime(datetime.datetime.strptime(remote_source_last_modified[:-4], "%a, %d %b %Y %H:%M:%S").timetuple())
		else:
			logging.error("Could not get cache - bad apikey?")
			return

		if os.path.exists(local_source):
			local_source_last_modified = os.path.getmtime(local_source)
			if local_source_last_modified == remote_source_last_modified:
				pass
				#print("Not Modified")
			else:
				logging.debug("Modified downloading")
				#urlretrieve(remote_source, local_source)
				r = requests.get(remote_source, allow_redirects=True, verify=False, params=params)
				open(local_source, 'wb').write(r.content)
				self.updateCache(r.json())
				os.utime(local_source, (remote_source_last_modified, remote_source_last_modified))
		else:
			logging.debug("Downloading first")
			#urlretrieve(remote_source, local_source)
			r = requests.get(remote_source, allow_redirects=True, verify=False, params=params)
			open(local_source, 'wb').write(r.content)
			self.updateCache(r.json())
			os.utime(local_source, (remote_source_last_modified, remote_source_last_modified))


	def loop(self):
		self.syncCheck()
		time.sleep(self.sync_delay)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
