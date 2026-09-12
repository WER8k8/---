import httpx

ids = ['GHSA-cp6q-959q-f8rh', 'GHSA-j95f-988m-3j2f', 'GHSA-fgmj-fm8m-jvvx', 'GHSA-67mh-4wv8-2f99',
       'GHSA-2883-xcg3-v3hh', 'GHSA-5339-hvwr-7582', 'GHSA-95h2-gj7x-gx9w', 'GHSA-g5xx-pwrp-g3fv']
with httpx.Client(timeout=30) as c:
    for g in ids:
        for attempt in range(5):
            try:
                d = c.get(f'https://api.osv.dev/v1/vulns/{g}').json()
                summary = d.get('summary', '')[:120]
                aliases = d.get('aliases', [])
                sev = d.get('severity', [])
                fixed = []
                for a in d.get('affected', []):
                    for rng in a.get('ranges', []):
                        for ev in rng.get('events', []):
                            if 'fixed' in ev:
                                fixed.append(ev['fixed'])
                print(f'{g} | {summary} | severity={sev} | fixed_in={sorted(set(fixed))} | aliases={aliases}')
                break
            except Exception as e:
                if attempt == 4:
                    print(g, 'ERR', type(e).__name__)
