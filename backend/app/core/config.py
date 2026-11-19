"""全局配置：数据库连接串、分页、鉴权密钥。

切换数据库只改一个环境变量 DATABASE_URL：
  MySQL  mysql+pymysql://root:123456@127.0.0.1:3306/tk_shop?charset=utf8mb4
  SQLite sqlite:///./data/app.db
默认走 SQLite，是为了没有 MySQL 的机器也能一条命令跑起来演示。
"""
from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class Settings:
    APP_NAME: str = "TK Shop 智能运营看板"
    API_PREFIX: str = "/api"

    # 默认 SQLite，生产/演示切 MySQL
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{(DATA_DIR / 'app.db').as_posix()}"
    )
    DB_ECHO: bool = os.getenv("DB_ECHO", "0") == "1"

    # 演示用固定 token，真实项目换成 JWT
    DEMO_TOKEN_PREFIX: str = "tk-demo-token-"

    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 200

    # 逗号分隔，部署时用环境变量覆盖；演示环境默认放开（不带 cookie，只靠 Bearer token）
    CORS_ORIGINS: list[str] = [
        o.strip()
        for o in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,*",
        ).split(",")
        if o.strip()
    ]


settings = Settings()
