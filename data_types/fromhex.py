from core.data_type import DataType
from copy import deepcopy


class FromHex(DataType):
    help_text = """Supply hex-encoded parts of the binary body."""

    def injection_points(self, data, all_injectable=False):
        injs = []
        self.params = []
        params_list = self._process_values(data)
        for idx, param in enumerate(params_list):
            self.params.append(param)
            if all_injectable or self.tag in param:
                injs.append({'field': 'Body', 'param': idx})
        return injs

    def _process_values(self, values):
        return values.copy()

    def get_params(self):
        return b"".join([bytes.fromhex(x.replace(self.tag, "")) for x in self.params])

    def inject(self, injection, inj):
        params = deepcopy(self.params)
        if self.tag in params[inj.get('param')]:
            params[inj.get('param')] = params[inj.get('param')].replace(self.tag, injection.encode().hex())
        else:
            params[inj.get('param')] = injection.encode().hex()
        return b"".join([bytes.fromhex(x.replace(self.tag, "")) for x in params])
