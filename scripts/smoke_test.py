#!/usr/bin/env python3
"""Exercise a running synthetic demo through FastAPI or the Next.js proxy.

This creates demo cases and performs the documented demo reset. It refuses
non-demo servers. It never contacts real council services or paid AI APIs.
"""
import argparse
import json
import urllib.error
import urllib.request


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:3000')
    args = parser.parse_args()

    def request(path, method='GET', body=None, role=None, expected=(200, 201)):
        headers = {'Content-Type': 'application/json'}
        if role:
            headers['X-Demo-Role'] = role
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(args.url.rstrip('/') + '/api' + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                status, payload = response.status, json.load(response)
        except urllib.error.HTTPError as exc:
            status, payload = exc.code, json.load(exc)
        if expected == 'error':
            assert status >= 400, f'{method} {path} unexpectedly accepted unsafe/unauthorised input'
        else:
            accepted = expected if isinstance(expected, tuple) else (expected,)
            assert status in accepted, f'{method} {path}: {status} {payload}'
        return payload

    health = request('/health')
    assert health['demo_mode'] is True, 'Smoke reset is restricted to synthetic demo mode.'
    assert health['provider'] in ('deterministic', 'deterministic-demo'), 'Select deterministic AI before repeatable smoke validation.'
    request('/cases', expected='error')
    request('/demo/reset', 'POST', {}, 'staff', 'error')
    baseline = request('/demo/reset', 'POST', {}, 'admin')['case_count']
    config = request('/config')
    modules = request('/modules')['modules']
    prompts = {
        'service-navigator': 'I need help with housing repairs and damp in my rented home.',
        'employment': 'I have communication and customer service skills and want an entry level job.',
        'community': 'I want to volunteer in my community and find a local support group.',
        'triage': 'There is a missed bin collection on my street. Please route this enquiry.',
        'learning': 'I want to learn digital skills and progress towards a new career.',
        'custom': 'My home is cold and I want a practical energy and warmth plan.',
    }
    created = []
    for module in modules:
        if not module['enabled']:
            continue
        case = request('/enquiries', 'POST', {
            'message': prompts[module['id']], 'module_id': module['id'],
            'borough': config['challenge']['borough'], 'resident_name': 'Synthetic smoke test',
        })
        assert case['analysis']['simulated'] is True
        assert 0 <= case['analysis']['confidence'] <= 1
        assert case['analysis']['workflow_steps']
        assert case['status'] != 'resolved', 'AI must not resolve consequential requests automatically.'
        assert case['analysis']['sources'], f"No evidence for known scenario {module['id']}"
        assert all(s['synthetic'] for s in case['analysis']['sources'])
        created.append(case)
        print(f"PASS {module['id']}: {case['reference']} with {len(case['analysis']['sources'])} attributed sources")
    assert created, 'No activated modules to validate.'
    case = created[0]
    request(f"/cases/{case['id']}", 'PATCH', {'status': 'resolved', 'review_note': ''}, 'staff', 'error')
    reviewed = request(f"/cases/{case['id']}", 'PATCH', {
        'status': 'resolved', 'review_note': 'Synthetic staff review: checked evidence and supplied next steps; no eligibility decision.'
    }, 'staff')
    assert reviewed['status'] == 'resolved'
    request(f"/cases/{case['id']}/feedback", 'POST', {'rating': 4})
    impact = request('/impact', role='staff')
    assert impact['total_cases'] == baseline + len(created)
    assert impact['resolved_count'] >= 1
    assert all(m['kind'] in ('observed', 'prototype_test', 'estimated', 'simulated') for m in impact['metrics'])
    request('/documents', 'POST', {
        'title': 'Unapproved text', 'content': 'This is unapproved synthetic resource content for verification.',
        'borough': config['challenge']['borough'], 'module_id': modules[0]['id'],
        'source_label': 'Synthetic smoke fixture', 'synthetic': True, 'approved': False,
    }, 'admin', 'error')
    request('/enquiries', 'POST', {'message': '', 'module_id': modules[0]['id']}, expected='error')
    audit = request('/audit', role='admin')['events']
    assert audit, 'Workflows should be audited.'
    after = request('/demo/reset', 'POST', {}, 'admin')
    assert after['case_count'] == baseline
    repeat = request('/demo/reset', 'POST', {}, 'admin')
    assert repeat['case_count'] == baseline
    print('PASS staff review, feedback, labelled impact, auth boundaries, validation, audit, and two repeatable resets')


if __name__ == '__main__':
    main()
