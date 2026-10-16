#!/usr/bin/env python3
"""Check the actual API and retry during startup; no third-party dependency."""
import argparse
import json
import time
import urllib.error
import urllib.request

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:8765')
    parser.add_argument('--wait', type=float, default=0)
    args = parser.parse_args()
    deadline = time.monotonic() + args.wait
    while True:
        try:
            with urllib.request.urlopen(args.url.rstrip('/') + '/api/health', timeout=2) as response:
                result = json.load(response)
            if result.get('status') != 'ok':
                raise ValueError(f'API not healthy: {result}')
            print(json.dumps(result))
            return
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            if time.monotonic() >= deadline:
                raise SystemExit(f'API health check failed: {exc}')
            time.sleep(0.5)

if __name__ == '__main__':
    main()
