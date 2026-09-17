"""纯逻辑单测：只测 build_synthetic_business_rows 生成函数，不连真实数据库、不执行 seed() 写库。"""
from seed import SCENARIOS, build_synthetic_business_rows


def test_nonempty_and_tagged():
    rows = build_synthetic_business_rows()
    assert rows
    assert all(r["synthetic"] is True and r["scenario"] in SCENARIOS for r in rows)


def test_all_kinds_present():
    rows = build_synthetic_business_rows()
    assert {r["kind"] for r in rows} == {"category", "product", "inquiry"}


def test_schema_stable_across_calls():
    """同一次输入多次调用，each kind 字段键集合一致。"""
    def schema():
        out = {}
        for r in build_synthetic_business_rows(n=len(SCENARIOS)):
            out.setdefault(r["kind"], set()).update(r.keys())
        return out

    assert schema() == schema()


def test_count_respects_n():
    assert len(build_synthetic_business_rows(n=2)) == 6