"""FastAPI 入口。

启动时自动建表 + 灌演示数据（AUTO_SEED=1 时），
这样别人拿到代码 clone 下来 `python run.py` 就能看到有数据的看板，
不用先配 MySQL —— 面试官/HR 打开就能点，这一步很关键。
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api import router
from app.core.config import settings
from app.core.db import Base, SessionLocal, engine
from app.models import CollectTask, DailyMetric, Product, Shop, SocialPost  # noqa: F401 建表要用
from app.services.seed import seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    if os.getenv("AUTO_SEED", "1") == "1":
        with SessionLocal() as db:
            result = seed(db)
            print(f"[seed] {result}")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "TikTok Shop 与海外社媒矩阵的经营数据看板。\n\n"
        "演示账号：admin / admin123（可执行采集）、viewer / viewer123（只读）。\n"
        "数据为模拟数据，不含任何真实平台经营数据。"
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    # allow_origins 为 "*" 时不能开 credentials，浏览器会直接拒绝
    allow_credentials="*" not in settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.API_PREFIX)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.APP_NAME}
