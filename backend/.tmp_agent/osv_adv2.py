import httpx

ids = ['GHSA-82fw-gwwq-j7x9', 'GHSA-589f-c66p-hxr4', 'GHSA-v3m3-f69x-jf25', 'GHSA-w5hq-g745-h8pq']
with httpx.Client(timeout=30) as c:
    for g in ids:
        for attempt in range(5):
            try:
                d = c.get(f'https://api.osv.dev/v1/vulns/{g}').json()
                summary = d.get('summary', '')[:110]
                aliases = d.get('aliases', [])
                sev = d.get('severity', [])
                details = []
                for a in d.get('affected', []):
                    for rng in a.get('ranges', []):
                        details.append([ev for ev in rng.get('events', [])])
                print(f'{g} | {summary} | severity={sev} | ranges={details} | aliases={aliases}')
                break
            except Exception as e:
                if attempt == 4:
                    print(g, 'ERR', type(e).__name__)
