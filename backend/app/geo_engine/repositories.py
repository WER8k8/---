# mypy: ignore-errors
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any

from app.geo_engine.database_new import geo_db

logger = logging.getLogger(__name__)

_local_dev_counter = 9000
_local_dev_leads: list[dict[str, Any]] = []
_local_dev_alerts: list[dict[str, Any]] = []
_local_dev_rules: list[dict[str, Any]] = []
_local_dev_histories: list[dict[str, Any]] = []


def _as_float(value: Any) -> float:
    """_as_float。

    参数说明：
    :param value: 参数 value
    :return: 返回处理结果。
    """
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _next_local_id() -> int:
    """_next_local_id。
    :return: 返回处理结果。
    """
    global _local_dev_counter
    _local_dev_counter += 1
    return _local_dev_counter


DEFAULT_PRODUCT = {
    "slug": "polyurethane-lightweight-concrete",
    "name": "聚氨酯颗粒轻集料混凝土",
    "category": "轻集料混凝土",
    "density_kg_m3": 200,
    "strength_mpa": 1.5,
    "thermal_conductivity": 0.051,
    "factory_price": 320.0,
    "price_valid_until": "2026-06-30",
    "phone": "13800138000",
}

ALL_PRODUCTS: list[dict[str, Any]] = [
    {
        "slug": "polyurethane-lightweight-concrete",
        "name": "聚氨酯颗粒轻集料混凝土",
        "category": "轻集料混凝土",
        "density_kg_m3": 200,
        "strength_mpa": 1.5,
        "thermal_conductivity": 0.051,
        "factory_price": 320.0,
        "price_valid_until": "2026-06-30",
        "phone": "13800138000",
    },
    {
        "slug": "ceramsite-lightweight-concrete",
        "name": "陶粒轻集料混凝土",
        "category": "轻集料混凝土",
        "density_kg_m3": 350,
        "strength_mpa": 2.5,
        "thermal_conductivity": 0.085,
        "factory_price": 280.0,
        "price_valid_until": "2026-06-30",
        "phone": "13800138001",
    },
    {
        "slug": "foam-cement-insulation-board",
        "name": "泡沫水泥保温板",
        "category": "保温材料",
        "density_kg_m3": 150,
        "strength_mpa": 0.8,
        "thermal_conductivity": 0.045,
        "factory_price": 420.0,
        "price_valid_until": "2026-06-30",
        "phone": "13800138002",
    },
    {
        "slug": "aerated-lightweight-filler",
        "name": "加气轻质回填料",
        "category": "回填材料",
        "density_kg_m3": 250,
        "strength_mpa": 1.2,
        "thermal_conductivity": 0.065,
        "factory_price": 260.0,
        "price_valid_until": "2026-06-30",
        "phone": "13800138003",
    },
]


async def get_product_by_slug(slug: str) -> dict[str, Any]:
    """get_product_by_slug。

    参数说明：
    :param slug: 参数 slug
    :return: 返回处理结果。
    """
    try:
        async with geo_db.acquire() as connection:  # type: ignore[attr-defined]
            row = await connection.fetch_one(
                """
                SELECT
                  product_slug AS slug,
                  product_name AS name,
                  category,
                  density_kg_m3,
                  strength_mpa,
                  thermal_conductivity,
                  factory_price,
                  price_valid_until::text,
                  phone
                FROM material_specs
                WHERE product_slug = :slug AND status = 'active'
                """,
                {"slug": slug},
            )
    except (RuntimeError, OSError, Exception):
        return {**DEFAULT_PRODUCT, "slug": slug}

    if row is None:
        return {**DEFAULT_PRODUCT, "slug": slug}

    return dict(row)


async def list_products() -> list[dict[str, Any]]:
    """列出所有活跃产品，返回简要信息列表。"""
    try:
        async with geo_db.acquire() as connection:  # type: ignore[attr-defined]
            rows = await connection.fetch_all(
                """
                SELECT
                  product_slug AS slug,
                  product_name AS name,
                  category,
                  density_kg_m3,
                  strength_mpa,
                  thermal_conductivity,
                  factory_price,
                  price_valid_until::text,
                  phone
                FROM material_specs
                WHERE status = 'active'
                ORDER BY created_at ASC
                """
            )
        return [dict(row) for row in rows]
    except (RuntimeError, OSError, Exception):
        return [dict(p) for p in ALL_PRODUCTS]


async def upsert_default_product() -> None:
    """upsert_default_product。
    :return: 返回处理结果。
    """
    for product in ALL_PRODUCTS:
        try:
            async with geo_db.acquire() as connection:  # type: ignore[attr-defined]
                await connection.execute(
                    """
                    INSERT INTO material_specs (
                      product_slug,
                      product_name,
                      category,
                      density_kg_m3,
                      strength_mpa,
                      thermal_conductivity,
                      factory_price,
                      price_valid_until,
                      phone
                    )
                    VALUES (:slug, :name, :category, :density_kg_m3, :strength_mpa, :thermal_conductivity, :factory_price, :price_valid_until, :phone)
                    ON CONFLICT (product_slug) DO UPDATE SET
                      product_name = EXCLUDED.product_name,
                      category = EXCLUDED.category,
                      density_kg_m3 = EXCLUDED.density_kg_m3,
                      strength_mpa = EXCLUDED.strength_mpa,
                      thermal_conductivity = EXCLUDED.thermal_conductivity,
                      factory_price = EXCLUDED.factory_price,
                      price_valid_until = EXCLUDED.price_valid_until,
                      phone = EXCLUDED.phone,
                      updated_at = CURRENT_TIMESTAMP
                    """,
                    {
                        "slug": product["slug"],
                        "name": product["name"],
                        "category": product["category"],
                        "density_kg_m3": product["density_kg_m3"],
                        "strength_mpa": product["strength_mpa"],
                        "thermal_conductivity": product["thermal_conductivity"],
                        "factory_price": product["factory_price"],
                        "price_valid_until": product["price_valid_until"],
                        "phone": product["phone"],
                    },
                )
        except (RuntimeError, OSError, Exception):
            continue


async def save_content_chunk(
    product_slug: str,
    keyword: str,
    intent: str,
    content: str,
    score: float,
    status: str,
) -> int:
    """save_content_chunk。

    参数说明：
    :param product_slug: 参数 product_slug
    :param keyword: 参数 keyword
    :param intent: 参数 intent
    :param content: 参数 content
    :param score: 参数 score
    :param status: 参数 status
    :return: 返回处理结果。
    """
    try:
        async with geo_db.acquire() as connection:  # type: ignore[attr-defined]
            product_id = await connection.fetch_val(
                "SELECT id FROM material_specs WHERE product_slug = :slug",
                {"slug": product_slug},
            )
            if product_id is None:
                await upsert_default_product()
                product_id = await connection.fetch_val(
                    "SELECT id FROM material_specs WHERE product_slug = :slug",
                    {"slug": product_slug},
                )

            content_id = await connection.execute(
                """
                INSERT INTO content_chunks (
                  product_id, keyword, intent, chunk_type, title, content, rag_score, quality_status
                )
                VALUES (:product_id, :keyword, :intent, 'answer_summary', :title, :content, :score, :status)
                """,
                {
                    "product_id": product_id,
                    "keyword": keyword,
                    "intent": intent,
                    "title": keyword,
                    "content": content,
                    "score": score,
                    "status": status,
                },
            )
        return int(content_id)
    except (RuntimeError, OSError, Exception):
        return _next_local_id()


async def list_recent_leads(limit: int = 20) -> list[dict[str, Any]]:
    """list_recent_leads。

    参数说明：
    :param limit: 参数 limit
    :return: 返回处理结果。
    """
    try:
        async with geo_db.acquire() as connection:  # type: ignore[attr-defined]
            rows = await connection.fetch_all(
                """
                SELECT
                  id,
                  keyword,
                  name,
                  phone,
                  region,
                  distance_km,
                  quantity_m3,
                  estimated_price,
                  message,
                  source_url,
                  source_channel,
                  status,
                  created_at
                FROM lead_inquiries
                ORDER BY created_at DESC
                LIMIT :limit
                """,
                {"limit": limit},
            )
        return [dict(row) for row in rows]
    except (RuntimeError, OSError, Exception):
        return _local_dev_leads[:limit]


async def summarize_leads() -> dict[str, Any]:
    """summarize_leads。
    :return: 返回处理结果。
    """
    try:
        async with geo_db.acquire() as connection:  # type: ignore[attr-defined]
            row = await connection.fetch_one(
                """
                SELECT
                  COUNT(*)::int AS total,
                  COALESCE(SUM(quantity_m3), 0)::float AS total_quantity_m3,
                  COALESCE(AVG(estimated_price), 0)::float AS avg_estimated_price
                FROM lead_inquiries
                """
            )
            regions = await connection.fetch_all(
                """
                SELECT COALESCE(region, '未知') AS region, COUNT(*)::int AS count
                FROM lead_inquiries
                GROUP BY COALESCE(region, '未知')
                ORDER BY count DESC
                LIMIT 5
                """
            )
        return {
            "total": int(row["total"] or 0),
            "total_quantity_m3": float(row["total_quantity_m3"] or 0),
            "avg_estimated_price": float(row["avg_estimated_price"] or 0),
            "top_regions": [dict(r) for r in regions],
        }
    except (RuntimeError, OSError, Exception):
        total = len(_local_dev_leads)
        region_counts: dict[str, int] = {}
        for lead in _local_dev_leads:
            region = str(lead.get("region") or "未知")
            region_counts[region] = region_counts.get(region, 0) + 1
        total_quantity = sum(_as_float(lead.get("quantity_m3")) for lead in _local_dev_leads)
        price_values = [_as_float(lead.get("estimated_price")) for lead in _local_dev_leads]
        avg_price = sum(price_values) / len(price_values) if price_values else 0
        return {
            "total": total,
            "total_quantity_m3": round(total_quantity, 2),
            "avg_estimated_price": round(avg_price, 2),
            "top_regions": [
                {"region": region, "count": count}
                for region, count in sorted(region_counts.items(), key=lambda item: item[1], reverse=True)[:5]
            ],
        }


async def save_lead(payload: dict[str, Any], estimated_price: float | None) -> int:
    """save_lead。

    参数说明：
    :param payload: 参数 payload
    :param estimated_price: 参数 estimated_price
    :return: 返回处理结果。
    """
    try:
        async with geo_db.acquire() as connection:  # type: ignore[attr-defined]
            product_id = await connection.fetch_val(
                "SELECT id FROM material_specs WHERE product_slug = :slug",
                {"slug": payload["product_slug"]},
            )
            lead_id = await connection.execute(
                """
                INSERT INTO lead_inquiries (
                  product_id, keyword, name, phone, region, distance_km, quantity_m3,
                  estimated_price, message, source_url, source_channel
                )
                VALUES (:product_id, :keyword, :name, :phone, :region, :distance_km, :quantity_m3,
                        :estimated_price, :message, :source_url, :source_channel)
                """,
                {
                    "product_id": product_id,
                    "keyword": payload.get("keyword"),
                    "name": payload.get("name"),
                    "phone": payload["phone"],
                    "region": payload.get("region"),
                    "distance_km": payload.get("distance_km"),
                    "quantity_m3": payload.get("quantity_m3"),
                    "estimated_price": estimated_price,
                    "message": payload.get("message"),
                    "source_url": payload.get("source_url"),
                    "source_channel": payload.get("source_channel"),
                },
            )
        return int(lead_id)
    except (RuntimeError, OSError, Exception):
        lead_id = _next_local_id()
        _local_dev_leads.insert(
            0,
            {
                "id": lead_id,
                "keyword": payload.get("keyword"),
                "name": payload.get("name"),
                "phone": payload["phone"],
                "region": payload.get("region"),
                "distance_km": payload.get("distance_km"),
                "quantity_m3": payload.get("quantity_m3"),
                "estimated_price": estimated_price,
                "message": payload.get("message"),
                "source_url": payload.get("source_url"),
                "source_channel": payload.get("source_channel"),
                "status": "new",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        del _local_dev_leads[100:]
        return lead_id


async def create_alert_rule(rule_data: dict[str, Any]) -> dict[str, Any]:
    """create_alert_rule。

    参数说明：
    :param rule_data: 参数 rule_data
    :return: 返回处理结果。
    """
    try:
        import json
        async with geo_db.acquire() as connection:  # type: ignore[attr-defined]
            # 1. 插入数据（不使用 RETURNING）
            await connection.execute(
                """
                INSERT INTO geo_alert_rules (
                  name, description, alert_type, severity, enabled,
                  rule_config, check_interval_seconds,
                  created_at, updated_at
                )
                VALUES (:name, :description, :alert_type, :severity, :enabled,
                        :rule_config, :check_interval_seconds,
                        :created_at, :updated_at)
                """,
                {
                    "name": rule_data["name"],
                    "description": rule_data.get("description", ""),
                    "alert_type": rule_data["alert_type"],
                    "severity": rule_data["severity"],
                    "enabled": rule_data.get("enabled", True),
                    "rule_config": json.dumps(rule_data.get("rule_config", {})),  # dict -> JSON string
                    "check_interval_seconds": rule_data.get("check_interval_seconds", 60),
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                },
            )
            # 2. 获取最后插入的ID
            id_row = await connection.fetch_one("SELECT last_insert_rowid() as id")
            rule_id = id_row["id"]
            # 3. 查询完整记录
            row = await connection.fetch_one(
                """
                SELECT id, name, description, alert_type, severity, enabled,
                       rule_config, check_interval_seconds, last_triggered_at,
                       trigger_count, created_at, updated_at
                FROM geo_alert_rules
                WHERE id = :rule_id
                """,
                {"rule_id": rule_id},
            )
            return dict(row)
    except (RuntimeError, OSError, Exception):
        logger.error(f"❌ create_alert_rule 失败: {rule_data}", exc_info=True)
        return {
            "id": _next_local_id(),
            **rule_data,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "trigger_count": 0,
        }


async def list_alert_rules(enabled_only: bool = False) -> list[dict[str, Any]]:
    """list_alert_rules。

    参数说明：
    :param enabled_only: 参数 enabled_only
    :return: 返回处理结果。
    """
    try:
        async with geo_db.acquire() as connection:  # type: ignore[attr-defined]
            query = """
                SELECT id, name, description, alert_type, severity, enabled,
                       rule_config, check_interval_seconds, last_triggered_at,
                       trigger_count, created_at, updated_at
                FROM geo_alert_rules
            """
            if enabled_only:
                query += " WHERE enabled = TRUE"
            query += " ORDER BY created_at DESC"
            rows = await connection.fetch_all(query)
            return [dict(row) for row in rows]
    except (RuntimeError, OSError, Exception):
        return []


async def get_alert_rule(rule_id: int) -> dict[str, Any] | None:
    """get_alert_rule。

    参数说明：
    :param rule_id: 参数 rule_id
    :return: 返回处理结果。
    """
    try:
        async with geo_db.acquire() as connection:  # type: ignore[attr-defined]
            row = await connection.fetch_one(
                """
                SELECT id, name, description, alert_type, severity, enabled,
                       rule_config, check_interval_seconds, last_triggered_at,
                       trigger_count, created_at, updated_at
                FROM geo_alert_rules
                WHERE id = :rule_id
                """,
                {"rule_id": rule_id},
            )
            return dict(row) if row else None
    except (RuntimeError, OSError, Exception):
        return None


async def update_alert_rule(rule_id: int, rule_data: dict[str, Any]) -> dict[str, Any] | None:
    """update_alert_rule。

    参数说明：
    :param rule_id: 参数 rule_id
    :param rule_data: 参数 rule_data
    :return: 返回处理结果。
    """
    try:
        async with geo_db.acquire() as connection:  # type: ignore[attr-defined]
            update_fields = []
            params = {"rule_id": rule_id}
            param_idx = 2
            allowed_fields = ["name", "description", "alert_type", "severity", 
                              "enabled", "rule_config", "check_interval_seconds"]
            for field in allowed_fields:
                if field in rule_data:
                    update_fields.append(f"{field} = :{field}")
                    params[field] = rule_data[field]
            
            if not update_fields:
                return await get_alert_rule(rule_id)
            
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            query = f"""
                UPDATE geo_alert_rules
                SET {', '.join(update_fields)}
                WHERE id = :rule_id
                RETURNING id, name, description, alert_type, severity, enabled,
                          rule_config, check_interval_seconds, last_triggered_at,
                          trigger_count, created_at, updated_at
            """
            row = await connection.fetch_one(query, params)
            return dict(row) if row else None
    except (RuntimeError, OSError, Exception):
        return None


async def create_alert(alert_data: dict[str, Any]) -> dict[str, Any]:
    """create_alert。

    参数说明：
    :param alert_data: 参数 alert_data
    :return: 返回处理结果。
    """
    try:
        async with geo_db.acquire() as connection:  # type: ignore[attr-defined]
            row = await connection.fetch_one(
                """
                INSERT INTO geo_alerts (
                  rule_id, alert_type, severity, title, description,
                  impact_scope, proposed_solution, metadata
                )
                VALUES (:rule_id, :alert_type, :severity, :title, :description,
                        :impact_scope, :proposed_solution, :metadata)
                RETURNING id, rule_id, alert_type, severity, status, title,
                          description, impact_scope, proposed_solution, metadata,
                          acknowledged_at, acknowledged_by, resolved_at, resolved_by,
                          resolution_notes, created_at, updated_at
                """,
                {
                    "rule_id": alert_data.get("rule_id"),
                    "alert_type": alert_data["alert_type"],
                    "severity": alert_data["severity"],
                    "title": alert_data["title"],
                    "description": alert_data["description"],
                    "impact_scope": alert_data.get("impact_scope", ""),
                    "proposed_solution": alert_data.get("proposed_solution", ""),
                    "metadata": alert_data.get("metadata", {}),
                },
            )
            alert = dict(row)
            await connection.execute(
                """
                INSERT INTO geo_alert_histories (
                  alert_id, action_type, new_status, metadata
                )
                VALUES (:alert_id, 'created', :new_status, :metadata)
                """,
                {
                    "alert_id": alert["id"],
                    "new_status": alert["status"],
                    "metadata": {"source": "system"},
                },
            )
            return alert
    except (RuntimeError, OSError, Exception):
        alert = {
            "id": _next_local_id(),
            **alert_data,
            "status": "active",
            "acknowledged_at": None,
            "acknowledged_by": None,
            "resolved_at": None,
            "resolved_by": None,
            "resolution_notes": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        _local_dev_alerts.insert(0, alert)
        _local_dev_histories.append({
            "id": _next_local_id(),
            "alert_id": alert["id"],
            "action_type": "created",
            "action_by": None,
            "action_notes": None,
            "old_status": None,
            "new_status": alert["status"],
            "metadata": {"source": "system"},
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return alert


async def list_alerts(
    status: str | None = None,
    severity: str | None = None,
    alert_type: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """list_alerts。

    参数说明：
    :param status: 参数 status
    :param severity: 参数 severity
    :param alert_type: 参数 alert_type
    :param page: 参数 page
    :param page_size: 参数 page_size
    :return: 返回处理结果。
    """
    try:
        async with geo_db.acquire() as connection:  # type: ignore[attr-defined]
            conditions = []
            params = {}
            param_idx = 1
            if status:
                conditions.append(f"status = :status")
                params["status"] = status
            if severity:
                conditions.append(f"severity = :severity")
                params["severity"] = severity
            if alert_type:
                conditions.append(f"alert_type = :alert_type")
                params["alert_type"] = alert_type
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            total_row = await connection.fetch_one(
                f"SELECT COUNT(*)::int AS total FROM geo_alerts WHERE {where_clause}",
                params,
            )
            total = int(total_row["total"] or 0) if total_row else 0
            offset = (page - 1) * page_size
            params["page_size"] = page_size
            params["offset"] = offset
            rows = await connection.fetch_all(
                f"""
                SELECT id, rule_id, alert_type, severity, status, title,
                       description, impact_scope, proposed_solution, metadata,
                       acknowledged_at, acknowledged_by, resolved_at, resolved_by,
                       resolution_notes, created_at, updated_at
                FROM geo_alerts
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT :page_size OFFSET :offset
                """,
                params,
            )
            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": [dict(row) for row in rows],
            }
    except (RuntimeError, OSError, Exception):
        filtered = _local_dev_alerts
        if status:
            filtered = [a for a in filtered if a["status"] == status]
        if severity:
            filtered = [a for a in filtered if a["severity"] == severity]
        if alert_type:
            filtered = [a for a in filtered if a["alert_type"] == alert_type]
        
        total = len(filtered)
        offset = (page - 1) * page_size
        items = filtered[offset:offset + page_size]
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items,
        }


async def get_alert(alert_id: int) -> dict[str, Any] | None:
    """get_alert。

    参数说明：
    :param alert_id: 参数 alert_id
    :return: 返回处理结果。
    """
    try:
        async with geo_db.acquire() as connection:  # type: ignore[attr-defined]
            row = await connection.fetch_one(
                """
                SELECT id, rule_id, alert_type, severity, status, title,
                       description, impact_scope, proposed_solution, metadata,
                       acknowledged_at, acknowledged_by, resolved_at, resolved_by,
                       resolution_notes, created_at, updated_at
                FROM geo_alerts
                WHERE id = :alert_id
                """,
                {"alert_id": alert_id},
            )
            return dict(row) if row else None
    except (RuntimeError, OSError, Exception):
        for alert in _local_dev_alerts:
            if alert["id"] == alert_id:
                return alert
        return None


async def acknowledge_alert(alert_id: int, acknowledged_by: str, notes: str = "") -> dict[str, Any] | None:
    """acknowledge_alert。

    参数说明：
    :param alert_id: 参数 alert_id
    :param acknowledged_by: 参数 acknowledged_by
    :param notes: 参数 notes
    :return: 返回处理结果。
    """
    try:
        async with geo_db.acquire() as connection:  # type: ignore[attr-defined]
            old_status_row = await connection.fetch_one(
                "SELECT status FROM geo_alerts WHERE id = :alert_id",
                {"alert_id": alert_id},
            )
            old_status = old_status_row["status"] if old_status_row else None
            row = await connection.fetch_one(
                """
                UPDATE geo_alerts
                SET status = 'acknowledged',
                    acknowledged_at = CURRENT_TIMESTAMP,
                    acknowledged_by = :acknowledged_by,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :alert_id
                RETURNING id, rule_id, alert_type, severity, status, title,
                          description, impact_scope, proposed_solution, metadata,
                          acknowledged_at, acknowledged_by, resolved_at, resolved_by,
                          resolution_notes, created_at, updated_at
                """,
                {"acknowledged_by": acknowledged_by, "alert_id": alert_id},
            )
            if row:
                await connection.execute(
                    """
                    INSERT INTO geo_alert_histories (
                      alert_id, action_type, action_by, action_notes,
                      old_status, new_status, metadata
                    )
                    VALUES (:alert_id, 'acknowledged', :action_by, :action_notes,
                            :old_status, 'acknowledged', :metadata)
                    """,
                    {
                        "alert_id": alert_id,
                        "action_by": acknowledged_by,
                        "action_notes": notes,
                        "old_status": old_status,
                        "metadata": {"source": "user"},
                    },
                )
                return dict(row)
            return None
    except (RuntimeError, OSError, Exception):
        alert = None
        for a in _local_dev_alerts:
            if a["id"] == alert_id:
                alert = a
                break
        
        if alert:
            old_status = alert["status"]
            alert["status"] = "acknowledged"
            alert["acknowledged_at"] = datetime.now(timezone.utc).isoformat()
            alert["acknowledged_by"] = acknowledged_by
            alert["updated_at"] = datetime.now(timezone.utc).isoformat()
            _local_dev_histories.append({
                "id": _next_local_id(),
                "alert_id": alert_id,
                "action_type": "acknowledged",
                "action_by": acknowledged_by,
                "action_notes": notes,
                "old_status": old_status,
                "new_status": "acknowledged",
                "metadata": {"source": "user"},
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            return alert
        return None


async def resolve_alert(alert_id: int, resolved_by: str, resolution_notes: str) -> dict[str, Any] | None:
    """resolve_alert。

    参数说明：
    :param alert_id: 参数 alert_id
    :param resolved_by: 参数 resolved_by
    :param resolution_notes: 参数 resolution_notes
    :return: 返回处理结果。
    """
    try:
        async with geo_db.acquire() as connection:  # type: ignore[attr-defined]
            old_status_row = await connection.fetch_one(
                "SELECT status FROM geo_alerts WHERE id = :alert_id",
                {"alert_id": alert_id},
            )
            old_status = old_status_row["status"] if old_status_row else None
            row = await connection.fetch_one(
                """
                UPDATE geo_alerts
                SET status = 'resolved',
                    resolved_at = CURRENT_TIMESTAMP,
                    resolved_by = :resolved_by,
                    resolution_notes = :resolution_notes,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :alert_id
                RETURNING id, rule_id, alert_type, severity, status, title,
                          description, impact_scope, proposed_solution, metadata,
                          acknowledged_at, acknowledged_by, resolved_at, resolved_by,
                          resolution_notes, created_at, updated_at
                """,
                {"resolved_by": resolved_by, "resolution_notes": resolution_notes, "alert_id": alert_id},
            )
            if row:
                await connection.execute(
                    """
                    INSERT INTO geo_alert_histories (
                      alert_id, action_type, action_by, action_notes,
                      old_status, new_status, metadata
                    )
                    VALUES (:alert_id, 'resolved', :action_by, :action_notes,
                            :old_status, 'resolved', :metadata)
                    """,
                    {
                        "alert_id": alert_id,
                        "action_by": resolved_by,
                        "action_notes": resolution_notes,
                        "old_status": old_status,
                        "metadata": {"source": "user"},
                    },
                )
                return dict(row)
            return None
    except (RuntimeError, OSError, Exception):
        alert = None
        for a in _local_dev_alerts:
            if a["id"] == alert_id:
                alert = a
                break
        
        if alert:
            old_status = alert["status"]
            alert["status"] = "resolved"
            alert["resolved_at"] = datetime.now(timezone.utc).isoformat()
            alert["resolved_by"] = resolved_by
            alert["resolution_notes"] = resolution_notes
            alert["updated_at"] = datetime.now(timezone.utc).isoformat()
            _local_dev_histories.append({
                "id": _next_local_id(),
                "alert_id": alert_id,
                "action_type": "resolved",
                "action_by": resolved_by,
                "action_notes": resolution_notes,
                "old_status": old_status,
                "new_status": "resolved",
                "metadata": {"source": "user"},
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            return alert
        return None


async def get_alert_histories(alert_id: int) -> list[dict[str, Any]]:
    """get_alert_histories。

    参数说明：
    :param alert_id: 参数 alert_id
    :return: 返回处理结果。
    """
    try:
        async with geo_db.acquire() as connection:  # type: ignore[attr-defined]
            rows = await connection.fetch_all(
                """
                SELECT id, alert_id, action_type, action_by, action_notes,
                       old_status, new_status, metadata, created_at
                FROM geo_alert_histories
                WHERE alert_id = :alert_id
                ORDER BY created_at ASC
                """,
                {"alert_id": alert_id},
            )
            return [dict(row) for row in rows]
    except (RuntimeError, OSError, Exception):
        histories = [h for h in _local_dev_histories if h["alert_id"] == alert_id]
        histories.sort(key=lambda x: x["created_at"])
        return histories


async def get_alert_statistics() -> dict[str, Any]:
    """get_alert_statistics。
    :return: 返回处理结果。
    """
    from collections import defaultdict
    total_alerts = len(_local_dev_alerts)
    active_alerts = len([a for a in _local_dev_alerts if a["status"] == "active"])
    today = datetime.now(timezone.utc).date().isoformat()
    resolved_today = 0
    for a in _local_dev_alerts:
        if a["status"] == "resolved" and a["resolved_at"]:
            resolved_date = a["resolved_at"][:10]
            if resolved_date == today:
                resolved_today += 1
    
    by_severity = defaultdict(int)
    by_type = defaultdict(int)
    for a in _local_dev_alerts:
        by_severity[a["severity"]] += 1
        by_type[a["alert_type"]] += 1
    
    trend_last_7_days = []
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).date()
    for i in range(7):
        current_date = seven_days_ago + timedelta(days=i)
        date_str = current_date.isoformat()
        day_count = 0
        critical_count = 0
        error_count = 0
        warning_count = 0
        info_count = 0
        for a in _local_dev_alerts:
            alert_date = a["created_at"][:10]
            if alert_date == date_str:
                day_count += 1
                if a["severity"] == "critical":
                    critical_count += 1
                elif a["severity"] == "error":
                    error_count += 1
                elif a["severity"] == "warning":
                    warning_count += 1
                elif a["severity"] == "info":
                    info_count += 1
        
        trend_last_7_days.append({
            "date": date_str,
            "count": day_count,
            "critical_count": critical_count,
            "error_count": error_count,
            "warning_count": warning_count,
            "info_count": info_count,
        })
    
    return {
        "total_alerts": total_alerts,
        "active_alerts": active_alerts,
        "resolved_today": resolved_today,
        "by_severity": dict(by_severity),
        "by_type": dict(by_type),
        "trend_last_7_days": trend_last_7_days,
    }


async def update_alert_rule_trigger(rule_id: int) -> None:
    """update_alert_rule_trigger。

    参数说明：
    :param rule_id: 参数 rule_id
    :return: 返回处理结果。
    """
    try:
        async with geo_db.acquire() as connection:  # type: ignore[attr-defined]
            await connection.execute(
                """
                UPDATE geo_alert_rules
                SET last_triggered_at = CURRENT_TIMESTAMP,
                    trigger_count = trigger_count + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :rule_id
                """,
                {"rule_id": rule_id},
            )
    except (RuntimeError, OSError, Exception):
        pass
