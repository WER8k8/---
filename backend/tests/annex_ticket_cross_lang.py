"""跨语言票据协议兼容验证：UJ（Python HS256）↔ GoodJob（Node crypto）。

两侧独立实现同一票据协议（§9.3），此测试证明：
1. Python 签发的票据能被 Node 用相同密钥验签 + 解析声明；
2. Node 签发的票据能被 Python redeem 校验（验签 + 一次性 + 声明）；
3. 声明字段（iss/aud/sub/email/annex_role/jti/purpose）两侧理解一致。

用法：
  $env:ANNEX_TICKET_SECRET='x'; $env:UJ_BRIDGE_SECRET='x'; python -m tests.annex_ticket_cross_lang
依赖：node >= 18（子进程调用）。
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import types

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _BACKEND)

for _pkg in ("app", "app.services", "app.services.annex"):
    if _pkg not in sys.modules:
        _mod = types.ModuleType(_pkg)
        _mod.__path__ = []
        sys.modules[_pkg] = _mod

ts = _load_from_file = importlib.util.spec_from_file_location(
    "app.services.annex.ticket_service",
    os.path.join(_BACKEND, "app", "services", "annex", "ticket_service.py"),
)
tsm = importlib.util.module_from_spec(ts)
sys.modules["app.services.annex.ticket_service"] = tsm
ts.loader.exec_module(tsm)

SECRET = "cross-language-test-secret-at-least-32chars"
os.environ["ANNEX_TICKET_SECRET"] = SECRET

PASS = 0
FAIL = 0


def check(name: str, cond: bool, detail: str = ""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} {detail}")


# Node 侧：独立实现验签 + 声明校验（与 GoodJob 生产消费 UJ redeem 响应不同——
# 这里验证的是票据本身跨语言可验，即若附属侧直接持密钥也能校验的场景）。
NODE_VERIFY = r"""
const crypto = require("crypto");
const [secret, ticket, annex] = process.argv.slice(1);
const parts = ticket.split(".");
if (parts.length !== 3) { console.error("bad format"); process.exit(2); }
const [h, p, s] = parts;
const expected = crypto.createHmac("sha256", secret).update(`${h}.${p}`).digest();
const supplied = Buffer.from(s.replace(/-/g, "+").replace(/_/g, "/"), "base64");
if (expected.length !== supplied.length || !crypto.timingSafeEqual(expected, supplied)) {
  console.error("bad signature"); process.exit(3);
}
const payload = JSON.parse(Buffer.from(p.replace(/-/g, "+").replace(/_/g, "/"), "base64").toString("utf8"));
if (payload.aud !== `annex:${annex}`) { console.error("bad aud"); process.exit(4); }
if (payload.purpose !== "annex_ticket") { console.error("bad purpose"); process.exit(5); }
console.log(JSON.stringify({ sub: payload.sub, email: payload.email, annex_role: payload.annex_role, jti: payload.jti }));
"""

NODE_SIGN = r"""
const crypto = require("crypto");
const [secret, annex] = process.argv.slice(1);
const b64 = (buf) => Buffer.from(buf).toString("base64url");
const now = Math.floor(Date.now() / 1000);
const payload = {
  iss: "uj-master", aud: `annex:${annex}`, sub: "u-3003", name: "王五",
  email: "wangwu@example.com", uj_role: "sales", tenant_id: "t-99", annex,
  annex_role: annex === "goodjob" ? "sales" : "agent", purpose: "annex_ticket",
  jti: crypto.randomUUID().replaceAll("-", ""), iat: now, exp: now + 300
};
const header = b64(JSON.stringify({ alg: "HS256", typ: "JWT" }));
const body = b64(JSON.stringify(payload));
const sig = crypto.createHmac("sha256", secret).update(`${header}.${body}`).digest("base64url");
console.log(`${header}.${body}.${sig}`);
"""


def run_node(script: str, args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        ["node", "-e", script, *args],
        capture_output=True, text=True, timeout=30,
    )
    return proc.returncode, (proc.stdout or proc.stderr).strip()


print("== 1. Python 签发 → Node 验签 ==")
issued = tsm.issue_annex_ticket(
    user_id="u-3001", user_name="张三", user_email="zhangsan@example.com",
    uj_role="super_admin", annex="trade-ai", tenant_id="t-77",
)
code, out = run_node(NODE_VERIFY, [SECRET, issued["annex_ticket"], "trade-ai"])
check("Node 验签通过", code == 0, f"exit={code} out={out}")
if code == 0:
    claims = json.loads(out)
    check("Node 解析 sub 一致", claims["sub"] == "u-3001")
    check("Node 解析 email 一致", claims["email"] == "zhangsan@example.com")
    check("Node 解析 annex_role 一致", claims["annex_role"] == "admin")

print("== 2. Node 签发 → Python redeem 校验 ==")
code, ticket = run_node(NODE_SIGN, [SECRET, "goodjob"])
check("Node 签发成功", code == 0 and ticket.count(".") == 2, f"exit={code}")
if code == 0:
    result = tsm.redeem_annex_ticket(ticket, annex="goodjob")
    check("Python redeem 成功", result["ok"] is True)
    check("Python 解析 email", result["user"]["email"] == "wangwu@example.com")
    check("Python 解析 annex_role", result["annex_role"] == "sales")
    check("Python 解析租户", result["user"]["tenant_id"] == "t-99")
    try:
        tsm.redeem_annex_ticket(ticket, annex="goodjob")
        check("跨语言一次性防重放", False, "重放成功")
    except tsm.TicketRejected:
        check("跨语言一次性防重放", True)

print()
print(f"结果：{PASS} 通过 / {FAIL} 失败")
sys.exit(1 if FAIL else 0)
