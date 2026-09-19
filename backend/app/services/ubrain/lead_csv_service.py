# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""获客CSV导入导出 — FIX-38

支持：
- CSV 文件上传导入线索
- 线索列表导出为 CSV
- 批量导入验证 + 去重
"""

from __future__ import annotations

import csv
import io
import logging
from typing import Any, Optional

from app.models.unified_lead import UnifiedLead

log = logging.getLogger(__name__)


class LeadCSVService:
    """线索 CSV 导入导出服务。"""
    MAX_IMPORT_SIZE = 1000  # 单次最多导入1000条
    BATCH_SIZE = 100         # 分批处理大小
    async def import_csv(
        self,
        file_content: bytes,
        tenant_id: str = "",
        skip_duplicates: bool = True,
    ) -> dict:
        """从 CSV 内容导入线索。"""
        results = {
            "total": 0,
            "imported": 0,
            "skipped": 0,
            "errors": [],
            "imported_ids": [],
        }
        try:
            # 解码 CSV
            text = file_content.decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(text))
            # 验证列
            if not reader.fieldnames:
                return {"total": 0, "imported": 0, "skipped": 0, "errors": ["CSV 文件为空"]}

            # 检查必填列
            missing = self._check_required_columns(reader)
            if missing:
                return {
                    "total": 0, "imported": 0, "skipped": 0,
                    "errors": [f"缺少必填列: {', '.join(missing)}"],
                }

            # 逐行处理
            rows = list(reader)
            if len(rows) > self.MAX_IMPORT_SIZE:
                return {
                    "total": len(rows), "imported": 0, "skipped": 0,
                    "errors": [f"超过最大导入限制 ({self.MAX_IMPORT_SIZE})"],
                }

            results["total"] = len(rows)
            # 分批导入
            from app.db.session import SessionLocal
            from app.services.ubrain.dedup_engine import DedupEngine
            db = SessionLocal()
            dedup = DedupEngine(db)
            try:
                for batch_start in range(0, len(rows), self.BATCH_SIZE):
                    batch = rows[batch_start:batch_start + self.BATCH_SIZE]
                    batch_results = await self._process_csv_batch(
                        batch, tenant_id, dedup, db, skip_duplicates
                    )
                    results["imported"] += batch_results["imported"]
                    results["skipped"] += batch_results["skipped"]
                    results["errors"].extend(batch_results["errors"])
                    results["imported_ids"].extend(batch_results["imported_ids"])

                db.commit()
                log.info("CSV导入完成: %d/%d 条", results["imported"], results["total"])
            finally:
                db.close()

        except Exception as e:
            log.error("CSV导入失败: %s", e)
            results["errors"].append(str(e))

        return results

    def _check_required_columns(self, reader: csv.DictReader) -> list[str]:
        """检查必填列是否缺失。"""
        return [
            col for col in UnifiedLead.CSV_REQUIRED_COLUMNS
            if col not in [f.strip().lower() for f in reader.fieldnames]
        ]

    async def _process_csv_batch(
        self,
        batch: list[dict],
        tenant_id: str,
        dedup: Any,
        db: Any,
        skip_duplicates: bool,
    ) -> dict[str, Any]:
        """处理一批 CSV 行，返回本批结果。"""
        batch_results = {"imported": 0, "skipped": 0, "errors": [], "imported_ids": []}
        for i, row in enumerate(batch):
            try:
                normalized = {k.strip().lower(): v.strip() for k, v in row.items()}
                # 去重检查
                if skip_duplicates:
                    dup_result = await dedup.check_duplicate({
                        "email": normalized.get("email", ""),
                        "company": normalized.get("company", ""),
                    })
                    if dup_result.get("is_duplicate"):
                        batch_results["skipped"] += 1
                        continue

                # 创建 ProspectLead
                lead = UnifiedLead.from_csv_row(normalized)
                batch_results["imported_ids"].append(
                    self._create_prospect_lead(lead, tenant_id, db)
                )
                batch_results["imported"] += 1

            except Exception as e:
                batch_results["errors"].append(f"行 {batch.index(row) + i + 1}: {str(e)}")
        return batch_results

    def _create_prospect_lead(
        self, lead: Any, tenant_id: str, db: Any
    ) -> str:
        """创建 ProspectLead 记录并入库，返回 ID。"""
        import uuid
        from app.models.prospect_lead import ProspectLead
        prospect = ProspectLead(
            id=str(uuid.uuid4()),
            email=lead.identity.email,
            first_name=lead.identity.first_name,
            last_name=lead.identity.last_name,
            phone=lead.identity.phone,
            linkedin_url=lead.identity.linkedin_url,
            company=lead.company.company_name,
            website=lead.company.website,
            industry=lead.company.industry,
            country=lead.company.country,
            title=lead.position.title,
            source=lead.source.channel or "csv_import",
            status="new",
            tenant_id=tenant_id,
        )
        db.add(prospect)
        db.flush()
        return prospect.id

    async def export_csv(
        self,
        lead_ids: Optional[list[str]] = None,
        filters: Optional[dict] = None,
        tenant_id: Optional[str] = None,
    ) -> bytes:
        """导出线索为 CSV。

        Args:
            lead_ids: 指定导出的线索ID列表
            filters: 筛选条件

        Returns:
            CSV 文件内容（bytes）
        """
        from app.db.session import SessionLocal
        from app.models.prospect_lead import ProspectLead
        db = SessionLocal()
        try:
            query = db.query(ProspectLead)
            if lead_ids:
                query = query.filter(ProspectLead.id.in_(lead_ids))

            # P0-2: 补租户隔离，避免跨租户线索泄露
            if tenant_id:
                query = query.filter(ProspectLead.tenant_id == tenant_id)
            if filters:
                if filters.get("status"):
                    query = query.filter(ProspectLead.status == filters["status"])
                if filters.get("source"):
                    query = query.filter(ProspectLead.source == filters["source"])
                if filters.get("min_score") is not None:
                    # P0-2: 原代码引用不存在的 ProspectLead.score（实际字段为 overall_score），
                    # 且 min_score=0.0 时原 if 判定为假被跳过。修正为 overall_score 并用 is not None。
                    query = query.filter(ProspectLead.overall_score >= filters["min_score"])

            leads = query.order_by(ProspectLead.created_at.desc()).limit(5000).all()
            # 转为 UnifiedLead 再导出
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=UnifiedLead.CSV_COLUMNS)
            writer.writeheader()
            for lead in leads:
                unified = UnifiedLead.from_prospect_lead(lead)
                writer.writerow(unified.to_csv_row())

            return output.getvalue().encode("utf-8-sig")

        finally:
            db.close()


class LeadCSVValidator:
    """CSV 导入验证器。"""
    @staticmethod
    def validate_row(row: dict[str, str]) -> list[str]:
        """验证单行数据，返回错误列表。"""
        errors = []
        email = row.get("email", "").strip()
        if not email:
            errors.append("邮箱为空")
        elif "@" not in email or "." not in email.split("@")[-1]:
            errors.append(f"邮箱格式无效: {email}")

        phone = row.get("phone", "").strip()
        if phone:
            # 简单验证：至少7位数字
            digits = "".join(c for c in phone if c.isdigit())
            if len(digits) < 7:
                errors.append(f"电话格式无效: {phone}")

        website = row.get("website", "").strip()
        if website and not website.startswith(("http://", "https://")):
            errors.append(f"网站格式无效: {website}")

        return errors

    @staticmethod
    def validate_file(file_content: bytes) -> dict:
        """预验证 CSV 文件。"""
        try:
            text = file_content.decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(text))
            result = {
                "valid": True,
                "total_rows": 0,
                "columns": list(reader.fieldnames or []),
                "missing_required": [],
                "row_errors": [],
            }
            # 检查必填列
            for col in UnifiedLead.CSV_REQUIRED_COLUMNS:
                if col not in [c.strip().lower() for c in (reader.fieldnames or [])]:
                    result["missing_required"].append(col)

            if result["missing_required"]:
                result["valid"] = False
                return result

            # 检查行数据
            for i, row in enumerate(reader):
                result["total_rows"] += 1
                if result["total_rows"] > LeadCSVService.MAX_IMPORT_SIZE:
                    result["valid"] = False
                    result["row_errors"].append(f"超过最大导入限制 ({LeadCSVService.MAX_IMPORT_SIZE})")
                    break

                errors = LeadCSVValidator.validate_row(row)
                if errors:
                    result["row_errors"].append(f"行 {i + 2}: {'; '.join(errors)}")

            if result["row_errors"]:
                result["valid"] = False

            return result

        except Exception as e:
            return {"valid": False, "total_rows": 0, "columns": [], "missing_required": [], "row_errors": [str(e)]}