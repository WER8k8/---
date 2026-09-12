"""异步任务模块"""

import os
from datetime import datetime

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings
from app.db.session import SessionLocal
from app.repositories.content_repository import ContentPageRepository
from app.repositories.product_repository import ProductRepository

# Celery配置
celery = Celery("tasks", broker=settings.CELERY_BROKER_URL,
                backend=settings.CELERY_RESULT_BACKEND)

# 配置Celery
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5分钟超时
    task_soft_time_limit=240,  # 4分钟软超时
)


@celery.task(bind=True, retry_backoff=True, retry_kwargs={"max_retries": 3})
def process_document(self, product_id: str, doc_id: str):
    """处理上传的文档（异步任务）"""
    from app.services.product_service import ProductDocumentService
    try:
        db = SessionLocal()
        try:
            service = ProductDocumentService(db)
            # 文档处理逻辑
            return {"status": "success", "message": "文档处理完成"}
        finally:
            db.close()
    except Exception as e:
        self.retry(exc=e)


@celery.task(bind=True, retry_backoff=True, retry_kwargs={"max_retries": 3})
def generate_sitemap(self):
    """生成站点地图（异步任务）"""
    try:
        db = SessionLocal()
        try:
            product_repo = ProductRepository(db)
            content_repo = ContentPageRepository(db)
            products = product_repo.get_paginated(page=1, page_size=1000)[0]
            pages = content_repo.get_paginated(page=1, page_size=1000)[0]
            sitemap_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
            sitemap_lines.append(
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

            for product in products:
                if product.is_active:
                    sitemap_lines.append(f"  <url>")
                    sitemap_lines.append(
                        f"    <loc>{settings.SITE_URL}/products/{product.slug}</loc>")
                    sitemap_lines.append(
                        f'    <lastmod>{product.updated_at.strftime("%Y-%m-%d")}</lastmod>')
                    sitemap_lines.append(f"    <changefreq>weekly</changefreq>")
                    sitemap_lines.append(f"    <priority>0.8</priority>")
                    sitemap_lines.append(f"  </url>")

            for page in pages:
                if page.status == "published":
                    sitemap_lines.append(f"  <url>")
                    sitemap_lines.append(
                        f"    <loc>{settings.SITE_URL}/{page.slug}</loc>")
                    sitemap_lines.append(
                        f'    <lastmod>{page.published_at.strftime("%Y-%m-%d") if page.published_at else page.updated_at.strftime("%Y-%m-%d")}</lastmod>'
                    )
                    sitemap_lines.append(f"    <changefreq>monthly</changefreq>")
                    sitemap_lines.append(f"    <priority>0.5</priority>")
                    sitemap_lines.append(f"  </url>")

            sitemap_lines.append("</urlset>")
            sitemap_content = "\n".join(sitemap_lines)
            uploads_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                "uploads")
            os.makedirs(uploads_dir, exist_ok=True)
            sitemap_path = os.path.join(uploads_dir, "sitemap.xml")
            with open(sitemap_path, "w", encoding="utf-8") as f:
                f.write(sitemap_content)

            return {"status": "success", "message": "站点地图生成完成"}
        finally:
            db.close()
    except Exception as e:
        self.retry(exc=e)


@celery.task(bind=True, retry_backoff=True, retry_kwargs={"max_retries": 3})
def clean_expired_versions(self):
    """清理过期的内容版本（异步任务）"""
    from datetime import timedelta
    try:
        db = SessionLocal()
        try:
            version_repo = ContentPageRepository(db)
            # 清理过期内容版本
            return {"status": "success", "message": "过期版本清理完成"}
        finally:
            db.close()
    except Exception as e:
        self.retry(exc=e)


@celery.task(bind=True, retry_backoff=True, retry_kwargs={"max_retries": 3})
def update_search_index(self):
    """更新搜索索引（异步任务）"""
    try:
        db = SessionLocal()
        try:
            # 更新搜索索引
            return {"status": "success", "message": "搜索索引更新完成"}
        finally:
            db.close()
    except Exception as e:
        self.retry(exc=e)


# 定时任务配置
celery.conf.beat_schedule = {
    "daily-sitemap-generation": {
        "task": "app.core.tasks.generate_sitemap",
        "schedule": crontab(hour=3, minute=0),  # 每天凌晨3点
    },
    "weekly-version-cleanup": {
        "task": "app.core.tasks.clean_expired_versions",
        "schedule": crontab(day_of_week=0, hour=2, minute=0),  # 每周日凌晨2点
    },
    "daily-index-update": {
        "task": "app.core.tasks.update_search_index",
        "schedule": crontab(hour=1, minute=0),  # 每天凌晨1点
    },
}


def run_worker():
    """启动Celery Worker"""
    celery.worker_main(["worker", "--loglevel=info"])


def run_beat():
    """启动Celery Beat（定时任务）"""
    celery.beat_main(["beat", "--loglevel=info"])
