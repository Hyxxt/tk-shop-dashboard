"""经营指标聚合。

这里刻意不用 ORM 逐条遍历 —— 看板查询全部下推到 SQL 聚合，
一次往返拿完，前端拿到的就是画图要的数组。
这也是「接口响应速度」这条 JD 要求最直接的落点：
  1. 指标计算在数据库侧完成（SUM/GROUP BY），Python 只做格式化；
  2. 环比用一条 CASE WHEN 分桶的 SQL 同时算出本期和上期，避免两次往返；
  3. 列表类接口一次 JOIN 取商品名，不做「先查主表再循环查子表」的 N+1。
"""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import Integer, case, func, select
from sqlalchemy.orm import Session

from app.models import DailyMetric, Product, SocialPost, Shop


def _rate(numerator: float, denominator: float) -> float:
    return round(numerator / denominator * 100, 2) if denominator else 0.0


def get_overview(
    db: Session, shop_id: int | None, days: int = 30
) -> dict[str, float | int]:
    today = date.today()
    cur_end = today
    cur_start = today - timedelta(days=days - 1)
    prev_end = cur_start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=days - 1)

    in_cur = DailyMetric.stat_date.between(cur_start, cur_end)
    in_prev = DailyMetric.stat_date.between(prev_start, prev_end)

    stmt = select(
        func.coalesce(func.sum(case((in_cur, DailyMetric.gmv), else_=0)), 0).label("cur_gmv"),
        func.coalesce(func.sum(case((in_prev, DailyMetric.gmv), else_=0)), 0).label("prev_gmv"),
        func.coalesce(
            func.sum(case((in_cur, DailyMetric.orders), else_=0)), 0
        ).cast(Integer).label("cur_orders"),
        func.coalesce(
            func.sum(case((in_prev, DailyMetric.orders), else_=0)), 0
        ).cast(Integer).label("prev_orders"),
        func.coalesce(
            func.sum(case((in_cur, DailyMetric.visitors), else_=0)), 0
        ).cast(Integer).label("cur_visitors"),
        func.coalesce(
            func.sum(case((in_cur, DailyMetric.refund_amount), else_=0)), 0
        ).label("cur_refund"),
    ).where(
        DailyMetric.product_id.is_(None),  # 只取店铺级汇总行，避免和单品行重复累加
        DailyMetric.stat_date.between(prev_start, cur_end),
    )
    if shop_id:
        stmt = stmt.where(DailyMetric.shop_id == shop_id)

    row = db.execute(stmt).one()
    cur_gmv = float(row.cur_gmv)
    cur_orders = int(row.cur_orders)
    cur_visitors = int(row.cur_visitors)
    prev_gmv = float(row.prev_gmv)
    prev_orders = int(row.prev_orders)

    return {
        "gmv": round(cur_gmv, 2),
        "orders": cur_orders,
        "visitors": cur_visitors,
        "conversion_rate": _rate(cur_orders, cur_visitors),
        "avg_order_value": round(cur_gmv / cur_orders, 2) if cur_orders else 0.0,
        "refund_rate": _rate(float(row.cur_refund), cur_gmv),
        "gmv_growth": _rate(cur_gmv - prev_gmv, prev_gmv),
        "orders_growth": _rate(cur_orders - prev_orders, prev_orders),
    }


def get_trend(
    db: Session, shop_id: int | None, days: int = 30
) -> list[dict[str, object]]:
    today = date.today()
    start = today - timedelta(days=days - 1)

    stmt = (
        select(
            DailyMetric.stat_date,
            func.sum(DailyMetric.gmv).label("gmv"),
            func.sum(DailyMetric.orders).label("orders"),
            func.sum(DailyMetric.visitors).label("visitors"),
        )
        .where(
            DailyMetric.product_id.is_(None),
            DailyMetric.stat_date >= start,
        )
        .group_by(DailyMetric.stat_date)
        .order_by(DailyMetric.stat_date)
    )
    if shop_id:
        stmt = stmt.where(DailyMetric.shop_id == shop_id)

    return [
        {
            "stat_date": r.stat_date,
            "gmv": round(float(r.gmv or 0), 2),
            "orders": int(r.orders or 0),
            "visitors": int(r.visitors or 0),
        }
        for r in db.execute(stmt).all()
    ]


def get_top_products(
    db: Session,
    shop_id: int | None,
    days: int = 30,
    limit: int = 10,
    order_by: str = "gmv",
) -> list[dict[str, object]]:
    """单品排行。

    一次 JOIN 把商品标题带出来 —— 如果先查 metric 再循环查 product，
    10 条就是 11 次往返，这就是典型的 N+1。
    """
    today = date.today()
    start = today - timedelta(days=days - 1)
    order_col = {
        "gmv": func.sum(DailyMetric.gmv),
        "orders": func.sum(DailyMetric.orders),
        "visitors": func.sum(DailyMetric.visitors),
    }.get(order_by, func.sum(DailyMetric.gmv))

    stmt = (
        select(
            Product.id,
            Product.title,
            Product.sku,
            Product.category,
            Shop.name.label("shop_name"),
            func.sum(DailyMetric.gmv).label("gmv"),
            func.sum(DailyMetric.orders).label("orders"),
            func.sum(DailyMetric.visitors).label("visitors"),
        )
        .join(Product, Product.id == DailyMetric.product_id)
        .join(Shop, Shop.id == Product.shop_id)
        .where(DailyMetric.stat_date >= start, DailyMetric.product_id.is_not(None))
        .group_by(Product.id, Product.title, Product.sku, Product.category, Shop.name)
        .order_by(order_col.desc())
        .limit(limit)
    )
    if shop_id:
        stmt = stmt.where(DailyMetric.shop_id == shop_id)

    out = []
    for r in db.execute(stmt).all():
        orders = int(r.orders or 0)
        visitors = int(r.visitors or 0)
        out.append(
            {
                "product_id": r.id,
                "title": r.title,
                "sku": r.sku,
                "category": r.category,
                "shop_name": r.shop_name,
                "gmv": round(float(r.gmv or 0), 2),
                "orders": orders,
                "visitors": visitors,
                "conversion_rate": _rate(orders, visitors),
            }
        )
    return out


def get_social_summary(db: Session) -> list[dict[str, object]]:
    stmt = (
        select(
            SocialPost.platform,
            func.count(SocialPost.id).label("posts"),
            func.sum(SocialPost.views).label("views"),
            func.sum(SocialPost.likes).label("likes"),
            func.sum(SocialPost.comments).label("comments"),
            func.sum(SocialPost.shares).label("shares"),
        )
        .group_by(SocialPost.platform)
        .order_by(func.sum(SocialPost.views).desc())
    )
    rows = db.execute(stmt).all()
    out = []
    for r in rows:
        views = int(r.views or 0)
        interactions = int(r.likes or 0) + int(r.comments or 0) + int(r.shares or 0)
        out.append(
            {
                "platform": r.platform,
                "posts": int(r.posts or 0),
                "views": views,
                "likes": int(r.likes or 0),
                "comments": int(r.comments or 0),
                "shares": int(r.shares or 0),
                "engagement_rate": _rate(interactions, views),
                "avg_views": round(views / r.posts, 1) if r.posts else 0.0,
            }
        )
    return out


def list_shops_with_kpi(db: Session, days: int = 30) -> list[dict[str, object]]:
    """店铺列表带 KPI。

    用 LEFT JOIN + 子查询聚合，一条 SQL 出结果；
    不用「查店铺列表 → 循环每条查 GMV」。
    """
    today = date.today()
    start = today - timedelta(days=days - 1)
    sub = (
        select(
            DailyMetric.shop_id.label("sid"),
            func.sum(DailyMetric.gmv).label("gmv"),
            func.sum(DailyMetric.orders).label("orders"),
            func.sum(DailyMetric.visitors).label("visitors"),
        )
        .where(
            DailyMetric.product_id.is_(None),
            DailyMetric.stat_date >= start,
        )
        .group_by(DailyMetric.shop_id)
        .subquery()
    )
    stmt = (
        select(
            Shop.id,
            Shop.platform,
            Shop.name,
            Shop.region,
            Shop.currency,
            Shop.health_score,
            func.coalesce(sub.c.gmv, 0).label("gmv"),
            func.coalesce(sub.c.orders, 0).label("orders"),
            func.coalesce(sub.c.visitors, 0).label("visitors"),
        )
        .outerjoin(sub, sub.c.sid == Shop.id)
        .order_by(func.coalesce(sub.c.gmv, 0).desc())
    )
    return [
        {
            "id": r.id,
            "platform": r.platform,
            "name": r.name,
            "region": r.region,
            "currency": r.currency,
            "health_score": r.health_score,
            "gmv": round(float(r.gmv), 2),
            "orders": int(r.orders),
            "visitors": int(r.visitors),
            "conversion_rate": _rate(int(r.orders), int(r.visitors)),
        }
        for r in db.execute(stmt).all()
    ]
