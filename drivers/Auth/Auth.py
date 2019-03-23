from drivers.Loadable import Loadable
import logging

class Auth(Loadable):
	_events_ = ['auth', 'auth_processing']

	groups_allow = []
	groups_deny = []

	def __init__(self, config, loader):
		super().__init__(config, loader)

	def setup(self):
		self.groups_allow = self.config['groups_allow']
		self.groups_deny = self.config['groups_deny']
		logging.debug("groups_allow: %s" % self.groups_allow)
		logging.debug("groups_deny: %s" % self.groups_deny)

		self.auth_backend = self.getDriver('auth_backend')

		return False

	def auth(self, rfid_number):
		self.emit('auth_processing', True)

		permit = False

		user = self.auth_backend.getUser(rfid_number)

		if user != None:
			deny = any([x in user['groups'] for x in self.groups_deny])
			if not deny:
				permit = any([x in user['groups'] for x in self.groups_allow])

		emit_user = {
			"authorized": permit,
			"id": rfid_number,
			"user": user
		}

		self.emit('auth', emit_user)
