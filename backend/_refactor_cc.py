PATH = r"C:/Users/Administrator.WIN-36O2UQRI3U1/Desktop/上线网站开发完成/上线网站.worktrees/agents-install-vscode-cline-deploy-strix/backend/app/services/hermes/command_center.py"

with open(PATH, "r", encoding="utf-8") as f:
    lines = f.readlines()

# function _build_command_center_snapshot_uncached: def@305, end@456 (1-indexed)
# block1 (sections run incl inner _safe/_db_task): 312..395 -> 0-indexed 311..394
# block2 (payload assembly): 398..454 -> 0-indexed 397..453
assert lines[304].startswith("def _build_command_center_snapshot_uncached(")
assert lines[311].lstrip().startswith("def _safe(")
assert lines[397].lstrip().startswith("payload = {")

block1 = lines[311:395]
block2 = lines[397:454]

helper_sections = (
    'def _run_command_center_sections(db: Session) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str, int]:\n'
    '    """_run_command_center_sections。\n'
    '\n'
    '    参数说明：\n'
    '    :return: 返回 (sections, ops, ecc_hangar, overall, built_ms)。\n'
    '    """\n'
    '    from app.services.ubrain.deerflow_scheduled_service import load_deerflow_schedule_snapshot\n'
    '    from app.services.ubrain.deerflow_scheduler import deerflow_scheduler\n'
    + "".join(block1)
    + '    return sections, ops, ecc_hangar, overall, built_ms\n'
)

helper_payload = (
    'def _assemble_command_center_payload(\n'
    '    sections: dict[str, Any],\n'
    '    ops: dict[str, Any],\n'
    '    ecc_hangar: dict[str, Any],\n'
    '    overall: str,\n'
    '    built_ms: int,\n'
    ') -> dict[str, Any]:\n'
    '    """_assemble_command_center_payload。\n'
    '\n'
    '    参数说明：\n'
    '    :return: 返回处理结果。\n'
    '    """\n'
    + "".join(block2)
    + '    return payload\n'
)

call1 = (
    '    sections, ops, ecc_hangar, overall, built_ms = _run_command_center_sections(db)\n'
)
call2 = (
    '    payload = _assemble_command_center_payload(sections, ops, ecc_hangar, overall, built_ms)\n'
)

new_lines = lines[:307] + [call1, call2] + lines[454:] + ["\n", helper_sections, "\n\n", helper_payload, "\n"]

with open(PATH, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("done total:", len(new_lines))
