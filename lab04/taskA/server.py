from flask import Flask, Response, jsonify, request, render_template
import requests
import datetime
import os

app = Flask(__name__)
current_directory = os.path.dirname(os.path.abspath(__file__))
journal_filename = current_directory + '/' + datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S') + '.txt'
datetime_format = '%Y/%m/%dT%H:%M:%S'
user_agent = 'SanicServer3000 v1.4'


def fetch(url):
    try:
        response = requests.get(url, headers={'User-Agent': user_agent})
        
        return Response(response.content,
                        status=response.status_code,
                        content_type=response.headers.get('Content-Type', default='application/octet-stream'))
    except requests.exceptions.RequestException as E:
        return Response('{"error": "' + str(E) + '"}',
                        status=500,
                        content_type='application/json')


@app.get("/<path:url>")
def fetch_url(url):
    protocol = request.args.get('protocol', default='https')
    response = fetch(protocol + '://' + url)

    journal.write(f'{datetime.datetime.now().strftime(datetime_format)} GET  {url} {response.status}\n')
    journal.flush()

    return response


def post(url, data, content_type):
    try:
        response = requests.post(url, data,
                                 headers={'User-Agent': user_agent,
                                          'Content-Type': content_type})

        if response.status_code // 100 == 2:  # success
            return Response(response.content,
                            status=response.status_code,
                            content_type=response.headers.get('Content-Type', default='application/octet-stream'))
        else:
            return Response('{"error": "Failed to post data"}',
                            status=response.status_code,
                            content_type='application/json')
    except requests.exceptions.RequestException as E:
        return Response('{"error": "' + str(E) + '"}',
                        status=500,
                        content_type='application/json')


@app.post("/<path:url>")
def post_url(url):
    protocol = request.args.get('protocol', default='https')
    response = post(protocol + '://' + url, request.get_data(), request.headers.get('Content-Type', default='application/octet-stream'))

    journal.write(f'{datetime.datetime.now().strftime(datetime_format)} POST {url} {response.status}\n')
    journal.flush()

    return response


if __name__ == '__main__':
    with open(journal_filename, 'w') as journal:
        app.run(host='127.0.0.1', port=19283)