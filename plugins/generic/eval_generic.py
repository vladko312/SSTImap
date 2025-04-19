from core.plugin import Plugin
from utils import closures
from utils import rand


class Eval_generic(Plugin):
    header_type = "add"
    priority = 10
    plugin_info = {
        "Description": """Template engines with evaluation capabilities in tags""",
        "Usage notes": """This plugin is a fallback to detect SSTI with evaluation capabilities.
No OS-related exploitation is provided, language evaluation works directly in a tag.
You can try to detect the template engine to search for the RCE payloads.""",
        "Authors": [
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",
        ]
    }

    def language_init(self):
        self.update_actions({
            'render': {
                'render': '{code}',
                'header': '{header[0]}+{header[1]}',
                'trailer': '{trailer[0]}+{trailer[1]}',
                'test_render': f"{rand.randints[0]}+{rand.randints[1]}*{rand.randints[2]}",
                'test_render_expected': f'{rand.randints[0]+rand.randints[1]*rand.randints[2]}'
            },
            'evaluate': {
                'call': 'render',
                'evaluate': "{code}",
                'test_os': '"Unknown"',
                'test_os_expected': r'^Unknown$'
            }
        })

        self.set_contexts([
            # Text context, no closures
            {'level': 0, 'wrappers': ["{{{code}}}", "{{{{{code}}}}}", "${{{code}}}", "<%={code}%>"]},
            {'level': 0, 'wrappers': ["#{{{code}}}", "{{={code}}}", "{{{{={code}}}}}", "\n={code}\n"]},
            {'level': 2, 'prefix': '{closure}}}', 'wrappers': ["{{{code}}}"], 'suffix': '{',
             'closures': ctx_closures},
            {'level': 2, 'prefix': '{closure}}}}}', 'wrappers': ["{{{{{code}}}}}"], 'suffix': '{{',
             'closures': ctx_closures},
            {'level': 2, 'prefix': '{closure}}}', 'wrappers': ["${{{code}}}"], 'suffix': '${',
             'closures': ctx_closures},
            {'level': 2, 'prefix': '{closure}%>', 'wrappers': ["<%={code}>"], 'suffix': '<%=',
             'closures': ctx_closures},
            {'level': 3, 'prefix': '{closure}}}', 'wrappers': ["#{{{code}}}"], 'suffix': '#{',
             'closures': ctx_closures},
            {'level': 3, 'prefix': '{closure}}}', 'wrappers': ["{{={code}}}"], 'suffix': '{=',
             'closures': ctx_closures},
            {'level': 3, 'prefix': '{closure}}}}}', 'wrappers': ["{{{{={code}}}}}"], 'suffix': '{{=',
             'closures': ctx_closures},
            {'level': 3, 'prefix': '{closure}\n', 'wrappers': ["\n={code}\n"], 'suffix': '\n=',
             'closures': ctx_closures},
            {'level': 3, 'prefix': '{closure}%}}', 'wrappers': ["{{{code}}}", "{{{{{code}}}}}",
                                                                "{{={code}}}", "{{{{={code}}}}}"], 'suffix': '{%',
             'closures': ctx_closures},
            # Comments
            {'level': 4, 'prefix': '*}}', 'wrappers': ["{{{code}}}", "{{{{{code}}}}}", "${{{code}}}",
                                                       "#{{{code}}}", "{{={code}}}", "{{{{={code}}}}}"],
             'suffix': '{*'},
            {'level': 4, 'prefix': '#}}', 'wrappers': ["{{{code}}}", "{{{{{code}}}}}", "${{{code}}}",
                                                       "#{{{code}}}", "{{={code}}}", "{{{{={code}}}}}"],
             'suffix': '{#'},
        ])

    language = 'unknown'


ctx_closures = {
    1: [
        closures.close_single_double_quotes + closures.integer,
        closures.close_function + closures.empty
    ],
    2: [
        closures.close_single_double_quotes + closures.integer + closures.string + closures.var,
        closures.close_function + closures.empty
    ],
    3: [
        closures.close_single_double_quotes + closures.integer + closures.string + closures.close_triple_quotes + closures.var,
        closures.close_function + closures.close_list + closures.close_dict + closures.empty
    ],
    4: [
        closures.close_single_double_quotes + closures.integer + closures.string + closures.close_triple_quotes + closures.var,
        closures.close_function + closures.close_list + closures.close_dict + closures.empty
    ],
    5: [
        closures.close_single_double_quotes + closures.integer + closures.string + closures.close_triple_quotes + closures.var,
        closures.close_function + closures.close_list + closures.close_dict + closures.empty,
        closures.close_function + closures.close_list + closures.empty,
        closures.if_loops + closures.empty
    ],
}