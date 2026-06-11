from drivers.Log.Log import Log
import logging
import requests
import datetime
import socket

class KibanaLog(Log):
    def __init__(self, config, loader):
        super().__init__(config, loader)

        if 'url' not in config:
            raise Exception("KibanaLog requires 'url' (Elasticsearch endpoint)")

        self.es_url = config['url'].rstrip('/')
        self.index  = config.get('index', 'rfid-keymaster')
        self.device = config.get('device_name', socket.gethostname())

        level_str = config.get('log_level', 'debug').lower()
        loglevel = {'debug': logging.DEBUG,
                    'info':  logging.INFO,
                    'error': logging.ERROR}.get(level_str, logging.DEBUG)

        fmt     = config.get('format', '%(asctime)-15s %(message)s')
        datefmt = config.get('date_format', '%Y-%m-%d %H:%M:%S')

        if 'filename' in config:
            logging.basicConfig(filename=config['filename'], format=fmt,
                                level=loglevel, datefmt=datefmt)
        else:
            logging.basicConfig(format=fmt, level=loglevel, datefmt=datefmt)

    def _send(self, level, message, extra=None):
        doc = {
            '@timestamp': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'level':   level,
            'message': message,
            'device':  self.device,
            'service': 'rfid-keymaster',
        }
        if extra:
            doc.update(extra)
        try:
            requests.post(f'{self.es_url}/{self.index}/_doc',
                          json=doc,
                          headers={'Content-Type': 'application/json'},
                          timeout=3)
        except Exception:
            pass

    def auth(self, user):
        rfid_id    = user.get('id')         if isinstance(user, dict) else str(user)
        authorized = user.get('authorized') if isinstance(user, dict) else None
        msg = f"Auth: {user}"
        logging.info(msg)
        self._send('auth', msg, {'rfid_id': rfid_id, 'authorized': authorized})

    def engaged(self, status):
        msg = f"Engaged: {status}"
        logging.info(msg)
        self._send('info', msg, {'engaged': status})

    def debug(self, message):
        logging.debug(message)
        self._send('debug', message)

    def info(self, message):
        logging.info(message)
        self._send('info', message)

    def error(self, message):
        logging.error(message)
        self._send('error', message)
