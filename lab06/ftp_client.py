import socket
import os
import sys
import re
import configparser

UPL_DIR_NAME = 'files'
UPL_DIR = os.path.dirname(os.path.abspath(sys.argv[0])) + '/' + UPL_DIR_NAME
DL_DIR_NAME = 'download'
DL_DIR = os.path.dirname(os.path.abspath(sys.argv[0])) + '/' + DL_DIR_NAME


class FTPClient:
    def __init__(self, host, port):
        # Соединение
        print('Hello, this is SuperFTPClient 4000')
        print(f'Connecting to host: {host}, port: {port}')
        self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.main_socket.connect((host, port))
        print('Connected')
        self.recv()

    def recv(self):
        response = self.main_socket.recv(1024).decode().strip()
        print(f'Server: {response}')
        return response
    
    def send_command(self, command):
        print(f'Sending command {command.split()[0]}')
        self.main_socket.sendall((command + '\r\n').encode())
        return self.recv()
    
    def enter_passive_mode(self):
        response = self.send_command('PASV')
        # Выделить хост и порт из ответа на PASV
        parts = re.match(r'^[^\(\)]*\(([\d,]*)\)\.\s*$', response).group(1).split(',')
        
        host = '.'.join(parts[:4])
        port = int(parts[4]) * 256 + int(parts[5])
        print(f'Host: {host}\nPort: {port}')
        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_socket.connect((host, port))
        return data_socket
    
    def login(self, username, password):
        print(f'Logging in as user: {username}, password: {"*" * len(password)}')
        self.send_command(f'USER {username}')
        self.send_command(f'PASS {password}')

    def recv_data(self, socket, buffer, format='bytes'):
        while True:
            data = socket.recv(4096)
            if not data:
                break
            buffer.write(data.decode() if format == 'str' else data)

    def list_files(self):
        print('File list queried')

        data_socket = self.enter_passive_mode()
        self.send_command('LIST')
        print('File list:')
        self.recv_data(data_socket, sys.stdout, format='str')
        print()
        data_socket.close()
        self.recv()
    
    def upload(self, filename):
        # Защита от инъекций
        if filename.startswith('..'):
            print('-15 social credit 不好')
            return
        
        print(f'Uploading {filename}')

        data_socket = self.enter_passive_mode()
        self.send_command(f'STOR {filename}')
        with open(f'{UPL_DIR}/{filename}', 'rb') as file:
            data_socket.sendall(file.read())
        data_socket.close()
        self.recv()

        print(f'Successfully uploaded {filename}')
    
    def download(self, filename):
        print(f'Downloading {filename}')

        data_socket = self.enter_passive_mode()
        self.send_command(f'RETR {filename}')
        with open(f'{DL_DIR}/{filename}', 'wb') as file:
            self.recv_data(data_socket, file)
        data_socket.close()
        self.recv()

        print(f'Successfully downloaded {filename}')
    
    def close(self):
        self.send_command('QUIT')
        self.main_socket.close()


config = configparser.ConfigParser()
config.read('ftp_client.config')

ftp_client = FTPClient(config['Server']['host'], int(config['Server']['port']))
ftp_client.login(config['Server']['username'], config['Server']['password'])

print('Commands:\nls - list files\nput <filename> - upload file to server\nget <filename> - download file to server')
print(f'All files to upload are stored in the <program-path>/{UPL_DIR_NAME} directory')
print(f'All downloaded files are stored in the <program-path>/{DL_DIR_NAME} directory')

try:
    while True:
        cmd = input('>>> ')

        try:
            if cmd == 'ls':
                ftp_client.list_files()
            elif cmd.startswith('put'):
                ftp_client.upload(cmd.split()[1])
            elif cmd.startswith('get'):
                ftp_client.download(cmd.split()[1])
            else:
                print('Unknown command, try again')
        except KeyboardInterrupt:
            print('Interrupted')
        except Exception as E:
            print(f'Error: {E}')
except KeyboardInterrupt:
    print('Finished, exiting')
finally:
    ftp_client.close()