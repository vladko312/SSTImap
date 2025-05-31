from plugins.languages import python
from utils import rand


class Python_generic(python.Python):
    priority = 9
    plugin_info = {
        "Description": """Template engines with Python statement evaluation in tags""",
        "Usage notes": "This plugin can be used to speed up detection in simple contexts as well as for covering more of such engines.",
        "Authors": [
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",
        ],
    }

    def init(self):
        self.update_actions({
            'render': {
                'render': '{code}',
                'header': '{header[0]}+{header[1]}',
                'trailer': '{trailer[0]}+{trailer[1]}',
                'test_render': f"'{rand.randstrings[0]}'.join('{rand.randstrings[1]}')",
                'test_render_expected': f'{rand.randstrings[0].join(rand.randstrings[1])}'
            },
            'render_error': {
                'render': """{code}""",
                'header': """getattr("", str({header[0]}+{header[1]})+str(""",
                'trailer': """).rstrip()+str({trailer[0]}+{trailer[1]}))""",
                'wrapper_type': "global",
                'test_render': f"""str('{rand.randstrings[0]}'.join('{rand.randstrings[1]}'))""",
                'test_render_expected': f'{rand.randstrings[0].join(rand.randstrings[1])}'
            },
            'evaluate': {
                'evaluate': "{code}"
            }
        })

        self.set_contexts([
            # Text context, no closures
            {'level': 0, 'wrappers': ["{{{code}}}", "{{{{{code}}}}}", "${{{code}}}", "<%={code}%>"]},
            {'level': 0, 'wrappers': ["#{{{code}}}", "{{={code}}}", "{{{{={code}}}}}", "\n={code}\n"]},
            {'level': 2, 'prefix': '{closure}}}', 'wrappers': ["{{{code}}}"], 'suffix': '{',
             'closures': python.ctx_closures},
            {'level': 2, 'prefix': '{closure}}}}}', 'wrappers': ["{{{{{code}}}}}"], 'suffix': '{{',
             'closures': python.ctx_closures},
            {'level': 2, 'prefix': '{closure}}}', 'wrappers': ["${{{code}}}"], 'suffix': '${',
             'closures': python.ctx_closures},
            {'level': 2, 'prefix': '{closure}%>', 'wrappers': ["<%={code}>"], 'suffix': '<%=',
             'closures': python.ctx_closures},
            {'level': 3, 'prefix': '{closure}}}', 'wrappers': ["#{{{code}}}"], 'suffix': '#{',
             'closures': python.ctx_closures},
            {'level': 3, 'prefix': '{closure}}}', 'wrappers': ["{{={code}}}"], 'suffix': '{=',
             'closures': python.ctx_closures},
            {'level': 3, 'prefix': '{closure}}}}}', 'wrappers': ["{{{{={code}}}}}"], 'suffix': '{{=',
             'closures': python.ctx_closures},
            {'level': 3, 'prefix': '{closure}\n', 'wrappers': ["\n={code}\n"], 'suffix': '\n=',
             'closures': python.ctx_closures},
            {'level': 3, 'prefix': '{closure}%}}', 'wrappers': ["{{{code}}}", "{{{{{code}}}}}",
                                                                "{{={code}}}", "{{{{={code}}}}}"], 'suffix': '{%',
             'closures': python.ctx_closures},
            # Comments
            {'level': 4, 'prefix': '*}}', 'wrappers': ["{{{code}}}", "{{{{{code}}}}}", "${{{code}}}",
                                                       "#{{{code}}}", "{{={code}}}", "{{{{={code}}}}}"],
             'suffix': '{*'},
            {'level': 4, 'prefix': '#}}', 'wrappers': ["{{{code}}}", "{{{{{code}}}}}", "${{{code}}}",
                                                       "#{{{code}}}", "{{={code}}}", "{{{{={code}}}}}"],
             'suffix': '{#'},
        ])
