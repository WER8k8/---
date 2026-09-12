CREATE TABLE token_ledger_entries (
	id UUID NOT NULL, 
	tenant_id UUID NOT NULL, 
	delta INTEGER NOT NULL, 
	balance_after INTEGER NOT NULL, 
	reason VARCHAR(100) NOT NULL, 
	reference_id VARCHAR(100), 
	created_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id)
);
CREATE INDEX ix_token_ledger_entries_tenant_id ON token_ledger_entries (tenant_id);
CREATE INDEX ix_token_ledger_entries_created_at ON token_ledger_entries (created_at);

CREATE TABLE wallet_accounts (
	id UUID NOT NULL, 
	user_id VARCHAR(64) NOT NULL, 
	currency VARCHAR(8) NOT NULL, 
	balance INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE, 
	updated_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_wallet_account_user_currency UNIQUE (user_id, currency)
);
CREATE INDEX ix_wallet_accounts_user_id ON wallet_accounts (user_id);

CREATE TABLE wallet_transactions (
	id UUID NOT NULL, 
	tx_id VARCHAR(32) NOT NULL, 
	user_id VARCHAR(64) NOT NULL, 
	operation VARCHAR(20) NOT NULL, 
	amount INTEGER NOT NULL, 
	currency VARCHAR(8) NOT NULL, 
	balance_after INTEGER NOT NULL, 
	to_user_id VARCHAR(64), 
	ref_type VARCHAR(50), 
	ref_id VARCHAR(100), 
	created_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id)
);
CREATE INDEX ix_wallet_transactions_ref_id ON wallet_transactions (ref_id);
CREATE UNIQUE INDEX ix_wallet_transactions_tx_id ON wallet_transactions (tx_id);
CREATE INDEX ix_wallet_transactions_created_at ON wallet_transactions (created_at);
CREATE INDEX ix_wallet_transactions_user_id ON wallet_transactions (user_id);

CREATE TABLE content_masters (
	id UUID NOT NULL, 
	tenant_id UUID NOT NULL, 
	title VARCHAR(500) NOT NULL, 
	body TEXT, 
	media_urls JSON, 
	content_type VARCHAR(30), 
	tenant_canonical_url VARCHAR(1000), 
	status VARCHAR(20), 
	hub_slug VARCHAR(200), 
	hub_summary TEXT, 
	show_on_hub BOOLEAN, 
	hub_published_at TIMESTAMP WITH TIME ZONE, 
	created_by UUID, 
	created_at TIMESTAMP WITH TIME ZONE, 
	updated_at TIMESTAMP WITH TIME ZONE, 
	preflight_checklist_json TEXT, 
	preflight_approved_at TIMESTAMP WITH TIME ZONE, 
	preflight_approved_by UUID, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id), 
);
CREATE INDEX ix_content_masters_tenant_id ON content_masters (tenant_id);

CREATE TABLE email_outreachs (
	id UUID NOT NULL, 
	idempotency_key VARCHAR(64) NOT NULL, 
	tenant_id UUID, 
	user_id UUID, 
	from_email VARCHAR(255) NOT NULL, 
	from_name VARCHAR(255) NOT NULL, 
	to_email VARCHAR(255) NOT NULL, 
	reply_to VARCHAR(255), 
	subject VARCHAR(500) NOT NULL, 
	html_body TEXT NOT NULL, 
	text_body TEXT, 
	status email_status_enum NOT NULL, 
	sequence_id VARCHAR(64), 
	sequence_step INTEGER, 
	sequence_total_steps INTEGER, 
	tracking_pixel_id VARCHAR(64), 
	tracking_links JSON, 
	open_count INTEGER NOT NULL, 
	first_opened_at TIMESTAMP WITH TIME ZONE, 
	last_opened_at TIMESTAMP WITH TIME ZONE, 
	click_count INTEGER NOT NULL, 
	first_clicked_at TIMESTAMP WITH TIME ZONE, 
	last_clicked_at TIMESTAMP WITH TIME ZONE, 
	bounce_type bounce_type_enum, 
	bounce_reason VARCHAR(500), 
	bounced_at TIMESTAMP WITH TIME ZONE, 
	provider VARCHAR(32), 
	provider_message_id VARCHAR(255), 
	outreach_metadata JSON, 
	tags JSON, 
	scheduled_at TIMESTAMP WITH TIME ZONE, 
	sent_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id), 
	UNIQUE (tracking_pixel_id)
);
CREATE INDEX ix_email_outreachs_tenant_id ON email_outreachs (tenant_id);
CREATE INDEX idx_email_outreach_tenant_status ON email_outreachs (tenant_id, status);
CREATE INDEX ix_email_outreachs_sequence_id ON email_outreachs (sequence_id);
CREATE INDEX idx_email_outreach_sequence ON email_outreachs (sequence_id, sequence_step);
CREATE INDEX ix_email_outreachs_status ON email_outreachs (status);
CREATE INDEX idx_email_outreach_to_status ON email_outreachs (to_email, status);
CREATE UNIQUE INDEX ix_email_outreachs_idempotency_key ON email_outreachs (idempotency_key);
CREATE INDEX idx_email_outreach_created ON email_outreachs (created_at);
CREATE INDEX ix_email_outreachs_to_email ON email_outreachs (to_email);
CREATE INDEX ix_email_outreachs_user_id ON email_outreachs (user_id);

CREATE TABLE prospect_leads (
	id UUID NOT NULL, 
	email VARCHAR(255), 
	email_domain VARCHAR(255), 
	linkedin_url VARCHAR(500), 
	linkedin_id VARCHAR(64), 
	phone VARCHAR(50), 
	company_name VARCHAR(255), 
	company_name_normalized VARCHAR(255), 
	domain VARCHAR(255), 
	website VARCHAR(500), 
	country VARCHAR(8), 
	industry VARCHAR(100), 
	company_size VARCHAR(50), 
	revenue_range VARCHAR(50), 
	first_name VARCHAR(100), 
	last_name VARCHAR(100), 
	title VARCHAR(200), 
	department VARCHAR(100), 
	source lead_source_enum NOT NULL, 
	source_detail JSON, 
	status lead_status_enum NOT NULL, 
	fit_score INTEGER NOT NULL, 
	engagement_score INTEGER NOT NULL, 
	overall_score INTEGER NOT NULL, 
	score_match INTEGER NOT NULL, 
	score_email INTEGER NOT NULL, 
	score_evidence INTEGER NOT NULL, 
	score_contact INTEGER NOT NULL, 
	evidence_chain JSON, 
	last_opened_at TIMESTAMP WITH TIME ZONE, 
	open_count INTEGER NOT NULL, 
	last_clicked_at TIMESTAMP WITH TIME ZONE, 
	click_count INTEGER NOT NULL, 
	last_replied_at TIMESTAMP WITH TIME ZONE, 
	reply_count INTEGER NOT NULL, 
	email_verified VARCHAR(20), 
	email_verified_at TIMESTAMP WITH TIME ZONE, 
	phone_verified VARCHAR(20), 
	contact_count INTEGER NOT NULL, 
	last_contacted_at TIMESTAMP WITH TIME ZONE, 
	last_contacted_channel VARCHAR(20), 
	tags JSON, 
	notes TEXT, 
	tenant_id UUID, 
	assigned_to UUID, 
	created_by UUID, 
	merged_from JSON, 
	is_duplicate VARCHAR(64), 
	version INTEGER NOT NULL, 
	lead_metadata JSON, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_prospect_lead_email_tenant UNIQUE (email, tenant_id), 
	CONSTRAINT uq_prospect_lead_linkedin_tenant UNIQUE (linkedin_url, tenant_id), 
	CONSTRAINT ck_prospect_lead_overall_score CHECK (overall_score BETWEEN 0 AND 100), 
	CONSTRAINT ck_prospect_lead_score_match CHECK (score_match BETWEEN 0 AND 100), 
	CONSTRAINT ck_prospect_lead_score_email CHECK (score_email BETWEEN 0 AND 100), 
	CONSTRAINT ck_prospect_lead_score_evidence CHECK (score_evidence BETWEEN 0 AND 100), 
	CONSTRAINT ck_prospect_lead_score_contact CHECK (score_contact BETWEEN 0 AND 100), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id), 
);
CREATE INDEX ix_prospect_leads_linkedin_url ON prospect_leads (linkedin_url);
CREATE INDEX ix_prospect_leads_email ON prospect_leads (email);
CREATE INDEX ix_prospect_leads_status ON prospect_leads (status);
CREATE INDEX ix_prospect_leads_is_duplicate ON prospect_leads (is_duplicate);
CREATE INDEX ix_prospect_leads_domain ON prospect_leads (domain);
CREATE INDEX idx_prospect_lead_created ON prospect_leads (created_at);
CREATE INDEX idx_prospect_lead_domain_company ON prospect_leads (domain, company_name_normalized);
CREATE INDEX ix_prospect_leads_tenant_id ON prospect_leads (tenant_id);
CREATE INDEX ix_prospect_leads_email_domain ON prospect_leads (email_domain);
CREATE INDEX ix_prospect_leads_company_name_normalized ON prospect_leads (company_name_normalized);
CREATE INDEX idx_prospect_lead_status_score ON prospect_leads (status, overall_score);
CREATE INDEX ix_prospect_leads_created_at ON prospect_leads (created_at);
CREATE INDEX idx_prospect_lead_tenant_status ON prospect_leads (tenant_id, status);

CREATE TABLE ubrain_tenant_memory (
	tenant_id UUID NOT NULL, 
	memory_json TEXT NOT NULL, 
	tool_use_count INTEGER NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (tenant_id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id)
);
