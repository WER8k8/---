#!/usr/bin/env python3
"""PM 派工：多 AI 大模型调研大城+河间建筑相关产品名 → 共识 deliverable JSON。"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))

BACKLOG = ROOT / "backend" / "app" / "data" / "industry_belt_research_backlog.json"
OUT_DIR = ROOT / "backend" / "app" / "data" / "industry_belt_survey_samples"
RAW_DIR = OUT_DIR / "ai_raw"

REGION_LABEL = "大城县 + 河间市（廊坊/沧州建筑产业带）"


def _is_placeholder_key(value: str) -> bool:
    v = (value or "").strip().lower()
    if not v or len(v) < 8:
        return True
    return any(x in v for x in ("your_", "placeholder", "example", "_here", "changeme"))


def _load_env_files() -> None:
    """优先 dev 配置，避免根 .env 占位 Key 覆盖真实 Key。"""
    for rel in ("backend/config/dev/.env", ".env"):
        path = ROOT / rel
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key, val = key.strip(), val.strip().strip('"').strip("'")
            if "#" in val and not val.startswith('"'):
                val = val.split("#", 1)[0].strip()
            if _is_placeholder_key(val):
                continue
            # dev 配置优先：后加载的 .env 不覆盖已设的非占位值
            if key not in os.environ or rel.startswith("backend/config/dev"):
                os.environ[key] = val


_load_env_files()
OUT_DIR = ROOT / "backend" / "app" / "data" / "industry_belt_survey_samples"
RAW_DIR = OUT_DIR / "ai_raw"

REGION_LABEL = "大城县 + 河间市（廊坊/沧州建筑产业带）"

CATEGORY_EXTRA: dict[str, str] = {
    "steel_fire_coating": "区分薄型/厚型/超薄型/室内室外/膨胀与非膨胀；注意钢结构专用",
    "anti_corrosion_coating": "区分环氧/聚氨酯/氟碳/管道防腐/设备防腐",
    "finish_accessories": "网格布（耐碱/玻纤）、阴阳角、护角条、分隔条、网格带；按克重宽度",
    "fire_sealing": "阻火包、防火堵料、防火隔板、模块、防火密封胶",
    "fixing_accessories": "保温钉、塑料钉、锚固件、电焊网、挂片",
    "main_insulation": "岩棉/玻璃棉/橡塑/聚氨酯/XPS/酚醛/硅酸铝等主材",
    "hejian_rubber": "河间橡塑密封条、垫片、软接头、管道密封",
}


def _load_backlog() -> dict:
    return json.loads(BACKLOG.read_text(encoding="utf-8"))


def _find_category(backlog: dict, category_id: str) -> dict | None:
    for c in backlog.get("categories_to_survey") or []:
        if c.get("category_id") == category_id:
            return c
    return None


def _towns_from_backlog(backlog: dict) -> list[str]:
    towns: list[str] = []
    for r in backlog.get("priority_regions") or []:
        county = r.get("county") or ""
        for t in r.get("towns") or []:
            label = f"{county}{t}" if county else t
            if label not in towns:
                towns.append(label)
    return towns


def _build_region_prompt(*, region_label: str, towns: list[str]) -> str:
    towns_s = "、".join(towns) if towns else "大城留各庄、权村、广安、河间束城等"
    return f"""你是 B2B 建材产业带调研助手，只做事实型品名清单整理，不编造不存在的工厂或虚假国标。
若不确定，请在 notes 写「待核实」，不要捏造 evidence 或 URL。
输出必须是合法 JSON，不要 markdown 代码块包裹。

调研区域：{region_label}
重点乡镇/园区（可参考、可补充）：{towns_s}

请回答：这一带跟建筑、工地、工程相关的「产品名字」有哪些？尽量列全主材和附属配套。

必须覆盖（但不限于）：
1. 主材：岩棉、玻璃棉、橡塑、聚氨酯、XPS、酚醛、硅酸铝、夹芯板、净化板、冷库板等
2. 防火类：钢结构防火涂料（薄/厚/超薄型）、饰面型防火涂料、防火封堵（阻火包/堵料/模块）等
3. 防腐类：环氧/聚氨酯/氟碳等防腐涂料
4. 附属配套：网格布、耐碱网格布、阴阳角、护角条、分隔条、保温钉、锚固件、电焊网、粘结/抹面/抗裂砂浆、打包带等
5. 河间配套：橡塑密封条、垫片、软接头、管道密封等

每个品名：name, aliases, specs_common, town_cluster, product_role(main|accessory|coating|sealing),
export_suitable, notes, evidence（勿伪造链接）

按品类分组 categories（至少 8 组，每组 ≥5 品名；全区域合计尽量 ≥80 个不重复品名）。
category_id 可用：main_insulation, steel_fire_coating, fire_coating_general, anti_corrosion_coating,
fire_sealing, panel_system, finish_accessories, fixing_accessories, mortar_adhesive, pipe_support,
packaging, hejian_rubber, misc_building

另给 recommended_seo_keywords：20～40 个中文长尾词。

严格输出 JSON：
{{
  "region": "{region_label}",
  "research_question": "大城和河间一带有哪些建筑相关产品及附属配套品名",
  "categories": [],
  "recommended_seo_keywords": [],
  "research_limits": ""
}}"""


def _build_category_prompt(
    *,
    region_label: str,
    category_id: str,
    category_name_zh: str,
    towns: list[str],
) -> str:
    extra = CATEGORY_EXTRA.get(category_id, "")
    towns_s = "、".join(towns) if towns else "大城留各庄、权村、河间束城等"
    return f"""你是 B2B 建材产业带调研助手，只做事实型品名清单整理，不编造不存在的工厂或虚假国标。
若不确定，请在 notes 写「待核实」，不要捏造 evidence。
输出必须是合法 JSON，不要 markdown 代码块包裹。

调研区域：{region_label}
重点乡镇/园区：{towns_s}

在 {region_label} 产业带，请只列「{category_name_zh}」（category_id: {category_id}）下工厂常出货的品名（≥15 个）。
{("补充：" + extra) if extra else ""}

每个品名：name, aliases, specs_common, town_cluster, export_suitable, notes, evidence

另给 recommended_seo_keywords：10～20 个长尾词。

严格输出 JSON：
{{
  "region": "{region_label}",
  "categories": [{{ "category_id": "{category_id}", "category_name_zh": "{category_name_zh}", "products": [] }}],
  "recommended_seo_keywords": [],
  "research_limits": ""
}}"""


def _extract_json(text: str) -> dict | None:
    text = (text or "").strip()
    if not text:
        return None
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        text = m.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
    return None


def _norm_name(name: str) -> str:
    return re.sub(r"\s+", "", (name or "").strip().lower())


async def _query_one_model(model_info: dict, prompt: str, db=None) -> dict:
    from app.services.geo_engine_service import GEOEngine

    api_key = GEOEngine._resolve_api_key(model_info, db)
    if _is_placeholder_key(api_key):
        api_key = ""
    mid = model_info["id"]
    if not api_key:
        return {"model_id": mid, "model_name": model_info["name"], "status": "skipped", "error": "no_api_key"}

    import httpx
    import time

    max_tokens = 2500 if mid == "nvidia" else 6000
    timeout_s = 180 if mid == "nvidia" else 120
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            if mid == "anthropic":
                resp = await client.post(
                    f"{model_info['api_base']}/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model_info["model"],
                        "max_tokens": max_tokens,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                body = resp.json()
                content = body.get("content", [{}])[0].get("text", "")
            elif mid == "gemini":
                resp = await client.post(
                    f"{model_info['api_base']}/models/{model_info['model']}:generateContent",
                    params={"key": api_key},
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                )
                body = resp.json()
                content = (
                    body.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                )
            else:
                resp = await client.post(
                    f"{model_info['api_base']}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model_info["model"],
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": max_tokens,
                        "temperature": 0.2,
                    },
                )
                resp.raise_for_status()
                body = resp.json()
                content = body["choices"][0]["message"]["content"]

        parsed = _extract_json(content)
        latency = int((time.time() - start) * 1000)
        return {
            "model_id": mid,
            "model_name": model_info["name"],
            "status": "ok" if parsed else "parse_failed",
            "latency_ms": latency,
            "raw": content,
            "parsed": parsed,
        }
    except Exception as exc:
        err = str(exc).strip() or type(exc).__name__
        return {
            "model_id": mid,
            "model_name": model_info["name"],
            "status": "error",
            "error": err[:500],
            "latency_ms": int((time.time() - start) * 1000),
        }


def _model_count_from_evidence(evidence: str) -> int:
    m = re.search(r"models=([^;]+)", evidence or "")
    if not m:
        return 0
    return len([x for x in m.group(1).split(",") if x.strip()])


def _iter_parsed_products(parsed: dict) -> list[tuple[str, str, dict]]:
    """Yield (category_id, category_name_zh, product dict)."""
    out: list[tuple[str, str, dict]] = []
    if not parsed:
        return out
    blocks = parsed.get("categories") or []
    if not blocks and parsed.get("products"):
        cid = str(parsed.get("category_id") or "misc_building")
        cname = str(parsed.get("category_name_zh") or "其他建筑相关")
        blocks = [{"category_id": cid, "category_name_zh": cname, "products": parsed["products"]}]
    for block in blocks:
        cid = str(block.get("category_id") or "misc_building")
        cname = str(block.get("category_name_zh") or cid)
        for prod in block.get("products") or []:
            if prod.get("name"):
                out.append((cid, cname, prod))
    return out


def _consensus_by_category(model_results: list[dict]) -> list[dict]:
    """Merge products per category_id; ≥2 models → high consensus."""
    cat_names: dict[str, str] = {}
    buckets: dict[tuple[str, str], list[dict]] = {}
    models_seen: dict[tuple[str, str], set[str]] = {}

    for mr in model_results:
        if mr.get("status") != "ok" or not mr.get("parsed"):
            continue
        mid = mr["model_id"]
        for cid, cname, prod in _iter_parsed_products(mr["parsed"]):
            cat_names[cid] = cname
            name = str(prod.get("name") or "").strip()
            key = (cid, _norm_name(name))
            buckets.setdefault(key, []).append(prod)
            models_seen.setdefault(key, set()).add(mid)

    by_cat: dict[str, list[dict]] = {}
    for (cid, _nkey), variants in buckets.items():
        base = dict(variants[0])
        n_models = len(models_seen.get((cid, _nkey), set()))
        consensus = "high" if n_models >= 2 else "low"
        notes = str(base.get("notes") or "")
        if consensus == "low":
            notes = (notes + "；单模型提及，待复核").strip("；")
        base["notes"] = notes
        base["evidence"] = (
            f"ai_consensus={consensus}; models={','.join(sorted(models_seen.get((cid, _nkey), [])))}"
        )
        by_cat.setdefault(cid, []).append(base)

    categories: list[dict] = []
    for cid in sorted(by_cat.keys()):
        prods = by_cat[cid]
        prods.sort(key=lambda p: (-_model_count_from_evidence(p.get("evidence", "")), p.get("name", "")))
        categories.append(
            {
                "category_id": cid,
                "category_name_zh": cat_names.get(cid, cid),
                "products": prods,
            }
        )
    return categories


async def _run(
    *,
    prompt: str,
    survey_id: str,
    out_stem: str,
    region_county: str,
    towns: list[str],
    models_filter: list[str] | None,
    research_question: str,
) -> Path:
    from app.services.geo_engine_service import GEOEngine

    target = [m for m in GEOEngine.MODELS if not models_filter or m["id"] in models_filter]
    results = await asyncio.gather(*[_query_one_model(m, prompt) for m in target])

    today = date.today().isoformat()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = RAW_DIR / survey_id
    raw_path.mkdir(parents=True, exist_ok=True)
    for mr in results:
        (raw_path / f"{mr['model_id']}.json").write_text(
            json.dumps(mr, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    categories = _consensus_by_category(list(results))
    total_products = sum(len(c.get("products") or []) for c in categories)

    keywords: list[str] = []
    for mr in results:
        if mr.get("status") == "ok" and mr.get("parsed"):
            for kw in mr["parsed"].get("recommended_seo_keywords") or []:
                kw = str(kw).strip()
                if kw and kw not in keywords:
                    keywords.append(kw)

    used = [mr["model_id"] for mr in results if mr.get("status") == "ok"]
    skipped = [mr["model_id"] for mr in results if mr.get("status") == "skipped"]
    errors = [mr["model_id"] for mr in results if mr.get("status") == "error"]

    deliverable = {
        "survey_id": survey_id,
        "region_county": region_county,
        "towns_parks": towns,
        "survey_date": today,
        "surveyor": "PM派工·多AI大模型调研（GW-MR）",
        "survey_methods": ["b2b_catalog"],
        "research_question": research_question,
        "survey_method_note": (
            f"ai_models_used={used}; skipped={skipped}; errors={errors}; "
            f"consensus_rule=≥2 models; raw={raw_path.relative_to(ROOT).as_posix()}; "
            "须 PM approved + 实地 spot-check 后 merge"
        ),
        "evidence_refs": [str(raw_path.relative_to(ROOT).as_posix())],
        "categories": categories,
        "recommended_seo_keywords": keywords[:50],
        "pm_review": {"status": "pending", "reviewer": "", "reviewed_at": ""},
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUT_DIR / f"{out_stem}_{today.replace('-', '')}.json"
    out_file.write_text(json.dumps(deliverable, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {out_file} ({total_products} products in {len(categories)} categories, {len(used)} models ok)")
    if skipped:
        print(f"Skipped (no key): {', '.join(skipped)}")
    if errors:
        print(f"Errors: {', '.join(errors)}")
    return out_file


async def run_region(*, models_filter: list[str] | None) -> Path:
    """按 backlog 品类分批提问，避免单次超大 JSON 超时。"""
    from app.services.geo_engine_service import GEOEngine

    backlog = _load_backlog()
    towns = _towns_from_backlog(backlog)
    today = date.today().isoformat()
    today_compact = today.replace("-", "")
    question = "大城和河间一带有哪些建筑相关产品及附属配套品名"
    survey_id = f"ai-dacheng-hejian-{today_compact}"
    raw_path = RAW_DIR / survey_id
    raw_path.mkdir(parents=True, exist_ok=True)

    target = [m for m in GEOEngine.MODELS if not models_filter or m["id"] in models_filter]
    all_results: list[dict] = []
    ok_models: set[str] = set()
    skipped_models: set[str] = set()
    error_models: set[str] = set()

    cats = backlog.get("categories_to_survey") or []
    for idx, cat in enumerate(cats, 1):
        cid = cat.get("category_id") or "misc_building"
        name_zh = cat.get("name_zh") or cid
        prompt = _build_category_prompt(
            region_label=REGION_LABEL,
            category_id=cid,
            category_name_zh=name_zh,
            towns=towns,
        )
        print(f"[{idx}/{len(cats)}] {cid} ({name_zh}) …")
        batch = await asyncio.gather(*[_query_one_model(m, prompt) for m in target])
        for mr in batch:
            mid = mr.get("model_id", "")
            st = mr.get("status")
            if st == "ok":
                ok_models.add(mid)
            elif st == "skipped":
                skipped_models.add(mid)
            elif st in ("error", "parse_failed"):
                if st == "error":
                    error_models.add(mid)
            (raw_path / f"{cid}_{mid}.json").write_text(
                json.dumps(mr, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            all_results.append(mr)

    categories = _consensus_by_category(all_results)
    total_products = sum(len(c.get("products") or []) for c in categories)

    keywords: list[str] = []
    for mr in all_results:
        if mr.get("status") == "ok" and mr.get("parsed"):
            for kw in mr["parsed"].get("recommended_seo_keywords") or []:
                kw = str(kw).strip()
                if kw and kw not in keywords:
                    keywords.append(kw)

    used = sorted(ok_models)
    skipped = sorted(skipped_models - ok_models)
    errors = sorted(error_models - ok_models)

    deliverable = {
        "survey_id": survey_id,
        "region_county": REGION_LABEL,
        "towns_parks": towns,
        "survey_date": today,
        "surveyor": "PM派工·多AI大模型调研（GW-MR）",
        "survey_methods": ["b2b_catalog"],
        "research_question": question,
        "survey_method_note": (
            f"mode=region_by_category; ai_models_used={used}; skipped={skipped}; errors={errors}; "
            f"consensus_rule=≥2 models; raw={raw_path.relative_to(ROOT).as_posix()}; "
            "须 PM approved + 实地 spot-check 后 merge"
        ),
        "evidence_refs": [str(raw_path.relative_to(ROOT).as_posix())],
        "categories": categories,
        "recommended_seo_keywords": keywords[:50],
        "pm_review": {"status": "pending", "reviewer": "", "reviewed_at": ""},
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUT_DIR / f"ai_dacheng_hejian_{today_compact}.json"
    out_file.write_text(json.dumps(deliverable, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {out_file} ({total_products} products in {len(categories)} categories, models ok: {used})")
    if skipped:
        print(f"Skipped (no key): {', '.join(skipped)}")
    if errors:
        print(f"Errors: {', '.join(errors)}")
    return out_file


async def run_category(*, category_id: str, models_filter: list[str] | None) -> Path:
    backlog = _load_backlog()
    cat = _find_category(backlog, category_id)
    if not cat:
        raise SystemExit(f"品类 {category_id} 不在 backlog 中")
    towns = _towns_from_backlog(backlog)
    name_zh = cat.get("name_zh") or category_id
    today = date.today().isoformat().replace("-", "")
    return await _run(
        prompt=_build_category_prompt(
            region_label=REGION_LABEL,
            category_id=category_id,
            category_name_zh=name_zh,
            towns=towns,
        ),
        survey_id=f"ai-{category_id}-{today}",
        out_stem=f"ai_{category_id}",
        region_county=REGION_LABEL,
        towns=towns,
        models_filter=models_filter,
        research_question=f"{REGION_LABEL} · {name_zh} 品名加深",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="多 AI 调研大城+河间建筑相关产品名（PM 派工）"
    )
    parser.add_argument(
        "--region",
        default="dacheng_hejian",
        help="区域全量模式，默认 dacheng_hejian（大城+河间建筑品名+附属配套）",
    )
    parser.add_argument(
        "--category",
        default="",
        help="可选：单品类加深，如 finish_accessories",
    )
    parser.add_argument("--models", default="", help="逗号分隔 model id，默认全部")
    args = parser.parse_args()

    models = [m.strip() for m in args.models.split(",") if m.strip()] or None
    if args.category:
        asyncio.run(run_category(category_id=args.category, models_filter=models))
    else:
        asyncio.run(run_region(models_filter=models))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
