import base64
import sys
from utils import config
from utils.loggers import log

loaded_data_types = {}
failed_data_types = []


def unload_data_types():
    global loaded_data_types
    global failed_data_types
    for k in loaded_data_types:
        if loaded_data_types[k].__module__ in sys.modules:
            del sys.modules[loaded_data_types[k].__module__]
    loaded_data_types = {}
    for p in failed_data_types:
        if p.__module__ in sys.modules:
            del sys.modules[p.__module__]
    failed_data_types = []


def compatible_url_safe_base64_encode(code):
    code_b64 = code.encode(encoding='UTF-8')
    code_b64 = base64.urlsafe_b64encode(code_b64).decode(encoding='UTF-8')
    return code_b64


class DataType(object):
    sstimap_version = config.version

    def __init__(self, args, tag="*"):
        self.data_type = self.__class__.__name__
        self.params = ""
        self.args = args
        self.tag = tag
        self.help_text = ""

    def __init_subclass__(cls, **kwargs):
        module = cls.__module__.split(".")
        name = cls.__name__
        if config.compare_versions(cls.sstimap_version, config.min_version['data_type']) == "<":
            log.log(22, f'''{name} data type is outdated and cannot be loaded''')
            failed_data_types.append(cls)
            return
        if config.compare_versions(cls.sstimap_version, config.version) == ">":
            log.log(22, f'''{name} data type requires SSTImap update and cannot be loaded''')
            failed_data_types.append(cls)
            return
        if module[0] == "data_types":
            loaded_data_types[name.lower()] = cls

    def injection_points(self, data, all_injectable=False):
        return []

    def _process_values(self, values):
        return ""

    def get_params(self):
        return ""

    def inject(self, injection, inj):
        return ""
