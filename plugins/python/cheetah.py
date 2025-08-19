from plugins.languages import python
from utils import rand


class Cheetah(python.Python):
    priority = 5
    generic_plugin = True
    plugin_info = {
        "Description": """Cheetah3 template engine""",
        "Authors": [
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",
        ],
        "Engine": [
            "Homepage: https://cheetahtemplate.org/",
            "Github: https://github.com/CheetahTemplate3/cheetah3",
        ],
    }

    def init(self):
        self.update_actions({
            'render': {
                'render': '{code}',
                'header': '${{{header[0]}+{header[1]}}}',
                'trailer': '${{{trailer[0]}+{trailer[1]}}}',
                # ${{getVar('a', '').replace($getVar('a', ''), '')}} is a way to trigger getVar and get empty result
                'test_render': f"""${{getVar('a', '').replace($getVar('a', ''), '')}}${{'{rand.randstrings[0]}'.join('{rand.randstrings[1]}')}}""",
                'test_render_expected': f'{rand.randstrings[0].join(rand.randstrings[1])}'
            },
            'render_error': {
                'render': """{code}""",
                'header': """${{getattr("", str({header[0]}+{header[1]})+str(""",
                'trailer': """).rstrip()+str({trailer[0]}+{trailer[1]}))}}""",
                'test_render': f"""$getVar('a', '').replace($getVar('a', ''), '')+'{rand.randstrings[0]}'.join('{rand.randstrings[1]}')""",
                'test_render_expected': f'{rand.randstrings[0].join(rand.randstrings[1])}'
            },
            'evaluate': {
                'evaluate': """${{getVar('a', '').replace($getVar('a', ''), '')}}${{{code}}}"""
            },
            'evaluate_error': {
                'evaluate': """$getVar('a', '').replace($getVar('a', ''), '')+str({code})"""
            },
            'evaluate_boolean': {
                'call': 'inject',
                'evaluate_blind': """${{getVar('a', '').replace($getVar('a', ''), '')}}${{str(1 / bool(eval(__import__('base64').urlsafe_b64decode('{code_b64}').decode())))}}"""
            },
        })

        self.set_contexts([
            # Text context, no closures
            # Reflecting tag name $inject is also escaped by non-letter symbols, which $ is
            {'level': 0},
            # Normal reflecting tags ${}, $[], $()
            {'level': 1, 'prefix': '{closure}}}', 'suffix': '', 'closures': python.ctx_closures},
            {'level': 1, 'prefix': '{closure}]', 'suffix': '', 'closures': python.ctx_closures},
            {'level': 1, 'prefix': '{closure})', 'suffix': '', 'closures': python.ctx_closures},
            # comments
            {'level': 2, 'prefix': '*#\n', 'suffix': ''},
            # comment out part of syntax, like in IF oneliners
            {'level': 2, 'prefix': '{closure}', 'suffix': ' ##', 'closures': python.ctx_closures},
            # Code blocks
            # This covers <%= %s %>, <% %s %>
            {'level': 2, 'prefix': '{closure}%>', 'suffix': '<%', 'closures': python.ctx_closures},
            # If and for blocks
            {'level': 5, 'prefix': '{closure}##\n', 'suffix': '\n', 'closures': python.ctx_closures},
            # Cheetah blocks
            {'level': 5, 'prefix': '#end cache', 'suffix': '#cache'},
            {'level': 5, 'prefix': '#end def', 'suffix': '#def t(x)'},
            {'level': 5, 'prefix': '#end block', 'suffix': '#block'},
            {'level': 5, 'prefix': '#end raw ', 'suffix': ' #raw'},
        ])
