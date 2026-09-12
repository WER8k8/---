"""
QA-04 · 管理端 BFF + 健康检查 Locust 冒烟

运行:
  cd backend && python -m locust -f locustfile.py --host=http://127.0.0.1:8001
"""

from locust import HttpUser, between, task


class AdminBffUser(HttpUser):
    wait_time = between(0.5, 2)

    @task(5)
    def health(self):
        self.client.get("/api/v1/health", name="/api/v1/health")

    @task(2)
    def bff_dict(self):
        self.client.get("/api/v1/admin-bff/dict/plan_features", name="bff:plan_features")
