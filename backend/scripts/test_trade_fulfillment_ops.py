import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.user import User
from app.models.tenant import UserTenant
from app.core.security import create_access_token

def test_endpoints():
    client = TestClient(app)
    db = SessionLocal()
    user = db.query(User).filter(User.username == "tenant").first()
    if not user:
        link = db.query(UserTenant).first()
        user = db.query(User).filter(User.id == link.user_id).first()

    token = create_access_token({"sub": str(user.id), "username": user.username, "role": user.role})
    db.close()

    # 1. 先发一次 GET 获取 csrf_token
    init_res = client.get("/api/v1/health")
    csrf_token = init_res.cookies.get("csrf_token") or ""

    headers = {
        "Authorization": f"Bearer {token}",
        "X-CSRF-Token": csrf_token,
    }
    cookies = {"csrf_token": csrf_token}

    print("==================================================")
    print("🚀 外贸 7 步履约与 4 大极速操作端到端联调测试")
    print("==================================================")

    # 2. 测试【找客户】POST /trade/inquiries/capture
    print("1. 测试【找客户】POST /api/v1/trade/inquiries/capture...")
    res1 = client.post("/api/v1/trade/inquiries/capture", json={
        "buyer_name": "Sultan Al-Otaibi",
        "company": "Riyadh Metro Consortium",
        "region": "SA",
        "product_interest": "50mm Rockwool Sandwich Panels",
        "budget": "$120,000",
        "phone": "+966509876543"
    }, headers=headers, cookies=cookies)
    print(f"   状态码: {res1.status_code}")
    if res1.status_code == 200:
        d1 = res1.json().get("data", {})
        print(f"   ✓ 成功捕获线索数: {d1.get('total_captured')}, 第一条买家: {d1.get('leads', [{}])[0].get('buyer_name')} ({d1.get('leads', [{}])[0].get('company')})")
    else:
        print(f"   ❌ 响应: {res1.text[:200]}")

    # 3. 测试【报价格】POST /orders/fulfillment/quote
    print("2. 测试【报价格】POST /api/v1/orders/fulfillment/quote...")
    res2 = client.post("/api/v1/orders/fulfillment/quote", json={
        "spec_key": "rockwool_sandwich_50mm",
        "quantity_sqm": 2400.0,
        "destination_port": "Dammam, Saudi Arabia",
        "incoterm": "CIF"
    }, headers=headers, cookies=cookies)
    print(f"   状态码: {res2.status_code}")
    if res2.status_code == 200:
        d2 = res2.json().get("data", {})
        print(f"   ✓ 核价总金额: ${d2.get('destination', {}).get('total_amount_usd')} USD ({d2.get('destination', {}).get('total_amount_sar')} SAR), 40HQ货柜数: {d2.get('packaging', {}).get('containers_40hq')}")
    else:
        print(f"   ❌ 响应: {res2.text[:200]}")

    # 4. 测试【开单证】POST /orders/fulfillment/docs
    print("3. 测试【开单证】POST /api/v1/orders/fulfillment/docs...")
    res3 = client.post("/api/v1/orders/fulfillment/docs", json={
        "doc_type": "PI",
        "buyer_name": "Sultan Al-Otaibi",
        "company": "Riyadh Metro Consortium",
        "buyer_address": "Olaya District, Riyadh, Saudi Arabia",
        "buyer_country": "Saudi Arabia",
        "delivery_terms": "CIF Dammam Port"
    }, headers=headers, cookies=cookies)
    print(f"   状态码: {res3.status_code}")
    if res3.status_code == 200:
        d3 = res3.json().get("data", {})
        print(f"   ✓ 生成单证号: {d3.get('doc_no')}, 总计: ${d3.get('total_amount_usd')}, 单证类型: {d3.get('doc_type')}")
    else:
        print(f"   ❌ 响应: {res3.text[:200]}")

    # 5. 测试【查物流】GET /trade/fulfillment/timeline
    print("4. 测试【查物流】GET /api/v1/trade/fulfillment/timeline...")
    res4 = client.get("/api/v1/trade/fulfillment/timeline", headers=headers, cookies=cookies)
    print(f"   状态码: {res4.status_code}")
    if res4.status_code == 200:
        d4 = res4.json().get("data", {})
        print(f"   ✓ 当前阶段: {d4.get('current_stage')}, 进度: {d4.get('progress_pct')}%, 承运商: {d4.get('shipping_tracking', {}).get('carrier')}")
    else:
        print(f"   ❌ 响应: {res4.text[:200]}")

    # 6. 测试【今日三步】GET /client/today-three
    print("5. 测试【今日三步】GET /api/v1/client/today-three...")
    res5 = client.get("/api/v1/client/today-three", headers=headers, cookies=cookies)
    print(f"   状态码: {res5.status_code}")
    if res5.status_code == 200:
        d5 = res5.json().get("data", {})
        inqs = d5.get("recent_inquiries") or []
        print(f"   ✓ 今日步骤完成数: {d5.get('done_count')}/{d5.get('total_steps')}, 实盘询盘数: {len(inqs)}, 第一条买家: {inqs[0].get('buyer_name') if inqs else 'None'}")
    else:
        print(f"   ❌ 响应: {res5.text[:200]}")

    print("\n==================================================")
    all_ok = all(r.status_code == 200 for r in [res1, res2, res3, res4, res5])
    print(f"测试总结果: {'全部通过 (PASS)' if all_ok else '存在异常 (FAIL)'}")
    print("==================================================")
    return all_ok

if __name__ == "__main__":
    ok = test_endpoints()
    sys.exit(0 if ok else 1)
