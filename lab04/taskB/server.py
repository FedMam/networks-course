from flask import Flask, Response, jsonify, request, render_template
import requests
import datetime
import os
import sys
import urllib.parse
import json
import random

from email.utils import parsedate_tz, mktime_tz, formatdate

app = Flask(__name__)
current_directory = os.path.dirname(os.path.abspath(__file__))
cache_directory = current_directory + '/cache/'
journal_filename = current_directory + '/' + datetime.datetime.now().isoformat() + '.txt'
user_agent = 'SanicServer3000 v2.0'


class Cache:
    def __init__(self, dir, expiration_time: int):
        self.dir = dir
        self.expiration_time = datetime.timedelta(seconds=int(expiration_time))
        self.cache_control = f'max-age={int(expiration_time)}'

    def _quote_url(self, url):
        # Примечание: я делаю это, чтобы избежать плохих символов в именах файлов
        return urllib.parse.quote(url, safe='')
    
    def _has_record(self, urlq):
        return os.path.isfile(self.dir + urlq + '.json')

    def _get_info(self, urlq):
        with open(self.dir + urlq + '.json', 'r') as file:
            return json.load(file)
    
    def _get_info_safe(self, urlq):
        return self._get_info(urlq) if self._has_record(urlq) else None
    
    def _get_data(self, urlq):
        with open(self.dir + urlq + '.bin', 'rb') as file:
            return file.read()
    
    def _get_data_safe(self, urlq):
        return self._get_data(urlq) if self._has_record(urlq) else None

    def _expired(self, info):
        return (datetime.datetime.now() - datetime.datetime.fromisoformat(info['date'])) > self.expiration_time

    def _delete_record(self, urlq):
        os.remove(self.dir + urlq + '.json')
        os.remove(self.dir + urlq + '.bin')
    
    def add_record(self, url: str, data: bytes, content_type: str):
        urlq = self._quote_url(url)
        
        etag = hex(random.randint(0, 0xffffffff))[2:]

        date = datetime.datetime.now()
        info = {
            'etag': etag,
            'url': url,
            'content-type': content_type,
            'date': date.replace(microsecond=0).isoformat(),
            'expires': (date.replace(microsecond=0) + self.expiration_time).isoformat()
        }
        with open(self.dir + urlq + '.json', 'w') as json_file:
            json.dump(info, json_file)
        with open(self.dir + urlq + '.bin', 'wb') as data_file:
            data_file.write(data)
        return info

    def get_info_if_not_expired(self, url: str):
        urlq = self._quote_url(url)

        if not self._has_record(urlq):
            return None
        
        info = self._get_info(urlq)
        if self._expired(info):
            self._delete_record(urlq)
            return None

        return info

    def get_data(self, url):
        urlq = self._quote_url(url)
        return self._get_data(urlq)


def parse_rfc2822_datetime(rfc2822: str):
    return datetime.datetime.fromtimestamp(mktime_tz(parsedate_tz(rfc2822)))


def convert_datetime_to_rfc2822(date: datetime.datetime):
    return formatdate(date.timestamp(), localtime=False, usegmt=True)


def fetch(url: str | None, if_modified_since: datetime.datetime | None=None, if_none_match: str | None=None):
    cache_info = cache.get_info_if_not_expired(url)
    if cache_info:
        expires = convert_datetime_to_rfc2822(datetime.datetime.fromisoformat(cache_info['expires']))
        cache_headers = {
            'Expires': expires,
            'Etag': cache_info['etag'],
            'Cache-Control': cache.cache_control
        }

        if if_modified_since is not None:
            not_modified_response = Response(None,
                                headers=cache_headers,
                                status=304)

            if datetime.datetime.fromisoformat(cache_info['date']) <= if_modified_since or \
               (if_none_match is not None and cache_info['etag'] == if_none_match):
                journal.write(f'{datetime.datetime.now().isoformat()} [INFO] Cache: {url} not modified\n')
                journal.flush()
                return not_modified_response
        
        journal.write(f'{datetime.datetime.now().isoformat()} [INFO] Cache: {url} retrieved from cache\n')
        journal.flush()
        return Response(cache.get_data(url),
                        status=200,
                        headers=cache_headers,
                        content_type=cache_info['content-type'])
    
    try:
        response = requests.get(url, headers={'User-Agent': user_agent})
        content_type = response.headers.get('Content-Type', default='application/octet-stream')
        
        if response.status_code // 100 == 2:  # success
            info = cache.add_record(url, response.content, content_type=content_type)
            date = convert_datetime_to_rfc2822(datetime.datetime.fromisoformat(info['date']))
            expires = convert_datetime_to_rfc2822(datetime.datetime.fromisoformat(info['expires']))
            
            return Response(response.content,
                            status=response.status_code,
                            headers={
                                'Expires': expires,
                                'Etag': info['etag'],
                                'Cache-Control': cache.cache_control
                            },
                            content_type=content_type)
        
        return Response(response.content,
                        status=response.status_code,
                        content_type=content_type)
    except requests.exceptions.RequestException as E:
        return Response('{"error": "' + str(E) + '"}',
                        status=500,
                        content_type='application/json')


@app.get("/<path:url>")
def fetch_url(url):
    journal.write(f'{datetime.datetime.now().isoformat()} [INFO] Request:  GET {url}\n')
    journal.flush()

    protocol = request.args.get('protocol', default='https')
    if_modified_since = request.headers.get('If-Modified-Since', default=None)
    if_modified_since = parse_rfc2822_datetime(if_modified_since) if if_modified_since is not None else None
    if_none_match = request.headers.get('If-None-Match', default=None)
    response = fetch(protocol + '://' + url, if_modified_since, if_none_match)

    journal.write(f'{datetime.datetime.now().isoformat()} [INFO] Response: GET {url} {response.status}\n')
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

    journal.write(f'{datetime.datetime.now().isoformat()} [INFO] Request: POST {url} {response.status}\n')
    journal.flush()

    return response


if __name__ == '__main__':
    os.makedirs(cache_directory, exist_ok=True)

    try:
        expiration_time = int(sys.argv[1])
        cache = Cache(cache_directory, expiration_time)
    except:
        cache = Cache(cache_directory, 300)

    with open(journal_filename, 'w') as journal:
        app.run(host='127.0.0.1', port=19283)