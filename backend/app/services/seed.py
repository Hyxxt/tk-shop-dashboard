"""演示数据初始化。

造的是「看起来像真店铺」的数据：有增长趋势、有周末波动、有爆品和滞销品，
这样前端看板不会是一堆平直线，面试演示才有得讲。

注意：全部为模拟数据，不代表任何真实平台经营数据。
"""
from __future__ import annotations

import random
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import CollectTask, DailyMetric, Product, Shop
from app.services.collector import seed_social_posts

SHOPS = [
    # (platform, name, region, currency, health, 日单量基数)
    ("TIKTOK_SHOP", "GlowCare US", "US", "USD", 86, 220),
    ("TIKTOK_SHOP", "GlowCare UK", "UK", "GBP", 74, 130),
    ("TIKTOK_SHOP", "AuraSkin SEA", "SEA", "USD", 68, 90),
    ("INSTAGRAM", "glowcare.ig", "US", "USD", 62, 40),
    ("FACEBOOK", "GlowCare Page", "US", "USD", 55, 25),
]

CATEGORIES = ["SKINCARE", "MAKEUP", "HAIRCARE", "TOOLS", "SUPPLEMENT"]

TITLES = [
    "Niacinamide 10% Serum 30ml",
    "Hydrating Toner Mist",
    "Vitamin C Brightening Cream",
    "Matte Lip Tint Set",
    "Silk Heatless Curling Set",
    "Silicone Body Scrubber",
    "Collagen Peptide Powder",
    "Jade Roller & Gua Sha Kit",
]


def seed(db: Session, days: int = 70) -> dict[str, int]:
    rng = random.Random(20261119)
    today = date.today()

    if db.scalar(select(func.count(Shop.id))):
        return {"shops": 0, "products": 0, "metrics": 0, "posts": 0, "note": "已初始化，跳过"}

    shops: list[Shop] = []
    for platform, name, region, currency, health, _ in SHOPS:
        s = Shop(
            platform=platform,
            name=name,
            region=region,
            currency=currency,
            health_score=health,
            opened_at=today - timedelta(days=rng.randint(120, 900)),
        )
        db.add(s)
        shops.append(s)
    db.flush()

    products: list[Product] = []
    for s, (_, _, _, _, _, base) in zip(shops, SHOPS):
        for i, title in enumerate(TITLES):
            p = Product(
                shop_id=s.id,
                sku=f"SKU-{s.name.split()[0][:4].upper()}-{i:03d}",
                title=title,
                category=CATEGORIES[i % len(CATEGORIES)],
                price=Decimal(str(round(rng.uniform(8.9, 79.9), 2))),
                stock=rng.randint(0, 900),
                status="ON_SALE" if rng.random() > 0.12 else "OFF_SHELF",
            )
            db.add(p)
            products.append(p)
    db.flush()

    metrics = 0
    by_shop: dict[int, list[Product]] = {}
    for p in products:
        by_shop.setdefault(p.shop_id, []).append(p)

    for s, (_, _, _, _, _, base) in zip(shops, SHOPS):
        shop_products = by_shop[s.id]
        # 每个商品一个热度权重，制造爆品长尾
        weights = [1 / (i + 1) ** 1.15 for i in range(len(shop_products))]
        total_w = sum(weights)

        for d in range(days):
            stat_date = today - timedelta(days=days - 1 - d)
            # 整体缓慢增长 + 周末抬升 + 噪声
            growth = 1 + (d / days) * 0.55
            weekend = 1.28 if stat_date.weekday() >= 5 else 1.0
            day_factor = growth * weekend * rng.uniform(0.86, 1.14)

            day_gmv = Decimal("0")
            day_orders = 0
            day_visitors = 0

            for prod, w in zip(shop_products, weights):
                share = rng.uniform(0.75, 1.25) * w
                orders = max(0, int(base * day_factor * share / 6))
                visitors = int(orders * rng.uniform(9, 26))
                gmv = Decimal(str(round(orders * float(prod.price), 2)))
                refund = Decimal(str(round(float(gmv) * rng.uniform(0, 0.06), 2)))

                db.add(
                    DailyMetric(
                        shop_id=s.id,
                        product_id=prod.id,
                        stat_date=stat_date,
                        gmv=gmv,
                        orders=orders,
                        visitors=visitors,
                        page_views=visitors * rng.randint(2, 4),
                        refund_amount=refund,
                    )
                )
                metrics += 1
                day_gmv += gmv
                day_orders += orders
                day_visitors += visitors

            # 店铺级汇总行（product_id = NULL），看板主查询走这一行
            db.add(
                DailyMetric(
                    shop_id=s.id,
                    product_id=None,
                    stat_date=stat_date,
                    gmv=day_gmv,
                    orders=day_orders,
                    visitors=day_visitors,
                    page_views=day_visitors * 3,
                    refund_amount=Decimal(str(round(float(day_gmv) * 0.03, 2))),
                )
            )
            metrics += 1

    posts = seed_social_posts(db)

    for s, (_, name, _, _, _, _) in zip(shops, SHOPS):
        db.add(
            CollectTask(
                source="tk_shop" if s.platform == "TIKTOK_SHOP" else "export",
                target=name,
                schedule="0 2 * * *",
                status="OK" if rng.random() > 0.25 else "FAILED",
                last_run_at=datetime.now() - timedelta(hours=rng.randint(1, 20)),
                last_rows=rng.randint(120, 1600),
                error_msg=None,
            )
        )

    db.commit()
    return {"shops": len(shops), "products": len(products), "metrics": metrics, "posts": posts}
