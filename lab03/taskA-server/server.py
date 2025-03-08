import os
import sys
import socket
import re
from urllib.parse import unquote

FILES_DIR = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))) + '/files'
GET_REQUEST_RE = r'GET /([^ ]+) HTTP/1\.(0|1).*'
ENCODING = 'iso-8859-1'
HTML_BAD_REQUEST = '''<!DOCTYPE html>
<html>
<head>
    <title>400 Bad Request</title>
</head>
<body>
    <h1>400 Bad Request</h1>
    <p>Usage: GET /<filename></p>
</body>
</html>'''
HTML_NOT_FOUND = '''<!DOCTYPE html>
<html>
<head>
    <title>404 Not Found</title>
</head>
<body>
    <h1>404 Not Found</h1>
    <p>The requested URL was not found on this server.</p>
</body>
</html>'''


def build_response(status_code: str = '200 OK', content_type: str = 'application/octet-stream', data: bytes = b''):
    return (f'HTTP/1.1 {status_code}\n' +
            f'Content-Type: {content_type}\n' +
            f'Content-Length: {len(data)}\n' +
            f'Connection: close\n\n').encode(ENCODING) + data


def build_response_bad_request():
    return build_response(status_code='400 Bad Request',
                          content_type='text/html; charset=UTF-8',
                          data=HTML_BAD_REQUEST.encode('utf-8'))


def build_response_not_found():
    return build_response(status_code='404 Not Found',
                          content_type='text/html; charset=UTF-8',
                          data=HTML_NOT_FOUND.encode('utf-8'))


if __name__ == '__main__':
    host = '127.0.0.1'
    if len(sys.argv) < 2 or not sys.argv[1].isdigit():
        print('usage: server.py <server-port>')
        exit(-1)
    port = int(sys.argv[1])

    print(f'[INFO] Starting server at host {host}, port {port}...')

    serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serv_sock.bind((host, port))
    backlog = 10
    serv_sock.listen(backlog)

    print(f'[INFO] Server ready')

    while True:
        clnt_sock, addr = serv_sock.accept()
        request = clnt_sock.recv(1024).decode(ENCODING)

        try:
            match = re.match(GET_REQUEST_RE, request)
            if not match:
                print(f'[ERRO] Invalid request: {request[:32]}...')
                clnt_sock.sendall(build_response_bad_request())
            else:
                filename = unquote(match.group(1))
                file_path = f'{FILES_DIR}/{filename}'
                if not os.path.isfile(file_path):
                    print(f'[ERRO] File not found: {filename}')
                    clnt_sock.sendall(build_response_not_found())
                else:
                    with open(file_path, 'rb') as file_data:
                        print(f'[INFO] Sending file: {filename}')
                        clnt_sock.sendall(build_response(status_code='200 OK',
                                                           content_type='application/octet-stream',
                                                           data=file_data.read()))
        finally:
            clnt_sock.close()