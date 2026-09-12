import httpx, json

payload = {"undici": ["7.29.1"], "@vitest/mocker": ["4.1.7"], "echarts": ["5.6.0"], "esbuild": ["0.21.5"]}
with httpx.Client(timeout=60) as c:
    r = c.post('https://registry.npmjs.org/-/npm/v1/security/advisories/bulk', json=payload)
    print('HTTP', r.status_code)
    try:
        j = r.json()
        for pkg, advs in j.items():
            if not advs:
                print('%s: clean' % pkg)
            else:
                print('%s: %d advisories' % (pkg, len(advs)))
                for a in advs:
                    print('   ', a.get('severity'), a.get('module_name'), a.get('vulnerable_versions'))
    except Exception as e:
        print('PARSE-ERR', e, r.text[:300])
