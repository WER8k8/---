#!/usr/bin/env python3
"""
压力测试脚本 - Phase 4
使用locust进行1000 QPS压测，验证P99 < 500ms
"""

import subprocess
import sys
import time
import json
from pathlib import Path

# 测试配置
BASE_URL = "http://localhost:8000"
TARGET_QPS = 1000
TEST_DURATION = "5m"
CONCURRENT_USERS = 100
SPAWN_RATE = 10

def install_locust():
    """安装locust"""
    print("安装locust...")
    subprocess.run([sys.executable, "-m", "pip", "install", "locust"], check=True)

def create_locustfile():
    """创建locust测试文件"""
    locust_content = '''
from locust import HttpUser, task, between, events
import random
import json

class WebsiteUser(HttpUser):
    wait_time = between(0.001, 0.01)  # 最小等待时间以支持高QPS

    @task(10)
    def index(self):
        """首页访问"""
        self.client.get("/")

    @task(8)
    def api_health(self):
        """健康检查API"""
        self.client.get("/api/v1/health")

    @task(6)
    def products_list(self):
        """产品列表"""
        self.client.get("/api/v1/products?page=1&page_size=20")

    @task(5)
    def cases_list(self):
        """案例列表"""
        self.client.get("/api/v1/cases?page=1&page_size=20")

    @task(4)
    def seo_dashboard(self):
        """SEO仪表盘（需要认证）"""
        headers = {"Authorization": "Bearer test-token"}
        self.client.get("/api/v1/seo/dashboard", headers=headers, name="/api/v1/seo/dashboard (auth)")

    @task(3)
    def content_optimizer(self):
        """内容优化器"""
        payload = {
            "title": "轻集料混凝土产品介绍",
            "description": "高性能轻集料混凝土，密度等级LC5.0-LC25.0",
            "keywords": ["轻集料", "混凝土", "建材"]
        }
        self.client.post("/api/v1/seo/optimize", json=payload, name="/api/v1/seo/optimize (POST)")

    @task(2)
    def site_audit(self):
        """网站审计"""
        self.client.get("/api/v1/seo/audit?url=https://example.com", name="/api/v1/seo/audit")

    @task(1)
    def llms_txt(self):
        """LLMs.txt生成"""
        self.client.get("/api/v1/seo/llms-txt/generate", name="/api/v1/seo/llms-txt/generate")
'''

    with open("locustfile.py", "w", encoding="utf-8") as f:
        f.write(locust_content)

    print("locustfile.py 已创建")

def run_headless_test(url, users, qps, duration):
    """运行无头模式压测"""
    print(f"\n{'='*60}")
    print(f"开始压力测试")
    print(f"目标URL: {url}")
    print(f"并发用户: {users}")
    print(f"测试时长: {duration}")
    print(f"{'='*60}\n")

    cmd = [
        sys.executable, "-m", "locust",
        "--headless",
        "--users", str(users),
        "--spawn-rate", str(10),
        "--run-time", duration,
        "--host", url,
        "--csv", "results/load_test_results",
        "--html", "results/load_test_report.html"
    ]

    try:
        subprocess.run(cmd, check=True)
        print("\n压力测试完成!")
        analyze_results()
    except subprocess.CalledProcessError as e:
        print(f"\n压力测试失败: {e}")
        return False

    return True

def run_web_ui(url, users):
    """运行Web UI模式"""
    print("\n启动Locust Web UI...")
    print("访问 http://localhost:8089 开始测试\n")

    cmd = [
        sys.executable, "-m", "locust",
        "--users", str(users),
        "--spawn-rate", str(10),
        "--host", url
    ]

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n测试已停止")

def analyze_results():
    """分析测试结果"""
    print("\n" + "="*60)
    print("测试结果分析")
    print("="*60)

    # 读取CSV结果
    stats_file = Path("results/load_test_results_stats.csv")
    if stats_file.exists():
        import csv
        with open(stats_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("Name") == "Aggregated":
                    total_requests = int(row.get("# Requests", 0))
                    fails = float(row.get("Failure%", 0))
                    avg_response = float(row.get("Average Response Time", 0))
                    p95_response = float(row.get("95% Response Time", 0))
                    p99_response = float(row.get("99% Response Time", 0))
                    current_rps = float(row.get("Current RPS", 0))

                    print(f"\n总请求数: {total_requests:,}")
                    print(f"失败率: {fails:.2f}%")
                    print(f"平均响应时间: {avg_response:.2f}ms")
                    print(f"P95响应时间: {p95_response:.2f}ms")
                    print(f"P99响应时间: {p99_response:.2f}ms")
                    print(f"当前RPS: {current_rps:.2f}")

                    # 验证目标
                    print("\n" + "-"*40)
                    if p99_response < 500:
                        print("P99 < 500ms: PASS")
                    else:
                        print(f"P99 < 500ms: FAIL ({p99_response:.2f}ms)")

                    if current_rps >= TARGET_QPS:
                        print(f"QPS >= {TARGET_QPS}: PASS")
                    else:
                        print(f"QPS >= {TARGET_QPS}: FAIL ({current_rps:.2f})")

                    if fails < 1:
                        print("失败率 < 1%: PASS")
                    else:
                        print(f"失败率 < 1%: FAIL ({fails:.2f}%)")
                    print("-"*40)

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="压力测试工具")
    parser.add_argument("--mode", choices=["headless", "web"], default="headless",
                       help="运行模式: headless(命令行) 或 web(Web UI)")
    parser.add_argument("--url", default="http://localhost:8000", help="测试目标URL")
    parser.add_argument("--users", type=int, default=100, help="并发用户数")
    parser.add_argument("--qps", type=int, default=1000, help="目标QPS")
    parser.add_argument("--duration", default="5m", help="测试持续时间 (如: 5m, 30s)")

    args = parser.parse_args()

    # 使用局部变量
    test_url = args.url
    concurrent_users = args.users
    target_qps = args.qps
    test_duration = args.duration

    # 创建结果目录
    Path("results").mkdir(exist_ok=True)

    # 安装依赖
    try:
        import locust
    except ImportError:
        install_locust()

    # 创建测试文件
    create_locustfile()

    # 运行测试
    if args.mode == "headless":
        run_headless_test(test_url, concurrent_users, target_qps, test_duration)
    else:
        run_web_ui(test_url, concurrent_users)

if __name__ == "__main__":
    main()
