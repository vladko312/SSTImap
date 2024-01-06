from core.data_type import DataType
from urllib import parse
from copy import deepcopy


class Form(DataType):
    help_text = """Supply key=value pairs for application/x-www-form-urlencoded content-type.
    keep_blank_values=True - keep empty values (e.g. in a=&b=5, param 'a' will not be removed)"""

    def injection_points(self, data, all_injectable=False):
        injs = []
        self.params = {}
        params_dict_list = self._process_values(data)
        for param, value_list in params_dict_list.items():
            self.params[param] = value_list
            if self.tag in param:
                injs.append({'field': 'Body', 'part': 'param', 'param': param})
            for idx, value in enumerate(value_list):
                if all_injectable or self.tag in value:
                    injs.append({'field': 'Body', 'part': 'value', 'value': value, 'param': param, 'idx': idx})
        return injs

    def _process_values(self, values):
        return parse.parse_qs('&'.join(values), keep_blank_values=self.args.get("data_params", {}).get("keep_blank_values", True))

    def get_params(self):
        return deepcopy(self.params)

    def inject(self, injection, inj):
        params = deepcopy(self.params)
        if inj.get('part') == 'param':
            old_value = params[inj.get('param')]
            del params[inj.get('param')]
            if self.tag in inj.get('param'):
                new_param = inj.get('param').replace(self.tag, injection)
            else:
                new_param = injection
            params[new_param] = old_value
        if inj.get('part') == 'value':
            if self.tag in params[inj.get('param')][inj.get('idx')]:
                params[inj.get('param')][inj.get('idx')] = params[inj.get('param')][inj.get('idx')].replace(
                    self.tag, injection)
            else:
                params[inj.get('param')][inj.get('idx')] = injection
        return params
