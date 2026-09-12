import sys

def indent_of(s):
    return len(s) - len(s.lstrip(" "))

def main():
    path = sys.argv[1]
    func_name = sys.argv[2]
    helper_name = sys.argv[3]
    bstart = int(sys.argv[4])
    bend = int(sys.argv[5])
    inputs = [x.strip() for x in sys.argv[6].split(",") if x.strip()]
    outputs = [x.strip() for x in sys.argv[7].split(",") if x.strip()]
    is_async = (len(sys.argv) > 8 and sys.argv[8] == "1")
    do_return = (len(sys.argv) > 9 and sys.argv[9] == "1")

    with open(path, encoding="utf-8") as f:
        src = f.read()
    lines = src.split("\n")

    def_idx = None
    for i, ln in enumerate(lines):
        if ("def " + func_name + "(") in ln or ("async def " + func_name + "(") in ln:
            def_idx = i
            break
    if def_idx is None:
        print("FUNC_NOT_FOUND", func_name); sys.exit(2)

    orig_async = lines[def_idx].lstrip().startswith("async def")

    block = lines[bstart-1:bend]
    while block and block[-1].strip() == "":
        block = block[:-1]

    params = ", ".join(inputs)
    out_expr = ", ".join(outputs)
    helper_lines = []
    helper_lines.append("def %s(%s):" % (helper_name, params))
    for bl in block:
        helper_lines.append(bl)
    if outputs:
        helper_lines.append("    return %s" % out_expr)

    call_indent = " " * indent_of(lines[bstart-1])
    core = "%s(%s)" % (helper_name, params)
    if do_return:
        call = "%sreturn %s%s" % (call_indent, "await " if orig_async else "", core)
    elif outputs:
        call = "%s%s = %s%s" % (call_indent, out_expr, "await " if orig_async else "", core)
    else:
        call = "%s%s%s" % (call_indent, "await " if orig_async else "", core)

    new_lines = lines[:bstart-1] + [call] + lines[bend:]
    helper_block = [""] + helper_lines
    final_lines = new_lines[:def_idx] + helper_block + new_lines[def_idx:]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(final_lines))

    print("OK", helper_name, "block", bstart, "-", bend, "inputs", inputs, "outputs", outputs,
          "helper_lines", len(helper_lines))

main()
