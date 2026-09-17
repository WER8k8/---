## 任务：§5 开发信 SPF/DKIM/DMARC 邮件认证配置

工作目录：$BASE/backend
现有代码：backend/app/services/ubrain/email_queue_service.py, email_service.py
产出：outputs/prime-agent/t05-email-auth/

### 实现：email_dns_auth_service.py
路径：backend/app/services/email_dns_auth_service.py

1. DNS记录生成器：
   - generate_spf_record(domain, mail_servers) → TXT record string
   - generate_dkim_selector(domain, public_key) → DKIM TXT record
   - generate_dmarc_record(domain, policy) → DMARC TXT record ("v=DMARC1; p=none|quarantine|reject")

2. 密钥管理：
   - generate_dkim_keypair(bits=2048) → (private_key_pem, public_key_base64)
   - 密钥轮换：rotate_dkim_key(tenant_id) → 新旧密钥交替期管理

3. 送达率监控：
   - 解析 bounce/backscatter 邮件，更新 tenant 的 deliverability_score
   - 低分预警（<60%）自动通知管理员

4. 写测试：test_email_dns_auth_service.py 覆盖生成+验证逻辑
