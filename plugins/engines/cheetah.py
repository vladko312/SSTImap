from plugins.languages import python
from utils import rand


class Cheetah(python.Python):
    def init(self):
        self.update_actions({
            'render': {
                'render': '{code}',
                'header': '${{{header}}}',
                'trailer': '${{{trailer}}}',
                'test_render': f"""${{'{rand.randstrings[0]}'.join('{rand.randstrings[1]}')}}""",
                'test_render_expected': f'{rand.randstrings[0].join(rand.randstrings[1])}'
            },
            'evaluate': {
                # A way to check for actual Mako syntax
                'evaluate': """${{{code}}}"""
            }
        })

        self.set_contexts([
            # Text context, no closures
            {'level': 0},
            # Normal reflecting tag ${}
            {'level': 1, 'prefix': '{closure}}}', 'suffix': '', 'closures': python.ctx_closures},
            # Code blocks
            # This covers <% %s %>, <%! %s %>, <% %s=1 %>
            {'level': 1, 'prefix': '{closure}%>', 'suffix': '<%#', 'closures': python.ctx_closures},
            # If and for blocks
            # % if %s:\n% endif
            # % for a in %s:\n% endfor
            {'level': 5, 'prefix': '{closure}#\n', 'suffix': '\n', 'closures': python.ctx_closures},
            # Mako blocks
            {'level': 5, 'prefix': '</%doc>', 'suffix': '<%doc>'},
            {'level': 5, 'prefix': '</%def>', 'suffix': '<%def name="t(x)">', 'closures': python.ctx_closures},
            {'level': 5, 'prefix': '</%block>', 'suffix': '<%block>', 'closures': python.ctx_closures},
            {'level': 5, 'prefix': '</%text>', 'suffix': '<%text>', 'closures': python.ctx_closures},
        ])
