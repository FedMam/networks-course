import socket
import random


host = '127.0.0.1'
port = 19288

print('Hello, this is UnreliableServer 3000')

server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_sock.bind((host, port))

print('Server started')

try:
    while True:
        msg, addr = server_sock.recvfrom(1024)
        msg = msg.decode()
        if random.random() >= 0.2:
            print(f'Received: {msg}')
            server_sock.sendto(msg.upper().encode(), addr)
        else:
            print('Package lost :(')
except KeyboardInterrupt:
    print('Finishing')
finally:
    server_sock.close()
