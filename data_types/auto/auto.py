from core.data_type import DataType, loaded_data_types
from urllib import parse
import json
from utils.loggers import log


class Auto(DataType):
    data_type_info = {
        "Description": """Guess POST body format based on supplied parts.""",
        "Usage notes": """By default, only 'json' and 'form' are detected with 'text' as fallback.
Appropriate Content-Type header is often required by the server.
This data type also supports passing options to detected data types.""",
        "Authors": [
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",
        ],
        "Options": [
            "special=False - also test for 'fromhex' and 'fromfile' data types",
            "['json' only] deep_update=True - recursively update dictionaries",
            "['form' only] keep_blank_values=True - keep empty values (e.g. in a=&b=5, param 'a' will not be removed)",
        ],
    }

    _detected = None

    def injection_points(self, data, all_injectable=False):
        if not self._detected:
            self._detect(data)
        return self._detected.injection_points(data, all_injectable=all_injectable)

    def _detect(self, values):
        test_json = True
        for v in values:
            try:
                # Ensure dict at top level
                json.loads(v.replace(self.tag, "")).keys()
            except:
                test_json = False
                break
        if test_json:
            log.log(24, "POST data type detected as 'json'")
            self._detected = loaded_data_types["json"](self.args, self.tag)
            return
        test_form = True
        try:
            # TODO: even more strict detection
            parse.parse_qs('&'.join(values), strict_parsing=True)
        except:
            test_form = False
        if test_form:
            log.log(24, "POST data type detected as 'form'")
            self._detected = loaded_data_types["form"](self.args, self.tag)
            return
        if self.args.get("data_params", {}).get("special", False):
            test_hex = True
            for v in values:
                try:
                    bytes.fromhex(v.replace(self.tag, ""))
                except:
                    test_hex = False
                    break
            if test_hex:
                log.log(24, "POST data type detected as 'fromhex'")
                self._detected = loaded_data_types["fromhex"](self.args, self.tag)
                return
            test_file = True
            for v in values:
                try:
                    open(v, "rb").close()
                except:
                    test_file = False
                    break
            if test_file:
                log.log(24, "POST data type detected as 'fromfile'")
                self._detected = loaded_data_types["fromfile"](self.args, self.tag)
                return
        log.log(25, "POST data type not detected, assuming 'text'")
        self._detected = loaded_data_types["text"](self.args, self.tag)
        return

    def get_params(self):
        if not self._detected:
            return {}
        return self._detected.get_params()

    def inject(self, injection, inj):
        if not self._detected:
            return {}
        return self._detected.inject(injection, inj)
