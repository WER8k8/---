PATH = r"C:/Users/Administrator.WIN-36O2UQRI3U1/Desktop/上线网站开发完成/上线网站.worktrees/agents-install-vscode-cline-deploy-strix/backend/app/services/hermes/greedy_contest_memory_service.py"

with open(PATH, "r", encoding="utf-8") as f:
    lines = f.readlines()

# function _close_arena_and_open_next: def@301, end@430 (1-indexed)
# block1: 322..364 -> 0-indexed 321..363 ; block2: 366..420 -> 0-indexed 365..419
assert lines[300].startswith("def _close_arena_and_open_next(")
assert lines[321].lstrip().startswith("winner_bonus =")
assert lines[365].lstrip().startswith("for key, val in list(_fallback.items())")

block1 = lines[321:364]
block2 = lines[365:420]

helper1 = (
    'def _apply_arena_winners(\n'
    '    state: dict[str, Any],\n'
    '    winners: list[dict[str, Any]],\n'
    '    closed_id: str,\n'
    '    closed_at: str,\n'
    '    scoring: dict[str, Any],\n'
    '    prot: dict[str, Any],\n'
    '    cfg: dict[str, Any],\n'
    '    top_n: int,\n'
    '    arenas_per_year: int,\n'
    '    trigger: str,\n'
    ') -> tuple[list[dict[str, Any]], str, bool, int, int]:\n'
    '    """_apply_arena_winners。\n'
    '\n'
    '    参数说明：\n'
    '    :return: 返回 (winners, closed_id, year_rollover, next_year, next_index)。\n'
    '    """\n'
    + "".join(block1)
    + '    return winners, closed_id, year_rollover, next_year, next_index\n'
)

helper2 = (
    'def _finalize_arena_state(\n'
    '    state: dict[str, Any],\n'
    '    closed_id: str,\n'
    '    closed_at: str,\n'
    '    winners: list[dict[str, Any]],\n'
    '    year_rollover: bool,\n'
    '    next_year: int,\n'
    '    next_index: int,\n'
    '    ec: dict[str, Any],\n'
    '    trigger: str,\n'
    ') -> dict[str, Any]:\n'
    '    """_finalize_arena_state。\n'
    '\n'
    '    参数说明：\n'
    '    :return: 返回新的 arena state。\n'
    '    """\n'
    + "".join(block2)
    + '    return new_state\n'
)

call = (
    '    winners, closed_id, year_rollover, next_year, next_index = _apply_arena_winners(\n'
    '        state, winners, closed_id, closed_at, scoring, prot, cfg, top_n, arenas_per_year, trigger,\n'
    '    )\n'
    '    new_state = _finalize_arena_state(\n'
    '        state, closed_id, closed_at, winners, year_rollover, next_year, next_index, ec, trigger,\n'
    '    )\n'
)

new_lines = lines[:321] + [call] + lines[420:] + ["\n", helper1, "\n\n", helper2, "\n"]

with open(PATH, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("done total:", len(new_lines))
