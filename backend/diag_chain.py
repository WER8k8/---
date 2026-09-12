import warnings, logging
warnings.filterwarnings("ignore")
logging.disable(logging.CRITICAL)

from fastapi.routing import APIRoute
def n(r): return len([x for x in r.routes if isinstance(x, APIRoute)])

import app.api.v1.routes as rv
print("1) v1.routes.router routes (聚合器):", n(rv.router), " prefix=", rv.router.prefix)

import app.api as api
print("2) api.router routes (app.api):", n(api.router))

from app.main import app
print("3) app routes (最终):", n(app), " prefix of api_router include applied?")
sample = [x.path for x in app.routes if isinstance(x, APIRoute)]
print("   sample app paths:", sample[:10])
print("   total app.routes entries:", len(app.routes))
for x in app.routes:
    print("   -", type(x).__name__, getattr(x, "path", "(mount)"))
