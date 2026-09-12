"""菜单树 → UacMenuRoute 转换（无 HTTP）"""

from __future__ import annotations

from typing import List

from app.api.v1.admin_bff.schemas import UacMenuRoute, UacRouteMeta


def dict_to_route(node: dict) -> UacMenuRoute:
    """dict_to_route。

    参数说明：
    :param node: 参数 node
    :return: 返回处理结果。
    """
    meta_raw = node.get("meta") or {}
    if "title" in node and "meta" not in node:
        meta_raw = {"title": node["title"], **meta_raw}
    meta = UacRouteMeta(
        title=meta_raw.get("title") or node.get("title") or "",
        icon=meta_raw.get("icon") or node.get("icon"),
        order=meta_raw.get("order", node.get("sort_order", 0)),
        keepAlive=bool(meta_raw.get("keepAlive", False)),
        hideInMenu=bool(meta_raw.get("hideInMenu", meta_raw.get("isHide", False))),
        shell=meta_raw.get("shell"),
        roles=meta_raw.get("roles") or [],
    )
    children = [dict_to_route(c) for c in node.get("children") or []]
    path = node.get("path") or ""
    name = node.get("name") or path.replace("/", "_") or "Route"
    return UacMenuRoute(
        name=name,
        path=path,
        component=node.get("component") or node.get("component_path"),
        redirect=node.get("redirect"),
        meta=meta,
        children=children,
    )


def db_tree_to_routes(tree: List[dict], shell: str) -> List[UacMenuRoute]:
    """db_tree_to_routes。

    参数说明：
    :param tree: 参数 tree
    :param shell: 参数 shell
    :return: 返回处理结果。
    """
    routes: List[UacMenuRoute] = []
    for node in tree:
        enriched = {
            **node,
            "meta": {**(node.get("meta") or {}), "shell": shell, "title": node.get("title", "")},
        }
        routes.append(dict_to_route(enriched))
    return routes


def seed_nodes_to_routes(seeds: List[dict]) -> List[UacMenuRoute]:
    """seed_nodes_to_routes。

    参数说明：
    :param seeds: 参数 seeds
    :return: 返回处理结果。
    """
    return [dict_to_route(n) for n in seeds]
