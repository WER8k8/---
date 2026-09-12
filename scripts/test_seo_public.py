#!/usr/bin/env python3
"""
SEO公开API测试脚本
验证所有SEO端点是否可以公开访问
"""

import requests
import json

BASE_URL = "http://localhost:8000"
DEFAULT_HEADERS = {"User-Agent": "YouDingSaaS-Internal/1.0 (seo-public-test)"}

def test_seo_endpoints():
    print("="*60)
    print("SEO公开API测试")
    print("="*60)
    
    test_cases = [
        {
            "name": "SEO仪表盘",
            "method": "GET",
            "url": "/api/v1/seo/dashboard",
            "headers": {"Origin": "http://localhost:8000"},
            "expected_status": 200
        },
        {
            "name": "内容优化器",
            "method": "POST",
            "url": "/api/v1/seo/content-optimizer/optimize",
            "headers": {"Origin": "http://localhost:8000"},
            "json": {"title": "测试", "content": "测试内容"},
            "expected_status": 200
        },
        {
            "name": "LLMs.txt生成",
            "method": "POST",
            "url": "/api/v1/seo/llms-txt/generate",
            "headers": {"Origin": "http://localhost:8000"},
            "json": {"company_name": "测试公司"},
            "expected_status": 200
        },
        {
            "name": "关键词列表",
            "method": "GET",
            "url": "/api/v1/seo/keywords",
            "headers": {"Origin": "http://localhost:8000"},
            "expected_status": 200
        },
        {
            "name": "健康检查",
            "method": "GET",
            "url": "/api/v1/system/health",
            "headers": {"Origin": "http://localhost:8000"},
            "expected_status": 200
        },
        {
            "name": "产品列表",
            "method": "GET",
            "url": "/api/v1/products?page=1&page_size=20",
            "headers": {"Origin": "http://localhost:8000"},
            "expected_status": 200
        },
        {
            "name": "案例列表",
            "method": "GET",
            "url": "/api/v1/case-studies?page=1&page_size=20",
            "headers": {"Origin": "http://localhost:8000"},
            "expected_status": 200
        }
    ]
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        try:
            url = f"{BASE_URL}{test['url']}"
            headers = {**DEFAULT_HEADERS, **test.get("headers", {})}
            
            if test["method"] == "GET":
                response = requests.get(url, headers=headers)
            elif test["method"] == "POST":
                response = requests.post(url, headers=headers, json=test.get("json"))
            
            status_code = response.status_code
            
            if status_code == test["expected_status"]:
                print(f"✅ {test['name']}: {status_code}")
                passed += 1
            else:
                print(f"❌ {test['name']}: {status_code} (预期: {test['expected_status']})")
                print(f"   响应: {response.text[:200]}")
                failed += 1
                
        except Exception as e:
            print(f"❌ {test['name']}: 异常 - {str(e)}")
            failed += 1
    
    print("="*60)
    print(f"测试结果: {passed}/{len(test_cases)} 通过")
    print("="*60)
    
    return failed == 0

if __name__ == "__main__":
    success = test_seo_endpoints()
    exit(0 if success else 1)
