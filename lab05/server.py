import socket
import subprocess

host = '127.0.0.1'
port = 19283

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((host, port))
server_socket.listen(1)

print(f"Server started on host={host}, port={port}")

while True:
    client_socket, addr = server_socket.accept()
    print(f"Client connected: {addr}")
    command = client_socket.recv(1024).decode('utf-8')
    print(f"Command received: {command}")

    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        output = result.stdout + result.stderr
    except Exception as E:
        output = f'ERROR: {E}'

    client_socket.sendall(output.encode('utf-8'))
    client_socket.close()
    print('Successful, connection closed')
