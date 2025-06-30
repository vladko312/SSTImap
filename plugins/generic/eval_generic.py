from core.plugin import Plugin
from utils import closures
from utils import rand
from utils.loggers import log


class Eval_generic(Plugin):
    header_type = "add"
    priority = 10
    plugin_info = {
        "Description": """Template engines with evaluation capabilities in tags""",
        "Usage notes": """This plugin is a fallback to detect SSTI with evaluation capabilities.
No OS-related exploitation is provided, language evaluation works directly in a tag.
You can try to detect the template engine to search for the RCE payloads.""",
        "Authors": [
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",
        ]
    }

    def language_init(self):
        self.update_actions({
            'render': {
                'render': '{code}',
                'header': '{header[0]}+{header[1]}',
                'trailer': '{trailer[0]}+{trailer[1]}',
                'test_render': f"{rand.randints[0]}+{rand.randints[1]}*{rand.randints[2]}",
                'test_render_expected': f'{rand.randints[0]+rand.randints[1]*rand.randints[2]}'
            },
            'render_error': {
                # Not actually rendering, just inject (1/0).zxy.zxy and look for errors
                # This both checks division by zero, nonexistent attributes and attribute of undefined
                'wrapper_type': "global",
                'render': '{code}',
                'header': '',
                'trailer': '',
                'test_render': f"({rand.randints[0]}/0).zxy.zxy",
                'test_render_expected': f'zxy'
            },
            'evaluate': {
                'call': 'render',
                'evaluate': "{code}",
                'test_os': '"Unknown"',
                'test_os_expected': r'^Unknown$'
            }
        })

        self.set_contexts([
            # Text context, no closures
            {'level': 0, 'wrappers': ["{{{code}}}", "{{{{{code}}}}}", "${{{code}}}", "<%={code}%>",
                                      "#{{{code}}}", "{{={code}}}", "{{{{={code}}}}}", "\n={code}\n"]},
            {'level': 2, 'prefix': '{closure}}}', 'wrappers': ["{{{code}}}"], 'suffix': '{"1"',
             'closures': ctx_closures},
            {'level': 2, 'prefix': '{closure}}}}}', 'wrappers': ["{{{{{code}}}}}"], 'suffix': '{{"1"',
             'closures': ctx_closures},
            {'level': 2, 'prefix': '{closure}}}', 'wrappers': ["${{{code}}}"], 'suffix': '${"1"',
             'closures': ctx_closures},
            {'level': 2, 'prefix': '{closure}%>', 'wrappers': ["<%={code}%>"], 'suffix': '<%="1"',
             'closures': ctx_closures},
            {'level': 3, 'prefix': '{closure}}}', 'wrappers': ["#{{{code}}}"], 'suffix': '#{"1"',
             'closures': ctx_closures},
            {'level': 3, 'prefix': '{closure}}}', 'wrappers': ["{{={code}}}"], 'suffix': '{="1"',
             'closures': ctx_closures},
            {'level': 3, 'prefix': '{closure}}}}}', 'wrappers': ["{{{{={code}}}}}"], 'suffix': '{{="1"',
             'closures': ctx_closures},
            {'level': 3, 'prefix': '{closure}\n', 'wrappers': ["\n={code}\n"], 'suffix': '\n="1"',
             'closures': ctx_closures},
            {'level': 3, 'prefix': '{closure}%}}', 'wrappers': ["{{{code}}}", "{{{{{code}}}}}",
                                                                "{{={code}}}", "{{{{={code}}}}}"], 'suffix': '{%"1"',
             'closures': ctx_closures},
            # Comments
            {'level': 4, 'prefix': '*}}', 'wrappers': ["{{{code}}}", "{{{{{code}}}}}", "${{{code}}}",
                                                       "#{{{code}}}", "{{={code}}}", "{{{{={code}}}}}"],
             'suffix': '{*'},
            {'level': 4, 'prefix': '#}}', 'wrappers': ["{{{code}}}", "{{{{{code}}}}}", "${{{code}}}",
                                                       "#{{{code}}}", "{{={code}}}", "{{{{={code}}}}}"],
             'suffix': '{#'},
        ])

    language = 'unknown'

    def _detect_render(self, reflection="render"):
        if reflection != "render_error":
            return super()._detect_render(reflection=reflection)
        render_action = self.actions.get("render_error")
        if not render_action:
            return
        true_render_action = self.actions.get("render")
        if not true_render_action:
            return
        # Print what it's going to be tested
        log.log(23, f'{self.plugin} plugin is testing reflection for error-based injection')
        for prefix, suffix, wrapper in self._generate_contexts():
            payload = render_action.get('test_render')
            wrapper_type = render_action.get(f'wrapper_type', 'local')
            header_rand = [rand.randint_n(10, 4), rand.randint_n(10, 4)]
            header = render_action.get('header')
            trailer_rand = [rand.randint_n(10, 4), rand.randint_n(10, 4)]
            trailer = render_action.get('trailer')
            discovered = False
            result = self.render(code=payload, header=header, trailer=trailer, header_rand=header_rand,
                                 trailer_rand=trailer_rand, prefix=prefix, suffix=suffix, wrapper=wrapper,
                                 wrapper_type=wrapper_type, error=True)
            resultl = result.lower()
            if "ZeroDivisionError" in result:
                log.log(24, f'{self.plugin} plugin detected reflection of Python error message')
                discovered = True
                self.language = "python"
            elif "java.lang.ArithmeticException" in result:
                log.log(24, f'{self.plugin} plugin detected reflection of Java error message')
                discovered = True
                self.language = "java"
            elif "Arithmetic operation failed" in result:
                log.log(24, f'{self.plugin} plugin detected reflection of Freemarker (Java) error message')
                discovered = True
                self.language = "java"
            elif "ReferenceError" in result or "TypeError" in result:
                log.log(24, f'{self.plugin} plugin detected reflection of JavaScript error message')
                discovered = True
                self.language = "javascript"
            elif "Division by zero" in result or "DivisionByZeroError" in result:
                log.log(24, f'{self.plugin} plugin detected possible reflection of PHP error message')
                discovered = True
                self.language = "php"
            elif "divided by 0" in result:
                log.log(24, f'{self.plugin} plugin detected possible reflection of Ruby error message')
                discovered = True
                self.language = "ruby"
            elif "divi" in resultl and ("0" in resultl or "zero" in resultl):
                log.log(24, f'{self.plugin} plugin detected possible reflection of a generic zero division error message')
                discovered = True
            elif "function" in resultl and ("error" in resultl or "exception" in resultl or "unknown" in resultl):
                log.log(24, f'{self.plugin} plugin detected possible reflection of a generic unknown function error message')
                discovered = True
            elif "template" in resultl and ("error" in resultl or "exception" in resultl):
                log.log(24, f'{self.plugin} plugin detected possible reflection of a generic template error message')
                discovered = True
            if discovered:
                # Assume rendering to have the same context
                self.set('render', true_render_action.get('render'))
                self.set('error', True)
                self.set('header', true_render_action.get('header'))
                self.set('trailer', true_render_action.get('trailer'))
                self.set('prefix', prefix)
                self.set('suffix', suffix)
                self.set('wrapper', wrapper)
                self.set('wrapper_type', true_render_action.get(f'wrapper_type', 'local'))
                self.channel.detected("render_error", {'expected': "Any error"})
                return


ctx_closures = {
    1: [
        closures.close_single_double_quotes + closures.integer,
        closures.close_function + closures.empty
    ],
    2: [
        closures.close_single_double_quotes + closures.integer + closures.string + closures.var,
        closures.close_function + closures.empty
    ],
    3: [
        closures.close_single_double_quotes + closures.integer + closures.string + closures.close_triple_quotes + closures.var,
        closures.close_function + closures.close_list + closures.close_dict + closures.empty
    ],
    4: [
        closures.close_single_double_quotes + closures.integer + closures.string + closures.close_triple_quotes + closures.var,
        closures.close_function + closures.close_list + closures.close_dict + closures.empty
    ],
    5: [
        closures.close_single_double_quotes + closures.integer + closures.string + closures.close_triple_quotes + closures.var,
        closures.close_function + closures.close_list + closures.close_dict + closures.empty,
        closures.close_function + closures.close_list + closures.empty,
        closures.if_loops + closures.empty
    ],
}