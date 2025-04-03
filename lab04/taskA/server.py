from flask import Flask, jsonify, render_template
import requests
import datetime

app = Flask(__name__)
journal_filename = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S') + '.txt'
datetime_format = '%Y/%m/%dT%H:%M:%S'

def fetch(url):
    try:
        response = requests.get(url, headers={'User-Agent': 'SanicServer3000 v1.0'})
        
        if response.status_code // 100 == 2:  # success
            return response.content, response.status_code
        else:
            return jsonify({'error': 'Failed to fetch data', 'status_code': response.status_code}), response.status_code
    except requests.exceptions.RequestException as E:
        return jsonify({'error': str(E)}), 500

@app.get("/<path:url>")
def fetch_url(url):
    response, status_code = fetch('https://' + url)

    journal.write(f'{datetime.datetime.now().strftime(datetime_format)} GET {url} {status_code}\n')
    journal.flush()

    return response, status_code

@app.post("/<path:url>")
def post(url):
    pass

if __name__ == '__main__':
    with open(journal_filename, 'w') as journal:
        app.run(host='127.0.0.1', port=19283)