PATH = r"C:/Users/Administrator.WIN-36O2UQRI3U1/Desktop/上线网站开发完成/上线网站.worktrees/agents-install-vscode-cline-deploy-strix/backend/app/services/hermes/video_matrix_workflow.py"

with open(PATH, "r", encoding="utf-8") as f:
    lines = f.readlines()

# guard block: 1-indexed 58..122 -> 0-indexed 57..121

# helper body: keep comment + steps.append, skip the preflight= assignment line, keep rest
body = lines[57:59] + lines[60:122]

helper = (
    'def _video_matrix_run_guards(\n'
    '    ctx: dict[str, Any],\n'
    '    steps: list[dict[str, Any]],\n'
    '    media_task_id: str,\n'
    '    preflight: dict[str, Any],\n'
    ') -> dict[str, Any] | None:\n'
    '    """_video_matrix_run_guards。\n'
    '\n'
    '    参数说明：\n'
    '    :return: 返回处理结果（或 None 表示放行）。\n'
    '    """\n'
    + "".join(body)
    + '    return None\n'
)

call = (
    '    preflight = preflight_workers()\n'
    '    ret = _video_matrix_run_guards(ctx, steps, media_task_id, preflight)\n'
    '    if ret is not None:\n'
    '        return ret\n'
)

new_lines = lines[:57] + [call] + lines[122:] + ["\n", helper, "\n"]

with open(PATH, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("done total:", len(new_lines))
