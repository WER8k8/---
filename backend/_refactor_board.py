PATH = r"C:/Users/Administrator.WIN-36O2UQRI3U1/Desktop/上线网站开发完成/上线网站.worktrees/agents-install-vscode-cline-deploy-strix/backend/app/services/hermes/greedy_project_board_service.py"

with open(PATH, "r", encoding="utf-8") as f:
    lines = f.readlines()

# ---- evolution helper: block 180..257 (1-indexed) -> 0-indexed 179..256 ----
evo_block = lines[179:257]
call_evo = (
    '    directions, low_completion, mojin_lessons = _accumulate_evolution_directions(\n'
    '        projects, employees, lessons_digest, summary, highlights,\n'
    '    )\n'
)
helper_evo = (
    'def _accumulate_evolution_directions(\n'
    '    projects: list[dict[str, Any]],\n'
    '    employees: list[dict[str, Any]],\n'
    '    lessons_digest: dict[str, Any],\n'
    '    summary: dict[str, Any],\n'
    '    highlights: list[str],\n'
    ') -> tuple[list[dict[str, Any]], list[Any], list[Any]]:\n'
    '    """_accumulate_evolution_directions。\n'
    '\n'
    '    参数说明：\n'
    '    :return: 返回 (directions, low_completion, mojin_lessons)。\n'
    '    """\n'
    + "".join(evo_block)
    + '    return directions, low_completion, mojin_lessons\n'
)

# ---- earnings_board helpers ----
A = lines[303:332]   # sku_stats aggregation (304..332)
B = lines[333:346]   # review_stats (334..346)
C = lines[347:388]   # projects build + sort (348..388)
D = lines[389:416]   # top_employees build + sort + [:10] (390..416)

call_A = '    sku_stats = _aggregate_sku_stats(rounds, rows_by_id)\n'
call_B = '    review_stats = _aggregate_review_stats(history)\n'
call_C = '    projects = _build_project_rows(sku_stats, catalog, review_stats)\n'
call_D = '    top_employees = _build_top_employees(lb, rounds)\n'

helper_A = (
    'def _aggregate_sku_stats(\n'
    '    rounds: list[dict[str, Any]],\n'
    '    rows_by_id: dict[str, dict[str, Any]],\n'
    ') -> dict[str, dict[str, Any]]:\n'
    '    """_aggregate_sku_stats。\n'
    '\n'
    '    参数说明：\n'
    '    :return: 返回 sku_stats 聚合结果。\n'
    '    """\n'
    + "".join(A)
    + '    return sku_stats\n'
)
helper_B = (
    'def _aggregate_review_stats(\n'
    '    history: list[dict[str, Any]],\n'
    ') -> dict[str, dict[str, int]]:\n'
    '    """_aggregate_review_stats。\n'
    '\n'
    '    参数说明：\n'
    '    :return: 返回 review_stats 聚合结果。\n'
    '    """\n'
    + "".join(B)
    + '    return review_stats\n'
)
helper_C = (
    'def _build_project_rows(\n'
    '    sku_stats: dict[str, dict[str, Any]],\n'
    '    catalog: dict[str, Any],\n'
    '    review_stats: dict[str, dict[str, int]],\n'
    ') -> list[dict[str, Any]]:\n'
    '    """_build_project_rows。\n'
    '\n'
    '    参数说明：\n'
    '    :return: 返回 projects 列表。\n'
    '    """\n'
    + "".join(C)
    + '    return projects\n'
)
helper_D = (
    'def _build_top_employees(\n'
    '    lb: dict[str, Any],\n'
    '    rounds: list[dict[str, Any]],\n'
    ') -> list[dict[str, Any]]:\n'
    '    """_build_top_employees。\n'
    '\n'
    '    参数说明：\n'
    '    :return: 返回 top_employees 列表（已排序并截断）。\n'
    '    """\n'
    + "".join(D)
    + '    return top_employees\n'
)

# Apply replacements descending by start index (0-indexed inclusive)
replacements = [
    (389, 415, call_D),
    (347, 387, call_C),
    (333, 345, call_B),
    (303, 331, call_A),
    (179, 256, call_evo),
]
new_lines = list(lines)
for start, end, text in replacements:
    new_lines[start:end+1] = [text]

helpers_all = "\n\n".join([helper_A, helper_B, helper_C, helper_D, helper_evo])
new_lines = new_lines + ["\n", helpers_all, "\n"]

with open(PATH, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("done total:", len(new_lines))
