-- 自动生成：补建 4188869502e0（11 表）+ 069（8 表）在真 PG 缺失的表
-- 断点续做 2026-09-03；结构对齐迁移文件，最小可跑（§25.6 风险条款适用）
-- 注：所有 id/uuid 类列统一 VARCHAR(36)，与 tenants.id VARCHAR(36) 对齐（069 _uuid_type 修复口径）
BEGIN;

CREATE TABLE IF NOT EXISTS glossary_terms (
  id VARCHAR(36) PRIMARY KEY,
  zh VARCHAR(200) NOT NULL,
  en VARCHAR(200) NOT NULL,
  ja VARCHAR(200) NULL,
  ko VARCHAR(200) NULL,
  de VARCHAR(200) NULL,
  fr VARCHAR(200) NULL,
  es VARCHAR(200) NULL,
  pt VARCHAR(200) NULL,
  it VARCHAR(200) NULL,
  nl VARCHAR(200) NULL,
  ru VARCHAR(200) NULL,
  ar VARCHAR(200) NULL,
  tr VARCHAR(200) NULL,
  fa VARCHAR(200) NULL,
  he VARCHAR(200) NULL,
  th VARCHAR(200) NULL,
  vi VARCHAR(200) NULL,
  ms VARCHAR(200) NULL,
  hi VARCHAR(200) NULL,
  id_ba VARCHAR(200) NULL,
  tl VARCHAR(200) NULL,
  bn VARCHAR(200) NULL,
  my VARCHAR(200) NULL,
  km VARCHAR(200) NULL,
  pl VARCHAR(200) NULL,
  cs VARCHAR(200) NULL,
  uk VARCHAR(200) NULL,
  sv VARCHAR(200) NULL,
  sw VARCHAR(200) NULL,
  ha VARCHAR(200) NULL,
  zu VARCHAR(200) NULL,
  am VARCHAR(200) NULL,
  category VARCHAR(50) NULL,
  status VARCHAR(20) NULL,
  is_active BOOLEAN NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_am ON glossary_terms (am);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_ar ON glossary_terms (ar);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_bn ON glossary_terms (bn);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_category ON glossary_terms (category);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_cs ON glossary_terms (cs);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_de ON glossary_terms (de);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_en ON glossary_terms (en);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_es ON glossary_terms (es);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_fa ON glossary_terms (fa);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_fr ON glossary_terms (fr);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_ha ON glossary_terms (ha);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_he ON glossary_terms (he);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_hi ON glossary_terms (hi);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_id_ba ON glossary_terms (id_ba);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_it ON glossary_terms (it);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_ja ON glossary_terms (ja);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_km ON glossary_terms (km);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_ko ON glossary_terms (ko);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_ms ON glossary_terms (ms);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_my ON glossary_terms (my);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_nl ON glossary_terms (nl);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_pl ON glossary_terms (pl);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_pt ON glossary_terms (pt);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_ru ON glossary_terms (ru);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_status ON glossary_terms (status);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_sv ON glossary_terms (sv);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_sw ON glossary_terms (sw);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_th ON glossary_terms (th);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_tl ON glossary_terms (tl);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_tr ON glossary_terms (tr);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_uk ON glossary_terms (uk);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_vi ON glossary_terms (vi);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_zh ON glossary_terms (zh);
CREATE INDEX IF NOT EXISTS ix_glossary_terms_zu ON glossary_terms (zu);

CREATE TABLE IF NOT EXISTS international_target_sites (
  id VARCHAR(36) PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  url VARCHAR(500) NOT NULL,
  region VARCHAR(10) NOT NULL,
  language VARCHAR(10) NULL,
  crawl_interval INTEGER NULL,
  last_crawled_at TIMESTAMPTZ NULL,
  status VARCHAR(20) NULL,
  is_active BOOLEAN NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_international_target_sites_region ON international_target_sites (region);
CREATE INDEX IF NOT EXISTS ix_international_target_sites_status ON international_target_sites (status);

CREATE TABLE IF NOT EXISTS payment_channels (
  id VARCHAR(36) PRIMARY KEY,
  channel VARCHAR(20) NOT NULL,
  config TEXT NULL,
  is_active BOOLEAN NOT NULL,
  created_at TIMESTAMPTZ NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_payment_channels_channel ON payment_channels (channel);

CREATE TABLE IF NOT EXISTS translation_tasks (
  id VARCHAR(36) PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  source_lang VARCHAR(10) NOT NULL,
  target_lang VARCHAR(10) NOT NULL,
  total_items INTEGER NULL,
  completed_items INTEGER NULL,
  status VARCHAR(20) NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_translation_tasks_status ON translation_tasks (status);

CREATE TABLE IF NOT EXISTS international_crawl_logs (
  id VARCHAR(36) PRIMARY KEY,
  site_id VARCHAR(36) NULL,
  status VARCHAR(20) NULL,
  pages_crawled INTEGER NULL,
  inquiries_found INTEGER NULL,
  error_message TEXT NULL,
  duration_seconds INTEGER NULL,
  ip_used VARCHAR(50) NULL,
  created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_international_crawl_logs_site_id ON international_crawl_logs (site_id);
CREATE INDEX IF NOT EXISTS ix_international_crawl_logs_status ON international_crawl_logs (status);

CREATE TABLE IF NOT EXISTS international_inquiries (
  id VARCHAR(36) PRIMARY KEY,
  source_site_id VARCHAR(36) NULL,
  source_url VARCHAR(1000) NOT NULL,
  source_title VARCHAR(500) NULL,
  customer_name VARCHAR(200) NULL,
  email VARCHAR(200) NULL,
  phone VARCHAR(100) NULL,
  wechat VARCHAR(100) NULL,
  company VARCHAR(300) NULL,
  product_interest VARCHAR(500) NULL,
  product_model VARCHAR(200) NULL,
  quantity VARCHAR(200) NULL,
  budget VARCHAR(200) NULL,
  message TEXT NULL,
  inquiry_time VARCHAR(100) NULL,
  crawled_at TIMESTAMPTZ NULL,
  language VARCHAR(10) NULL,
  region VARCHAR(10) NULL,
  confidence INTEGER NULL,
  raw_data TEXT NULL,
  status VARCHAR(20) NULL,
  is_active BOOLEAN NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_international_inquiries_customer_name ON international_inquiries (customer_name);
CREATE INDEX IF NOT EXISTS ix_international_inquiries_email ON international_inquiries (email);
CREATE INDEX IF NOT EXISTS ix_international_inquiries_language ON international_inquiries (language);
CREATE INDEX IF NOT EXISTS ix_international_inquiries_product_interest ON international_inquiries (product_interest);
CREATE INDEX IF NOT EXISTS ix_international_inquiries_region ON international_inquiries (region);
CREATE INDEX IF NOT EXISTS ix_international_inquiries_source_site_id ON international_inquiries (source_site_id);
CREATE INDEX IF NOT EXISTS ix_international_inquiries_status ON international_inquiries (status);

CREATE TABLE IF NOT EXISTS translation_records (
  id VARCHAR(36) PRIMARY KEY,
  task_id VARCHAR(36) NULL,
  source_text TEXT NOT NULL,
  translated_text TEXT NULL,
  source_lang VARCHAR(10) NOT NULL,
  target_lang VARCHAR(10) NOT NULL,
  status VARCHAR(20) NULL,
  rating INTEGER NULL,
  created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_translation_records_status ON translation_records (status);
CREATE INDEX IF NOT EXISTS ix_translation_records_task_id ON translation_records (task_id);

CREATE TABLE IF NOT EXISTS tenant_subscriptions (
  id VARCHAR(36) PRIMARY KEY,
  tenant_id VARCHAR(36) NOT NULL,
  plan_id VARCHAR(36) NOT NULL,
  billing_cycle VARCHAR(20) NOT NULL,
  amount INTEGER NOT NULL,
  status VARCHAR(20) NOT NULL,
  started_at TIMESTAMPTZ NOT NULL,
  ended_at TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_tenant_subscriptions_plan_id ON tenant_subscriptions (plan_id);
CREATE INDEX IF NOT EXISTS ix_tenant_subscriptions_status ON tenant_subscriptions (status);
CREATE INDEX IF NOT EXISTS ix_tenant_subscriptions_tenant_id ON tenant_subscriptions (tenant_id);

CREATE TABLE IF NOT EXISTS user_tenants (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL,
  tenant_id VARCHAR(36) NOT NULL,
  role VARCHAR(20) NULL,
  is_active BOOLEAN NOT NULL,
  created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_user_tenants_tenant_id ON user_tenants (tenant_id);
CREATE INDEX IF NOT EXISTS ix_user_tenants_user_id ON user_tenants (user_id);

CREATE TABLE IF NOT EXISTS payment_orders (
  id VARCHAR(36) PRIMARY KEY,
  tenant_id VARCHAR(36) NOT NULL,
  subscription_id VARCHAR(36) NULL,
  order_no VARCHAR(100) NOT NULL,
  amount INTEGER NOT NULL,
  currency VARCHAR(10) NOT NULL,
  channel VARCHAR(20) NOT NULL,
  subject VARCHAR(200) NOT NULL,
  status VARCHAR(20) NOT NULL,
  paid_at TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_payment_orders_channel ON payment_orders (channel);
CREATE UNIQUE INDEX IF NOT EXISTS ix_payment_orders_order_no ON payment_orders (order_no);
CREATE INDEX IF NOT EXISTS ix_payment_orders_status ON payment_orders (status);
CREATE INDEX IF NOT EXISTS ix_payment_orders_subscription_id ON payment_orders (subscription_id);
CREATE INDEX IF NOT EXISTS ix_payment_orders_tenant_id ON payment_orders (tenant_id);

CREATE TABLE IF NOT EXISTS tenant_invoices (
  id VARCHAR(36) PRIMARY KEY,
  tenant_id VARCHAR(36) NOT NULL,
  subscription_id VARCHAR(36) NULL,
  amount INTEGER NOT NULL,
  status VARCHAR(20) NOT NULL,
  paid_at TIMESTAMPTZ NULL,
  due_at TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_tenant_invoices_status ON tenant_invoices (status);
CREATE INDEX IF NOT EXISTS ix_tenant_invoices_subscription_id ON tenant_invoices (subscription_id);
CREATE INDEX IF NOT EXISTS ix_tenant_invoices_tenant_id ON tenant_invoices (tenant_id);


-- ===== 069_add_evolution_deerflow =====

CREATE TABLE IF NOT EXISTS deerflow_jobs (
  id VARCHAR(36) PRIMARY KEY,
  tenant_id VARCHAR(36) NOT NULL,
  intent VARCHAR(64) NOT NULL,
  status VARCHAR(20) NOT NULL,
  payload_json TEXT NOT NULL,
  result_json TEXT NULL,
  error_message TEXT NULL,
  log_text TEXT NOT NULL,
  created_by UUID NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  started_at TIMESTAMPTZ NULL,
  finished_at TIMESTAMPTZ NULL,
  FOREIGN KEY (tenant_id) REFERENCES public.tenants(id),
  FOREIGN KEY (created_by) REFERENCES public.users(id)
);

CREATE TABLE IF NOT EXISTS evolution_task_records (
  id VARCHAR(36) PRIMARY KEY,
  tenant_id VARCHAR(36) NULL,
  task_type VARCHAR(80) NOT NULL,
  executor_type VARCHAR(30) NOT NULL,
  executor_id VARCHAR(100) NOT NULL,
  success BOOLEAN NOT NULL,
  duration_ms INTEGER NOT NULL,
  cost FLOAT NOT NULL,
  tokens_used INTEGER NOT NULL,
  error_code VARCHAR(50) NULL,
  error_message TEXT NULL,
  input_summary TEXT NULL,
  output_summary TEXT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  FOREIGN KEY (tenant_id) REFERENCES public.tenants(id)
);

CREATE TABLE IF NOT EXISTS evolution_experiences (
  id VARCHAR(36) PRIMARY KEY,
  task_type VARCHAR(80) NOT NULL,
  pattern_type VARCHAR(30) NOT NULL,
  title VARCHAR(200) NOT NULL,
  description TEXT NULL,
  pattern_data JSONB NOT NULL,
  source_record_ids JSONB NOT NULL,
  confidence FLOAT NOT NULL,
  occurrence_count INTEGER NOT NULL,
  applied BOOLEAN NOT NULL,
  applied_at TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS evolution_skill_versions (
  id VARCHAR(36) PRIMARY KEY,
  skill_id VARCHAR(100) NOT NULL,
  skill_name VARCHAR(200) NOT NULL,
  version VARCHAR(20) NOT NULL,
  major INTEGER NOT NULL,
  minor INTEGER NOT NULL,
  patch INTEGER NOT NULL,
  status VARCHAR(20) NOT NULL,
  prompt_template TEXT NULL,
  parameters JSONB NOT NULL,
  changelog TEXT NULL,
  based_on_experience_ids JSONB NOT NULL,
  success_rate FLOAT NULL,
  avg_duration_ms INTEGER NULL,
  total_invocations INTEGER NOT NULL,
  parent_version_id VARCHAR(36) NULL,
  canary_percentage FLOAT NOT NULL,
  canary_tenant_ids JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  FOREIGN KEY (parent_version_id) REFERENCES public.evolution_skill_versions(id)
);

CREATE TABLE IF NOT EXISTS evolution_sop_versions (
  id VARCHAR(36) PRIMARY KEY,
  sop_id VARCHAR(100) NOT NULL,
  sop_name VARCHAR(200) NOT NULL,
  version VARCHAR(20) NOT NULL,
  major INTEGER NOT NULL,
  minor INTEGER NOT NULL,
  patch INTEGER NOT NULL,
  status VARCHAR(20) NOT NULL,
  steps JSONB NOT NULL,
  decision_tree JSONB NOT NULL,
  exception_handling JSONB NOT NULL,
  changelog TEXT NULL,
  based_on_experience_ids JSONB NOT NULL,
  linked_skill_version_ids JSONB NOT NULL,
  completion_rate FLOAT NULL,
  avg_completion_time_ms INTEGER NULL,
  total_executions INTEGER NOT NULL,
  parent_version_id VARCHAR(36) NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  FOREIGN KEY (parent_version_id) REFERENCES public.evolution_sop_versions(id)
);

CREATE TABLE IF NOT EXISTS evolution_approvals (
  id VARCHAR(36) PRIMARY KEY,
  target_type VARCHAR(30) NOT NULL,
  target_id VARCHAR(36) NOT NULL,
  action VARCHAR(30) NOT NULL,
  status VARCHAR(20) NOT NULL,
  requester VARCHAR(100) NOT NULL,
  reviewer VARCHAR(100) NULL,
  review_comment TEXT NULL,
  evidence JSONB NOT NULL,
  submitted_at TIMESTAMPTZ NOT NULL,
  reviewed_at TIMESTAMPTZ NULL
);

CREATE TABLE IF NOT EXISTS evolution_canary_routes (
  id VARCHAR(36) PRIMARY KEY,
  tenant_id VARCHAR(36) NULL,
  skill_id VARCHAR(100) NOT NULL,
  routed_version VARCHAR(20) NULL,
  routed_version_id VARCHAR(36) NULL,
  is_canary BOOLEAN NOT NULL,
  request_hash VARCHAR(64) NULL,
  created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS n8n_workflows (
  id VARCHAR(36) PRIMARY KEY,
  tenant_id VARCHAR(36) NULL,
  workflow_id VARCHAR(100) NOT NULL,
  name VARCHAR(200) NOT NULL,
  description TEXT NULL,
  endpoint_url VARCHAR(500) NOT NULL,
  auth_type VARCHAR(30) NOT NULL,
  auth_config JSONB NOT NULL,
  scene VARCHAR(50) NULL,
  enabled BOOLEAN NOT NULL,
  last_triggered_at TIMESTAMPTZ NULL,
  trigger_count INTEGER NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  FOREIGN KEY (tenant_id) REFERENCES public.tenants(id)
);

ALTER TABLE inquiries ADD COLUMN IF NOT EXISTS wechat VARCHAR(100);

COMMIT;
