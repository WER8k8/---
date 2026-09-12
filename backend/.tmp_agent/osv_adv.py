import httpx

ids = ['GHSA-82fw-gwwq-j7x9', 'GHSA-fgmj-fm8m-jvvx', 'GHSA-67mh-4wv8-2f99',
       'GHSA-589f-c66p-hxr4', 'GHSA-v3m3-f69x-jf25', 'GHSA-w5hq-g745-h8pq']
with httpx.Client(timeout=30) as c:
    for g in ids:
        try:
            d = c.get(f'https://api.osv.dev/v1/vulns/{g}').json()
            summary = d.get('summary', '')[:110]
            aliases = d.get('aliases', [])
            fixed = []
            for a in d.get('affected', []):
                for rng in a.get('ranges', []):
                    for ev in rng.get('events', []):
                        if 'fixed' in ev:
                            fixed.append(ev['fixed'])
            print(f'{g} | {summary} | fixed_in={sorted(set(fixed))} | aliases={aliases}')
        except Exception as e:
            print(g, 'ERR', e)
