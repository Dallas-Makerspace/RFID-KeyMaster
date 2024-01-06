#
# Modified from FileLog class
#
#   By Rich Osman, 7 December 2023
#   Untested, and the coder is uninformed. 
#
#   Editing from the original is not complete. 
#

from drivers.Log.Log import Log
import logging
import logging.handlers
import syslog

class SysLogger(Log):
    def __init__(self, config, loader):
        super().__init__(config, loader)

        logmask = {"error":LOG_ERR, "info":LOG_INFO, "debug":LOG_DEBUG}

        format = "%(asctime)-15s %(message)s"
        datefmt = '%Y-%m-%d %H:%M:%S'
        loglevel = logging.LOG_DEBUG
        
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        syslog = logging.handlers.SysLogHandler(address='/dev/log')
        formatter = logging.Formatter('%(module)s: %(message)s')
        syslog.setFormatter(formatter)
        logger.add
        
        if 'log_level' in config:
            syslog.setlogmask(logmask{config['log_level'].lower()})

        Handler(syslog)
#        logger.info('This is an info message')

        if 'format' in config: format = config['format']

        
        if 'date_format' in config: datefmt = config['date_format']

    def auth(self, user):
        logger.info("Auth: " + str(user))

    def engaged(self, status):
        logger.info("Engaged: " + str(status))

    def debug(self, message):
        logger.debug(message)

    def info(self, message):
        logger.info(message)
    
    def error(self, message):
        logger.error(message)
    
#
#  RFC5424 message severity levels
#Numerical Code	Level	Severity
#0	Emergency	    system is unusable
#1	Alert	        action must be taken immediately
#2	Critical	    critical conditions
#3	Error	        error conditions
#4	Warning	        warning conditions
#5	Notice	        normal but significant condition
#6	Informational	Informational Messages
#7	Debug	        debug level messages
