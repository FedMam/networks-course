import socket
import time


host = '127.0.0.1'
port = 19288

print('Hello, this is PingerClient 2000')
client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    for i in range(1, 10+1):
        start_time = time.time()
        client_sock.settimeout(1.0)
        msg = f'Ping {i} {start_time}'
        print(f'Sending: {msg}')
        client_sock.sendto(msg.encode(), (host, port))
        try:
            resp, addr = client_sock.recvfrom(1024)
            end_time = time.time()
            print(f'Received response: {resp.decode()}\nRTT: {end_time - start_time}')
        except socket.timeout:
            print('Request timed out')

except Exception as E:
    print(f'Error: {E}')
finally:
    client_sock.close()