import os
os.environ['SECRET_KEY'] = 'dev-secret-key-for-local-development-123456789012'
os.environ['JWT_SECRET_KEY'] = 'dev-jwt-secret-key-for-local-development-123456789012'
os.environ['HERMES_GREEDY_AVATAR_ENABLED'] = 'true'

from app.core.config import settings
from app.db.session import get_db
from app.services.hermes.agency.role_loader import load_role
from app.services.hermes.expert_inspection_registry import inspect_expert

db = next(get_db())

rid = 'marketing/marketing-seo-specialist'
print(f"测试巡检: {rid}")
try:
    result = inspect_expert(rid, db)
    print(f"成功: {result}")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"错误: {e}")
