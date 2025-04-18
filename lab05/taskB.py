import os
import socket
import base64
from getpass import getpass


def exchange_msg(socket, msg: bytes):
    try:
        print('[YOU ]', msg.decode().strip())
        socket.send(msg)
        recv = socket.recv(1024).decode()
        print('[SERV]', recv)
    except Exception as E:
        print('[FAIL]', E)


smtp_server = 'smtp.mail.ru'
smtp_port = 465

username = input('Your email: ')
password = getpass('Your email password: ')
from_addr = username
to_addr = input('Recipient email: ')

files_dir = os.path.dirname(os.path.abspath(__file__)) + '/files'
filename = input('File name: ')

if filename.find('../') != -1:
    print('!!! Injection attempt, exiting !!!')
    exit(-2)
if not filename.endswith('.html') and not filename.endswith('.txt'):
    print('Unsupported file format')
    exit(-1)

subject = filename
with open(f'{files_dir}/{filename}', 'rb') as file:
    body = file.read()

print('[INFO] Connecting...')

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((smtp_server, smtp_port))

print('[INFO] Connection established')

# recv = client_socket.recv(1024).decode()
# print('[SERV]', recv)

exchange_msg(client_socket, f'HELO {smtp_server}\r\n'.encode())
exchange_msg(client_socket, b'AUTH LOGIN\r\n')
exchange_msg(client_socket, base64.b64encode(username.encode()) + b'\r\n')
exchange_msg(client_socket, base64.b64encode(password.encode()) + b'\r\n')
exchange_msg(client_socket, f'MAIL FROM:<{from_addr}>\r\n'.encode())
exchange_msg(client_socket, f'RCPT TO:<{to_addr}>\r\n'.encode())
exchange_msg(client_socket, f'Subject: {subject}\r\nFrom: {from_addr}\r\nTo: {to_addr}\r\n\r\n'.encode() + body + b'\r\n.\r\n')
exchange_msg(client_socket, b'QUIT\r\n')

client_socket.close()