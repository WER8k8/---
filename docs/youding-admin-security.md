# 优丁 Admin 百家组装 · 安全因素与加固清单

> 配套：`docs/youding-admin-composite-blueprint.md`  
> 范围：开源模板供应链、前端、BFF、权限、会话、审计、合规

---

## 一、开源模板共性风险（8 套通用）

| 风险类 | 说明 | 各模板常见表现 |
|--------|------|----------------|
| **供应链** | 依赖树深、传递漏洞 | Vben monorepo 包多；Element 系 npm 依赖量大 |
| **演示后门** | 默认账号、Mock 登录、关闭权限 | Vben `vben/123456`；Element Admin 演示路由 |
| **前端权限幻觉** | 只藏菜单不拦 API | 所有模板的 `v-access` / 路由守卫 **不能替代后端** |
| **Token 存 localStorage** | XSS 即盗号 | Vben / Art / Soybean 默认 Pinia persist → localStorage |
| **动态路由注入** | 恶意菜单 JSON 加载任意组件 | 后端菜单被篡改 → 前端 `import()` 路径风险 |
| **富文本 / 上传** | XSS、恶意文件 | Art wangEditor、各模板文件管理 demo |
| **CSP 冲突** | 模板 inline script、CDN | 与你们现有 CSP 需联调 |
| **许可证** | MIT 可商用，但组件内嵌字体/图库需另查 | 一般 OK |

**结论**：模板只借 **壳与模式**；**鉴权与数据权限必须在 FastAPI 层终局校验**。

---

## 二、分仓库安全特点

### 1. Vue Vben Admin（选定底座）

| 项 | 评估 |
|----|------|
| 权限模型 | 路由 + 按钮码，较完整；需接 **后端 codes** |
| 依赖 | monorepo + turbo，需 `pnpm audit` / Dependabot |
| Token | 默认 Bearer + 持久化；生产建议 **短 access + refresh 轮转** |
| 风险点 | 演示环境配置误上生产；`VITE_*` 泄露 API 地址（非密钥） |
| 加固 | 关闭 demo 路由；`accessMode` 固定 backend；CSP 与 Vite 构建策略 |

### 2. Art Design Pro / Edge

| 项 | 评估 |
|----|------|
| 多租户登录 | tenant_code、验证码 — **须防租户枚举**（Edge 的 tenant search） |
| 水印 | 防截图泄密（弱），不能替代权限 |
| 元素权限 authList | 细粒度按钮；**须与 DB permission 同步** |
| Edge BFF 契约 | 路径固定 `/private/admin/system/*` — 我们 UAC 已抽象，避免暴露内部结构 |
| 风险点 | captcha stub 上线前必须真验证码或限流 |

### 3. Soybean / Pure / Better / Naive / Element Admin

| 项 | 评估 |
|----|------|
| 共性 | 前端 RBAC 演示多、后端 Mock 多 |
| Element Admin | 历史 XSS 案例多（老版本），勿直接用 Vue2 主分支 |
| Naive | UI 组件安全更新跟随 naive-ui 版本 |
| Better 代码生成 | 生成页默认 **无权限注解** — 生成器须带 `permission_code` |
| 抽取原则 | **只抄结构与规范，不抄 Mock 鉴权** |

### 4. RuoYi-Plus-Soybean

| 项 | 评估 |
|----|------|
| 后端 | Spring Security + 数据权限注解 — **能力清单参考**，不引入 Java 攻击面 |
| 借鉴 | 操作日志、数据范围（本部门/本租户）、字典审计 |
| 勿借鉴 | 默认 Druid 监控弱口令、Swagger 生产暴露等 RuoYi 常见坑 |

---

## 三、你们现有后端安全（组装时保留）

已有能力（**换 UI 不能丢**）：

| 能力 | 位置 |
|------|------|
| JWT + jti + refresh scope | `app/core/security.py` |
| bcrypt rounds 12–14 | `pwd_context` |
| 登录暴力破解锁 | `login_bruteforce.py`（Redis/内存） |
| 超管会话吊销 | `admin_auth.py` Redis `admin_session_revoked` |
| RBAC 权限码 | `AdminPermission` + `require_permission_code` |
| 菜单树权限过滤 | `build_menu_tree` + `permission_code` |
| 安全响应头 CSP/HSTS | `security_headers.py` |
| WAF + 路径遍历 | `waf.py` + `security_middleware.py` |
| 限流 | `RateLimitMiddleware` |
| 租户隔离中间件 | `TenantMiddleware` |
| 生产 SECRET_KEY 强制 | `config.py` |

---

## 四、UAC / admin-bff 新增攻击面

| 端点 | 风险 | 加固要求 |
|------|------|----------|
| `POST /admin-bff/auth/login` | 暴力破解、撞库 | 继承现网 `check_login_allowed`；P1  captcha |
| `GET /admin-bff/auth/tenant/search` | **租户枚举** | 限流 + 模糊匹配最小长度 + 统一错误文案 |
| `GET /admin-bff/menu/routes` | 越权壳、菜单投毒 | **必须** `Depends(get_current_user)`；shell 由 **服务端** 按 role 解析，不信 query  alone |
| `GET /admin-bff/menu/permissions` | 泄露权限码全集 | 只返回 **当前用户** codes |
| `GET /admin-bff/user/info` | 信息泄露 | 最小字段；租户信息脱敏 |

### 当前待加固项（P0→P1）

1. **`shell` 查询参数**：客户端传 `shell=platform` 可能越权 — 应 **忽略或校验** 与 JWT role 一致  
2. **captcha stub**：生产必须启用或 WAF 限流登录  
3. **BFF 与 /auth 双入口**：审计日志需合并，防绕过监控  
4. **动态路由 component 路径**：白名单前缀 `views/`、`layouts/`，禁止 `http://`、`.` 路径遍历  

---

## 五、前端组装安全规范

### 5.1 会话与 Token

| 做法 | 说明 |
|------|------|
| access 短过期 | 已有 `ACCESS_TOKEN_EXPIRE_MINUTES` |
| refresh 轮转 + 黑名单 | 已有 `refresh_token_blacklist` |
| 存储 | 优先 **内存 + httpOnly cookie（若上同源网关）**；短期可保留 localStorage 但 **严格 CSP 防 XSS** |
| 退出 | 清 token + 调 revoke + 清 Pinia persist |

### 5.2 XSS

- 禁止未消毒 `v-html`（Markdown 渲染走 DOMPurify）  
- 富文本（Quill/wangEditor）上传 HTML 后端消毒  
- CSP：逐步收紧 `'unsafe-inline'` / `'unsafe-eval'`（Vben 构建期挑战）

### 5.3 CSRF

- API 纯 Bearer：**CSRF 风险低于 Cookie 会话**  
- 若改 Cookie 会话：必须 SameSite + CSRF token  

### 5.4 四壳隔离（安全视角）

| 壳 | 必须 |
|----|------|
| Client | 租户数据 `tenant_id` 后端强制，不信前端 |
| Platform | super_admin 菜单与 API 双重校验 |
| Agent | 禁止 agent 路由注册 platform 组件（组件路径白名单） |
| Ops | 与 Platform 角色矩阵文档化 |

### 5.5 财旺 / 第三方脚本

- 悬浮助手仅同源 API  
- 外链 `goFullCopilot` 同域路由，不注入第三方 script  

---

## 六、权限纵深（五层 + 数据层）

```
JWT 身份 → 壳 shell → 菜单/路由 → 按钮 authList → API permission_code → 数据 tenant_id 行级
```

| 层 | 失败模式 | 检测 |
|----|----------|------|
| 只藏菜单 | 直接调 API | 接口 403 单测 |
| 只拦路由 | curl 带 token | 集成测试 |
| BFF 信任 shell 参数 | 水平越权 | 安全测试用例 |
| 超管菜单泄漏到租户 | 代理壳 E2E | 每月验收清单 |

---

## 七、供应链与发布

| 步骤 | 动作 |
|------|------|
| 依赖 | `pnpm audit` / `pip audit` 进 CI |
| 模板升级 | 只 merge Vben 安全补丁，不整库覆盖业务 |
| 密钥 | 生产 `JWT_SECRET_KEY`、`SECRET_KEY` ≥32，禁入仓库 |
| 演示账号 | 生产库删除 vben/demo 类账号 |
| 头信息 | API 走 `APISecurityHeadersMiddleware`，Admin SPA 走 CSP |
| 日志 | 登录失败、权限 403、菜单变更、角色授权 — 进 `LoginLog` / audit |

---

## 八、组装验收 · 安全门禁

- [ ] BFF 所有写操作与敏感读 **必须** `get_current_user`  
- [ ] `shell` 仅服务端解析，或 query 与 role 不一致则 403  
- [ ] 菜单 `component` 字段白名单校验  
- [ ] 前端路由守卫 + 后端 403 **成对测试**（每壳 1 套）  
- [ ] 登录限流 + 可选 captcha 生产开启  
- [ ] 无默认弱口令；演示路由 `clean:dev` 等价清理  
- [ ] CSP / HSTS 预发环境扫描（Mozilla Observatory 或 zaproxy）  
- [ ] 租户 A token 不能访问租户 B `/client/*` 数据（IDOR 测试）  

---

## 九、与百家抽取的对应

| 来源 | 安全要素抽取 |
|------|--------------|
| Vben | 路由守卫、按钮权限指令、环境变量隔离 |
| Art Edge | 验证码、水印（弱防泄）、元素权限树 |
| Element Admin | 路由白名单、登录 redirect 校验 |
| RuoYi | 操作审计、数据范围（待 FastAPI 实现） |
| Soybean | 类型安全减低级注入误用 |
| 现网 FastAPI | **唯一信任根** — JWT、RBAC、租户中间件、WAF |

**原则**：美观和权限都来自组装，**安全只信后端 + 白名单 + 审计**。
