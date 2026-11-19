# TK Shop 智能运营看板

TikTok Shop 与海外社媒矩阵（Instagram / Facebook / YouTube）的经营数据看板。
覆盖**数据采集 → 清洗入库 → 指标聚合 → 前端可视化 → 权限控制**完整闭环。

**在线演示：https://tk-shop-dashboard.onrender.com**
（免费实例 15 分钟无请求会休眠，首次打开约 50 秒冷启动）

- 仓库：https://github.com/Hyxxt/tk-shop-dashboard
- API 文档：https://tk-shop-api.onrender.com/docs
- 部署说明：[docs/DEPLOY.md](docs/DEPLOY.md)（Render Blueprint，前端 + 后端一起拉起来）
- 演示账号：`admin / admin123`（全权限）、`viewer / viewer123`（只读，可验证 403）

> 数据说明：本项目所有经营数据均为**模拟数据**，用于演示技术链路，不含任何真实平台经营数据，也不涉及任何平台私有接口。

![看板](docs/shots/02-dashboard.png)

## 技术栈

| 层 | 选型 |
|---|---|
| 前端 | Vue 3 + TypeScript + Vite + vue-router（权限码动态菜单） |
| 后端 | Python 3.13 + FastAPI + SQLAlchemy 2.0（Mapped 声明式） |
| 数据库 | MySQL 8.0 / SQLite（同一套 ORM，切 `DATABASE_URL` 即可） |
| 采集 | Playwright（真实后台）+ CSV 导出兜底 + 数据库原生 UPSERT |
| 图表 | 手写 SVG（无 ECharts 依赖，体积 102KB gzip 40KB） |

## 快速开始

```bash
# 1. 后端（默认 SQLite，零配置，首次启动自动灌演示数据）
cd backend
pip install -r requirements.txt
python run.py            # http://127.0.0.1:8000/docs

# 2. 前端
cd frontend
npm install
npm run dev              # http://localhost:5173
```

**演示账号**

| 账号 | 密码 | 权限 |
|---|---|---|
| `admin` | `admin123` | 全部 7 个权限码，可执行采集 |
| `viewer` | `viewer123` | 5 个只读权限码，无 `collect:run` / `system:admin` |

用 viewer 登录可以现场验证权限链路：侧边栏少一项、采集按钮置灰、手敲 `#/system` 被守卫弹回、直接调接口返回 403。

### 切 MySQL

```bash
mysql -uroot -p < backend/sql/schema.sql     # 建库建表
set DATABASE_URL=mysql+pymysql://root:123456@127.0.0.1:3306/tk_shop?charset=utf8mb4
python run.py
```

ORM 与 SQL DDL 一一对应，切库不用改一行业务代码。

## 线上部署状态

| 项 | 地址 / 说明 |
|---|---|
| 前端 | https://tk-shop-dashboard.onrender.com |
| 后端 | https://tk-shop-api.onrender.com （`/docs` 可看接口文档） |
| 数据库 | SQLite，容器重启后 `AUTO_SEED=1` 自动重灌演示数据 |
| 配置 | `render.yaml`（Blueprint），`docs/verify-online.js`（生产站点浏览器验收脚本） |

`docs/verify-online.js` 是对**生产环境**跑的真实浏览器验收，实测结果：

- 指标卡 `$334.9k / 8,786 / 15.5万 / $38.12`，折线图 30 个数据点，店铺列表 5 行；
- admin 账号采集按钮可用，viewer 账号按钮 `disabled=true`；
- viewer 登录后侧边栏自动少「数据规模」，手敲 `#/system` 被守卫弹回看板；
- console 零报错、零失败请求，`access-control-allow-origin: *` 正常返回。

## 目录结构

```
backend/
  app/
    core/        config.py（配置） db.py（引擎/会话）
    models/      5 张表的 ORM 定义，索引写在 __table_args__
    schemas/     Pydantic 出入参
    services/    metrics.py（指标聚合） collector.py（采集） seed.py（演示数据）
    api/         auth.py（认证+权限码） __init__.py（路由）
  sql/
    schema.sql        MySQL 8 建表脚本（含生成列、联合索引、注释）
    explain_demo.sql  索引优化前后对比 + 造 100 万行压测数据
frontend/
  src/
    api/         http.ts（拦截器） index.ts（接口 + 类型）
    router/      路由表即菜单，meta.perm 挂权限码
    stores/      auth.ts（登录态 + hasPerm）
    layouts/     BasicLayout.vue（侧边栏 / 顶栏）
    views/       Login / Dashboard / ShopList / TopProducts / Social / Collect / System
    components/  StatCard / LineChart / BarList / DonutChart（均为手写 SVG）
docs/
  shot.js        交互截图脚本（Playwright + 系统 Edge）
  shots/         各页面截图
```

## 四个可以深讲的技术点

### 1. 数据建模：一张表两种粒度

`daily_metric` 同时存**店铺级汇总**（`product_id = NULL`）和**商品级明细**（`product_id` 非空）。

- 看板主查询只扫店铺行，行数 = 店铺数 × 天数，不受商品数量影响；
- 单品排行扫明细行，`JOIN product` 一次取齐；
- 唯一键 `(shop_id, product_id, stat_date)` 保证采集重跑幂等。

MySQL 的唯一索引对 `NULL` 不生效（多个 NULL 不算重复），所以 DDL 里加了生成列
`product_key = IFNULL(product_id, 0)` 并把唯一键建在它上面 —— 这一点在 SQLite 与 MySQL
之间行为不同，是最容易踩的坑，`sql/schema.sql` 里有注释说明。

### 2. 索引：都来自真实查询模式

| 索引 | 服务的查询 |
|---|---|
| `uk_shop_product_date` | 采集幂等（UPSERT 冲突判定） |
| `idx_shop_date_gmv` | 看板区间聚合 + 单品排行排序 |
| `idx_shop_category_price` | 商品列表「店铺 → 类目 → 价格」 |
| `idx_platform_post` | 社媒内容去重 |

最左前缀原则：`(shop_id, stat_date, gmv)` 能服务 `WHERE shop_id=?`、
`WHERE shop_id=? AND stat_date=?`、以及三列全用上并排序；
但 `WHERE stat_date=?` 单独用会索引失效 —— `explain_demo.sql` 里三种情况都写了 `EXPLAIN`。

**千万级以后索引救不了聚合。** 真正的解法是预聚合表 `daily_metric_rollup`，
看板只查日汇总，明细留 90 天。这是数据分层问题，不是加索引能解决的。

### 3. 接口：把计算下推到数据库

- 环比用一条 `CASE WHEN` 分桶 SQL 同时算本期和上期，省一次往返；
- 单品排行 `JOIN product` 一次拿标题，不做「查主表 → 循环查子表」的 N+1；
- 所有金额在 SQL 侧 `SUM`，Python 只做格式化与百分比换算；
- 分页必须带稳定排序（`ORDER BY product.id`），否则翻页会重复或漏行。

### 4. 采集：采集与入库解耦

```
Adapter（取数）  →  upsert（入库）
Playwright / CSV      ON DUPLICATE KEY UPDATE
```

- **为什么必须幂等**：定时任务失败重试、补跑历史是常态。用 `INSERT` 重跑一次 GMV 就翻倍，
  看板直接废掉。所以走数据库原生 UPSERT，一次往返批量写入。
- **两条取数路径**：Playwright 抓后台需要登录态（`storage_state` 持久化），
  平台没开接口时用后台导出 CSV 兜底。采集器不能只有一条腿。
- **失败要可见**：任务表有 `status / last_run_at / last_rows / error_msg`，前端能直接看到哪次失败。

真实抓取注意：登录态持久化、分页限速、验证码人工介入、只采自己有权限访问的后台数据。

## 权限模型：三道锁

中后台的权限不是「把按钮藏起来」。这个项目做了三层，缺一不可：

1. **菜单层** — 侧边栏由路由表按 `meta.perm` 过滤生成，没权限的菜单不渲染；
2. **路由层** — `router.beforeEach` 校验 `to.meta.perm`，手敲 URL 也进不去；
3. **接口层** — FastAPI 依赖 `require_perm("collect:run")`，绕过前端直接调接口返回 403。

前两层是体验，第三层才是安全。

## 接口一览

| 方法 | 路径 | 权限码 |
|---|---|---|
| POST | `/api/auth/login` | — |
| GET | `/api/dashboard/overview?shop_id&days` | `dashboard:view` |
| GET | `/api/dashboard/trend` | `dashboard:view` |
| GET | `/api/dashboard/top-products?order_by` | `product:view` |
| GET | `/api/shops` | `shop:view` |
| GET | `/api/shops/{id}/products` | `product:view` |
| GET | `/api/social/summary` | `social:view` |
| GET | `/api/collect/tasks` | `collect:view` |
| POST | `/api/collect/tasks/{id}/run` | `collect:run` |
| GET | `/api/system/stats` | `system:admin` |

完整文档：`http://127.0.0.1:8000/docs`

## 面试可能被追问的点

**Q：为什么金额用 DECIMAL 不用 FLOAT？**
浮点在求和时会产生精度漂移，GMV 累加到百万级后误差会体现在报表上。DECIMAL 是定点数，精确。

**Q：店铺级和商品级为什么不分两张表？**
分表会导致「店铺 GMV ≠ 商品 GMV 求和」的对账问题（退款、优惠券分摊在店铺级）。
同表 + 两种粒度，口径统一，代价是查询时必须显式带 `product_id IS NULL` 过滤 —— 这个约束写在 service 层。

**Q：采集怎么保证不重复？**
唯一键 + 数据库原生 UPSERT，冲突即更新，不冲突即插入。重跑 100 次结果一致。

**Q：数据量涨到 5000 万行怎么办？**
三步：① 明细表按月分区（`PARTITION BY RANGE (TO_DAYS(stat_date))`）；② 上预聚合表，看板只查汇总；
③ 冷数据归档到对象存储，热数据保留 90 天。索引在这个量级只能解决点查，解决不了全区间聚合。

**Q：为什么前端不用 ECharts？**
这个场景只有折线、条形、环形三种图，手写 SVG 约 200 行，构建产物 40KB gzip。
引 ECharts 是 300KB+。中小项目里，图表库的维护成本往往大于收益。

**Q：接口慢怎么排查？**
先看慢查询日志定位 SQL → `EXPLAIN` 看 type 和 rows → 判断是缺索引、索引失效（函数运算/隐式转换/最左前缀断裂）
还是数据量问题 → 前者加索引，后者改架构（预聚合 / 缓存 / 异步）。

## 已知限制

- 认证是演示级的固定 token，生产要换 JWT + 刷新令牌；
- 采集器只实现了 TikTok Shop 的后台适配和一个 CSV 通用源，其余平台留了扩展位；
- 没有单元测试，验证靠 `docs/shot.js` 的端到端交互脚本 + 接口冒烟；
- 数据为模拟数据。
