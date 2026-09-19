---
feature: annex-domain-merge
status: delivered
updated: 2026-09-19
branch: feat/annex-domain-merge
commits: f76947e4f6d985680cec2bf860c9fe0ac836ae7e..82f1e939585ea9be7a834af45201002643f3c107
---

# 闄勫睘鍔熻兘鍩熻瀺鍏ヤ紭涓侊紙GoodJob + TradeAI锛?
## Report

**What was built** 鈥?GoodJob/TradeAI 浠?*鍔熻兘鍩熻彍鍗?*锛堢ぞ濯掓嫇瀹?/ 澶栬锤灞ョ害锛屾棤鐗规潈锛夊苟鍏ヤ紭涓侊紱韬唤渚?login/瓒呯/绠＄悊鍙扮敓浜?410锛堜繚鐣?annex-ticket + uj-bridge锛夛紱Hermes 鍙屽钩闈㈠绾︼紙浜や簰 API vs 浠诲姟 L1锛孌SH 闈炲繀缁忥級锛涢粍閲戣矾寰?API锛歚POST /api/v1/orchestration/golden-path/fulfillment`锛圙P-A锛変笌 `/outreach`锛圙P-B锛夛紝灞ョ害闃熷垪椤点€屼竴閿饱绾?路 Hermes銆嶄笌 PI 鍔ㄤ綔鎺ュ叆浠诲姟闈紱TradeAI 鎶€鑳藉悕杩涘叆 planner 鐧藉悕鍗曪紱鍗忚瀹¤鏂囨。钀界洏銆?
**Verification** 鈥?`pytest` annex/planner 鐩稿叧 **PASS**锛沗verify_annex_domain_merge.py` / `verify_annex_work_mode.py` / `verify_annex_identity_strip.py` **PASS**锛沗orchestration_selfcheck` **19/19**锛涜瘎瀹″悗淇锛氬彲绉绘璺緞銆乣${msg}`銆佽鍗曚笂涓嬫枃鎸夐挳銆佸幓闄ゃ€岄檮灞炰竴/浜屻€嶆畫鐣欐枃妗堛€?
**Journey log** 鈥?鈶?Compose 宸ヤ綔鍖猴細鏅鸿兘鍒ゆ柇鈫掑綋鍓?AGENTS 璺緞 + `feat/annex-domain-merge`锛堥潪宓屽 worktree锛夈€傗憽 鑼冨洿锛氭櫤鑳藉垽鏂啋P0 鏀跺彛 + GP-A 闂幆 + P1 鏍稿績锛堥潪 P0鈥揚3 鍏ㄩ噺锛夈€傗憿 璇勫 critical锛氭湭鎻愪氦娣峰叆鏃犲叧鑴忔枃浠垛啋鎻愪氦椤?path-filter锛沴ive HTTP 渚濊禆鍚庣杩涚▼銆傗懀 鍓ヨ韩浠藉湪 `_external`锛屼富浠撻棬绂佷负闈欐€佹爣璁?鍙Щ妞嶈矾寰勩€傗懁 鏃с€岄檮灞炴墽琛屽彴銆嶅彊浜嬪凡浠庝笟鍔¤彍鍗曚笌鑳藉姏鎻忚堪绉婚櫎銆?
## [S1] Problem
GoodJob 涓?TradeAI 闇€鎴愪负浼樹竵**瀹屾暣浣撳姛鑳藉煙**锛堟棤闅旈槀銆佹棤鐗规潈鑿滃崟銆丠ermes 鏃犵紳椹卞姩锛夛紝鑰岄潪绗簩濂楀彲鐧诲綍绯荤粺銆?
## [S2] Design
- **鍙屽钩闈?*锛氫氦浜?CRUD 鈫?UJ API锛涗换鍔￠潰 鈫?Hermes锛堥粯璁?L1锛孌SH 闈炲繀缁忥級銆?- **鍔熻兘鍩熻彍鍗?*锛氱ぞ濯掓嫇瀹?/ 澶栬锤灞ョ害锛宍privileged:false`锛孶J RBAC銆?- **韬唤**锛氶檮灞?login/platform/admin 鈫?410锛涗繚鐣?annex-ticket + uj-bridge銆?- **GP-A**锛歚POST /orchestration/golden-path/fulfillment` 鈫?L1 `_fulfillment_graph`锛堝惈 goodjob_crm锛夈€?- **GP-B**锛歚POST /orchestration/golden-path/outreach` 鈫?trade_ai_agent L1锛涙妧鑳借繘 FALLBACK 鐧藉悕鍗曘€?- **鍗忚瀹¤**锛歚docs/annex-protocol-audit-2026-09-19.md`銆?- **鏁版嵁**锛氱湡鐩镐粎浼樹竵 PG锛涙棤 Key 璇氬疄 failed銆?
## [S3] Out of Scope
- 闄勫睘鐙珛鍓嶇鐗╃悊褰掓。锛圥3锛夛紱澶栭儴 Key 鐪熷彂锛汫oodJob Node Python 鍖栵紱鏂板缓宓屽 git worktree銆?
## Tasks
- [x] T1: GP-A 涓€閿饱绾?API 鈥?acceptance: golden-path/fulfillment 璺敱 + L1 鍚?goodjob_crm锛坈overs: S2锛?- [x] T2: 灞ョ害闃熷垪 Hermes 鎸夐挳 鈥?acceptance: fulfillment.vue 璋冪敤 GP-A API锛屽睍绀?plan_id锛坈overs: S2; depends: T1锛?- [x] T3: TradeAI 鎶€鑳界櫧鍚嶅崟 鈥?acceptance: trade_ai.* / skill.social_scraper 鍦?FALLBACK_CAPABILITIES锛坈overs: S2锛?- [x] T4: 澶嶅悎鑸亾濂戠害娴嬭瘯 鈥?acceptance: golden_path helper + verify_annex_work_mode 鍏ㄧ豢锛坈overs: S2锛?- [x] T5: 鍗忚/鍑哄瀹¤鏂囨。 鈥?acceptance: docs/annex-protocol-audit-2026-09-19.md锛坈overs: S2锛?- [x] T6: 闂ㄧ涓庡洖褰?鈥?acceptance: pytest annex+planner銆乿erify_annex_*銆乻elfcheck 19/19锛坈overs: S2锛?
