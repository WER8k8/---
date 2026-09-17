"""
QA-04 · 管理端 BFF + 健康检查 Locust 冒烟

运行:
  cd backend && python -m locust -f locustfile.py --host=http://127.0.0.1:8001

注意：项目 WAF 拦截裸 HTTP 客户端 UA，内部调用须带
  User-Agent: YouDingSaaS-Internal/1.0
  （curl/python-requests 默认 UA 会吃 403）
"""

from locust import HttpUser, between, task

# 内部调用白名单 UA（对齐 start-dev-admin.ps1 Test-LoginProxy / WAF USER_AGENT_WHITELIST）
_UA = {"User-Agent": "YouDingSaaS-Internal/1.0"}


class AdminBffUser(HttpUser):
    wait_time = between(0.5, 2)

    @task(5)
    def health(self):
        self.client.get("/api/v1/health", name="/api/v1/health", headers=_UA)

    @task(2)
    def bff_dict(self):
        self.client.get(
            "/api/v1/admin-bff/dict/plan_features",
            name="bff:plan_features",
            headers=_UA,
        )
