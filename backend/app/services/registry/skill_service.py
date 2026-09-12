"""Skill 注册表服务（轮17-1/17-2）。

替代 SkillRegistry 的内存 list（Trade AI skill_base.py 的 register/get/list_all
桩），改为 083 表持久化。提供：
- register_skill / create_version：注册 Skill 与其版本；
- list_skills / get_skill / get_versions：查询；
- set_publish_status：发布态跃迁（Draft→Testing→Active→Disabled→Rollback）；
- to_runtime：把持久化 Skill 组装为 Trade AI BaseSkill 可调度的实体/字典。
"""

from __future__ import annotations

import logging
from typing import Any

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.registry import (
    RegistrySkill,
    RegistrySkillVersion,
    SKILL_STATUSES,
)
from app.services.registry.common import ensure_in, into_json, parse_json, valid_name
from app.services.registry.matrix import publish_transition

log = logging.getLogger(__name__)

LIFECYCLE_HOOKS = ("on_start", "on_success", "on_failure", "on_skip")


def _validate_validators(validators: dict | None) -> None:
    """validators 若提供则必须含 lifecycle 钩子（对齐 PG CHECK，SQLite 冒烟亦拦截）。"""
    if not validators:
        return
    lifecycle = validators.get("lifecycle") if isinstance(validators, dict) else None
    if not isinstance(lifecycle, dict):
        raise ValueError("validators 必须含 lifecycle 对象")
    missing = [h for h in LIFECYCLE_HOOKS if h not in lifecycle]
    if missing:
        raise ValueError(f"validators.lifecycle 缺少钩子: {missing}")


class SkillNotFoundError(Exception):
    """指定 skill 不存在。"""


class SkillConflictError(Exception):
    """Skill 唯一键冲突（tenant_id+name 已存在）。"""


class IllegalTransitionError(Exception):
    """发布态跃迁非法。"""


class SkillService:
    """Skill 生命周期管理服务。"""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------- 查询
    def get(self, skill_id: str) -> RegistrySkill | None:
        return self.db.query(RegistrySkill).filter(RegistrySkill.id == skill_id).first()

    def get_by_name(
        self, name: str, tenant_id: str | None = None
    ) -> RegistrySkill | None:
        q = self.db.query(RegistrySkill).filter(RegistrySkill.name == name)
        if tenant_id is not None:
            q = q.filter(RegistrySkill.tenant_id == tenant_id)
        return q.first()

    def list_skills(
        self,
        *,
        tenant_id: str | None = None,
        category: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        q = self.db.query(RegistrySkill)
        if tenant_id is not None:
            q = q.filter(RegistrySkill.tenant_id == tenant_id)
        if category:
            q = q.filter(RegistrySkill.category == category)
        if status:
            q = q.filter(RegistrySkill.status == status)
        total = q.count()
        rows = (
            q.order_by(RegistrySkill.priority.desc(), RegistrySkill.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {
            "items": [self._to_dict(s) for s in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def list_by_category(self, category: str) -> list[dict[str, Any]]:
        """按分类列出，priority 降序（轮18 §A.2 17.5 验收口径）。"""
        rows = (
            self.db.query(RegistrySkill)
            .filter(RegistrySkill.category == category)
            .order_by(RegistrySkill.priority.desc(), RegistrySkill.created_at.desc())
            .all()
        )
        return [self._to_dict(s) for s in rows]

    def list_versions(self, skill_id: str) -> list[dict[str, Any]]:
        rows = (
            self.db.query(RegistrySkillVersion)
            .filter(RegistrySkillVersion.skill_id == skill_id)
            .order_by(RegistrySkillVersion.created_at.desc())
            .all()
        )
        return [self._version_to_dict(v) for v in rows]

    # ------------------------------------------------------------- 写入
    def register_skill(
        self,
        *,
        name: str,
        display_name: str | None = None,
        category: str | None = None,
        description: str | None = None,
        tenant_id: str | None = None,
        source_type: str = "builtin",
        license: str | None = None,
        priority: int = 50,
        timeout: int | None = None,
        retry_count: int = 0,
        retry_delay: int = 0,
        triggers: list[str] | None = None,
        keywords: list[str] | None = None,
        modules: list[str] | None = None,
        tool_refs: list[str] | None = None,
        config_schema: dict | None = None,
        default_config: dict | None = None,
        permissions: dict | None = None,
        version: str = "1.0.0",
        implementation_type: str = "prompt",
        implementation: dict | None = None,
        input_schema: dict | None = None,
        output_schema: dict | None = None,
        validators: dict | None = None,
        examples: list | None = None,
        version_tool_refs: list[str] | None = None,
    ) -> RegistrySkill:
        if not valid_name(name):
            raise ValueError(f"非法 skill 名: {name!r}")
        _validate_validators(validators)
        if self.get_by_name(name, tenant_id):
            raise SkillConflictError(f"tenant={tenant_id} 已存在 skill: {name}")
        skill = RegistrySkill(
            tenant_id=tenant_id,
            name=name,
            display_name=display_name,
            category=category,
            description=description,
            current_version=version,
            status="draft",
            priority=priority,
            timeout=timeout,
            retry_count=retry_count,
            retry_delay=retry_delay,
            source_type=source_type,
            license=license,
            triggers_json=into_json(triggers),
            keywords_json=into_json(keywords),
            modules_json=into_json(modules),
            tool_refs_json=into_json(tool_refs),
            config_schema_json=into_json(config_schema),
            default_config_json=into_json(default_config),
            permissions_json=into_json(permissions),
        )
        self.db.add(skill)
        self.db.flush()  # 取得 skill.id 供版本外键
        self.db.add(
            RegistrySkillVersion(
                skill_id=skill.id,
                version=version,
                implementation_type=implementation_type,
                implementation_json=into_json(implementation),
                input_schema_json=into_json(input_schema),
                output_schema_json=into_json(output_schema),
                tool_refs_json=into_json(version_tool_refs if version_tool_refs is not None else tool_refs),
                validators_json=into_json(validators),
                examples_json=into_json(examples),
                status="draft",
                canary_percent=0,
            )
        )
        self.db.commit()
        self.db.refresh(skill)
        return skill

    def create_version(
        self,
        skill_id: str,
        *,
        version: str,
        implementation_type: str = "prompt",
        implementation: dict | None = None,
        input_schema: dict | None = None,
        output_schema: dict | None = None,
        validators: dict | None = None,
        examples: list | None = None,
        tool_refs: list[str] | None = None,
        canary_percent: int = 0,
    ) -> RegistrySkillVersion:
        skill = self.get(skill_id)
        if not skill:
            raise SkillNotFoundError(skill_id)
        _validate_validators(validators)
        existing = (
            self.db.query(RegistrySkillVersion)
            .filter(
                RegistrySkillVersion.skill_id == skill_id,
                RegistrySkillVersion.version == version,
            )
            .first()
        )
        if existing:
            raise SkillConflictError(f"skill={skill_id} 已存在版本 {version}")
        ver = RegistrySkillVersion(
            skill_id=skill_id,
            version=version,
            implementation_type=implementation_type,
            implementation_json=into_json(implementation),
            input_schema_json=into_json(input_schema),
            output_schema_json=into_json(output_schema),
            tool_refs_json=into_json(tool_refs),
            validators_json=into_json(validators),
            examples_json=into_json(examples),
            status="draft",
            canary_percent=canary_percent,
        )
        self.db.add(ver)
        skill.current_version = version
        skill.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(ver)
        return ver

    def set_publish_status(
        self, skill_id: str, target: str, *, approved_by: str | None = None
    ) -> RegistrySkill:
        skill = self.get(skill_id)
        if not skill:
            raise SkillNotFoundError(skill_id)
        ensure_in(target, SKILL_STATUSES, "status")
        if skill.status == target:
            return skill
        if not publish_transition(skill.status, target):
            raise IllegalTransitionError(
                f"非法发布态跃迁: {skill.status} -> {target}"
            )
        skill.status = target
        # 同步所有未发布的版本状态（简化：仅当前版本跟随发布态）
        self.db.query(RegistrySkillVersion).filter(
            RegistrySkillVersion.skill_id == skill_id,
            RegistrySkillVersion.version == skill.current_version,
        ).update({"status": target})
        if target == "active" and approved_by:
            self.db.query(RegistrySkillVersion).filter(
                RegistrySkillVersion.skill_id == skill_id,
                RegistrySkillVersion.version == skill.current_version,
            ).update({"approved_by": approved_by})
        self.db.commit()
        self.db.refresh(skill)
        return skill

    # ------------------------------------------------------------ 组装
    def to_runtime(self, skill_id: str) -> dict[str, Any]:
        """把持久化 Skill 组装为 BaseSkill 可调度实体（含 schema/配置/权限）。"""
        skill = self.get(skill_id)
        if not skill:
            raise SkillNotFoundError(skill_id)
        return {
            "id": str(skill.id),
            "name": skill.name,
            "display_name": skill.display_name,
            "category": skill.category,
            "description": skill.description,
            "version": skill.current_version,
            "status": skill.status,
            "priority": skill.priority,
            "timeout": skill.timeout,
            "retry_count": skill.retry_count,
            "retry_delay": skill.retry_delay,
            "source_type": skill.source_type,
            "license": skill.license,
            "triggers": skill.triggers,
            "keywords": skill.keywords,
            "modules": skill.modules,
            "tool_refs": skill.tool_refs,
            "config_schema": skill.config_schema,
            "default_config": skill.default_config,
            "permissions": skill.permissions,
        }

    # ------------------------------------------------------------ 序列化
    def _to_dict(self, s: RegistrySkill) -> dict[str, Any]:
        return {
            "id": str(s.id),
            "tenant_id": str(s.tenant_id) if s.tenant_id else None,
            "name": s.name,
            "display_name": s.display_name,
            "category": s.category,
            "description": s.description,
            "current_version": s.current_version,
            "status": s.status,
            "priority": s.priority,
            "timeout": s.timeout,
            "retry_count": s.retry_count,
            "retry_delay": s.retry_delay,
            "source_type": s.source_type,
            "license": s.license,
            "triggers": s.triggers,
            "keywords": s.keywords,
            "modules": s.modules,
            "tool_refs": s.tool_refs,
            "config_schema": s.config_schema,
            "default_config": s.default_config,
            "permissions": s.permissions,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
        }

    def _version_to_dict(self, v: RegistrySkillVersion) -> dict[str, Any]:
        return {
            "id": str(v.id),
            "skill_id": str(v.skill_id),
            "version": v.version,
            "implementation_type": v.implementation_type,
            "implementation": parse_json(v.implementation_json),
            "input_schema": v.input_schema,
            "output_schema": v.output_schema,
            "tool_refs": v.tool_refs,
            "validators": v.validators,
            "examples": parse_json(v.examples_json),
            "status": v.status,
            "canary_percent": v.canary_percent,
            "approved_by": v.approved_by,
            "approved_at": v.approved_at,
            "created_at": v.created_at,
        }


# 兼容 083 注释"替代 agent_hub_service 内存 list"：暴露模块级工厂
def build_skill_service(db: Session) -> SkillService:
    """build_skill_service。
    :param db: 会话。
    :return: SkillService 实例。
    """
    return SkillService(db)


# ──────────────────────────────────────────────
# 场景路由 + 种子（打通 ECC 节点：Hermes 按 scene_type 命中 Skill → 取 SOP）
# ──────────────────────────────────────────────
def match_skill_scored(
    db: Session, query: str, top_k: int = 3, *, auto_seed: bool = True
) -> list[tuple[RegistrySkill, int]]:
    """按意图/场景给已发布(active)的 Skill 打分，返回 [(skill, score), ...]。

    这是「Hermes/DeerFlow 自动智能判断调用哪个 skill」的路由核心：
      - 别名表命中（如 buyer_research → customer-research）权重最高；
      - 其次 name 匹配、触发词匹配、描述命中；
      - 只返回分数 > 0 的结果，按分数降序。

    ``auto_seed=True`` 时，若表里没有任何 active 技能（首次运行 / 库被清空），
    自动调用 :func:`seed_skill_pack` 从磁盘技能包补齐——避免"链路看着通、
    实则无技能可路由"的空转。
    """
    from app.services.registry.skill_pack_loader import score_skill

    def _query_active() -> list[RegistrySkill]:
        return (
            db.query(RegistrySkill)
            .filter(RegistrySkill.status == "active")
            .order_by(RegistrySkill.priority.desc())
            .all()
        )

    rows = _query_active()
    if not rows and auto_seed:
        log.info("match_skill_scored: 无 active 技能，自动从技能包补齐")
        try:
            seed_skill_pack(db)
            rows = _query_active()
        except Exception as exc:  # noqa: BLE001
            log.warning("match_skill_scored: 自动补齐技能包失败 %s", exc)

    scored = [(s, score_skill(s, query)) for s in rows]
    scored = [(s, sc) for s, sc in scored if sc > 0]
    scored.sort(key=lambda x: (-x[1], x[0].name or ""))
    return scored[:top_k]


def match_skill(db: Session, scene_type: str) -> RegistrySkill | None:
    """按 scene_type 命中已发布(active)的 Skill（兼容旧签名的单值版本）。

    内部走 :func:`match_skill_scored` 的打分路由，取分数最高者。
    """
    hits = match_skill_scored(db, scene_type, top_k=1)
    return hits[0][0] if hits else None


def _publish_active(svc: SkillService, skill_id: str) -> None:
    """把 Skill 沿合法状态机发布到 active。

    状态机是 ``draft -> testing -> active``（见 matrix.publish_transition），
    **不能直接 draft -> active**。此前 seed 直接跳 active 会抛
    IllegalTransitionError，导致技能注册了却永远发布不了（静默失效）。
    """
    svc.set_publish_status(skill_id, "testing")
    svc.set_publish_status(skill_id, "active")


def seed_skill_pack(
    db: Session,
    *,
    publish: bool = True,
    update_existing: bool = False,
    limit: int | None = None,
) -> dict[str, Any]:
    """幂等把**磁盘上的技能包**批量入库到 skills 表。

    背景：``skills`` 表长期为 0 条，Hermes/DeerFlow 的"按场景路由技能"无内容
    可路由。真正的技能资产（76 个业务 SKILL.md，可选 286 个 ECC 技能）一直躺在
    磁盘上，从没被代码读过。本函数把它们搬进注册表，让链路真正有技能可用。

    幂等性：按 ``name`` 去重。已存在的默认跳过（不覆盖运维改动）；
    ``update_existing=True`` 时更新描述/触发词/版本。

    入库记录的 ``implementation`` 里写入 ``skill_pack_path``，运行时据此
    取回 SKILL.md 正文（SOP）注入 LLM，实现"技能包驱动执行"。

    Args:
        db: 会话。
        publish: 是否直接发布为 active（否则保持 draft，不参与匹配）。
        update_existing: 是否更新已存在技能。
        limit: 最多处理条数（调试用）。

    Returns:
        {"discovered": int, "created": int, "updated": int, "skipped": int,
         "failed": int, "total_in_table": int}
    """
    # 局部导入避免循环依赖（skill_pack_loader 不依赖本模块）
    from app.services.registry.skill_pack_loader import (
        discover_skill_packs,
        resolve_skill_pack_dirs,
    )

    stats = {
        "discovered": 0,
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
        "total_in_table": 0,
    }
    dirs = resolve_skill_pack_dirs()
    if not dirs:
        log.warning("seed_skill_pack: 未解析到任何技能包目录，跳过入库")
        return stats

    entries = discover_skill_packs(dirs)
    stats["discovered"] = len(entries)
    if limit:
        entries = entries[:limit]

    svc = SkillService(db)
    for e in entries:
        try:
            existing = svc.get_by_name(e.name)
            if existing is not None:
                # 已存在但尚未发布（例如上次入库中途失败留下的 draft 残留）→ 补发布，
                # 否则重跑 seed 永远修不好这批"注册了却用不了"的技能。
                if publish and existing.status != "active":
                    try:
                        if existing.status == "draft":
                            svc.set_publish_status(str(existing.id), "testing")
                        svc.set_publish_status(str(existing.id), "active")
                        stats["updated"] += 1
                        continue
                    except Exception as exc:  # noqa: BLE001
                        db.rollback()
                        stats["failed"] += 1
                        log.warning(
                            "seed_skill_pack: 技能 %s 补发布失败: %s", e.name, exc
                        )
                        continue
                if not update_existing:
                    stats["skipped"] += 1
                    continue
                existing.description = e.description or existing.description
                existing.category = e.category or existing.category
                existing.current_version = e.version
                existing.triggers_json = into_json(e.triggers)
                existing.keywords_json = into_json(e.keywords)
                db.commit()
                stats["updated"] += 1
                continue

            skill = svc.register_skill(
                name=e.name,
                display_name=e.display_name or e.name,
                category=e.category,
                description=e.description,
                source_type="skill_pack",
                priority=50,
                triggers=e.triggers,
                keywords=e.keywords,
                version=e.version,
                implementation_type="prompt",
                implementation={
                    "skill_pack_path": e.path,
                    "skill_pack_source": e.source,
                    "skill_pack_name": e.name,
                },
                input_schema={"query": "string", "context": "object"},
                output_schema={"result": "object"},
            )
            if publish:
                _publish_active(svc, str(skill.id))
            stats["created"] += 1
        except Exception as exc:  # noqa: BLE001  单个技能失败不影响整批
            db.rollback()
            stats["failed"] += 1
            log.warning("seed_skill_pack: 技能 %s 入库失败: %s", e.name, exc)

    stats["total_in_table"] = db.query(RegistrySkill).count()
    log.info(
        "seed_skill_pack: 发现 %d | 新建 %d | 更新 %d | 跳过 %d | 失败 %d | 表内共 %d",
        stats["discovered"], stats["created"], stats["updated"],
        stats["skipped"], stats["failed"], stats["total_in_table"],
    )
    return stats


def seed_default_skills(db: Session) -> RegistrySkill | None:
    """幂等种子：为建站场景注册并发布 build_site Skill（含 ECC 外贸 SOP 触发词）。

    让 ECC 注册表从"空壳"变为"有真实内容可被 match_skill 命中"。重复调用安全
    （按 name 去重）。返回已注册/既有 Skill。
    """
    svc = SkillService(db)
    existing = svc.get_by_name("build_site")
    if existing:
        return existing
    skill = svc.register_skill(
        name="build_site",
        display_name="多语独立站生成",
        category="site_build",
        description="上传图片/需求 → 生成多语言外贸独立站（ECC 外贸 SOP：CE 认证/承重/质保/MOQ/柜量注入）",
        triggers=["ai_site_build", "site_build", "建站", "独立站", "website"],
        keywords=["site", "website", "bicycle", "product", "i18n", "多语", "外贸"],
        priority=90,
        version="1.0.0",
        implementation_type="workflow",
        implementation={"bridge_task_type": "ai_site_builder_v1"},
        input_schema={"product_name": "string", "product_images": "array"},
        output_schema={"url": "string", "product_name": "string"},
    )
    # 走合法状态机 draft -> testing -> active（直接 set active 会抛跃迁异常）
    _publish_active(svc, str(skill.id))
    return skill