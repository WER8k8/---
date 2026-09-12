"""官方绿色部署引导（P0-B 处置：以 create_all + stamp 为正式建库路径）。

背景（详见 audit/2026-09-05 BC 报告与 ticket 10）：
    历史 alembic 迁移链存在 ID 类型分裂（部分迁移硬编码 String(36)，模型为
    UUID_TYPE），greenfield `upgrade heads` 无法从 001 跑通。而项目实践（
    youding_dev / uj_test）早已用 `Base.metadata.create_all` + `alembic stamp`
    建库且 schema 一致（200 表、uuid 统一）。本脚本把这一实践转正：

用法：
    DB_TYPE=postgresql DATABASE_URL=postgresql+psycopg2://... python scripts/bootstrap_greenfield.py
可选：
    --seed   建库后写入最小演示数据（两租户/用户/绑定），供 RLS 验证
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("bootstrap")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", action="store_true", help="写入 RLS 验证演示数据")
    args = ap.parse_args()

    from alembic.config import Config
    from alembic import command
    from sqlalchemy import inspect

    from app.core.database import Base, engine
    import app.models  # noqa: F401  注册全部模型

    insp = inspect(engine)
    existing = set(insp.get_table_names())
    Base.metadata.create_all(engine)
    after = set(inspect(engine).get_table_names())
    created = len(after - existing)
    log.info("create_all 完成：表 %d（新建 %d）", len(after), created)

    # stamp 到当前 head，使后续新迁移可正常 upgrade
    cfg = Config("alembic.ini")
    from alembic.script import ScriptDirectory
    head = ScriptDirectory.from_config(cfg).get_heads()[0]
    cfg.set_main_option("sqlalchemy.url", engine.url.render_as_string(hide_password=False))
    command.stamp(cfg, head)
    log.info("stamp 到 head=%s", head)

    if args.seed:
        _seed()
        log.info("seed 完成")

    log.info("bootstrap OK")
    return 0


def _seed() -> None:
    """最小演示数据：两租户 + 各一 admin 用户 + UserTenant 绑定 + pilot 行。"""
    import uuid
    from datetime import datetime, timezone

    from sqlalchemy import text

    from app.db.session import SessionLocal
    from app.core.database import UUID_TYPE
    from app.models.tenant import Tenant, UserTenant
    from app.models.user import User
    from app.models.content import ContentMaster  # pilot 表之一

    db = SessionLocal()
    try:
        def mk_tenant(name: str) -> Tenant:
            t = db.query(Tenant).filter(Tenant.name == name).first()
            if t is None:
                t = Tenant(id=str(uuid.uuid4()), name=name, domain=f"{name}.local",
                           plan_id=None, status="active", created_at=datetime.now(timezone.utc))
                db.add(t)
                db.flush()
            return t

        def mk_user(username: str) -> User:
            u = db.query(User).filter(User.username == username).first()
            if u is None:
                u = User(id=str(uuid.uuid4()), username=username, email=f"{username}@local",
                         hashed_password="x", role="tenant_admin", is_active=True,
                         is_default_password=False)
                db.add(u)
                db.flush()
            return u

        ta = mk_tenant("rls-tenant-a")
        tb = mk_tenant("rls-tenant-b")
        ua = mk_user("rls_admin_a")
        ub = mk_user("rls_admin_b")
        for u, t in ((ua, ta), (ub, tb)):
            if not db.query(UserTenant).filter(UserTenant.user_id == u.id).first():
                db.add(UserTenant(id=str(uuid.uuid4()), user_id=u.id, tenant_id=t.id,
                                  role="admin", is_active=True))

        # pilot 表行：各租户一条 content_master（存在才种）
        cols = [c["name"] for c in _columns(db, "content_masters")]
        if cols:
            for t, tag in ((ta, "A"), (tb, "B")):
                row = {"id": str(uuid.uuid4()), "tenant_id": t.id}
                if "title" in cols: row["title"] = f"RLS-DEMO-{tag}"
                if "name" in cols: row["name"] = f"RLS-DEMO-{tag}"
                obj = ContentMaster(**{k: v for k, v in row.items() if hasattr(ContentMaster, k)})
                db.add(obj)
        db.commit()
        log.info("seed: tenants=%s users=%s", [ta.name, tb.name], [ua.username, ub.username])
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _columns(db, table: str):
    from sqlalchemy import inspect
    try:
        return inspect(db.bind).get_columns(table)
    except Exception:
        return []


if __name__ == "__main__":
    sys.exit(main())
