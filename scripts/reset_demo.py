#!/usr/bin/env python3
"""Reset a running demo through its guarded API."""
import argparse
import json
import os
import urllib.error
import urllib.request

def main():
    parser = argparse.ArgumentParser(description='Reset synthetic demo data only.')
    parser.add_argument('--url', default='http://127.0.0.1:8765')
    args = parser.parse_args()
    headers = {'Content-Type': 'application/json', 'X-Demo-Role': 'admin'}
    token = os.environ.get('ADMIN_API_TOKEN')
    if token:
        headers['Authorization'] = f'Bearer {token}'
    request = urllib.request.Request(args.url.rstrip('/') + '/api/demo/reset', data=b'{}', headers=headers, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            print(json.dumps(json.load(response), indent=2))
    except urllib.error.HTTPError as exc:
        raise SystemExit(f'Reset refused ({exc.code}): {exc.read().decode()}')

if __name__ == '__main__':
    main()
