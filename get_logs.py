import requests
import json

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
login_resp = requests.post('http://127.0.0.1:8001/api/v1/auth/login', json={'username_or_email': 'admin', 'password': 'admin123'}, headers=headers)
token = login_resp.json()['data']['access_token']
auth_headers = {'Authorization': f'Bearer {token}', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

logs_resp = requests.get('http://127.0.0.1:8001/api/v1/system/audit/logs?page_size=100', headers=auth_headers)
data = logs_resp.json()
print(f'总日志数: {data.get("total", 0)}')
print(f'当前页日志数: {len(data.get("data", []))}')
print()
for log in data.get('data', []):
    print(f"[{log.get('created_at')}] {log.get('action')} - {log.get('resource_type')} - {log.get('resource_id')}")
