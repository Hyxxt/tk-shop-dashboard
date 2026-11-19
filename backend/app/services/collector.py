"""数据采集。

结构上分成两块，这也是面试要讲的重点：「采集」和「入库」解耦。

  Adapter（取数）  ——  每个平台一个实现，返回统一结构
        ↓
  upsert（入库）   ——  按唯一键 UPSERT，重跑幂等，不会重复累加

为什么必须幂等：定时任务失败重试、补跑历史日期是常态。
如果用 INSERT，重跑一次 GMV 就翻倍，看板直接废掉。
所以 `daily_metric` 用 (shop_id, product_id, stat_date) 做唯一键，
入库走 ON DUPLICATE KEY UPDATE（MySQL）/ ON CONFLICT DO UPDATE（SQLite）。

真实抓取注意点（TikTok Shop 后台需要登录态）：
  1. 登录态用 storage_state 持久化，不要每次跑都登录；
  2. 分页要限速，别把账号跑封；
  3. 账号双因素/验证码走人工介入，不硬闯；
  4. 只采自己有权访问的后台数据，不碰第三方隐私数据。
"""
from __future__ import annotations

import csv
import random
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import engine
from app.models import CollectTask, DailyMetric, Product, SocialPost

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


class CollectError(RuntimeError):
    pass


# ---------------------------------------------------------------- adapters


def _playwright_available() -> bool:
    try:
        import playwright  # noqa: F401

        return True
    except ImportError:
        return False


def fetch_tiktok_shop(shop_name: str, stat_date: date) -> list[dict[str, Any]]:
    """TikTok Shop 后台抓取（真实实现）。

    需要先在本地跑一次 `python -m playwright install chromium`，
    并把登录后的 storage_state 存到 data/tk_state.json。
    没有安装 Playwright 时抛 CollectError，由上层降级到导出文件源。
    """
    if not _playwright_available():
        raise CollectError("未安装 playwright，请先 pip install playwright 并安装 chromium")

    from playwright.sync_api import sync_playwright

    state_file = DATA_DIR / "tk_state.json"
    if not state_file.exists():
        raise CollectError("缺少登录态 data/tk_state.json，请先手动登录导出 storage_state")

    url = f"https://seller.tiktokglobalshop.com/product/performance?date={stat_date.isoformat()}"
    rows: list[dict[str, Any]] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(storage_state=str(state_file))
        page = ctx.new_page()
        page.goto(url, wait_until="networkidle", timeout=60_000)
        page.wait_for_timeout(1500)
        # 后台表格结构会变，选择器集中放这里方便维护
        for tr in page.query_selector_all("table tbody tr"):
            cells = [c.inner_text().strip() for c in tr.query_selector_all("td")]
            if len(cells) < 5:
                continue
            rows.append(
                {
                    "sku": cells[0],
                    "title": cells[1],
                    "orders": _to_int(cells[2]),
                    "gmv": _to_float(cells[3]),
                    "visitors": _to_int(cells[4]),
                    "stat_date": stat_date,
                }
            )
        ctx.close()
        browser.close()
    return rows


def fetch_from_export_file(path: Path) -> list[dict[str, Any]]:
    """备用取数源：后台导出的 CSV。

    真实业务里很常见 —— 平台开放接口没权限、或者干脆靠人工导出，
    所以这条路径必须留着，采集器不能只有一条腿。
    """
    if not path.exists():
        raise CollectError(f"导出文件不存在：{path}")
    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for item in csv.DictReader(f):
            rows.append(
                {
                    "sku": item["sku"],
                    "title": item.get("title", ""),
                    "orders": _to_int(item.get("orders", 0)),
                    "gmv": _to_float(item.get("gmv", 0)),
                    "visitors": _to_int(item.get("visitors", 0)),
                    "stat_date": datetime.strptime(item["stat_date"], "%Y-%m-%d").date(),
                }
            )
    return rows


def _to_int(v: Any) -> int:
    try:
        return int(float(str(v).replace(",", "").replace("$", "").strip() or 0))
    except (TypeError, ValueError):
        return 0


def _to_float(v: Any) -> float:
    try:
        return float(str(v).replace(",", "").replace("$", "").strip() or 0)
    except (TypeError, ValueError):
        return 0.0


# ---------------------------------------------------------------- upsert


def _upsert_daily_metric(db: Session, rows: list[dict[str, Any]]) -> int:
    """批量 UPSERT，走数据库原生语法，一次往返。

    不用「查一下存不存在再决定 INSERT 还是 UPDATE」——
    那是 N+1 的变种，行数一多直接拖死。唯一键冲突交给数据库判断。
    """
    if not rows:
        return 0

    payload = [
        {
            "shop_id": r["shop_id"],
            "product_id": r.get("product_id"),
            "stat_date": r["stat_date"],
            "gmv": r["gmv"],
            "orders": r["orders"],
            "visitors": r["visitors"],
            "page_views": r.get("page_views", r["visitors"] * 3),
            "refund_amount": r.get("refund_amount", 0),
        }
        for r in rows
    ]

    dialect = engine.dialect.name
    if dialect == "mysql":
        from sqlalchemy.dialects.mysql import insert as dialect_insert

        stmt = dialect_insert(DailyMetric).values(payload)
        stmt = stmt.on_duplicate_key_update(
            gmv=stmt.inserted.gmv,
            orders=stmt.inserted.orders,
            visitors=stmt.inserted.visitors,
            page_views=stmt.inserted.page_views,
            refund_amount=stmt.inserted.refund_amount,
            updated_at=func.now(),
        )
    else:
        from sqlalchemy.dialects.sqlite import insert as dialect_insert

        stmt = dialect_insert(DailyMetric).values(payload)
        stmt = stmt.on_conflict_do_update(
            index_elements=["shop_id", "product_id", "stat_date"],
            set_={
                "gmv": stmt.excluded.gmv,
                "orders": stmt.excluded.orders,
                "visitors": stmt.excluded.visitors,
                "page_views": stmt.excluded.page_views,
                "refund_amount": stmt.excluded.refund_amount,
                "updated_at": func.now(),
            },
        )

    db.execute(stmt)
    db.commit()
    return len(payload)


def run_collect(db: Session, task: CollectTask) -> dict[str, Any]:
    """跑一个采集任务：取数 → 映射到本地商品 → UPSERT → 回写任务状态。"""
    task.status = "RUNNING"
    task.error_msg = None
    db.commit()

    try:
        source_rows = _fetch_by_source(task)
        if not source_rows:
            raise CollectError("采集结果为空，检查账号权限或页面结构是否变更")

        # 商品主数据先同步好，采集只负责指标，不负责建商品
        shop_id = _shop_id_of_task(db, task)
        shop_products = {
            p.sku: p for p in db.scalars(select(Product).where(Product.shop_id == shop_id)).all()
        }

        mapped: list[dict[str, Any]] = []
        for r in source_rows:
            prod = shop_products.get(r["sku"])
            if prod is None:
                continue  # 本地没有的商品先跳过，商品主数据由商品同步任务负责
            mapped.append({"shop_id": shop_id, "product_id": prod.id, **r})

        rows = _upsert_daily_metric(db, mapped)

        task.status = "OK"
        task.last_rows = rows
        task.last_run_at = datetime.now()
        db.commit()
        return {"task_id": task.id, "status": "OK", "rows": rows, "message": f"写入/更新 {rows} 行"}
    except CollectError as e:
        task.status = "FAILED"
        task.error_msg = str(e)
        task.last_run_at = datetime.now()
        db.commit()
        return {"task_id": task.id, "status": "FAILED", "rows": 0, "message": str(e)}
    except Exception as e:  # noqa: BLE001
        task.status = "FAILED"
        task.error_msg = f"{type(e).__name__}: {e}"
        task.last_run_at = datetime.now()
        db.commit()
        return {"task_id": task.id, "status": "FAILED", "rows": 0, "message": str(e)}


def _shop_id_of_task(db: Session, task: CollectTask) -> int:
    from app.models import Shop

    shop = db.scalar(select(Shop).where(Shop.name == task.target))
    if shop is None:
        raise CollectError(f"本地没有店铺主数据：{task.target}")
    return shop.id


def _fetch_by_source(task: CollectTask) -> list[dict[str, Any]]:
    """按 source 分发到具体 adapter；TikTok 失败时降级到导出文件。"""
    if task.source == "tk_shop":
        for day_offset in range(1, 4):
            stat_date = date.today() - timedelta(days=day_offset)
            try:
                return fetch_tiktok_shop(task.target, stat_date)
            except CollectError:
                export = DATA_DIR / f"export_{task.target}_{stat_date.isoformat()}.csv"
                if export.exists():
                    return fetch_from_export_file(export)
                if day_offset == 3:
                    raise
        return []
    if task.source == "export":
        return fetch_from_export_file(DATA_DIR / task.target)
    raise CollectError(f"暂不支持的采集源：{task.source}")


# ---------------------------------------------------------------- mock 源


def make_export_mock(shop_name: str, stat_date: date, days: int = 1) -> Path:
    """生成一份模拟的后台导出 CSV，给没有登录态的机器演示用。

    注意：这是造的演示数据，不是真实平台数据，README 里写清楚。
    """
    rng = random.Random(f"{shop_name}{stat_date}")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"export_{shop_name}_{stat_date.isoformat()}.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["sku", "title", "orders", "gmv", "visitors", "stat_date"])
        for i in range(8):
            orders = rng.randint(5, 120)
            price = rng.uniform(9, 89)
            w.writerow(
                [
                    f"SKU-{shop_name[:4].upper()}-{i:03d}",
                    f"Demo Product {i}",
                    orders,
                    round(orders * price, 2),
                    orders * rng.randint(8, 30),
                    stat_date.isoformat(),
                ]
            )
    return path


def seed_social_posts(db: Session, count_per_account: int = 20) -> int:
    """造社媒内容数据，用于看板矩阵分析。"""
    accounts = {
        "TIKTOK": ["@glowcare.us", "@glowcare_official", "@beautyfind.uk"],
        "INSTAGRAM": ["@glowcare.ig", "@skinlab.daily"],
        "FACEBOOK": ["GlowCare Page"],
        "YOUTUBE": ["GlowCare Studio"],
    }
    rng = random.Random(20261119)
    n = 0
    for platform, names in accounts.items():
        for name in names:
            for i in range(count_per_account):
                post_id = f"{platform[:2].lower()}-{abs(hash(name)) % 100000}-{i:04d}"
                views = rng.randint(2_000, 480_000)
                likes = int(views * rng.uniform(0.02, 0.11))
                comments = int(likes * rng.uniform(0.02, 0.09))
                shares = int(likes * rng.uniform(0.01, 0.06))
                exists = db.scalar(
                    select(func.count(SocialPost.id)).where(
                        SocialPost.platform == platform, SocialPost.post_id == post_id
                    )
                )
                if exists:
                    continue
                db.add(
                    SocialPost(
                        platform=platform,
                        account_name=name,
                        post_id=post_id,
                        content_type="VIDEO" if platform in ("TIKTOK", "YOUTUBE") else "IMAGE",
                        published_at=datetime.now() - timedelta(days=rng.randint(0, 30), hours=rng.randint(0, 23)),
                        views=views,
                        likes=likes,
                        comments=comments,
                        shares=shares,
                        saves=int(likes * rng.uniform(0.05, 0.2)),
                        duration_sec=rng.randint(15, 90),
                    )
                )
                n += 1
    db.commit()
    return n
