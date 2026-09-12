"""OpenAPI → TypeScript 自动生成 — FIX-45

从 FastAPI OpenAPI schema 自动生成 TypeScript 类型定义和 API 客户端。
用法：
  python scripts/generate_api_types.py
  python scripts/generate_api_types.py --watch  # 监听模式
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

# 配置
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_URL = os.getenv("API_URL", "http://127.0.0.1:8001")
OPENAPI_URL = f"{BACKEND_URL}/openapi.json"
OUTPUT_DIR = PROJECT_ROOT / "frontend" / "admin" / "src" / "api" / "generated"
TYPES_FILE = OUTPUT_DIR / "api-types.ts"
CLIENT_FILE = OUTPUT_DIR / "api-client.ts"


def fetch_openapi_schema() -> dict | None:
    """获取 OpenAPI schema。"""
    try:
        import requests
        resp = requests.get(OPENAPI_URL, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[ERROR] 无法获取 OpenAPI schema: {e}")
        print(f"  请确保后端服务运行在 {BACKEND_URL}")
        return None


def generate_types(schema: dict) -> str:
    """从 OpenAPI schema 生成 TypeScript 类型定义。"""
    lines = [
        "// 自动生成 — 请勿手动编辑",
        f"// 来源: {OPENAPI_URL}",
        "// 生成命令: python scripts/generate_api_types.py",
        "",
        "/* eslint-disable @typescript-eslint/no-explicit-any */",
        "",
    ]

    # 提取 schemas
    schemas = schema.get("components", {}).get("schemas", {})
    if schemas:
        lines.append("// ============================================================")
        lines.append("// 数据模型")
        lines.append("// ============================================================")
        lines.append("")

        for name, definition in schemas.items():
            ts_name = _to_pascal_case(name)
            ts_type = _schema_to_ts(definition)
            lines.append(f"export interface {ts_name} {{")
            if ts_type:
                for prop_line in ts_type.split("\n"):
                    lines.append(f"  {prop_line}")
            lines.append("}")
            lines.append("")

    # 提取 API 端点
    paths = schema.get("paths", {})
    if paths:
        lines.append("// ============================================================")
        lines.append("// API 端点类型")
        lines.append("// ============================================================")
        lines.append("")

        for path, methods in paths.items():
            for method, details in methods.items():
                if method not in ("get", "post", "put", "delete", "patch"):
                    continue

                operation_id = details.get("operationId", "")
                if not operation_id:
                    continue

                ts_func_name = _to_camel_case(operation_id)
                tags = details.get("tags", [])
                summary = details.get("summary", "")

                # 请求体类型
                request_body = details.get("requestBody", {})
                req_type = "void"
                if request_body:
                    content = request_body.get("content", {})
                    json_content = content.get("application/json", {})
                    schema_ref = json_content.get("schema", {})
                    if "$ref" in schema_ref:
                        req_type = _to_pascal_case(schema_ref["$ref"].split("/")[-1])
                    elif schema_ref.get("type") == "array":
                        items_ref = schema_ref.get("items", {}).get("$ref", "")
                        if items_ref:
                            req_type = f"{_to_pascal_case(items_ref.split('/')[-1])}[]"
                        else:
                            req_type = "any[]"

                # 响应类型
                responses = details.get("responses", {})
                resp_type = "any"
                for status_code, resp in responses.items():
                    if status_code.startswith("2"):
                        resp_content = resp.get("content", {})
                        json_resp = resp_content.get("application/json", {})
                        resp_schema = json_resp.get("schema", {})
                        if "$ref" in resp_schema:
                            resp_type = _to_pascal_case(resp_schema["$ref"].split("/")[-1])

                lines.append(f"/** {summary or operation_id} [{', '.join(tags)}] */")
                lines.append(
                    f"export type {ts_func_name}Request = {req_type};"
                )
                lines.append(
                    f"export type {ts_func_name}Response = {resp_type};"
                )
                lines.append("")

    return "\n".join(lines)


def generate_client(schema: dict) -> str:
    """从 OpenAPI schema 生成 TypeScript API 客户端。"""
    lines = [
        "// 自动生成 — 请勿手动编辑",
        f"// 来源: {OPENAPI_URL}",
        "// 生成命令: python scripts/generate_api_types.py",
        "",
        "import axios from 'axios';",
        "import type { AxiosRequestConfig } from 'axios';",
        "",
        f"const BASE_URL = '{BACKEND_URL}/api/v1';",
        "",
        "const api = axios.create({",
        "  baseURL: BASE_URL,",
        "  withCredentials: true,",
        "  timeout: 15000,",
        "});",
        "",
        "// ============================================================",
        "// 自动生成的 API 方法",
        "// ============================================================",
        "",
    ]

    paths = schema.get("paths", {})
    for path, methods in paths.items():
        for method, details in methods.items():
            if method not in ("get", "post", "put", "delete", "patch"):
                continue

            operation_id = details.get("operationId", "")
            if not operation_id:
                continue

            ts_func_name = _to_camel_case(operation_id)
            summary = details.get("summary", "")

            # 路径参数
            path_params = details.get("parameters", [])
            query_params = [p for p in path_params if p.get("in") == "query"]
            has_params = len(query_params) > 0

            # 请求体
            has_body = "requestBody" in details

            # 生成函数签名
            param_list = []
            if has_params:
                param_list.append("params?: Record<string, any>")
            if has_body:
                param_list.append("data?: any")

            params_str = ", ".join(param_list) if param_list else ""

            # 注释
            lines.append(f"/** {summary or operation_id} */")
            lines.append(f"export async function {ts_func_name}({params_str}) {{")

            # 方法体
            http_method = f"api.{method}"
            if has_params and has_body:
                lines.append(f"  return {http_method}('{path}', data, {{ params }});")
            elif has_params:
                lines.append(f"  return {http_method}('{path}', {{ params }});")
            elif has_body:
                lines.append(f"  return {http_method}('{path}', data);")
            else:
                lines.append(f"  return {http_method}('{path}');")

            lines.append("}")
            lines.append("")

    lines.append("export default api;")
    return "\n".join(lines)


def _schema_to_ts(schema: dict, indent: int = 0) -> str:
    """将 JSON Schema 转为 TypeScript 类型。"""
    if not schema:
        return ""

    if "$ref" in schema:
        return _to_pascal_case(schema["$ref"].split("/")[-1])

    schema_type = schema.get("type", "object")

    if schema_type == "object":
        props = schema.get("properties", {})
        required = schema.get("required", [])
        lines = []
        for prop_name, prop_schema in props.items():
            optional = "?" if prop_name not in required else ""
            prop_type = _schema_to_ts(prop_schema, indent + 1)
            lines.append(f"{prop_name}{optional}: {prop_type};")
        return "\n".join(lines)

    if schema_type == "array":
        items = schema.get("items", {})
        item_type = _schema_to_ts(items, indent)
        return f"{item_type}[]"

    if schema_type == "string":
        enum = schema.get("enum")
        if enum:
            return " | ".join(f"'{v}'" for v in enum)
        return "string"

    if schema_type in ("integer", "number"):
        return "number"

    if schema_type == "boolean":
        return "boolean"

    return "any"


def _to_pascal_case(name: str) -> str:
    """转为 PascalCase。"""
    return "".join(
        word.capitalize() for word in re.split(r"[-_\s]", name) if word
    )


def _to_camel_case(name: str) -> str:
    """转为 camelCase。"""
    parts = re.split(r"[-_\s]", name)
    return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])


def main():
    """主函数。"""
    print("=" * 60)
    print("OpenAPI → TypeScript 自动生成")
    print("=" * 60)

    schema = fetch_openapi_schema()
    if not schema:
        print("✗ 生成失败")
        sys.exit(1)

    # 确保输出目录存在
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 生成类型
    types_content = generate_types(schema)
    TYPES_FILE.write_text(types_content, encoding="utf-8")
    print(f"✓ 类型定义: {TYPES_FILE} ({len(types_content)} bytes)")

    # 生成客户端
    client_content = generate_client(schema)
    CLIENT_FILE.write_text(client_content, encoding="utf-8")
    print(f"✓ API 客户端: {CLIENT_FILE} ({len(client_content)} bytes)")

    # 统计
    paths_count = len(schema.get("paths", {}))
    schemas_count = len(schema.get("components", {}).get("schemas", {}))
    print(f"  端点: {paths_count} | 模型: {schemas_count}")
    print("✓ 生成完成")


if __name__ == "__main__":
    main()