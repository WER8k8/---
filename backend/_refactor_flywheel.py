PATH = r"C:/Users/Administrator.WIN-36O2UQRI3U1/Desktop/上线网站开发完成/上线网站.worktrees/agents-install-vscode-cline-deploy-strix/backend/app/services/hermes/flywheel_workflow.py"

with open(PATH, "r", encoding="utf-8") as f:
    lines = f.readlines()

# function run_closed_loop_flywheel: def@35, end@190 (1-indexed)
# block1: 51..120 -> 0-indexed 50..119 ; block2: 122..162 -> 0-indexed 121..161
assert lines[34].startswith("def run_closed_loop_flywheel(")
assert lines[50].lstrip().startswith("# ①")
assert lines[121].lstrip().startswith("# ③")
assert lines[161].rstrip().endswith("}") or lines[161].rstrip().endswith(")")

block1 = lines[50:120]
block2 = lines[121:162]

helper1 = (
    'def _run_flywheel_research_and_buyers(\n'
    '    db: Session,\n'
    '    tenant_id: str,\n'
    '    message: str,\n'
    '    user_id: str | None,\n'
    '    auto_run_jobs: bool,\n'
    '    mem: Any,\n'
    '    steps: list[dict[str, Any]],\n'
    '    errors: list[str],\n'
    ') -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], str]:\n'
    '    """_run_flywheel_research_and_buyers。\n'
    '\n'
    '    参数说明：\n'
    '    :return: 返回 (research, insight_hook, buyers, diligence, research_job_id)。\n'
    '    """\n'
    + "".join(block1)
    + '    return research, insight_hook, buyers, diligence, research_job_id\n'
)

helper2 = (
    'def _run_flywheel_pipeline_and_letters(\n'
    '    db: Session,\n'
    '    tenant_id: str,\n'
    '    message: str,\n'
    '    auto_run_jobs: bool,\n'
    '    steps: list[dict[str, Any]],\n'
    '    errors: list[str],\n'
    '    research: dict[str, Any],\n'
    '    insight_hook: dict[str, Any],\n'
    '    research_job_id: str,\n'
    '    buyers: dict[str, Any],\n'
    ') -> tuple[dict[str, Any], dict[str, Any]]:\n'
    '    """_run_flywheel_pipeline_and_letters。\n'
    '\n'
    '    参数说明：\n'
    '    :return: 返回 (pipeline, letters)。\n'
    '    """\n'
    + "".join(block2)
    + '    return pipeline, letters\n'
)

call = (
    '    research, insight_hook, buyers, diligence, research_job_id = _run_flywheel_research_and_buyers(\n'
    '        db, tenant_id, message, user_id, auto_run_jobs, mem, steps, errors,\n'
    '    )\n'
    '    pipeline, letters = _run_flywheel_pipeline_and_letters(\n'
    '        db, tenant_id, message, auto_run_jobs, steps, errors,\n'
    '        research, insight_hook, research_job_id, buyers,\n'
    '    )\n'
)

new_lines = lines[:50] + [call] + lines[162:] + ["\n", helper1, "\n\n", helper2, "\n"]

with open(PATH, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("done total:", len(new_lines))
