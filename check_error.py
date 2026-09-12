import requests

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
login_resp = requests.post('http://127.0.0.1:8001/api/v1/auth/login', json={'username_or_email': 'admin', 'password': 'admin123'}, headers=headers)
token = login_resp.json()['data']['access_token']
auth_headers = {'Authorization': f'Bearer {token}', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

rid = 'marketing/marketing-seo-specialist'
resp = requests.get(f'http://127.0.0.1:8001/api/v1/hermes/greedy/expert-inspect/{rid}', headers=auth_headers)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text}")
