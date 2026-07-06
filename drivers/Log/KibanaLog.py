from drivers.Log.Log import Log
import logging
import queue
import threading
import traceback
import requests
import datetime
import socket
import urllib3

# KibanaLog is used to stand in for FileLog
# It will write logs to a file (KeyMaster.log)
# It will add itself as a logging handler to python stdlib logger 
# It will also send those logs to ELK endpoint asynchronously

class KibanaLog(Log):
    def __init__(self, config, loader):
        super().__init__(config, loader)

        if 'url' not in config:
            raise Exception("KibanaLog requires 'url' (Elasticsearch endpoint)")

        self.es_url = config['url'].rstrip('/')
        self.index  = config.get('index', 'rfid-keymaster')
        self.host = config.get('device_name', socket.gethostname())
        self.api_key = config.get('api_key', None)

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        # urllib3 log only warnings and errors
        logging.getLogger('urllib3').setLevel(logging.WARNING)

        level_str = config.get('log_level', 'debug').lower()
        loglevel = {'debug': logging.DEBUG,
                    'info':  logging.INFO,
                    'error': logging.ERROR}.get(level_str, logging.DEBUG)

        fmt     = config.get('format', '%(asctime)-15s %(message)s')
        datefmt = config.get('date_format', '%Y-%m-%d %H:%M:%S')

        if 'filename' in config:
            logging.basicConfig(filename=config['filename'], format=fmt, level=loglevel, datefmt=datefmt)
        else:
            logging.basicConfig(format=fmt, level=loglevel, datefmt=datefmt)

        # Add messages to queue to send to Kibana asynchronously
        self.send_queue = queue.Queue(maxsize=1000)
        threading.Thread(target=self._send_forever, daemon=True).start()

        # Attach kibana as a logging handler to python stdlib logger
        logging.getLogger().addHandler(_KibanaHandler(self))

    def _queue(self, level, message):
        try:
            self.send_queue.put_nowait((level, message))
        except queue.Full:
            # if queue is full, drop message
            pass

    def _send_forever(self):
        while True:
            level, message = self.send_queue.get()
            self._send(level, message)

    def _send(self, level, message):
        doc = {
            '@timestamp': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'level':   level,
            'message': str(message),
            'host':    self.host,
            'service': 'rfid-keymaster',
        }
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f'ApiKey {self.api_key}'
        try:
            resp = requests.post(f'{self.es_url}/{self.index}/_doc',
                                 json=doc,
                                 headers=headers,
                                 timeout=3,
                                 verify=False)
            print(f"[KibanaLog] {resp.status_code} {resp.text}")
        except Exception as e:
            print(f"[KibanaLog] ERROR: {e}")

    def auth(self, user):
        logging.info("Auth: " + str(user))

    def engaged(self, status):
        logging.info("Engaged: " + str(status))

    def debug(self, message):
        logging.debug(message)

    def info(self, message):
        logging.info(message)

    def error(self, message, exc_info=False):
        logging.error(message, exc_info=exc_info)


class _KibanaHandler(logging.Handler):
    def __init__(self, kibana):
        super().__init__()
        self.kibana = kibana

    def emit(self, record):
        # Filter out logs that are not from the root logger to prevent infinite loops
        if record.name != 'root':
            return
        message = record.getMessage()
        if record.exc_info:
            message += "\n" + "".join(traceback.format_exception(*record.exc_info))
        self.kibana._queue(record.levelname.lower(), message)
