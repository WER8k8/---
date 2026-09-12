import httpx, time

checks = [
    ('undici', '7.29.1'), ('@vitest/mocker', '4.1.7'), ('echarts', '5.6.0'), ('esbuild', '0.21.5'),
    ('axios', '1.20.0'), ('dompurify', '3.4.15'), ('ws', '8.21.3'), ('js-yaml', '4.3.2'),
    ('@xmldom/xmldom', '0.9.12'), ('browserslist', '4.28.9'), ('form-data', '4.0.6'),
    ('@babel/core', '7.29.7'), ('engine.io-client', '6.6.6'), ('vue-echarts', '6.7.3'),
]
with httpx.Client(timeout=40) as c:
    for name, ver in checks:
        done = False
        for _ in range(3):
            try:
                j = c.post('https://api.osv.dev/v1/query',
                           json={'package': {'name': name, 'ecosystem': 'npm'}, 'version': ver}).json()
                vulns = j.get('vulns') or []
                status = 'VULNERABLE %d' % len(vulns) if vulns else 'clean'
                print('%s@%s: %s' % (name, ver, status))
                done = True
                break
            except Exception:
                time.sleep(3)
        if not done:
            print('%s@%s: OSV-UNREACHABLE' % (name, ver))
