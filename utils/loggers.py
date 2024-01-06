import logging.handlers
import logging
import sys
import utils.config
import os

log = None
logfile = None
logging.addLevelName(21, "SUCCESS")
logging.addLevelName(22, "FAIL")
logging.addLevelName(23, "MAJOR")
logging.addLevelName(24, "POSITIVE")
logging.addLevelName(25, "NEGATIVE")
logging.addLevelName(26, "MINOR")


class SSTImapFormatter(logging.Formatter):
    style = '{'
    FORMATS = {
        logging.DEBUG: "\033[94m[D]\033[0m [\033[4m{module}\033[0m] {message}",
        logging.INFO: "\033[94m[!]\033[0m {message}",
        logging.WARNING: "\033[93m[*]\033[0m [\033[4m{module}\033[0m] {message}",
        21: "\033[92m[+]\033[0m {message}",
        22: "\033[91m[-]\033[0m {message}",
        23: "\033[94m[*]\033[0m {message}",
        24: "\033[32m[+]\033[0m {message}",
        25: "\033[31m[-]\033[0m {message}",
        26: "\033[34m[*]\033[0m {message}",
        27: "\033[93m[*]\033[0m {message}",
        28: "\033[33m[*]\033[0m {message}",
        29: "\033[33m[!]\033[0m {message}",
        logging.ERROR: "\033[91m[-]\033 [0m[\033[4m{module}\033[0m] {message}",
        logging.CRITICAL: "\033[91m[!]\033[0m [\033[4m{module}\033[0m] {message}",
        'DEFAULT': "\033[91m[{levelname}]\033[0m {message}"
    }

    def __init__(self):
        super().__init__(style='{')

    def format(self, record):
        super().__init__(self.FORMATS.get(record.levelno, self.FORMATS['DEFAULT']), style='{')
        return logging.Formatter.format(self, record)


if not os.path.isdir(utils.config.base_path):
    os.makedirs(utils.config.base_path)

"""Initialize the handler to dump log to files"""
log_path = os.path.join(utils.config.base_path, 'sstimap.log')
file_handler = logging.handlers.RotatingFileHandler(log_path, mode='a', maxBytes=5*1024*1024,
                                                    backupCount=2, encoding=None, delay=False)
file_handler.setFormatter(SSTImapFormatter())

stream_handler = logging.StreamHandler(stream=sys.stdout)
stream_handler.setFormatter(SSTImapFormatter())

log = logging.getLogger('log')
log.propagate = False
log.addHandler(file_handler)
log.addHandler(stream_handler)
log.setLevel(logging.DEBUG)
file_handler.setLevel(logging.INFO)
stream_handler.setLevel(logging.INFO)

dlog = logging.getLogger('dlog')
dlog.propagate = False
dlog.addHandler(file_handler)
dlog.setLevel(logging.INFO)
