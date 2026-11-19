"""看板 / 店铺 / 商品 / 社媒 / 采集 接口。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.auth import CurrentUser, get_current_user, login, require_perm
from app.core.config import settings
from app.core.db import get_db
from app.models import CollectTask, DailyMetric, Product, Shop
from app.schemas import (
    CollectRunResult,
    CollectTaskOut,
    LoginIn,
    LoginOut,
    OverviewOut,
    ProductOut,
    ShopOut,
    SocialSummaryOut,
    TopProductOut,
    TrendPoint,
)
from app.services import metrics as svc
from app.services.collector import run_collect

router = APIRouter()


@router.post("/auth/login", response_model=LoginOut, tags=["auth"])
def do_login(payload: LoginIn) -> LoginOut:
    return login(payload)


@router.get("/auth/me", response_model=LoginOut, tags=["auth"])
def me(user: CurrentUser = Depends(get_current_user)) -> LoginOut:
    return LoginOut(
        token=f"{settings.DEMO_TOKEN_PREFIX}{user.username}",
        username=user.username,
        display_name=user.info["display_name"],
        roles=user.info["roles"],
        permissions=user.permissions,
    )


@router.get("/dashboard/overview", response_model=OverviewOut, tags=["dashboard"])
def overview(
    shop_id: int | None = None,
    days: int = Query(30, ge=1, le=180),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_perm("dashboard:view")),
) -> OverviewOut:
    return OverviewOut(**svc.get_overview(db, shop_id, days))


@router.get("/dashboard/trend", response_model=list[TrendPoint], tags=["dashboard"])
def trend(
    shop_id: int | None = None,
    days: int = Query(30, ge=1, le=180),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_perm("dashboard:view")),
) -> list[TrendPoint]:
    return [TrendPoint(**p) for p in svc.get_trend(db, shop_id, days)]


@router.get("/dashboard/top-products", response_model=list[TopProductOut], tags=["dashboard"])
def top_products(
    shop_id: int | None = None,
    days: int = Query(30, ge=1, le=180),
    limit: int = Query(10, ge=1, le=50),
    order_by: str = Query("gmv", pattern="^(gmv|orders|visitors)$"),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_perm("product:view")),
) -> list[TopProductOut]:
    return [
        TopProductOut(**r)
        for r in svc.get_top_products(db, shop_id, days, limit, order_by)
    ]


@router.get("/shops", tags=["shop"])
def shops(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_perm("shop:view")),
) -> list[dict]:
    return svc.list_shops_with_kpi(db)


@router.get("/shops/{shop_id}/products", response_model=list[ProductOut], tags=["shop"])
def shop_products(
    shop_id: int,
    keyword: str | None = None,
    category: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_perm("product:view")),
) -> list[ProductOut]:
    stmt = select(Product).where(Product.shop_id == shop_id)
    if keyword:
        stmt = stmt.where(Product.title.like(f"%{keyword}%"))
    if category:
        stmt = stmt.where(Product.category == category)
    # 分页必须带稳定排序，否则翻页会重复/漏行
    stmt = stmt.order_by(Product.id).offset((page - 1) * page_size).limit(page_size)
    return [ProductOut.model_validate(p) for p in db.scalars(stmt).all()]


@router.get("/social/summary", response_model=list[SocialSummaryOut], tags=["social"])
def social_summary(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_perm("social:view")),
) -> list[SocialSummaryOut]:
    return [SocialSummaryOut(**r) for r in svc.get_social_summary(db)]


@router.get("/collect/tasks", response_model=list[CollectTaskOut], tags=["collect"])
def collect_tasks(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_perm("collect:view")),
) -> list[CollectTaskOut]:
    rows = db.scalars(select(CollectTask).order_by(CollectTask.id)).all()
    return [CollectTaskOut.model_validate(t) for t in rows]


@router.post(
    "/collect/tasks/{task_id}/run",
    response_model=CollectRunResult,
    tags=["collect"],
)
def run_task(
    task_id: int,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_perm("collect:run")),
) -> CollectRunResult:
    task = db.get(CollectTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return CollectRunResult(**run_collect(db, task))


@router.get("/system/stats", tags=["system"])
def system_stats(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_perm("system:admin")),
) -> dict:
    """数据规模，顺手给 README 里的性能测试做对照。"""
    return {
        "shops": db.scalar(select(func.count(Shop.id))),
        "products": db.scalar(select(func.count(Product.id))),
        "daily_metrics": db.scalar(select(func.count(DailyMetric.id))),
        "collect_tasks": db.scalar(select(func.count(CollectTask.id))),
        "dialect": db.bind.dialect.name if db.bind else "unknown",
    }
