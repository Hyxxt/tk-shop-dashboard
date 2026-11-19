"""Pydantic 出参模型。统一 camelCase 交给前端，省一层转换。"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ShopOut(ORMModel):
    id: int
    platform: str
    name: str
    region: str
    currency: str
    health_score: int
    opened_at: date | None = None


class ProductOut(ORMModel):
    id: int
    shop_id: int
    sku: str
    title: str
    category: str
    price: Decimal
    stock: int
    status: str


class OverviewOut(BaseModel):
    gmv: float
    orders: int
    visitors: int
    conversion_rate: float = Field(description="订单/访客，百分比")
    avg_order_value: float
    refund_rate: float
    gmv_growth: float = Field(description="对比上一等长周期，百分比")
    orders_growth: float


class TrendPoint(BaseModel):
    stat_date: date
    gmv: float
    orders: int
    visitors: int


class TopProductOut(BaseModel):
    product_id: int
    title: str
    sku: str
    category: str
    shop_name: str
    gmv: float
    orders: int
    visitors: int
    conversion_rate: float


class SocialSummaryOut(BaseModel):
    platform: str
    posts: int
    views: int
    likes: int
    comments: int
    shares: int
    engagement_rate: float
    avg_views: float


class CollectTaskOut(ORMModel):
    id: int
    source: str
    target: str
    schedule: str
    status: str
    last_run_at: datetime | None = None
    last_rows: int
    error_msg: str | None = None


class CollectRunResult(BaseModel):
    task_id: int
    status: str
    rows: int
    message: str


class LoginIn(BaseModel):
    username: str
    password: str


class LoginOut(BaseModel):
    token: str
    username: str
    display_name: str
    roles: list[str]
    permissions: list[str]
