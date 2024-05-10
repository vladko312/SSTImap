from plugins.languages import python
from utils import rand


class Cheetah(python.Python):
    generic_plugin = True

    def init(self):
        self.update_actions({
            'render': {
                'render': '{code}',
                'header': '${{{header}}}',
                'trailer': '${{{trailer}}}',
                # ${{getVar('a', '').replace($getVar('a', ''), '')}} is a way to trigger getVar and get empty result
                'test_render': f"""${{getVar('a', '').replace($getVar('a', ''), '')}}${{'{rand.randstrings[0]}'.join('{rand.randstrings[1]}')}}""",
                'test_render_expected': f'{rand.randstrings[0].join(rand.randstrings[1])}'
            },
            'evaluate': {
                'evaluate': """${{getVar('a', '').replace($getVar('a', ''), '')}}${{{code}}}"""
            }
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
