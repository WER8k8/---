PATH = r"C:/Users/Administrator.WIN-36O2UQRI3U1/Desktop/上线网站开发完成/上线网站.worktrees/agents-install-vscode-cline-deploy-strix/backend/app/services/hermes/expert_inspection_registry.py"

with open(PATH, "r", encoding="utf-8") as f:
    lines = f.readlines()

# function spans 1284..1506 (1-indexed). 0-indexed: 1283..1505
# dict entries lines (1-indexed) 1292..1501 -> 0-indexed 1291..1500
assert lines[1283].startswith("def _get_role_specific_inspector(")
assert lines[1289].rstrip().endswith('"""')  # docstring close
assert lines[1290].strip().startswith("role_specific_patterns = {")

entry_lo, entry_hi = 1291, 1501  # 0-indexed slice of the 210 entry lines
entries = lines[entry_lo:entry_hi]
# split into 4 contiguous groups preserving order
cut = [0, 53, 106, 159, len(entries)]  # 4 groups of ~53 each
groups = [entries[cut[i]:cut[i+1]] for i in range(4)]

def make_helper(name, body_lines):
    return (
        f"def {name}() -> dict[str, InspectionFunc]:\n"
        f"    return {{\n"
        + "".join(body_lines)
        + "    }\n"
    )

helpers = "\n\n".join(
    make_helper(f"_role_patterns_group{i+1}", groups[i]) for i in range(4)
)

new_func = (
    'def _get_role_specific_inspector(role_id: str) -> InspectionFunc | None:\n'
    '    """_get_role_specific_inspector。\n'
    '\n'
    '    参数说明：\n'
    '    :param role_id: 参数 role_id\n'
    '    :return: 返回处理结果。\n'
    '    """\n'
    '    patterns: dict[str, InspectionFunc] = {}\n'
    '    patterns.update(_role_patterns_group1())\n'
    '    patterns.update(_role_patterns_group2())\n'
    '    patterns.update(_role_patterns_group3())\n'
    '    patterns.update(_role_patterns_group4())\n'
    '    for pattern, func in patterns.items():\n'
    '        if re.search(pattern, role_id):\n'
    '            return func\n'
    '    return None\n'
)

new_lines = lines[:1283] + [new_func, "\n"] + lines[1506:] + ["\n", helpers, "\n"]

with open(PATH, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("done; groups sizes:", [len(g) for g in groups], "total lines:", len(new_lines))
