
from locust import HttpUser, task, between, events
import random
import json

class WebsiteUser(HttpUser):
    wait_time = between(0.001, 0.01)  # 最小等待时间以支持高QPS
    
    def on_start(self):
        """用户启动时自动登录获取真实token"""
        try:
            # 设置全局headers
            self.client.headers.update({"Origin": "http://localhost:8000"})
            
            response = self.client.post("/api/v1/auth/login", json={
                "username_or_email": "admin",
                "password": "admin123"
            }, name="/api/v1/auth/login")
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token") or data.get("token")
                if self.token:
                    self.client.headers.update({"Authorization": f"Bearer {self.token}"})
        except Exception as e:
            print(f"登录异常: {str(e)[:100]}")

    @task(10)
    def index(self):
        """首页访问"""
        self.client.get("/")

    @task(8)
    def api_health(self):
        """健康检查API"""
        self.client.get("/api/v1/system/health")

    @task(6)
    def products_list(self):
        """产品列表"""
        try:
            self.client.get("/api/v1/products?page=1&page_size=20")
        except Exception as e:
            pass

    @task(5)
    def cases_list(self):
        """案例列表"""
        self.client.get("/api/v1/case-studies?page=1&page_size=20")

    @task(4)
    def seo_dashboard(self):
        """SEO仪表盘 - 公开API"""
        self.client.get("/api/v1/seo/dashboard", name="/api/v1/seo/dashboard")

    @task(3)
    def content_optimizer(self):
        """内容优化器 - 使用正确的路由"""
        payload = {
            "title": "轻集料混凝土产品介绍",
            "description": "高性能轻集料混凝土,密度等级LC5.0-LC25.0",
            "keywords": ["轻集料", "混凝土", "建材"]
        }
        try:
            self.client.post("/api/v1/seo/content-optimizer/optimize", json=payload, name="/api/v1/seo/content-optimizer/optimize")
        except Exception as e:
            pass

    @task(2)
    def site_audit(self):
        """网站审计 - 使用system路由"""
        try:
            self.client.get("/api/v1/system/logs?page=1&page_size=10", name="/api/v1/system/logs")
        except Exception as e:
            pass

    @task(1)
    def llms_txt(self):
        """LLMs.txt生成 - 使用POST方法"""
        self.client.post("/api/v1/seo/llms-txt/generate", json={}, name="/api/v1/seo/llms-txt/generate")
