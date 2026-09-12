import urllib.request, json
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
def get(path):
    req = urllib.request.Request("http://127.0.0.1:8000"+path, headers={"User-Agent":UA})
    try:
        r = urllib.request.urlopen(req, timeout=8)
        return r.status, r.read()[:3000]
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:3000]
    except Exception as e:
        return "ERR", str(e).encode()[:400]

for p in ["/api/v1/health", "/openapi.json"]:
    s,b = get(p)
    print(f"=== {p} -> {s} ===")
    if p=="/openapi.json":
        try:
            d=json.loads(b); paths=d.get("paths",{})
            print("openapi version:", d.get("openapi"))
            print("PATH COUNT:", len(paths))
            from collections import Counter
            c=Counter()
            for k in paths:
                parts=k.split("/")
                seg=parts[3] if len(parts)>3 else k
                c[seg]+=1
            print("TOP PREFIXES:", dict(c.most_common(30)))
        except Exception as e:
            print("parse err", e, b[:400])
    else:
        print(b.decode("utf-8","ignore")[:600])
