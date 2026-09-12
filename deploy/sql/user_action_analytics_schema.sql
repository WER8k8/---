-- UserActionAnalyzePlatform 结果库（与上游 README 表结构一致）
-- 部署：mysql < deploy/sql/user_action_analytics_schema.sql

CREATE DATABASE IF NOT EXISTS user_action_analytics DEFAULT CHARSET utf8mb4;
USE user_action_analytics;

CREATE TABLE IF NOT EXISTS `task` (
  `task_id` int NOT NULL AUTO_INCREMENT,
  `task_name` varchar(255) DEFAULT NULL,
  `create_time` varchar(255) DEFAULT NULL,
  `start_time` varchar(255) DEFAULT NULL,
  `finish_time` varchar(255) DEFAULT NULL,
  `task_type` varchar(255) DEFAULT NULL,
  `task_status` varchar(255) DEFAULT NULL,
  `task_param` text,
  PRIMARY KEY (`task_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `session_aggr_stat` (
  `task_id` int NOT NULL,
  `session_count` int DEFAULT NULL,
  `1s_3s` double DEFAULT NULL,
  `4s_6s` double DEFAULT NULL,
  `7s_9s` double DEFAULT NULL,
  `10s_30s` double DEFAULT NULL,
  `30s_60s` double DEFAULT NULL,
  `1m_3m` double DEFAULT NULL,
  `3m_10m` double DEFAULT NULL,
  `10m_30m` double DEFAULT NULL,
  `30m` double DEFAULT NULL,
  `1_3` double DEFAULT NULL,
  `4_6` double DEFAULT NULL,
  `7_9` double DEFAULT NULL,
  `10_30` double DEFAULT NULL,
  `30_60` double DEFAULT NULL,
  `60` double DEFAULT NULL,
  PRIMARY KEY (`task_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `session_random_extract` (
  `task_id` int NOT NULL,
  `session_id` varchar(255) DEFAULT NULL,
  `start_time` varchar(50) DEFAULT NULL,
  `end_time` varchar(50) DEFAULT NULL,
  `search_keywords` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`task_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `top10_category` (
  `task_id` int NOT NULL,
  `category_id` int DEFAULT NULL,
  `click_count` int DEFAULT NULL,
  `order_count` int DEFAULT NULL,
  `pay_count` int DEFAULT NULL,
  PRIMARY KEY (`task_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `top10_category_session` (
  `task_id` int NOT NULL,
  `category_id` int DEFAULT NULL,
  `session_id` varchar(255) DEFAULT NULL,
  `click_count` int DEFAULT NULL,
  PRIMARY KEY (`task_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `session_detail` (
  `task_id` int NOT NULL,
  `user_id` int DEFAULT NULL,
  `session_id` varchar(255) DEFAULT NULL,
  `page_id` int DEFAULT NULL,
  `action_time` varchar(255) DEFAULT NULL,
  `search_keyword` varchar(255) DEFAULT NULL,
  `click_category_id` int DEFAULT NULL,
  `click_product_id` int DEFAULT NULL,
  `order_category_ids` varchar(255) DEFAULT NULL,
  `order_product_ids` varchar(255) DEFAULT NULL,
  `pay_category_ids` varchar(255) DEFAULT NULL,
  `pay_product_ids` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`task_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 页面单跳转化（Sidecar 从 session_detail 聚合写入）
CREATE TABLE IF NOT EXISTS `page_conversion_stat` (
  `task_id` int NOT NULL,
  `from_page` varchar(64) NOT NULL,
  `to_page` varchar(64) NOT NULL,
  `transition_count` int DEFAULT 0,
  `conversion_rate` double DEFAULT 0,
  PRIMARY KEY (`task_id`, `from_page`, `to_page`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
