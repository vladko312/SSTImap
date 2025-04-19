from core.data_type import DataType
import json
from copy import deepcopy
from utils.loggers import log
from functools import reduce


def deepupdate(a, b):
    if type(a) != type(b):
        log.log(22, "Supplied JSON body parts have different types. Body will be ignored")
        raise TypeError
    if isinstance(a, dict):
        for key, value in b.items():
            if key in a:
                deepupdate(a[key], value)
            else:
                a[key] = value
    elif isinstance(a, list):
        a.extend(b)
    else:
        a = b
    return a


def update(a, b):
    if type(a) != type(b):
        log.log(22, "Supplied JSON body parts have different types. Body will be ignored")
        raise TypeError
    if isinstance(a, dict):
        a.update(b)
    elif isinstance(a, list):
        a.extend(b)
    else:
        a = b
    return a


class Json(DataType):
    data_type_info = {
        "Description": """JSON data (application/json MIME type)""",
        "Usage notes": """Supply JSON objects to be merged into one.
Appropriate Content-Type header is often required by the server.""",
        "Authors": [
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",
        ],
        "Options": [
            "deep_update=True - recursively update dictionaries."
        ],
    }

    def injection_points(self, data, all_injectable=False):
        injs = []
        self.params = self._process_values(data)
        self._deep_injection_points(self.params, injs, [], all_injectable)
        return injs

    def _deep_injection_points(self, params, injs, rpath, all_injectable):
        if isinstance(params, dict):
            for param, value in params.items():
                path = rpath.copy()
                path.append(param)
                if self.tag in param:
                    injs.append({'field': 'Body', 'part': 'param', 'param': self._param_by_path(path), "path": path})
                self._deep_injection_points(value, injs, path, all_injectable)
        elif isinstance(params, list):
            for idx, value in enumerate(params):
                path = rpath.copy()
                path.append(idx)
                self._deep_injection_points(value, injs, path, all_injectable)
        elif isinstance(params, str):
            if all_injectable or self.tag in params:
                injs.append({'field': 'Body', 'part': 'value', 'param': self._param_by_path(rpath), 'path': rpath})

    def _param_by_path(self, path):
        return ".".join([str(x).replace("\\", "\\\\").replace(".", "\\.") for x in path])

    def _process_values(self, values):
        parts = [json.loads(x) for x in values]
        updater = deepupdate if self.args.get("data_params", {}).get("deep_update", True) else update
        try:
            res = reduce(updater, parts)
        except TypeError:
            return ""
        return res

    def get_params(self):
        return json.dumps(self.params)

    def inject(self, injection, inj):
        params = deepcopy(self.params)
        param = params
        if inj.get('part') == 'param':
            for p in inj.get('path')[:-1]:
                param = param[p]
            old_value = param[inj.get('path')[-1]]
            del param[inj.get('path')[-1]]
            if self.tag in inj.get('path')[-1]:
                new_param = inj.get('path')[-1].replace(self.tag, injection)
            else:
                new_param = injection
            param[new_param] = old_value
        if inj.get('part') == 'value':
            for p in inj.get('path')[:-1]:
                param = param[p]
            if self.tag in param[inj.get('path')[-1]]:
                param[inj.get('path')[-1]] = param[inj.get('path')[-1]].replace(self.tag, injection)
            else:
                param[inj.get('path')[-1]] = injection
        return json.dumps(params)
