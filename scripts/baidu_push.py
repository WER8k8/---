#!/usr/bin/env python3
"""
百度站长平台主动推送脚本
用于将网站URL主动推送到百度搜索引擎，加速收录
"""

import os
import sys
import json
import requests
from typing import List
from datetime import datetime

# 配置
BAIDU_PUSH_API = os.getenv("BAIDU_PUSH_API", "")
SITE_URL = os.getenv("SITE_URL", "https://youding.com")

# 需要推送的URL列表模板
URL_TEMPLATES = [
    # 首页
    "{site}/",

    # 产品页面
    "{site}/products/",
    "{site}/products/lc5-concrete",
    "{site}/products/lc7-concrete",
    "{site}/products/lc10-concrete",
    "{site}/products/lc15-concrete",
    "{site}/products/lc20-concrete",

    # 案例页面
    "{site}/cases/",

    # 文章/新闻页面
    "{site}/news/",

    # 关于我们
    "{site}/about",

    # 联系我们
    "{site}/contact",

    # SEO页面
    "{site}/llms.txt",
]


def get_urls_to_push() -> List[str]:
    """获取需要推送的URL列表"""
    urls = []

    for template in URL_TEMPLATES:
        url = template.format(site=SITE_URL.rstrip("/"))
        urls.append(url)

    return urls


def push_to_baidu(urls: List[str]) -> dict:
    """
    推送URL到百度站长平台

    Args:
        urls: 要推送的URL列表

    Returns:
        推送结果
    """
    if not BAIDU_PUSH_API:
        print("警告: BAIDU_PUSH_API未配置，跳过推送")
        print("请在环境变量中设置BAIDU_PUSH_API")
        return {"success": False, "message": "API未配置"}

    headers = {
        "Content-Type": "text/plain"
    }

    # URL列表转换为纯文本格式，每行一个URL
    data = "\n".join(urls)

    try:
        response = requests.post(
            BAIDU_PUSH_API,
            headers=headers,
            data=data.encode("utf-8"),
            timeout=30
        )

        result = response.json()

        if response.status_code == 200:
            print(f"推送成功!")
            print(f"  成功推送: {result.get('success', 0)} 条")
            print(f"  剩余配额: {result.get('remain', 0)} 条")
            print(f"  当日配额: {result.get('quota', 0)} 条")
            return {"success": True, "result": result}
        else:
            print(f"推送失败: {response.status_code}")
            print(f"  错误信息: {result}")
            return {"success": False, "error": result}

    except requests.exceptions.RequestException as e:
        print(f"请求失败: {str(e)}")
        return {"success": False, "error": str(e)}
    except json.JSONDecodeError:
        print(f"响应解析失败: {response.text}")
        return {"success": False, "error": "响应格式错误"}


def main():
    """主函数"""
    print("=" * 60)
    print("百度站长平台主动推送工具")
    print("=" * 60)
    print(f"站点: {SITE_URL}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 获取URL列表
    urls = get_urls_to_push()
    print(f"待推送URL数量: {len(urls)}")
    print()

    # 显示URL列表
    print("URL列表:")
    for i, url in enumerate(urls, 1):
        print(f"  {i}. {url}")
    print()

    # 确认推送
    confirm = input("是否执行推送? (y/n): ").strip().lower()
    if confirm != "y":
        print("已取消推送")
        return

    # 执行推送
    print("\n正在推送...")
    result = push_to_baidu(urls)

    print()
    if result.get("success"):
        print("推送完成!")
    else:
        print("推送失败，请检查配置")
        print(f"错误: {result.get('error', '未知错误')}")


if __name__ == "__main__":
    main()
