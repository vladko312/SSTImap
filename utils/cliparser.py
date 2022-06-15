import argparse
from sstimap import version


def banner():
    msg = """\033[93m
    ╔══════╦══════╦═══════╗ ▀█▀
    ║ ╔════╣ ╔════╩══╗ ╔══╝═╗\033[41m▀\033[40m╔═
    ║ ╚════╣ ╚════╗  ║ ║    ║\033[41m{\033[40m║ \033[94m _ __ ___   __ _ _ __\033[93m
    ╚════╗ ╠════╗ ║  ║ ║    ║\033[41m*\033[40m║ \033[94m| '_ ` _ \\ / _` | '_ \\\033[93m
    ╔════╝ ╠════╝ ║  ║ ║    ║\033[41m}\033[40m║ \033[94m| | | | | | (_| | |_) |\033[93m
    ╚══════╩══════╝  ╚═╝    ╚╦╝\033[94m |_| |_| |_|\\__,_| .__/\033[93m
                             │                  \033[94m| |
                                                |_|\033[0m"""
    msg += f"\n\033[94m[*]\033[0m Version: {version}" \
           f"\n\033[94m[*]\033[0m Author: \033]8;;https://t.me/vladko312\007@vladko312\033]8;;\007" \
           f"\n\033[34m[*]\033[0m Based on \033]8;;https://github.com/epinna/tplmap\007Tplmap\033]8;;\007" \
           f"\n\033[91m[!] LEGAL DISCLAIMER\033[0m: Usage of SSTImap for attacking targets without prior mutual " \
           f"consent is illegal.\nIt is the end user's responsibility to obey all applicable local, state and " \
           f"federal laws.\nDevelopers assume no liability and are not responsible for any misuse or damage " \
           f"caused by this program\n\n"
    return msg


parser = argparse.ArgumentParser(description='SSTImap is an automatic SSTI detection and exploitation tool '
                                             'with predetermined and interactive modes.')
parser.add_argument('-v', '--version', action='version', version=f'SSTImap version {version}')


target = parser.add_argument_group(title="target",
                                   description="At least one of these options has to be provided to define target(s)")
target.add_argument("-u", "--url", dest="url",
                    help="Target URL (e.g. 'https://example.com/?name=test')")
target.add_argument("-i", "--interactive", action="store_true", dest="interactive",
                    help="Run SSTImap in interactive mode")


request = parser.add_argument_group(title="request", description="These options can specify how to connect to the "
                                                                 "target URL and add possible attack vectors")
request.add_argument("-M", "--marker", dest="marker",
                     help="Use string as injection marker (default '*')", default='*')
request.add_argument("-d", "--data", action="append", dest="data",
                     help="POST data param to send (e.g. 'param=value') [Stackable]", default=[])
request.add_argument("-H", "--header", action="append", dest="headers", metavar="HEADER",
                     help="Header to send (e.g. 'Header: Value') [Stackable]", default=[])
request.add_argument("-c", "--cookie", action="append", dest="cookies", metavar="COOKIE",
                     help="Cookie to send (e.g. 'Field=Value') [Stackable]", default=[])
request.add_argument("-m", "--method", dest="method",
                     help="HTTP method to use (default 'GET')", default='GET')
request.add_argument("-a", "--user-agent", dest="user_agent",
                     help="User-Agent header value to use", default=f'SSTImap/{version}')
request.add_argument("-A", "--random-user-agent", action="store_true", dest="random_agent",
                     help="Random User-Agent header value from a list of desktop browsers on every attempt")
request.add_argument("-p", "--proxy", dest="proxy",
                     help="Use a proxy to connect to the target URL")
request.add_argument("-V", "--verify-ssl", action="store_true", dest="verify_ssl",
                     help="Verify SSL certificates (not verified by default)")


detection = parser.add_argument_group(title="detection",
                                      description="These options can be used to customize the detection phase.")
detection.add_argument("-l", "--level", dest="level", type=int, default=1,
                       help="Level of escaping to perform (1-5, Default: 1)")
detection.add_argument("-L", "--force-level", dest="force_level", metavar=("LEVEL", "CLEVEL",),
                       help="Force a LEVEL and CLEVEL to test", nargs=2)
detection.add_argument("-e", "--engine", dest="engine",
                       help="Check only this backend template engine")
detection.add_argument("-r", "--technique", dest="technique",
                       help="Techniques R(endered) T(ime-based blind). Default: RT", default="RT")
detection.add_argument("-P", "--legacy", "--legacy-payloads", dest="legacy", action="store_true",
                       help="Include old payloads, that no longer work with newer versions of the engines")


payload = parser.add_argument_group(title="payload",
                                    description="These options can be used to get access to the template engine, "
                                                "filesystem or OS shell after an attack.")
payload.add_argument("-t", "--tpl-shell", dest="tpl_shell", action="store_true",
                     help="Prompt for an interactive shell on the template engine")
payload.add_argument("-T", "--tpl-code", dest="tpl_code",
                     help="Inject code in the template engine")
payload.add_argument("-x", "--eval-shell", dest="eval_shell", action="store_true",
                     help="Prompt for an interactive shell on the template engine base language")
payload.add_argument("-X", "--eval-code", dest="eval_code",
                     help="Evaluate code in the template engine base language")
payload.add_argument("-s", "--os-shell", dest="os_shell", action="store_true",
                     help="Prompt for an interactive operating system shell")
payload.add_argument("-S", "--os-cmd", dest="os_cmd",
                     help="Execute an operating system command")
payload.add_argument("-B", "--bind-shell", dest="bind_shell", nargs=1, type=int, metavar="PORT",
                     help="Spawn a system shell on a TCP PORT of the target and connect to it")
payload.add_argument("-R", "--reverse-shell", dest="reverse_shell", nargs=2, metavar=("HOST", "PORT",),
                     help="Run a system shell and back-connect to local HOST PORT")
payload.add_argument("-F", "--force-overwrite", dest="force_overwrite", action="store_true",
                     help="Force file overwrite when uploading")
payload.add_argument("-U", "--upload", dest="upload", metavar=("LOCAL", "REMOTE",),
                     help="Upload LOCAL to REMOTE files", nargs=2)
payload.add_argument("-D", "--download", dest="download", metavar=("REMOTE", "LOCAL",),
                     help="Download REMOTE to LOCAL files", nargs=2)

options = parser.parse_args()
