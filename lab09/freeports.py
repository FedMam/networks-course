import socket
import sys


def get_sysarg_safe(index: int, default: str):
    if len(sys.argv) <= index:
        return default
    return sys.argv[index]


ip = get_sysarg_safe(1, '127.0.0.1')
start_port = int(get_sysarg_safe(2, '0'))
end_port   = int(get_sysarg_safe(3, '65535'))

for port in range(start_port, end_port+1):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if sock.connect_ex((ip, port)) != 0:
        print(port, end='\t')
print()