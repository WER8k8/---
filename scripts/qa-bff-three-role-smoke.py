#!/usr/bin/env python3

"""QA-01 · 三壳 BFF 登录 + menu/permissions 冒烟（platform / client / agent）"""



from __future__ import annotations



import os

import sys



BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))

if BACKEND not in sys.path:

    sys.path.insert(0, BACKEND)



from tests.helpers.qa_bff_bootstrap import (  # noqa: E402

    EXPECTED_SHELL,

    QA_USERS,

    bff_headers,

    bff_login,

    build_qa_client,

)



BFF = "/api/v1/admin-bff"





def main() -> int:

    client = build_qa_client()

    fails = 0



    for username, password, _role in QA_USERS:

        shell_key = EXPECTED_SHELL[username]

        token = bff_login(client, username, password)

        if not token:

            print(f"[FAIL] {username} login")

            fails += 1

            continue

        print(f"[PASS] {username} login")



        hdrs = bff_headers(token)

        perm = client.get(f"{BFF}/menu/permissions", headers=hdrs).json()

        if perm.get("code") != 0:

            print(f"[FAIL] {username} permissions")

            fails += 1

            continue

        got_shell = perm.get("data", {}).get("shell")

        if got_shell != shell_key:

            print(f"[FAIL] {username} shell expected={shell_key} got={got_shell}")

            fails += 1

        else:

            print(f"[PASS] {username} shell={got_shell}")



        routes = client.get(f"{BFF}/menu/routes", headers=hdrs).json()

        if routes.get("code") != 0 or not isinstance(routes.get("data"), list):

            print(f"[FAIL] {username} menu/routes")

            fails += 1

        elif len(routes["data"]) < 1:

            print(f"[FAIL] {username} menu empty")

            fails += 1

        else:

            print(f"[PASS] {username} menu routes={len(routes['data'])}")



        info = client.get(f"{BFF}/user/info", headers=hdrs).json()

        if info.get("code") != 0:

            print(f"[FAIL] {username} user/info")

            fails += 1

        else:

            print(f"[PASS] {username} user/info")



    print("")

    if fails:

        print(f"QA three-role BFF: {fails} FAILED")

        return 1

    print("QA three-role BFF: ALL PASS")

    return 0





if __name__ == "__main__":

    sys.exit(main())

