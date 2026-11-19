-- ============================================================
-- 索引优化实操：同一句 SQL 加索引前后的执行计划对比
-- 用途：面试现场可以打开 MySQL 直接演示，比嘴上说「我会优化」有力得多
-- 前置：先把 daily_metric 灌到 100 万行以上（见文件末尾造数脚本）
-- ============================================================

USE tk_shop;

-- ------------------------------------------------------------
-- 场景一：看板主查询 —— 某店近 30 天按日汇总 GMV
-- ------------------------------------------------------------
-- 加索引前（先删掉 idx_shop_date 试）
-- ALTER TABLE daily_metric DROP INDEX idx_shop_date;

EXPLAIN FORMAT=TREE
SELECT stat_date, SUM(gmv), SUM(orders)
FROM daily_metric
WHERE shop_id = 1 AND product_id IS NULL AND stat_date >= '2026-10-20'
GROUP BY stat_date
ORDER BY stat_date;

-- 预期（无 idx_shop_date）：
--   Table scan on daily_metric  ->  type=ALL, rows≈1,000,000, Extra=Using temporary
-- 预期（有 idx_shop_date）：
--   Index range scan on daily_metric using idx_shop_date
--   type=range, rows≈30, Extra=Using index condition
--
-- 关键点：索引最左列必须是 shop_id（等值），第二列 stat_date（范围），
-- 顺序反了（stat_date, shop_id）就只能走 date 范围扫描，等于白建。


-- ------------------------------------------------------------
-- 场景二：单品 GMV 排行 Top 10
-- ------------------------------------------------------------
EXPLAIN ANALYZE
SELECT p.id, p.title, SUM(m.gmv) AS gmv
FROM daily_metric m
JOIN product p ON p.id = m.product_id
WHERE m.shop_id = 1 AND m.stat_date >= '2026-10-20' AND m.product_id IS NOT NULL
GROUP BY p.id, p.title
ORDER BY gmv DESC
LIMIT 10;

-- 关键点：
-- 1. (shop_id, stat_date, gmv) 联合索引让 WHERE 段命中索引，
--    但 GROUP BY 仍会产生临时表 —— 这是聚合查询的固有成本，
--    所以真正的优化方向是「预聚合」，见场景四。
-- 2. JOIN 用 p.id（主键）驱动，不会出现 N+1。


-- ------------------------------------------------------------
-- 场景三：最左前缀 —— 为什么 idx_shop_date_gmv 能覆盖三种查询
-- ------------------------------------------------------------
-- 命中（用到 shop_id）
EXPLAIN SELECT * FROM daily_metric WHERE shop_id = 1;
-- 命中（shop_id + stat_date）
EXPLAIN SELECT * FROM daily_metric WHERE shop_id = 1 AND stat_date = '2026-11-01';
-- 命中（三列全用上，且 gmv 可走索引排序）
EXPLAIN SELECT * FROM daily_metric WHERE shop_id = 1 AND stat_date = '2026-11-01' ORDER BY gmv DESC;
-- 不命中（跳过最左列 stat_date，索引失效）
EXPLAIN SELECT * FROM daily_metric WHERE stat_date = '2026-11-01';


-- ------------------------------------------------------------
-- 场景四：真到千万级怎么办 —— 预聚合表
-- ------------------------------------------------------------
-- 思路：明细保留 90 天，日汇总/月汇总单独存，看板只查汇总表。
-- 这不是「索引能解决」的问题，是数据分层问题。
CREATE TABLE IF NOT EXISTS daily_metric_rollup (
  shop_id   INT UNSIGNED NOT NULL,
  stat_date DATE         NOT NULL,
  gmv       DECIMAL(12,2) NOT NULL DEFAULT 0,
  orders    INT          NOT NULL DEFAULT 0,
  visitors  INT          NOT NULL DEFAULT 0,
  PRIMARY KEY (shop_id, stat_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='看板预聚合表';

-- 每天凌晨由定时任务重算前一天：
-- INSERT INTO daily_metric_rollup (shop_id, stat_date, gmv, orders, visitors)
-- SELECT shop_id, stat_date, SUM(gmv), SUM(orders), SUM(visitors)
-- FROM daily_metric
-- WHERE product_id IS NULL AND stat_date = CURDATE() - INTERVAL 1 DAY
-- GROUP BY shop_id, stat_date
-- ON DUPLICATE KEY UPDATE gmv = VALUES(gmv), orders = VALUES(orders), visitors = VALUES(visitors);


-- ------------------------------------------------------------
-- 造数：把 daily_metric 灌到 100 万行用于压测
-- ------------------------------------------------------------
-- INSERT INTO daily_metric (shop_id, product_id, stat_date, gmv, orders, visitors)
-- WITH RECURSIVE seq AS (
--   SELECT 0 AS n UNION ALL SELECT n + 1 FROM seq WHERE n < 999
-- )
-- SELECT 1 + (n % 5), NULL, DATE_SUB(CURDATE(), INTERVAL (n % 365) DAY),
--        ROUND(RAND() * 10000, 2), FLOOR(RAND() * 300), FLOOR(RAND() * 6000)
-- FROM seq;
