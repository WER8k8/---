# 出海计 — Capacitor 真机构建说明

> 包名：`com.youding.chuhaiji` · Web 目录：`frontend/admin/dist`

## 1. 安装依赖（一次性）

在 `frontend/admin` 目录：

```powershell
npm install @capacitor/core @capacitor/cli @capacitor/android @capacitor/ios
```

## 2. 构建 Web 并同步

```powershell
npm run build
npx cap sync
```

## 3. 打开原生工程

```powershell
npx cap open android
npx cap open ios
```

## 4. Push（FCM）

后端环境变量：

| 变量 | 说明 |
|------|------|
| `FCM_SERVER_KEY` | Firebase 控制台 Legacy Server Key；未配置时为 stub 日志模式 |

设备注册：`POST /api/v1/app/v1/devices/register`（platform: `android` / `ios`）。

## 5. PWA（无需商店）

- 入口：`/client/app`（`manifest.webmanifest` 已指向该路径）
- Service Worker：`public/sw.js`（仅缓存壳资源，不缓存 `/api/*`）
- 添加到主屏幕后即可全屏使用四 Tab

## 6. 验收

1. 登录租户账号 → 打开 `/client/app`
2. 助手 Tab 发送「保温板能出口沙特吗」
3. 今日 Tab 显示待办与蓝海提示
4. 我的 → 桌面版可回到 `/client/dashboard`
