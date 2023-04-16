import threading
import socket
import sys
from utils.loggers import log


class TcpClient:
    sock = None
    timeout = None

    def __init__(self, host, port, timeout=1):
        self.sock = socket.create_connection((host, port)) #, timeout=timeout)
        self.timeout = timeout

    def shell(self):
        shell_exited = threading.Event()
        def get_output():
            while not shell_exited.is_set():
                try:
                    output = self.sock.recv(1)
                    if output:
                        stdout = getattr(sys.stdout, 'buffer', sys.stdout)
                        stdout.write(output)
                        stdout.flush()
                except EOFError:
                    log.log(25, 'Reverse shell closed connection')
                    shell_exited.set()
        t = threading.Thread(target=get_output)
        t.daemon = True
        t.start()
        try:
            while not shell_exited.is_set():
                stdin = getattr(sys.stdin, 'buffer', sys.stdin)
                user_input = stdin.read(1)
                if user_input:
                    try:
                        self.sock.send(user_input)
                    except EOFError:
                        log.log(25, 'Your system closed connection')
                        shell_exited.set()
                else:
                    shell_exited.set()
        except KeyboardInterrupt:
            shell_exited.set()
        while t.is_alive():
            t.join(timeout=self.timeout)
        log.log(21, 'Exiting bind shell 2')

