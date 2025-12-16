import argparse
from sstimap import version


def banner():
    msg = """\033[93m
    ╔══════╦══════╦═══════╗ ▀█▀
    ║ ╔════╣ ╔════╩══╗ ╔══╝═╗\033[41m▀\033[49m╔═
    ║ ╚════╣ ╚════╗  ║ ║    ║\033[41m{\033[49m║ \033[94m _ __ ___   __ _ _ __\033[93m
    ╚════╗ ╠════╗ ║  ║ ║    ║\033[41m*\033[49m║ \033[94m| '_ ` _ \\ / _` | '_ \\\033[93m
    ╔════╝ ╠════╝ ║  ║ ║    ║\033[41m}\033[49m║ \033[94m| | | | | | (_| | |_) |\033[93m
    ╚══════╩══════╝  ╚═╝    ╚╦╝\033[94m |_| |_| |_|\\__,_| .__/\033[93m
                             │                  \033[94m| |
                                                |_|\033[0m"""
    msg += f"\n\033[94m[*]\033[0m Version: {version}" \
           f"\n\033[94m[*]\033[0m Author: \033]8;;https://github.com/vladko312\007@vladko312\033]8;;\007" \
           f"\n\033[34m[*]\033[0m Based on \033]8;;https://github.com/epinna/tplmap\007Tplmap\033]8;;\007" \
           f"\n\033[91m[!] LEGAL DISCLAIMER\033[0m: Usage of SSTImap for attacking targets without prior mutual " \
           f"consent is illegal.\nIt is the end user's responsibility to obey all applicable local, state and " \
           f"federal laws.\nDevelopers assume no liability and are not responsible for any misuse or damage " \
           f"caused by this program"
    return msg


parser = argparse.ArgumentParser(description='SSTImap is an automatic SSTI detection and exploitation tool '
                                             'with predetermined and interactive modes.')
parser.add_argument('-V', '--version', action='version', version=f'SSTImap version {version}')
parser.add_argument("--module", dest="module", help="Provide information about the module ('list' to show all modules)")
parser.add_argument("--config", dest="config", help="Use custom config file or directory")
parser.add_argument("--no-color", action="store_const", const=False, dest="colour", help="Disable color in output")


target = parser.add_argument_group(title="target",
                                   description="At least one of these options has to be provided to define target(s)")
target.add_argument("-u", "--url", dest="url",
                    help="Target URL (e.g. 'https://example.com/?name=test')")
target.add_argument("-i", "--interactive", action="store_const", const=True, dest="interactive",
                    help="Run SSTImap in interactive mode")
target.add_argument("--load-urls", dest="load_urls", help="File or directory to load URLs from")
target.add_argument("--load-forms", dest="load_forms", help="File or directory to load forms from")

request = parser.add_argument_group(title="request", description="These options can specify how to connect to the "
                                                                 "target URL and add possible attack vectors")
request.add_argument("-M", "--marker", dest="marker",
                     help="Use string as injection marker (default '*')")
request.add_argument("-d", "--data", action="append", dest="data",
                     help="Request body data param to send (e.g. 'param=value') [Stackable]", default=[])
request.add_argument("--data-type", dest="data_type",
                     help="Request body data type (default 'auto')")
request.add_argument("--data-params", action="append", dest="data_params", metavar="KEY=VALUE",
                     help="Request body data processing params", default=[])
request.add_argument("-H", "--header", action="append", dest="headers", metavar="HEADER",
                     help="Header to send (e.g. 'Header: Value') [Stackable]", default=[])
request.add_argument("-C", "--cookie", action="append", dest="cookies", metavar="COOKIE",
                     help="Cookie to send (e.g. 'Field=Value') [Stackable]", default=[])
request.add_argument("-m", "--method", dest="method",
                     help="HTTP method to use (default 'GET')")
request.add_argument("-a", "--user-agent", dest="user_agent",
                     help="User-Agent header value to use")
request.add_argument("-A", "--random-user-agent", action="store_const", const=True, dest="random_agent",
                     help="Random User-Agent header value from a list of desktop browsers on every request")
request.add_argument("--delay", dest="delay", type=float, help="Delay between requests (Default/0: no delay)")
request.add_argument("-p", "--proxy", dest="proxy",
                     help="Use a proxy to connect to the target URL")
request.add_argument("--verify-ssl", action="store_const", const=True, dest="verify_ssl",
                     help="Verify SSL certificates (not verified by default)")
request.add_argument("--log-response", action="store_const", const=True, dest="log_response",
                     help="Include HTTP responses into ~/.sstimap/sstimap.log")

crawler = parser.add_argument_group(title="crawler", description="These options can specify how to detect URLs and "
                                                                 "forms on the target website.")
crawler.add_argument("-c", "--crawl", dest="crawl_depth", type=int,
                     help="Depth to crawl (default/0: don't crawl)")
crawler.add_argument("-f", "--forms", action="store_const", const=True, dest="forms",
                     help="Scan page(s) for forms")
crawler.add_argument("--empty-forms", action="store_const", const=True, dest="empty_forms",
                     help="Treat pages without params as GET forms")
crawler.add_argument("--crawl-exclude", dest="crawl_exclude", help="RegEx in URLs to not crawl")
crawler.add_argument("--crawl-domains", dest="crawl_domains",
                     help="Crawl other domains: Y(es) / S(ubdomains) / N(o). Default: S")
crawler.add_argument("--save-urls", dest="save_urls", help="File or directory to save crawled URLs to")
crawler.add_argument("--save-forms", dest="save_forms", help="File or directory to save crawled forms to")

detection = parser.add_argument_group(title="detection",
                                      description="These options can be used to customize the detection phase.")
detection.add_argument("-l", "--level", dest="level", type=int,
                       help="Level of escaping to perform (1-5, Default: 1)")
detection.add_argument("-L", "--force-level", dest="force_level", metavar=("LEVEL", "CLEVEL",),
                       help="Force a LEVEL and CLEVEL to test", nargs=2, type=int)
detection.add_argument("-e", "--engine", dest="engine",
                       help="Check only this backend template engine")
detection.add_argument("-r", "--technique", dest="technique",
                       help="Techniques: R(endered) E(rror-based) B(oolean error-based blind) T(ime-based blind). Default: REBT")
detection.add_argument("--bool-ok", dest="boolean_regex_ok",
                       help="RegEx to match when boolean error-based blind payload evaluates correctly")
detection.add_argument("--bool-err", dest="boolean_regex_err",
                       help="RegEx to match when boolean error-based blind payload causes an error")
detection.add_argument("--bool-match", dest="boolean_match",
                       help="Comma-separated list of matching params or 'all'. Default: code,header_count,cookie_count,"
                            "byte_len,body_len,body_words,body_lines,encoding,redirects,time,url,content_type,server")
detection.add_argument("--bool-match-min", dest="boolean_match_min", type=int,
                       help="Minimum amount of usable params for matching. Default: 7")
detection.add_argument("--bool-fuzzy", dest="boolean_fuzzy", nargs=2, type=float, metavar=("STABLE", "ERROR",),
                       help="Allow small deviations in some of the matching parameters. Default: 0.05 0.1")
detection.add_argument("--bool-samples", dest="boolean_samples", nargs=3, type=int, metavar=("COUNT", "MIN", "MAX",),
                       help="Amount of tests to profile the page and payload sizes. Default: 10 1 7")
detection.add_argument("--blind-delay", dest="time_based_blind_delay", type=int,
                       help="Delay to detect time-based blind injection (Default: 4 seconds)")
detection.add_argument("--verify-blind-delay", dest="time_based_verify_blind_delay", type=int,
                       help="Delay to verify and exploit time-based blind injection (Default: 30 seconds)")
detection.add_argument("--legacy", dest="legacy", action="store_const", const=True,
                       help="Include old payloads, that no longer work with newer versions of the engines")
detection.add_argument("--generic", dest="generic", action="store_const", const=False,
                       help="Try dedicated payloads for generic engines, detecting more context.")
detection.add_argument("--run", dest="run", action="store_const", const=True,
                       help="Run detection at the start of SSTImap in interactive mode.")

payload = parser.add_argument_group(title="payload",
                                    description="These options can be used to get access to the template engine, "
                                                "filesystem or OS shell after an attack.")
payload.add_argument("-t", "--tpl-shell", dest="tpl_shell", action="store_const", const=True,
                     help="Prompt for an interactive shell on the template engine")
payload.add_argument("-T", "--tpl-code", dest="tpl_code",
                     help="Inject code in the template engine")
payload.add_argument("-x", "--eval-shell", dest="eval_shell", action="store_const", const=True,
                     help="Prompt for an interactive shell on the template engine base language")
payload.add_argument("-X", "--eval-code", dest="eval_code",
                     help="Evaluate code in the template engine base language")
payload.add_argument("-s", "--os-shell", dest="os_shell", action="store_const", const=True,
                     help="Prompt for an interactive operating system shell")
payload.add_argument("-S", "--os-cmd", dest="os_cmd",
                     help="Execute an operating system command")
payload.add_argument("-B", "--bind-shell", dest="bind_shell", nargs=1, type=int, metavar="PORT",
                     help="Spawn a system shell on a TCP PORT of the target and connect to it")
payload.add_argument("-R", "--reverse-shell", dest="reverse_shell", nargs=2, metavar=("HOST", "PORT",),
                     help="Run a system shell and back-connect to local HOST PORT")
payload.add_argument("--remote-shell", dest="remote_shell",
                     help="Expected system shell on the target (default '/bin/sh')")
payload.add_argument("-F", "--force-overwrite", dest="force_overwrite", action="store_const", const=True,
                     help="Force file overwrite when uploading")
payload.add_argument("-U", "--upload", dest="upload", metavar=("LOCAL", "REMOTE",),
                     help="Upload LOCAL to REMOTE files", nargs=2)
payload.add_argument("-D", "--download", dest="download", metavar=("REMOTE", "LOCAL",),
                     help="Download REMOTE to LOCAL files", nargs=2)

options = parser.parse_args()
