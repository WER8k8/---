"""
全球化多语言服务
- 术语库 CRUD
- 翻译任务管理
- 语言统计
"""

from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.globalization import GlossaryTerm, TranslationTask, TranslationRecord


class GlobalizationService:

    # ========== 术语库 ==========

    @staticmethod
    def list_glossary(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
    ):
        """list_glossary。

        参数说明：
        :param db: 参数 db
        :param page: 参数 page
        :param page_size: 参数 page_size
        :param search: 参数 search
        :param category: 参数 category
        :param status: 参数 status
        :return: 返回处理结果。
        """
        q = db.query(GlossaryTerm).filter(GlossaryTerm.is_active)
        if search:
            like = f"%{search}%"
            q = q.filter(
                GlossaryTerm.zh.ilike(like)
                | GlossaryTerm.en.ilike(like)
                | GlossaryTerm.ja.ilike(like)
                | GlossaryTerm.ko.ilike(like)
                | GlossaryTerm.ar.ilike(like)
            )
        if category:
            q = q.filter(GlossaryTerm.category == category)
        if status:
            q = q.filter(GlossaryTerm.status == status)

        total = q.count()
        items = q.order_by(GlossaryTerm.created_at.desc()).offset(
            (page - 1) * page_size).limit(page_size).all()
        return items, total

    @staticmethod
    def create_glossary_term(db: Session, data: dict):
        """create_glossary_term。

        参数说明：
        :param db: 参数 db
        :param data: 参数 data
        :return: 返回处理结果。
        """
        term = GlossaryTerm(**data)
        db.add(term)
        db.commit()
        db.refresh(term)
        return term

    @staticmethod
    def update_glossary_term(db: Session, term_id: str, data: dict):
        """update_glossary_term。

        参数说明：
        :param db: 参数 db
        :param term_id: 参数 term_id
        :param data: 参数 data
        :return: 返回处理结果。
        """
        term = db.query(GlossaryTerm).filter(
            GlossaryTerm.id == term_id, GlossaryTerm.is_active).first()
        if not term:
            return None
        for k, v in data.items():
            if v is not None:
                setattr(term, k, v)
        db.commit()
        db.refresh(term)
        return term

    @staticmethod
    def delete_glossary_term(db: Session, term_id: str):
        """delete_glossary_term。

        参数说明：
        :param db: 参数 db
        :param term_id: 参数 term_id
        :return: 返回处理结果。
        """
        term = db.query(GlossaryTerm).filter(
            GlossaryTerm.id == term_id, GlossaryTerm.is_active).first()
        if not term:
            return False
        term.is_active = False
        db.commit()
        return True

    @staticmethod
    def get_glossary_stats(db: Session):
        """get_glossary_stats。

        参数说明：
        :param db: 参数 db
        :return: 返回处理结果。
        """
        total = db.query(GlossaryTerm).filter(GlossaryTerm.is_active).count()
        confirmed = db.query(GlossaryTerm).filter(
            GlossaryTerm.is_active, GlossaryTerm.status == "confirmed").count()
        categories = (
            db.query(GlossaryTerm.category, func.count(GlossaryTerm.id))
            .filter(GlossaryTerm.is_active)
            .group_by(GlossaryTerm.category)
            .all()
        )
        return {
            "total": total,
            "confirmed": confirmed,
            "categories": {c: n for c, n in categories},
        }

    # ========== 翻译任务 ==========
    @staticmethod
    def list_tasks(db: Session, page: int = 1, page_size: int = 20):
        """list_tasks。

        参数说明：
        :param db: 参数 db
        :param page: 参数 page
        :param page_size: 参数 page_size
        :return: 返回处理结果。
        """
        q = db.query(TranslationTask)
        total = q.count()
        items = q.order_by(TranslationTask.created_at.desc()).offset(
            (page - 1) * page_size).limit(page_size).all()
        return items, total

    @staticmethod
    def create_task(db: Session, data: dict):
        """create_task。

        参数说明：
        :param db: 参数 db
        :param data: 参数 data
        :return: 返回处理结果。
        """
        task = TranslationTask(**data)
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    # ========== 翻译记录 ==========
    @staticmethod
    def list_records(db: Session, task_id: Optional[str] = None, limit: int = 50):
        """list_records。

        参数说明：
        :param db: 参数 db
        :param task_id: 参数 task_id
        :param limit: 参数 limit
        :return: 返回处理结果。
        """
        q = db.query(TranslationRecord)
        if task_id:
            q = q.filter(TranslationRecord.task_id == task_id)
        items = q.order_by(TranslationRecord.created_at.desc()).limit(limit).all()
        return items

    # ========== 语言统计 ==========
    @staticmethod
    def get_supported_languages():
        """返回系统支持的语言列表（面向出口市场）"""
        return [
            # 东亚
            {"code": "zh-CN", "name": "简体中文", "flag": "🇨🇳"},
            {"code": "ja-JP", "name": "日本語", "flag": "🇯🇵"},
            {"code": "ko-KR", "name": "한국어", "flag": "🇰🇷"},
            # 欧美
            {"code": "en-US", "name": "English", "flag": "🇺🇸"},
            {"code": "de-DE", "name": "Deutsch", "flag": "🇩🇪"},       # 德国
            {"code": "fr-FR", "name": "Français", "flag": "🇫🇷"},      # 法国
            {"code": "es-ES", "name": "Español", "flag": "🇪🇸"},       # 西班牙
            {"code": "pt-PT", "name": "Português", "flag": "🇵🇹"},     # 葡萄牙/巴西
            {"code": "it-IT", "name": "Italiano", "flag": "🇮🇹"},      # 意大利
            {"code": "nl-NL", "name": "Nederlands", "flag": "🇳🇱"},    # 荷兰
            {"code": "ru-RU", "name": "Русский", "flag": "🇷🇺"},       # 俄罗斯
            # 中东
            {"code": "ar-SA", "name": "العربية", "flag": "🇸🇦"},       # 阿拉伯
            {"code": "tr-TR", "name": "Türkçe", "flag": "🇹🇷"},        # 土耳其
            {"code": "fa-IR", "name": "فارسی", "flag": "🇮🇷"},         # 波斯语
            {"code": "he-IL", "name": "עברית", "flag": "🇮🇱"},          # 希伯来语
            # 东南亚
            {"code": "th-TH", "name": "ไทย", "flag": "🇹🇭"},
            {"code": "vi-VN", "name": "Tiếng Việt", "flag": "🇻🇳"},
            {"code": "ms-MY", "name": "Bahasa Melayu", "flag": "🇲🇾"},  # 马来语
            # 南亚
            {"code": "hi-IN", "name": "हिन्दी", "flag": "🇮🇳"},          # 印度
            {"code": "id-ID", "name": "Bahasa Indonesia", "flag": "🇮🇩"},  # 印尼
            {"code": "tl-PH", "name": "Filipino", "flag": "🇵🇭"},        # 菲律宾
            {"code": "bn-BD", "name": "বাংলা", "flag": "🇧🇩"},           # 孟加拉
            {"code": "my-MM", "name": "မြန်မာဘာသာ", "flag": "🇲🇲"},        # 缅甸
            {"code": "km-KH", "name": "ភាសាខ្មែរ", "flag": "🇰🇭"},          # 柬埔寨
            # 中东欧
            {"code": "pl-PL", "name": "Polski", "flag": "🇵🇱"},          # 波兰
            {"code": "cs-CZ", "name": "Čeština", "flag": "🇨🇿"},         # 捷克
            {"code": "uk-UA", "name": "Українська", "flag": "🇺🇦"},      # 乌克兰
            # 北欧
            {"code": "sv-SE", "name": "Svenska", "flag": "🇸🇪"},         # 瑞典
            # 非洲
            {"code": "sw-KE", "name": "Kiswahili", "flag": "🇰🇪"},       # 肯尼亚/东非
            {"code": "ha-NG", "name": "Hausa", "flag": "🇳🇬"},           # 尼日利亚/西非
            {"code": "zu-ZA", "name": "isiZulu", "flag": "🇿🇦"},         # 南非
            {"code": "am-ET", "name": "አማርኛ", "flag": "🇪🇹"},             # 埃塞俄比亚
        ]

    @staticmethod
    def get_overview(db: Session) -> dict:
        """获取全球化概览数据"""
        languages = GlobalizationService.get_supported_languages()
        _, glossary_total = GlobalizationService.list_glossary(db, page=1, page_size=1)
        tasks, _ = GlobalizationService.list_tasks(db)
        today = func.date(TranslationRecord.created_at)
        today_count = (
            db.query(func.count(TranslationRecord.id))
            .filter(func.date(TranslationRecord.created_at) == func.current_date())
            .scalar()
            or 0
        )
        # 模拟翻译覆盖率（后续根据内容模型实际计算）
        coverage_data = []
        for lang in languages:
            records = db.query(TranslationRecord).filter(
                TranslationRecord.target_lang == lang["code"]
            ).count()
            coverage = min(records * 5, 100) if records else 0
            coverage_data.append({
                "code": lang["code"],
                "name": lang["name"],
                "flag": lang["flag"],
                "coverage": coverage,
            })

        return {
            "languages": coverage_data,
            "stats": {
                "total_languages": len(languages),
                "glossary_terms": glossary_total,
                "tasks": len(tasks),
                "today_translations": today_count,
            },
        }
