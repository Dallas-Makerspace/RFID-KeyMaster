from drivers.Log.Log import Log
import logging
import persistqueue

class RemoteLog(Log):
    def setup(self):

        log_database = 'RemoteLog.dat' 
        if 'log_database' in self.config:
            log_database = self.config['log_database']

        self.queue = persistqueue.SQLiteAckQueue(log_database)

        return True

    def run(self):
        pass
