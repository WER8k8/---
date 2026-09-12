import re
import os
import ast

INIT_FILE = "app/api/v1/routes/__init__.py"
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    init_path = os.path.join(BACKEND_DIR, INIT_FILE)
    with open(init_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. 提取 Import 映射: router_name -> module_path
    # 例如: from app.api.v1.routes.health import router as health_router
    import_pattern = re.compile(r"from\s+([a-zA-Z0-9_\.]+)\s+import\s+(?:router|api_router)\s+as\s+([a-zA-Z0-9_]+)")
    router_to_module = {}
    for match in import_pattern.finditer(content):
        module_path_str = match.group(1)
        router_alias = match.group(2)
        # 转换为文件路径
        # 例如 app.api.v1.routes.health -> app/api/v1/routes/health.py
        file_path = module_path_str.replace(".", "/") + ".py"
        router_to_module[router_alias] = file_path

    # 2. 提取 router.include_router 调用
    # 解析 ast
    tree = ast.parse(content)
    
    modifications = {}
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
            if isinstance(call.func, ast.Attribute) and call.func.attr == "include_router":
                if not call.args:
                    continue
                router_arg = call.args[0]
                if not isinstance(router_arg, ast.Name):
                    continue
                router_name = router_arg.id
                
                if router_name not in router_to_module:
                    continue
                    
                file_path = router_to_module[router_name]
                
                prefix = '""' # default
                tags = None
                
                for kw in call.keywords:
                    if kw.arg == "prefix":
                        if isinstance(kw.value, ast.Constant):
                            prefix = f'"{kw.value.value}"'
                    elif kw.arg == "tags":
                        if isinstance(kw.value, ast.List):
                            tags_list = []
                            for elt in kw.value.elts:
                                if isinstance(elt, ast.Constant):
                                    tags_list.append(f'"{elt.value}"')
                            if tags_list:
                                tags = "[" + ", ".join(tags_list) + "]"
                
                modifications[file_path] = {
                    "prefix": prefix,
                    "tags": tags
                }

    print(f"Found {len(modifications)} routes to migrate.")
    
    # 3. 注入到目标文件
    for file_path, mods in modifications.items():
        full_path = os.path.join(BACKEND_DIR, file_path)
        if not os.path.exists(full_path):
            print(f"Warning: File not found {full_path}")
            continue
            
        with open(full_path, "r", encoding="utf-8") as f:
            file_content = f.read()
            
        # 检查是否已经注入
        if "ROUTE_PREFIX" in file_content:
            continue
            
        # 找到 router = APIRouter(...) 的位置
        lines = file_content.split("\n")
        insert_idx = -1
        for i, line in enumerate(lines):
            if line.startswith("router = APIRouter") or line.startswith("router = fastapi.APIRouter"):
                insert_idx = i
                break
                
        if insert_idx == -1:
            # 如果没找到 router 定义，就把代码加在最前面（但在 docstring 和 import 后面）
            for i, line in enumerate(lines):
                if line.startswith("from ") or line.startswith("import "):
                    insert_idx = i
                    break
            if insert_idx == -1:
                insert_idx = 0
                
        injection = []
        injection.append(f"\n# FIX-30 自动注入：保留原有的自定义前缀与标签")
        injection.append(f"ROUTE_PREFIX = {mods['prefix']}")
        if mods['tags']:
            injection.append(f"ROUTE_TAGS = {mods['tags']}")
        injection.append("")
        
        # 插入内容
        lines = lines[:insert_idx] + injection + lines[insert_idx:]
        
        with open(full_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
            
        print(f"Injected constants into {file_path}")

    # 4. 生成一个被清理过的 __init__.py 以备后用 (放在同级目录下，让开发者确认后替换)
    lines = content.split("\n")
    cleaned_lines = []
    skip = False
    for line in lines:
        if "from app.api.v1." in line and "import router as" in line:
            continue # 跳过 import
        if "router.include_router(" in line:
            continue # 跳过 include
        cleaned_lines.append(line)
        
    cleaned_path = init_path + ".new"
    with open(cleaned_path, "w", encoding="utf-8") as f:
        f.write("\n".join(cleaned_lines))
        
    print(f"\nMigration complete. A cleaned __init__.py has been generated at {cleaned_path}.")
    print("Please review the changes and rename it to __init__.py to apply.")

if __name__ == "__main__":
    main()
