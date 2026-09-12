import warnings, logging
warnings.filterwarnings("ignore")
logging.disable(logging.CRITICAL)

from fastapi import APIRouter
from fastapi.routing import APIRoute
def n(r): return len([x for x in r.routes if isinstance(x, APIRoute)])

import app.api.v1.routes as rv
print("rv.router id:", id(rv.router), " routes:", n(rv.router))

from app.api.v1.routes.auto_discovery import auto_register_routes

# 实验A：全新 router
T1 = APIRouter(prefix="/v1")
c1 = auto_register_routes(T1)
print("实验A 全新router -> count:", c1, " routes:", n(T1))

# 实验B：再对 rv.router 注册
before = n(rv.router)
c2 = auto_register_routes(rv.router)
after = n(rv.router)
print(f"实验B rv.router -> before:{before} count:{c2} after:{after}")

# 取样：T1 的前10个路径
print("T1 样例路径:", [x.path for x in T1.routes if isinstance(x, APIRoute)][:10])
# rv.router 的路径
print("rv.router 路径:", [x.path for x in rv.router.routes if isinstance(x, APIRoute)])
