from plugins.languages import ruby
from utils import rand
from utils.loggers import log


class Mustache_detect(ruby.Ruby):
    formatter = "sstimap"
    header_type = "cat"
    priority = 5
    plugin_info = {
        "Description": """Detect vulnerable versions of Mustache engine in Ruby""",
        "Usage notes": """Full exploitation payload would be released later""",
        "Authors": [
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",  # Original SSTImap payload
        ],
        "References": [
            "GHSA-5hrj-7fc3-cmx9: https://github.com/mustache/mustache/security/advisories/GHSA-5hrj-7fc3-cmx9",
        ],
        "Engine": [
            "Homepage: https://mustache.github.io/",
            "Github: https://github.com/mustache/mustache",
        ],
    }

    def language_init(self):
        self.update_actions({
            'render': {
                'render': """SSTIMAP:code;""",
                'header': """SSTIMAP:header:get,0;{{!1337}}SSTIMAP:header:get,1;""",
                'trailer': """SSTIMAP:trailer:get,0;{{!7331}}SSTIMAP:trailer:get,1;""",
                'test_render': """{{class.class.to_s.reverse}}{{#escape}}><{{/escape}}""",
                'test_render_expected': 'ssalC&gt;&lt;'
            },
            'render_error': {
                'render': """SSTIMAP:code;""",
                'header': "",
                'trailer': "",
                'test_render': """{{#method}}zxyzxy{{/method}}method""",
                'test_render_expected': 'unknown error',
            },
            'boolean': {
                'call': 'inject',
                # Using a mix of runtime and syntax errors
                'test_bool_true':  "{{#zxyzxy}}#method{{/zxyzxy}}/method",
                'test_bool_false': "{{#method}}#zxyzxy{{/method}}/zxyzxy",
                'verify_bool_true':  "{{#class}}zxyzxy{{/class}}",
                'verify_bool_false': "{{#zxyzxy}}class{{/class}}"
            },
        })

        self.set_contexts([
            {'level': 0},
            {'level': 1, 'prefix': 'a}}', 'suffix': '{{!'},
        ])

    language = 'ruby'

    def _detect_render(self, reflection="render"):
        if reflection != "render_error":
            return super()._detect_render(reflection=reflection)
        render_action = self.actions.get("render_error")
        if not render_action:
            return
        true_render_action = self.actions.get("render")
        if not true_render_action:
            return
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
            if "undefined method 'zxyzxy' for class" in result:
                log.log(24, f'{self.plugin} plugin detected reflection of Ruby v4 error message')
                discovered = True
                self.language = "ruby:v4"
            elif "undefined method `zxyzxy' for class" in result:
                log.log(24, f'{self.plugin} plugin detected reflection of Ruby v2/v3 error message')
                discovered = True
                self.language = "ruby:v2-3"
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
                self.channel.detected("render_error", {'expected': "Ruby error"})
                return


