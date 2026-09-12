PATH = r"C:/Users/Administrator.WIN-36O2UQRI3U1/Desktop/上线网站开发完成/上线网站.worktrees/agents-install-vscode-cline-deploy-strix/backend/app/services/hermes/video_matrix_workflow.py"

with open(PATH, "r", encoding="utf-8") as f:
    lines = f.readlines()

# function run_video_matrix_v1: def@30, end@211 (1-indexed)
# extract block 124..180 (1-indexed) -> 0-indexed 123..179
assert lines[29].startswith("def run_video_matrix_v1(")

block = lines[123:180]  # 0-indexed 123..179 inclusive

call = (
    '    distribute_result, verified, unverified = _run_video_distribution(\n'
    '        db,\n'
    '        tenant_id=tenant_id,\n'
    '        media_task_id=media_task_id,\n'
    '        platform_ids=platform_ids,\n'
    '        include_tenant_site=include_tenant_site,\n'
    '        scheduled_dt=scheduled_dt,\n'
    '        steps=steps,\n'
    '        errors=errors,\n'
    '    )\n'
)

helper = (
    'def _run_video_distribution(\n'
    '    db: Session,\n'
    '    *,\n'
    '    tenant_id: str,\n'
    '    media_task_id: str,\n'
    '    platform_ids: list[Any],\n'
    '    include_tenant_site: bool,\n'
    '    scheduled_dt: Any,\n'
    '    steps: list[dict[str, Any]],\n'
    '    errors: list[str],\n'
    ') -> tuple[dict[str, Any], list[Any], list[Any]]:\n'
    '    """_run_video_distribution。\n'
    '\n'
    '    参数说明：\n'
    '    :return: 返回 (distribute_result, verified, unverified)。\n'
    '    """\n'
    + "".join(block)
    + '    return distribute_result, verified, unverified\n'
)

new_lines = lines[:123] + [call] + lines[180:] + ["\n", helper, "\n"]

with open(PATH, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("done total:", len(new_lines))
