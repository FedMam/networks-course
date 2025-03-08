import sys
import socket
import re
from urllib.parse import quote

ENCODING = 'iso-8859-1'
STATUS_CODE_RE = r'HTTP/1\.\d (\d+).*'


def build_request(serv_host: str, serv_port: int, file_name: str):
    return f'''GET /{quote(file_name)} HTTP/1.1
Host: {serv_host}:{serv_port}'''.encode(ENCODING)


if __name__ == '__main__':
    if len(sys.argv) < 4 or not sys.argv[2].isdigit():
        print('usage: client.py <server-host> <server-port> <filename>')
        exit(-1)

    serv_host = sys.argv[1]
    serv_port = int(sys.argv[2])
    file_name = sys.argv[3]

    try:
        clnt_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clnt_sock.connect((serv_host, serv_port))
        clnt_sock.send(build_request(serv_host, serv_port, file_name))

        response = b''
        while True:
            part = clnt_sock.recv(1024)
            response += part
            if len(part) < 1024:
                break
        
        response = response.decode(ENCODING)

        match = re.match(STATUS_CODE_RE, response)
        if not match:
            print(f'[ERRO] Invalid response format: {response[:32]}...')
        status_code = match.group(1)
        if status_code == '200':
            print('[INFO] File successfully received')
        elif status_code == '404':
            print(f'[ERRO] Error: file {file_name} not found')
        else:
            print(f'[ERRO] Failed to receive file: status code {status_code}')

        print()
        print(response)
        print()
        print('[INFO] Finished, exiting')
    except Exception as e:
        print(f'[ERRO] Failed to receive file: {e}')
        exit(-2)