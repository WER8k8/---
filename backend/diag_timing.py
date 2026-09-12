import warnings, logging
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.WARNING, format="SKIP %(name)s: %(message)s")

from fastapi.routing import APIRoute
def n(r): return len([x for x in r.routes if isinstance(x, APIRoute)])

# 触发包导入（会执行 __init__ 内的 auto_register_routes，期间 warning 会被打印）
print(">>> importing app.api.v1.routes ...")
import app.api.v1.routes as rv
print(">>> v1.routes.router routes after import:", n(rv.router))

# 导入后再次注册
from app.api.v1.routes.auto_discovery import auto_register_routes
added = auto_register_routes(rv.router)
print(">>> 导入后二次 auto_register 新增:", added, "现在 routes:", n(rv.router))
