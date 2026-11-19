"""数据模型（5 张表）。

设计要点，面试可以直接讲：
1. `daily_metric` 是核心大表，店铺级和商品级快照共用一张，
   product_id 为 NULL 表示店铺级汇总 —— 一张表两种粒度，
   用联合唯一键 (shop_id, product_id, stat_date) 保证幂等，采集重跑不会产生重复行。
2. 索引不是随手加的：都来自真实查询模式（见 sql/explain_demo.sql）。
3. 金额统一 DECIMAL(12,2)，不用 float —— 财务数据不用浮点。
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Shop(Base):
    """店铺 / 社媒账号的载体。"""

    __tablename__ = "shop"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(32), nullable=False, comment="TIKTOK_SHOP/INSTAGRAM/FACEBOOK/YOUTUBE")
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    region: Mapped[str] = mapped_column(String(16), default="US", comment="US/UK/SEA")
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    health_score: Mapped[int] = mapped_column(Integer, default=0, comment="店铺健康分 0-100")
    opened_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    products: Mapped[list["Product"]] = relationship(back_populates="shop")

    __table_args__ = (
        UniqueConstraint("platform", "name", name="uk_platform_name"),
        Index("idx_shop_platform", "platform"),
    )


class Product(Base):
    """商品（SPU 级，演示环境一个 SKU 一个商品）。"""

    __tablename__ = "product"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shop_id: Mapped[int] = mapped_column(ForeignKey("shop.id", ondelete="CASCADE"), index=True)
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(64), default="UNKNOWN")
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="ON_SALE")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    shop: Mapped["Shop"] = relationship(back_populates="products")

    __table_args__ = (
        # 采集去重靠它：同一店铺同一 SKU 只有一条
        UniqueConstraint("shop_id", "sku", name="uk_shop_sku"),
        # 列表页固定「先按店铺过滤，再按类目筛，最后按价格排序」
        Index("idx_shop_category_price", "shop_id", "category", "price"),
    )


class DailyMetric(Base):
    """每日经营快照 —— 全库最大的表。

    product_id 为空 = 店铺级汇总行；非空 = 单品行。
    """

    __tablename__ = "daily_metric"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shop_id: Mapped[int] = mapped_column(ForeignKey("shop.id", ondelete="CASCADE"))
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE"), nullable=True
    )
    stat_date: Mapped[date] = mapped_column(Date, nullable=False)

    gmv: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    orders: Mapped[int] = mapped_column(Integer, default=0)
    visitors: Mapped[int] = mapped_column(Integer, default=0)
    page_views: Mapped[int] = mapped_column(Integer, default=0)
    refund_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        # 幂等键：重跑采集只会 UPDATE，不会插重复
        UniqueConstraint("shop_id", "product_id", "stat_date", name="uk_shop_product_date"),
        # 覆盖索引场景：看板主查询「某店某区间按日聚合」
        Index("idx_shop_date", "shop_id", "stat_date"),
        # 单品排行：先过滤店铺+区间，再按 gmv 倒序取 Top N
        Index("idx_shop_date_gmv", "shop_id", "stat_date", "gmv"),
        Index("idx_product_date", "product_id", "stat_date"),
    )


class SocialPost(Base):
    """海外社媒内容（TK / IG / FB / YouTube 统一建模）。"""

    __tablename__ = "social_post"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    account_name: Mapped[str] = mapped_column(String(128), nullable=False)
    post_id: Mapped[str] = mapped_column(String(64), nullable=False, comment="平台侧内容 ID")
    content_type: Mapped[str] = mapped_column(String(16), default="VIDEO")
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    views: Mapped[int] = mapped_column(Integer, default=0)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    saves: Mapped[int] = mapped_column(Integer, default=0)
    duration_sec: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("platform", "post_id", name="uk_platform_post"),
        # 矩阵账号维度查内容表现
        Index("idx_account_published", "account_name", "published_at"),
        Index("idx_platform_published", "platform", "published_at"),
    )


class CollectTask(Base):
    """采集任务与运行状态，给前端「采集任务」页看。"""

    __tablename__ = "collect_task"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, comment="tk_shop/instagram/facebook/youtube")
    target: Mapped[str] = mapped_column(String(255), nullable=False, comment="店铺或账号标识")
    schedule: Mapped[str] = mapped_column(String(32), default="0 2 * * *")
    status: Mapped[str] = mapped_column(String(16), default="IDLE", comment="IDLE/RUNNING/OK/FAILED")
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_rows: Mapped[int] = mapped_column(Integer, default=0)
    error_msg: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (UniqueConstraint("source", "target", name="uk_source_target"),)
