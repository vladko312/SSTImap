from plugins.languages import python
from utils import rand


class Tornado(python.Python):
    
    def init(self):

        self.update_actions({
            'render': {
                'render': '{{{{{code}}}}}',
                'header': '{{{{{header}}}}}',
                'trailer': '{{{{{trailer}}}}}',
                'test_render': f"""'{rand.randstrings[0]}'}}}}{{% raw '{rand.randstrings[0]}'.join('{rand.randstrings[1]}') %}}{{{{'{rand.randstrings[1]}'""",
                'test_render_expected': f'{rand.randstrings[0] + rand.randstrings[0].join(rand.randstrings[1]) + rand.randstrings[1]}'
            }
        })

        self.set_contexts([
            # Text context, no closures
            {'level': 0},
            # This covers {{%s}}
            {'level': 1, 'prefix': '{closure}}}}}', 'suffix': '', 'closures': python.ctx_closures},
            # This covers {% %s %}
            {'level': 1, 'prefix': '{closure}%}}', 'suffix': '', 'closures': python.ctx_closures},
            # Comment blocks
            {'level': 5, 'prefix': '#}}', 'suffix': '{#'},
        ])

