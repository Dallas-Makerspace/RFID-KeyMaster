from drivers.Log.Log import Log
import logging

class FileLog(Log):
    def __init__(self, config, loader):
        super().__init__(config, loader)

        format = "%(asctime)-15s %(message)s"
        datefmt = '%Y-%m-%d %H:%M:%S'
        loglevel = logging.DEBUG

        if 'format' in config:
            format = config['format']

        if 'date_format' in config:
            datefmt = config['date_format']

        if 'log_level' in config:
            config_level = config['log_level'].lower()
            if config_level == "debug":
                loglevel = logging.DEBUG
            elif config_level == "info":
                loglevel = logging.INFO
            elif config_level == "error":
                loglevel = logging.ERROR

        if 'filename' in config:
            logging.basicConfig(filename=config['filename'], format=format, level=loglevel, datefmt=datefmt)        
        else:
            raise Exception("Could not find filename configuration")

    

