import socket
import sys
import os
import io
import protocol


def get_sysarg_safe(arg_index: int, default: str=''):
    if len(sys.argv) <= arg_index:
        return default
    return sys.argv(arg_index)


server_host = get_sysarg_safe(1, '127.0.0.1')
server_port = int(get_sysarg_safe(2, '19283'))
timeout = float(get_sysarg_safe(3, '1.0'))

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

files_dir = os.path.dirname(os.path.abspath(sys.argv[0])) + '/client_files/'

print(f'Client started, server is {server_host}:{server_port}')

try:
    while True:
        action = input('>>> Send file or receive file? (s/r) ')
        if action.lower() == 's':
            filename = files_dir + input('>>> File name: ')
            try:
                sender = protocol.Sender(sock, timeout=timeout)
                with open(filename, 'rb') as file:
                    sender.send(file, (server_host, server_port))
            except OSError as E:
                print(f'File cannot be open: {E}')
            except KeyboardInterrupt:
                print('Interrupted')
            except Exception as E:
                print(f'Error: {E}')
        elif action.lower() == 'r':
            try:
                receiver = protocol.Receiver(sock)
                received_data, address = receiver.receive()

                if address != (server_host, server_port):
                    print(f'Warning: the sender address {address} does not match the server address {server_host}:{server_port}')

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
