import requests

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
login_resp = requests.post('http://127.0.0.1:8001/api/v1/auth/login', json={'username_or_email': 'admin', 'password': 'admin123'}, headers=headers)
token = login_resp.json()['data']['access_token']
auth_headers = {'Authorization': f'Bearer {token}', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

rank_resp = requests.get('http://127.0.0.1:8001/api/v1/hermes/greedy/agency/economics/rank?limit=50', headers=auth_headers)
rank_data = rank_resp.json()['data']
roles = rank_data.get('roles', [])

print(f"有效的专家角色列表 ({len(roles)} 个):")
for i, role in enumerate(roles, 1):
    rid = role.get('role_id')
    name = role.get('name')
    category = role.get('category')
    print(f"{i}. {rid} ({name}) - {category}")

print(f"\n测试前5个有效的专家巡检:")
for i, role in enumerate(roles[:5], 1):
    rid = role.get('role_id')
    print(f"\n{i}. 巡检: {rid}")
    resp = requests.get(f'http://127.0.0.1:8001/api/v1/hermes/greedy/expert-inspect/{rid}', headers=auth_headers)
    data = resp.json()
    print(f"   响应: {data}")
