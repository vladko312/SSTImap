import base64
import sys

loaded_data_types = {}


def unload_data_types():
    global loaded_data_types
    for k in loaded_data_types:
        if loaded_data_types[k].__module__ in sys.modules:
            del sys.modules[loaded_data_types[k].__module__]
    loaded_data_types = {}


def compatible_url_safe_base64_encode(code):
    code_b64 = code.encode(encoding='UTF-8')
    code_b64 = base64.urlsafe_b64encode(code_b64).decode(encoding='UTF-8')
    return code_b64


class DataType(object):
    def __init__(self, args, tag="*"):
        self.data_type = self.__class__.__name__
        self.params = ""
        self.args = args
        self.tag = tag
        self.help_text = ""

    def __init_subclass__(cls, **kwargs):
        module = cls.__module__.split(".")
        name = cls.__name__
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
