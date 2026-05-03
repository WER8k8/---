-- ============================================
-- 全国县域建材SEO矩阵AI全自动后台系统
-- MySQL 8.0 数据库Schema设计
-- ============================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS seo_matrix_db 
  DEFAULT CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

USE seo_matrix_db;

-- ============================================
-- 1. 系统管理员表
-- ============================================
CREATE TABLE `admin_users` (
  `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  `username` VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
  `password_hash` VARCHAR(255) NOT NULL COMMENT '密码哈希',
  `nickname` VARCHAR(50) DEFAULT '' COMMENT '昵称',
  `avatar` VARCHAR(255) DEFAULT '' COMMENT '头像URL',
  `email` VARCHAR(100) DEFAULT '' COMMENT '邮箱',
  `phone` VARCHAR(20) DEFAULT '' COMMENT '手机号',
  `status` TINYINT DEFAULT 1 COMMENT '状态：1启用 0禁用',
  `last_login_at` DATETIME NULL COMMENT '最后登录时间',
  `last_login_ip` VARCHAR(45) DEFAULT '' COMMENT '最后登录IP',
  `login_fail_count` TINYINT DEFAULT 0 COMMENT '登录失败次数',
  `locked_until` DATETIME NULL COMMENT '锁定至',
  `expires_at` DATETIME NULL COMMENT '账号过期时间',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_status (`status`),
  INDEX idx_username (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='管理员表';

-- ============================================
-- 2. 角色表
-- ============================================
CREATE TABLE `roles` (
  `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(50) NOT NULL UNIQUE COMMENT '角色名称',
  `code` VARCHAR(50) NOT NULL UNIQUE COMMENT '角色编码',
  `description` TEXT COMMENT '角色描述',
  `status` TINYINT DEFAULT 1 COMMENT '状态：1启用 0禁用',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_status (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色表';

-- ============================================
-- 3. 权限表
-- ============================================
CREATE TABLE `permissions` (
  `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(100) NOT NULL COMMENT '权限名称',
  `code` VARCHAR(100) NOT NULL UNIQUE COMMENT '权限编码',
  `type` ENUM('menu', 'button', 'data') NOT NULL COMMENT '权限类型',
  `parent_id` INT UNSIGNED DEFAULT 0 COMMENT '父权限ID',
  `path` VARCHAR(255) DEFAULT '' COMMENT '路由路径',
  `sort_order` INT DEFAULT 0 COMMENT '排序',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_type (`type`),
  INDEX idx_parent_id (`parent_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='权限表';

-- ============================================
-- 4. 用户角色关联表
-- ============================================
CREATE TABLE `user_roles` (
  `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT UNSIGNED NOT NULL,
  `role_id` INT UNSIGNED NOT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_user_role (`user_id`, `role_id`),
  INDEX idx_user_id (`user_id`),
  INDEX idx_role_id (`role_id`),
  FOREIGN KEY (`user_id`) REFERENCES `admin_users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`role_id`) REFERENCES `roles`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户角色关联表';

-- ============================================
-- 5. 角色权限关联表
-- ============================================
CREATE TABLE `role_permissions` (
  `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  `role_id` INT UNSIGNED NOT NULL,
  `permission_id` INT UNSIGNED NOT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_role_perm (`role_id`, `permission_id`),
  INDEX idx_role_id (`role_id`),
  INDEX idx_perm_id (`permission_id`),
  FOREIGN KEY (`role_id`) REFERENCES `roles`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`permission_id`) REFERENCES `permissions`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色权限关联表';

-- ============================================
-- 6. 系统配置表
-- ============================================
CREATE TABLE `system_configs` (
  `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  `config_key` VARCHAR(100) NOT NULL UNIQUE COMMENT '配置键',
  `config_value` TEXT COMMENT '配置值',
  `config_type` ENUM('string', 'number', 'boolean', 'json') DEFAULT 'string' COMMENT '配置类型',
  `group_name` VARCHAR(50) DEFAULT 'default' COMMENT '配置分组',
  `description` VARCHAR(255) DEFAULT '' COMMENT '配置说明',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_group (`group_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表';

-- ============================================
-- 7. 省市区地域表
-- ============================================
CREATE TABLE `regions` (
  `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  `parent_id` INT UNSIGNED DEFAULT 0 COMMENT '父级ID',
  `level` TINYINT NOT NULL COMMENT '层级：1省 2市 3县',
  `name` VARCHAR(100) NOT NULL COMMENT '名称',
  `code` VARCHAR(20) DEFAULT '' COMMENT '行政区划代码',
  `pinyin` VARCHAR(100) DEFAULT '' COMMENT '拼音',
  `status` TINYINT DEFAULT 1 COMMENT '状态：1启用 0禁用',
  `sort_order` INT DEFAULT 0 COMMENT '排序',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_parent_id (`parent_id`),
  INDEX idx_level (`level`),
  INDEX idx_status (`status`),
  INDEX idx_code (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='省市区地域表';

-- ============================================
-- 8. 行业关键词库表
-- ============================================
CREATE TABLE `industry_keywords` (
  `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  `keyword` VARCHAR(200) NOT NULL COMMENT '关键词',
  `category` VARCHAR(50) DEFAULT '' COMMENT '分类：产品/厂家/工程/价格',
  `search_volume` INT DEFAULT 0 COMMENT '搜索量',
  `competition` TINYINT DEFAULT 0 COMMENT '竞争度：0低 1中 2高',
  `status` TINYINT DEFAULT 1 COMMENT '状态：1启用 0禁用',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_keyword (`keyword`),
  INDEX idx_category (`category`),
  INDEX idx_status (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='行业关键词库表';

-- ============================================
-- 9. 长尾关键词表
-- ============================================
CREATE TABLE `longtail_keywords` (
  `id` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  `region_id` INT UNSIGNED NOT NULL COMMENT '县域ID',
  `keyword` VARCHAR(300) NOT NULL COMMENT '长尾关键词',
  `template` VARCHAR(200) DEFAULT '' COMMENT '组词模板',
  `search_volume` INT DEFAULT 0 COMMENT '搜索量',
  `status` TINYINT DEFAULT 1 COMMENT '状态：1启用 0禁用 2已过滤',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_region_id (`region_id`),
  INDEX idx_keyword (`keyword`(191)),
  INDEX idx_status (`status`),
  FOREIGN KEY (`region_id`) REFERENCES `regions`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='长尾关键词表';

-- ============================================
-- 10. AI文案模板表
-- ============================================
CREATE TABLE `article_templates` (
  `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(100) NOT NULL COMMENT '模板名称',
  `content` TEXT NOT NULL COMMENT '模板内容',
  `category` VARCHAR(50) DEFAULT '' COMMENT '分类',
  `variables` JSON COMMENT '变量列表',
  `status` TINYINT DEFAULT 1 COMMENT '状态：1启用 0禁用',
  `usage_count` INT DEFAULT 0 COMMENT '使用次数',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_category (`category`),
  INDEX idx_status (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI文案模板表';

-- ============================================
-- 11. 生成文章表
-- ============================================
CREATE TABLE `articles` (
  `id` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  `region_id` INT UNSIGNED NOT NULL COMMENT '县域ID',
  `template_id` INT UNSIGNED DEFAULT NULL COMMENT '模板ID',
  `title` VARCHAR(300) NOT NULL COMMENT '文章标题',
  `content` LONGTEXT NOT NULL COMMENT '文章内容',
  `keywords` VARCHAR(500) DEFAULT '' COMMENT '关键词',
  `duplicate_rate` DECIMAL(5,2) DEFAULT 0 COMMENT '重复率',
  `compliance_status` TINYINT DEFAULT 0 COMMENT '合规状态：0未检测 1通过 2不通过',
  `status` TINYINT DEFAULT 0 COMMENT '状态：0草稿 1待发布 2已发布 3发布失败',
  `publish_platform` VARCHAR(100) DEFAULT '' COMMENT '发布平台',
  `publish_url` VARCHAR(500) DEFAULT '' COMMENT '发布链接',
  `publish_error` TEXT COMMENT '发布错误信息',
  `retry_count` TINYINT DEFAULT 0 COMMENT '重试次数',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `published_at` DATETIME NULL COMMENT '发布时间',
  INDEX idx_region_id (`region_id`),
  INDEX idx_status (`status`),
  INDEX idx_compliance (`compliance_status`),
  INDEX idx_created (`created_at`),
  FOREIGN KEY (`region_id`) REFERENCES `regions`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`template_id`) REFERENCES `article_templates`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='生成文章表';

-- ============================================
-- 12. 分发平台表
-- ============================================
CREATE TABLE `platforms` (
  `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(100) NOT NULL COMMENT '平台名称',
  `code` VARCHAR(50) NOT NULL UNIQUE COMMENT '平台编码',
  `category` VARCHAR(50) DEFAULT '' COMMENT '分类：百度系/阿里系/腾讯系/字节系/博客/B2B/论坛',
  `has_api` TINYINT DEFAULT 0 COMMENT '是否有API：1是 0否',
  `api_endpoint` VARCHAR(255) DEFAULT '' COMMENT 'API端点',
  `daily_limit` INT DEFAULT 50 COMMENT '每日发布上限',
  `status` TINYINT DEFAULT 1 COMMENT '状态：1启用 0禁用',
  `sort_order` INT DEFAULT 0 COMMENT '排序',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_category (`category`),
  INDEX idx_status (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='分发平台表';

-- ============================================
-- 13. 平台账号表
-- ============================================
CREATE TABLE `platform_accounts` (
  `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  `platform_id` INT UNSIGNED NOT NULL COMMENT '平台ID',
  `account_name` VARCHAR(100) NOT NULL COMMENT '账号名称',
  `username` VARCHAR(100) DEFAULT '' COMMENT '登录用户名',
  `password_encrypted` VARCHAR(255) DEFAULT '' COMMENT '加密密码',
  `access_token` TEXT COMMENT '访问令牌',
  `refresh_token` TEXT COMMENT '刷新令牌',
  `token_expires_at` DATETIME NULL COMMENT '令牌过期时间',
  `cookie_data` TEXT COMMENT 'Cookie数据',
  `cookie_expires_at` DATETIME NULL COMMENT 'Cookie过期时间',
  `status` TINYINT DEFAULT 1 COMMENT '状态：1正常 0禁用 2冻结 3异常',
  `daily_publish_count` INT DEFAULT 0 COMMENT '今日发布数',
  `last_publish_at` DATETIME NULL COMMENT '最后发布时间',
  `fail_count` TINYINT DEFAULT 0 COMMENT '连续失败次数',
  `frozen_until` DATETIME NULL COMMENT '冻结至',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_platform_id (`platform_id`),
  INDEX idx_status (`status`),
  FOREIGN KEY (`platform_id`) REFERENCES `platforms`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='平台账号表';

-- ============================================
-- 14. 发布任务表
-- ============================================
CREATE TABLE `publish_tasks` (
  `id` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  `article_id` BIGINT UNSIGNED NOT NULL COMMENT '文章ID',
  `account_id` INT UNSIGNED NOT NULL COMMENT '账号ID',
  `platform_id` INT UNSIGNED NOT NULL COMMENT '平台ID',
  `status` TINYINT DEFAULT 0 COMMENT '状态：0待发布 1发布中 2成功 3失败 4重试中',
  `retry_count` TINYINT DEFAULT 0 COMMENT '重试次数',
  `error_message` TEXT COMMENT '错误信息',
  `publish_url` VARCHAR(500) DEFAULT '' COMMENT '发布链接',
  `scheduled_at` DATETIME NULL COMMENT '计划发布时间',
  `published_at` DATETIME NULL COMMENT '实际发布时间',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_article_id (`article_id`),
  INDEX idx_account_id (`account_id`),
  INDEX idx_status (`status`),
  INDEX idx_scheduled (`scheduled_at`),
  FOREIGN KEY (`article_id`) REFERENCES `articles`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`account_id`) REFERENCES `platform_accounts`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`platform_id`) REFERENCES `platforms`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='发布任务表';

-- ============================================
-- 15. 发布日志表
-- ============================================
CREATE TABLE `publish_logs` (
  `id` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  `task_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '任务ID',
  `article_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '文章ID',
  `account_id` INT UNSIGNED DEFAULT NULL COMMENT '账号ID',
  `platform_id` INT UNSIGNED DEFAULT NULL COMMENT '平台ID',
  `action` VARCHAR(50) NOT NULL COMMENT '操作：publish/retry/fail/success',
  `message` TEXT COMMENT '日志内容',
  `ip_address` VARCHAR(45) DEFAULT '' COMMENT 'IP地址',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_task_id (`task_id`),
  INDEX idx_article_id (`article_id`),
  INDEX idx_platform_id (`platform_id`),
  INDEX idx_action (`action`),
  INDEX idx_created (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='发布日志表';

-- ============================================
-- 16. 收录监控表
-- ============================================
CREATE TABLE `indexing_monitor` (
  `id` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  `article_id` BIGINT UNSIGNED NOT NULL COMMENT '文章ID',
  `keyword` VARCHAR(300) NOT NULL COMMENT '监控关键词',
  `platform` VARCHAR(50) DEFAULT 'baidu' COMMENT '搜索引擎',
  `is_indexed` TINYINT DEFAULT 0 COMMENT '是否收录：1是 0否',
  `ranking` INT DEFAULT 0 COMMENT '排名位置',
  `is_homepage` TINYINT DEFAULT 0 COMMENT '是否首页：1是 0否',
  `checked_at` DATETIME NULL COMMENT '检测时间',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_article_id (`article_id`),
  INDEX idx_keyword (`keyword`(191)),
  INDEX idx_is_indexed (`is_indexed`),
  INDEX idx_ranking (`ranking`),
  FOREIGN KEY (`article_id`) REFERENCES `articles`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='收录监控表';

-- ============================================
-- 17. 操作日志表
-- ============================================
CREATE TABLE `operation_logs` (
  `id` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT UNSIGNED DEFAULT NULL COMMENT '操作用户ID',
  `action` VARCHAR(100) NOT NULL COMMENT '操作类型',
  `module` VARCHAR(50) NOT NULL COMMENT '操作模块',
  `description` TEXT COMMENT '操作描述',
  `ip_address` VARCHAR(45) DEFAULT '' COMMENT 'IP地址',
  `user_agent` VARCHAR(500) DEFAULT '' COMMENT '用户代理',
  `request_data` JSON COMMENT '请求数据',
  `is_sensitive` TINYINT DEFAULT 0 COMMENT '是否敏感操作',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_user_id (`user_id`),
  INDEX idx_module (`module`),
  INDEX idx_action (`action`),
  INDEX idx_created (`created_at`),
  INDEX idx_sensitive (`is_sensitive`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作日志表';

-- ============================================
-- 18. 登录日志表
-- ============================================
CREATE TABLE `login_logs` (
  `id` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT UNSIGNED DEFAULT NULL COMMENT '用户ID',
  `username` VARCHAR(50) DEFAULT '' COMMENT '登录用户名',
  `ip_address` VARCHAR(45) DEFAULT '' COMMENT 'IP地址',
  `device` VARCHAR(200) DEFAULT '' COMMENT '设备信息',
  `login_result` TINYINT DEFAULT 0 COMMENT '登录结果：1成功 0失败',
  `fail_reason` VARCHAR(255) DEFAULT '' COMMENT '失败原因',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_user_id (`user_id`),
  INDEX idx_ip (`ip_address`),
  INDEX idx_result (`login_result`),
  INDEX idx_created (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='登录日志表';

-- ============================================
-- 19. 数据统计汇总表
-- ============================================
CREATE TABLE `statistics_daily` (
  `id` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  `stat_date` DATE NOT NULL COMMENT '统计日期',
  `region_count` INT DEFAULT 0 COMMENT '覆盖县域数',
  `keyword_count` INT DEFAULT 0 COMMENT '关键词数',
  `article_generated` INT DEFAULT 0 COMMENT '生成文章数',
  `article_published` INT DEFAULT 0 COMMENT '发布成功数',
  `article_failed` INT DEFAULT 0 COMMENT '发布失败数',
  `indexed_count` INT DEFAULT 0 COMMENT '收录数',
  `homepage_count` INT DEFAULT 0 COMMENT '首页数',
  `success_rate` DECIMAL(5,2) DEFAULT 0 COMMENT '成功率',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_date (`stat_date`),
  INDEX idx_date (`stat_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='每日数据统计表';

-- ============================================
-- 初始化数据
-- ============================================

-- 插入默认超级管理员 (密码: Trae@2024)
INSERT INTO `admin_users` (`username`, `password_hash`, `nickname`, `status`) VALUES
('admin', '$2b$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '超级管理员', 1);

-- 插入默认角色
INSERT INTO `roles` (`name`, `code`, `description`, `status`) VALUES
('超级管理员', 'super_admin', '拥有所有权限', 1),
('运营人员', 'operator', '负责内容发布和监控', 1),
('审核人员', 'auditor', '负责内容审核', 1);

-- 插入基础系统配置
INSERT INTO `system_configs` (`config_key`, `config_value`, `config_type`, `group_name`, `description`) VALUES
('brand_name', '优丁建材', 'string', 'basic', '品牌名称'),
('official_website', 'https://www.youdingjiancai.com', 'string', 'basic', '官网域名'),
('contact_phone', '400-XXX-XXXX', 'string', 'basic', '联系电话'),
('company_intro', '优丁建材 - 专业保温建材供应商', 'string', 'basic', '公司简介'),
('link_insert_position', 'end', 'string', 'link', '外链插入位置'),
('link_format', '?source={region}', 'string', 'link', '外链格式'),
('ai_model', 'default', 'string', 'ai', 'AI模型'),
('article_length', '800', 'number', 'ai', '文章字数'),
('rewrite_strength', 'medium', 'string', 'ai', '伪原创强度'),
('daily_limit_per_platform', '50', 'number', 'risk', '单平台日上限'),
('publish_interval_min', '5', 'number', 'risk', '发布间隔最小(分钟)'),
('publish_interval_max', '30', 'number', 'risk', '发布间隔最大(分钟)');

-- 插入分发平台
INSERT INTO `platforms` (`name`, `code`, `category`, `has_api`, `daily_limit`, `status`) VALUES
('百家号', 'baijiahao', '百度系', 1, 50, 1),
('百度知道', 'zhidao', '百度系', 0, 30, 1),
('百度贴吧', 'tieba', '百度系', 0, 20, 1),
('大鱼号', 'dayu', '阿里系', 1, 40, 1),
('搜狐号', 'sohu', '其他', 1, 40, 1),
('头条号', 'toutiao', '字节系', 1, 50, 1),
('企鹅号', '企鹅号', '腾讯系', 1, 40, 1),
('新浪博客', 'sina_blog', '博客', 0, 30, 1),
('慧聪网', 'hc360', 'B2B', 0, 20, 1),
('建材网', 'jiancai', 'B2B', 0, 20, 1);
