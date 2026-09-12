"""客户产品图 ↔ site_content 挂接（客户只提供产品名与白底图，不生成装饰图）。"""

from __future__ import annotations

from typing import Any


def _normalize_image_urls(images: list[Any] | None) -> list[str]:
    """_normalize_image_urls。

    参数说明：
    :param images: 参数 images
    :return: 返回处理结果。
    """
    urls: list[str] = []
    if not isinstance(images, list):
        return urls
    for item in images:
        if isinstance(item, str) and item.strip():
            urls.append(item.strip())
        elif isinstance(item, dict):
            url = str(item.get("url") or item.get("image") or "").strip()
            if url:
                urls.append(url)
    return urls


def apply_customer_product_images(
    site_content: dict[str, Any],
    product_images: list[Any] | None,
) -> dict[str, Any]:
    """
    将客户上传的产品图挂到 productItems 与首屏 hero。
    - 不要求客户制作 Banner；第一张图可作首屏展示
    - 无图时保留 LLM 生成的纯文案站
    """
    urls = _normalize_image_urls(product_images)
    if not urls:
        return site_content

    out = dict(site_content)
    pages = dict(out.get("pages") or {})
    products = dict(pages.get("products") or {})
    home = dict(pages.get("home") or {})
    items = products.get("productItems")
    if not isinstance(items, list):
        items = []

    if not items:
        items = [
            {
                "name": f"Product {i + 1}",
                "summary": "",
                "image": url,
                "slug": f"product-{i + 1}",
                "specs": [
                    {"label": "Material", "value": "Export grade"},
                    {"label": "Density", "value": "Custom available"},
                    {"label": "Application", "value": "Industrial export"},
                ],
            }
            for i, url in enumerate(urls)
        ]
    else:
        merged: list[dict[str, Any]] = []
        for i, raw in enumerate(items):
            row = dict(raw) if isinstance(raw, dict) else {"name": str(raw), "summary": ""}
            if i < len(urls):
                row["image"] = urls[i]
            row.setdefault("slug", f"product-{i + 1}")
            row.setdefault(
                "specs",
                [
                    {"label": "Material", "value": "Export grade"},
                    {"label": "Density", "value": "Custom available"},
                    {"label": "Application", "value": "Industrial export"},
                ],
            )
            merged.append(row)
        if len(urls) > len(merged):
            for j in range(len(merged), len(urls)):
                merged.append(
                    {
                        "name": f"Product {j + 1}",
                        "summary": "",
                        "image": urls[j],
                        "slug": f"product-{j + 1}",
                        "specs": [
                            {"label": "Material", "value": "Export grade"},
                            {"label": "Density", "value": "Custom available"},
                            {"label": "Application", "value": "Industrial export"},
                        ],
                    },
                )
        items = merged

    products["productItems"] = items
    products["products"] = [
        str(it.get("name", "")).strip()
        for it in items
        if isinstance(it, dict) and it.get("name")
    ]
    if not str(home.get("heroImage") or "").strip():
        home["heroImage"] = urls[0]

    pages["products"] = products
    pages["home"] = home
    out["pages"] = pages
    out["assets"] = {
        **(out.get("assets") if isinstance(out.get("assets"), dict) else {}),
        "productImages": [{"url": u} for u in urls],
    }
    return out
