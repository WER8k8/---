## 任务：§15 安全合规自动化测试

工作目录：$BASE/backend
现有代码：
- backend/app/services/vault/crypto.py (加密存储)
- backend/app/core/security_middleware.py (防重放签名)
- backend/app/core/audit.py (审计日志)
产出：outputs/prime-agent/t09-security-tests/

### 实现测试套件：tests/integration/test_security_compliance.py

1. 加密存储测试：
   - vault_encrypt_decrypt_roundtrip(tenant_id, secret) → 加密后解密一致
   - 不同tenant的密文不可互解（隔离验证）
   - 密钥轮换后旧密文仍可解密

2. 审计日志测试：
   - 每次敏感操作写入审计表
   - 日志不可篡改（哈希链验证）
   - GDPR右删除时审计日志保留策略

3. 防重放签名测试：
   - 同一请求重放被拒绝
   - 签名过期（超过有效期）被拒绝
   - 不同tenant的签名不互通

4. RLS隔离测试（复用已完成的14/14绿，新增边界case）：
   - tenant A 无法通过ID猜测访问 tenant B 数据
   - 跨tenant聚合查询正确拒绝
