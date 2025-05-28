import socket
import sys
import os
import io
import protocol


def get_sysarg_safe(arg_index: int, default: str=''):
    if len(sys.argv) <= arg_index:
        return default
    return sys.argv(arg_index)


host = get_sysarg_safe(1, '127.0.0.1')
port = int(get_sysarg_safe(2, '19283'))
timeout = float(get_sysarg_safe(3, '1.0'))

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((host, port))

files_dir = os.path.dirname(os.path.abspath(sys.argv[0])) + '/server_files/'

clients = []

print('Server started')

try:
    while True:
        action = input('>>> Send file or receive file? (s/r) ')
        if action.lower() == 's':
            filename = files_dir + input('>>> File name: ')

            client_id = int(input('>>> Client ID: '))
            if client_id >= len(clients):
                print('Invalid client ID!')
                continue
            client_address = clients[client_id]

            try:
                sender = protocol.Sender(sock, timeout=timeout)
                with open(filename, 'rb') as file:
                    sender.send(file, client_address)
            except OSError as E:
                print(f'File cannot be open: {E}')
            except KeyboardInterrupt:
                print('Interrupted')
            except Exception as E:
                print(f'Error: {E}')
        elif action.lower() == 'r':
            try:
                receiver = protocol.Receiver(sock)
                received_data, client_address = receiver.receive()

                if client_address not in clients:
                    clients.append(client_address)
                print('Sender: Client #' + str(clients.index(client_address)))

                while True:
                    try:
                        filename = files_dir + input('>>> File name to save: ')
                        with open(filename, 'wb') as file:
                            file.write(received_data)
                        break
                    except OSError as E:
                        print(f'File cannot be open: {E}')
            except KeyboardInterrupt:
                print('Interrupted')
            except BaseException as E:
                print(f'Error: {E}')    
        else:
            print('Try again!')
except KeyboardInterrupt:
    print('Finishing')
except BaseException as E:
    print(f'Error: {E}')
finally:
    sock.close()