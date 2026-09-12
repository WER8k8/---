import requests

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
login_resp = requests.post('http://127.0.0.1:8001/api/v1/auth/login', json={'username_or_email': 'admin', 'password': 'admin123'}, headers=headers)
token = login_resp.json()['data']['access_token']
auth_headers = {'Authorization': f'Bearer {token}', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

experts = [
    'marketing/seo-expert',
    'marketing/marketing-seo-specialist',
    'marketing/marketing-content-creator',
    'marketing/marketing-growth-hacker',
    'engineering/site-reliability-engineer',
    'engineering/full-stack-developer',
    'finance/finance-fpa-analyst',
    'sales/sales-deal-strategist',
    'product/product-trend-researcher',
    'design/design-ui-designer',
    'testing/test-automation-engineer',
    'support/support-ticket-manager',
    'paid-media/paid-media-ppc-strategist',
    'game-development/game-designer',
    'project-management/project-manager-senior',
    'strategy/business-strategy-analyst',
    'specialized/ai-ethics-consultant',
]

print(f"开始巡检 {len(experts)} 个专家...")
for i, expert in enumerate(experts, 1):
    print(f"\n{i}. 巡检: {expert}")
    resp = requests.get(f'http://127.0.0.1:8001/api/v1/hermes/greedy/expert-inspect/{expert}', headers=auth_headers)
    data = resp.json()
    if data.get('code') == 0:
        result = data.get('data', {})
        print(f"   分类: {result.get('category')}")
        print(f"   分数: {result.get('score')}")
        print(f"   待办: {len(result.get('next_actions', []))}")
    else:
        print(f"   错误: {data.get('message')}")

print("\n\n获取日志总数...")
logs_resp = requests.get('http://127.0.0.1:8001/api/v1/system/audit/logs?page_size=100', headers=auth_headers)
logs_data = logs_resp.json()
print(f"总日志数: {logs_data.get('total', 0)}")
