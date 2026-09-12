import warnings, logging, importlib, pkgutil, traceback
from pathlib import Path
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.WARNING, format="WARN %(name)s: %(message)s")
from fastapi import APIRouter
from fastapi.routing import APIRoute
def n(r): return len([x for x in r.routes if isinstance(x, APIRoute)])

print("######## 场景A: 先预导入全部子模块，再 auto_register ########")
pkg = importlib.import_module("app.api.v1.routes")
pdir = Path(pkg.__file__).parent
imported_ok = 0
for _, m, _ in pkgutil.iter_modules([str(pdir)]):
    if m.startswith("_") or m == "auto_discovery": continue
    try:
        mm = importlib.import_module(f"app.api.v1.routes.{m}")
        if hasattr(mm, "router"): imported_ok += 1
    except Exception as e:
        print("PREIMPORT FAIL", m, type(e).__name__, str(e)[:120])
print("preimport router-ok:", imported_ok)
from app.api.v1.routes import auto_discovery as ad
Ta = APIRouter(prefix="/v1")
ca = ad.auto_register_routes(Ta)
print("场景A auto_register count:", ca, "routes:", n(Ta))

print("\n######## 场景B: 全新进程仅 import app.main，再 auto_register 新router ########")
# 注意：本进程已 import 过 app 包，为隔离用子进程
import subprocess, sys
code = '''
import warnings, logging, importlib, pkgutil
from pathlib import Path
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.WARNING, format="WARN %(name)s: %(message)s")
from fastapi import APIRouter
from fastapi.routing import APIRoute
def n(r): return len([x for x in r.routes if isinstance(x, APIRoute)])
try:
    from app.main import app
    from app.api.v1.routes import auto_discovery as ad
    T = APIRouter(prefix="/v1")
    c = ad.auto_register_routes(T)
    print("场景B app.main import OK; fresh auto_register count:", c, "routes:", n(T))
    import app.api.v1.routes as rv
    print("场景B v1.router routes:", n(rv.router))
except Exception as e:
    traceback.print_exc()
'''
r = subprocess.run([".venv/Scripts/python.exe", "-c", code], cwd=".", capture_output=True, text=True)
print(r.stdout)
print(r.stderr[:2000])
