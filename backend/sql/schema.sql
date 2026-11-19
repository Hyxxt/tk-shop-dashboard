-- ============================================================
-- TK Shop 智能运营看板 · MySQL 8.0 建表脚本
-- 与 ORM（backend/app/models）保持一一对应，可用于生产库初始化
-- 字符集统一 utf8mb4（店铺名、商品名会有 emoji 和多语言）
-- ============================================================

CREATE DATABASE IF NOT EXISTS tk_shop
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_0900_ai_ci;

USE tk_shop;

-- ------------------------------------------------------------
-- 1. 店铺 / 账号载体
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS shop (
  id           INT UNSIGNED NOT NULL AUTO_INCREMENT,
  platform     VARCHAR(32)  NOT NULL COMMENT 'TIKTOK_SHOP/INSTAGRAM/FACEBOOK/YOUTUBE',
  name         VARCHAR(128) NOT NULL,
  region       VARCHAR(16)  NOT NULL DEFAULT 'US' COMMENT 'US/UK/SEA',
  currency     VARCHAR(8)   NOT NULL DEFAULT 'USD',
  health_score TINYINT      NOT NULL DEFAULT 0 COMMENT '店铺健康分 0-100',
  opened_at    DATE         NULL,
  created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_platform_name (platform, name),
  KEY idx_shop_platform (platform)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='店铺与社媒账号';

-- ------------------------------------------------------------
-- 2. 商品
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS product (
  id         INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  shop_id    INT UNSIGNED  NOT NULL,
  sku        VARCHAR(64)   NOT NULL,
  title      VARCHAR(255)  NOT NULL,
  category   VARCHAR(64)   NOT NULL DEFAULT 'UNKNOWN',
  price      DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '金额一律 DECIMAL，不用 FLOAT',
  stock      INT           NOT NULL DEFAULT 0,
  status     VARCHAR(16)   NOT NULL DEFAULT 'ON_SALE',
  created_at DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_shop_sku (shop_id, sku),
  KEY idx_shop_category_price (shop_id, category, price),
  CONSTRAINT fk_product_shop FOREIGN KEY (shop_id) REFERENCES shop (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品主数据';

-- ------------------------------------------------------------
-- 3. 每日经营快照（核心大表）
--    product_id 为 NULL 表示店铺级汇总行，非 NULL 表示单品行。
--    MySQL 唯一索引对 NULL 不生效，所以店铺行用 product_id = 0 也不行，
--    这里改用「生成列」把 NULL 归一成 0，保证唯一键真正生效。
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS daily_metric (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  shop_id       INT UNSIGNED    NOT NULL,
  product_id    INT UNSIGNED    NULL COMMENT 'NULL = 店铺级汇总',
  product_key   INT UNSIGNED    AS (IFNULL(product_id, 0)) STORED COMMENT '为唯一键归一 NULL',
  stat_date     DATE            NOT NULL,
  gmv           DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
  orders        INT             NOT NULL DEFAULT 0,
  visitors      INT             NOT NULL DEFAULT 0,
  page_views    INT             NOT NULL DEFAULT 0,
  refund_amount DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
  created_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_shop_product_date (shop_id, product_key, stat_date),
  KEY idx_shop_date (shop_id, stat_date),
  KEY idx_shop_date_gmv (shop_id, stat_date, gmv),
  KEY idx_product_date (product_id, stat_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='每日经营指标快照';

-- ------------------------------------------------------------
-- 4. 海外社媒内容
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS social_post (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  platform     VARCHAR(32)  NOT NULL,
  account_name VARCHAR(128) NOT NULL,
  post_id      VARCHAR(64)  NOT NULL COMMENT '平台侧内容 ID',
  content_type VARCHAR(16)  NOT NULL DEFAULT 'VIDEO',
  published_at DATETIME     NOT NULL,
  views        INT          NOT NULL DEFAULT 0,
  likes        INT          NOT NULL DEFAULT 0,
  comments     INT          NOT NULL DEFAULT 0,
  shares       INT          NOT NULL DEFAULT 0,
  saves        INT          NOT NULL DEFAULT 0,
  duration_sec INT          NOT NULL DEFAULT 0,
  created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_platform_post (platform, post_id),
  KEY idx_account_published (account_name, published_at),
  KEY idx_platform_published (platform, published_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='社媒矩阵内容表现';

-- ------------------------------------------------------------
-- 5. 采集任务
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS collect_task (
  id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
  source      VARCHAR(32)  NOT NULL COMMENT 'tk_shop/export',
  target      VARCHAR(255) NOT NULL COMMENT '店铺名或导出文件名',
  `schedule`  VARCHAR(32)  NOT NULL DEFAULT '0 2 * * *',
  status      VARCHAR(16)  NOT NULL DEFAULT 'IDLE' COMMENT 'IDLE/RUNNING/OK/FAILED',
  last_run_at DATETIME     NULL,
  last_rows   INT          NOT NULL DEFAULT 0,
  error_msg   TEXT         NULL,
  created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_source_target (source, target),
  KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='采集任务与运行状态';
