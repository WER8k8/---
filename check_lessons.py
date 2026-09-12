import requests

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
login_resp = requests.post('http://127.0.0.1:8001/api/v1/auth/login', json={'username_or_email': 'admin', 'password': 'admin123'}, headers=headers)
token = login_resp.json()['data']['access_token']
auth_headers = {'Authorization': f'Bearer {token}', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

rank_resp = requests.get('http://127.0.0.1:8001/api/v1/hermes/greedy/agency/economics/rank?limit=20', headers=auth_headers)
rank_data = rank_resp.json()
print(f"Rank response keys: {list(rank_data.keys())}")

if 'data' in rank_data:
    ranks = rank_data['data']
    print(f"Data type: {type(ranks)}")
    if isinstance(ranks, dict):
        print(f"Data keys: {list(ranks.keys())}")
        roles = ranks.get('roles', [])
    else:
        roles = ranks
    
    print(f"\n获取到 {len(roles)} 个专家")
    
    for role in roles:
        rid = role.get('role_id')
        if rid:
            mem_resp = requests.get(f'http://127.0.0.1:8001/api/v1/hermes/greedy/agency/memory/{rid}', headers=auth_headers)
            mem_data = mem_resp.json()
            print(f"\n专家: {rid}")
            print(f"Memory response: {mem_data}")
