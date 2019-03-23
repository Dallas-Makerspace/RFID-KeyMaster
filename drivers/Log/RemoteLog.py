from drivers.Log.Log import Log
import logging
import persistqueue

class RemoteLog(Log):
	LOG_AUTH = {
		id: 100,
		'message': 'User Authenicated'
	}

	LOG_DEAUTH = {
		id: 200,
		'message': "User Deauthenicated"
	}

	LOG_NOT_AUTHORIZED = {
		id: 900,
		'message': "User not authenicated"
	}

	LOG_RELAY_CHANGE = {
		id: 500,
		'message': "Relay changed states"
	}

	LOG_CURRENT_SENSE = {
		id: 520,
		'message': "Current sense changed states"
	}

	LOG_STUCK_ON = {
		id: 1001,
		'message': "Current flowing with relay off"
	}

	LOG_SWITCH_LEFT_ON = {
		id: 1010,
		'message': "Current detected on startup"
	}

	LOG_AWATING_TURN_OFF = {
		id: 1030,
		'message': "Awating current drop to deauth"
	}

	LOG_CURRENT_ALREADY_OFF_ERROR = {
		id: 1050,
		'message': "Already off but detected current change to off"
	}

	LOG_OTHER_BADGE_OUT = {
		id: 910,
		'message': "Other badge, badged user out"
	}

	def setup(self):

		log_database = 'RemoteLog.dat' 
		if 'log_database' in self.config:
			log_database = self.config['log_database']

		self.queue = persistqueue.SQLiteAckQueue(log_database)

		return True

	def log(self, type, state):
		print("RemoteLog: (%d) %s" % (type.id, type.message) )
		#self.queue.put((type, state))

	def loop(self):
		return False


