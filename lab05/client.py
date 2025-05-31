import socket

host = '127.0.0.1'
port = 19283

command = input('Command: ')

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((host, port))
client_socket.sendall(command.encode('utf-8'))

result = client_socket.recv(4096).decode('utf-8')
print(f"Command output:\n{result}")
client_socket.close()

print('Success')
