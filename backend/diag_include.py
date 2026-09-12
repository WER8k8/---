import warnings, fastapi
warnings.filterwarnings("ignore")
from fastapi import APIRouter
from fastapi.routing import APIRoute
def n(r): return len([x for x in r.routes if isinstance(x, APIRoute)])

import app.api.v1.routes.products as p
print("src routes:", n(p.router))
T1 = APIRouter(); T1.include_router(p.router); print("no-prefix ->", n(T1))
T2 = APIRouter(); T2.include_router(p.router, prefix="/products"); print("prefix=/products ->", n(T2))
T3 = APIRouter(); T3.include_router(p.router, prefix="/products", tags=["产品"]); print("prefix+tags ->", n(T3))

# 自建简单 router 对照
S = APIRouter()
@S.get("/x")
def x():
    return {}
T4 = APIRouter(); T4.include_router(S, prefix="/y"); print("simple prefix=/y ->", n(T4))

print("fastapi version:", fastapi.__version__)
