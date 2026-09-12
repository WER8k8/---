PATH = r"C:/Users/Administrator.WIN-36O2UQRI3U1/Desktop/上线网站开发完成/上线网站.worktrees/agents-install-vscode-cline-deploy-strix/backend/app/services/hermes/greedy_production_readiness_service.py"

with open(PATH, "r", encoding="utf-8") as f:
    lines = f.readlines()

# function greedy_production_readiness: def@172, end@304 (1-indexed)
# block A: 177..254 -> 0-indexed 176..253 ; block B: 255..290 -> 0-indexed 254..289
assert lines[171].startswith("def greedy_production_readiness(")
assert lines[176].lstrip().startswith("greedy_on =")
assert lines[254-1].rstrip().endswith(")")  # line 254 closing

blockA = lines[176:254]
blockB = lines[254:290]

helperA = (
    'def _build_readiness_checks_part_a(db: Session) -> tuple[list[dict[str, Any]], Any, str, str, bool]:\n'
    '    """_build_readiness_checks_part_a。\n'
    '\n'
    '    参数说明：\n'
    '    :return: 返回 (checks, tenant_row, publish_tid, bootstrap_tid, greedy_on)。\n'
    '    """\n'
    + "".join(blockA)
    + '    return checks, tenant_row, publish_tid, bootstrap_tid, greedy_on\n'
)

helperB = (
    'def _build_readiness_checks_part_b(checks: list[dict[str, Any]]) -> list[dict[str, Any]]:\n'
    '    """_build_readiness_checks_part_b。\n'
    '\n'
    '    参数说明：\n'
    '    :return: 返回更新后的 checks。\n'
    '    """\n'
    + "".join(blockB)
    + '    return checks\n'
)

call = (
    '    checks, tenant_row, publish_tid, bootstrap_tid, greedy_on = _build_readiness_checks_part_a(db)\n'
    '    checks = _build_readiness_checks_part_b(checks)\n'
)

new_lines = lines[:176] + [call] + lines[290:] + ["\n", helperA, "\n\n", helperB, "\n"]

with open(PATH, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("done total:", len(new_lines))
