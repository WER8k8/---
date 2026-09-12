# MOD-06 · 出海计 App 商店提审清单

> **Capacitor**：`frontend/admin/capacitor.config.ts` · `appId: com.youding.chuhaiji`  
> **页面**：`/client/chuhaiji-app` · `chuhaiji-app.vue`

| 步 | 动作 | 命令 / 产物 |
|----|------|-------------|
| 1 | 安装 Capacitor | `cd frontend/admin && npm i @capacitor/core @capacitor/cli @capacitor/android @capacitor/ios --save-dev` |
| 2 | 构建 Web + sync | `npm run cap:sync` |
| 3 | Android 包 | `npx cap open android` → Release AAB |
| 4 | iOS 包 | `npx cap open ios` → Archive IPA |
| 5 | 隐私政策 URL | 与 `SITE_URL` 法务页一致 |
| 6 | 截图集 | 助手 / 今日 / 贸易情报 三 Tab |
| 7 | 提审 | 应用商店 Connect / 国内渠道 |

**验证**：`scripts/validate-mod-06-chuhaiji-app.py`
