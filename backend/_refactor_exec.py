PATH = r"C:/Users/Administrator.WIN-36O2UQRI3U1/Desktop/上线网站开发完成/上线网站.worktrees/agents-install-vscode-cline-deploy-strix/backend/app/services/hermes/expert_execution_registry.py"

with open(PATH, "r", encoding="utf-8") as f:
    lines = f.readlines()

# 0-indexed
assert lines[1057].startswith("def _get_role_specific_executor(")
assert lines[1063].rstrip().endswith('"""')
assert lines[1064].strip().startswith("role_specific_patterns = {")

entry_lo, entry_hi = 1065, 1275  # 0-indexed slice of entry lines (1-indexed 1066..1275)
entries = lines[entry_lo:entry_hi]
cut = [0, 53, 106, 159, len(entries)]
groups = [entries[cut[i]:cut[i+1]] for i in range(4)]

def make_helper(name, body_lines):
    return (
        f"def {name}() -> dict[str, ExecutionFunc]:\n"
        f"    return {{\n"
        + "".join(body_lines)
        + "    }\n"
    )

helpers = "\n\n".join(
    make_helper(f"_role_exec_patterns_group{i+1}", groups[i]) for i in range(4)
)

new_func = (
    'def _get_role_specific_executor(role_id: str) -> ExecutionFunc | None:\n'
    '    """_get_role_specific_executor。\n'
    '\n'
    '    参数说明：\n'
    '    :param role_id: 参数 role_id\n'
    '    :return: 返回处理结果。\n'
    '    """\n'
    '    patterns: dict[str, ExecutionFunc] = {}\n'
    '    patterns.update(_role_exec_patterns_group1())\n'
    '    patterns.update(_role_exec_patterns_group2())\n'
    '    patterns.update(_role_exec_patterns_group3())\n'
    '    patterns.update(_role_exec_patterns_group4())\n'
    '    for pattern, func in patterns.items():\n'
    '        if re.search(pattern, role_id):\n'
    '            return func\n'
    '    return None\n'
)

new_lines = lines[:1057] + [new_func, "\n"] + lines[1279:] + ["\n", helpers, "\n"]

with open(PATH, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("done; groups:", [len(g) for g in groups], "total:", len(new_lines))
