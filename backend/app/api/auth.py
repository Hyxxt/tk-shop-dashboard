"""认证与权限。

演示环境用固定账号 + 固定 token，重点是复刻中后台的**权限码**机制：
前端菜单按权限码过滤，后端接口再按权限码校验一遍。
只做前端隐藏、后端不校验，等于没做 —— 这句话面试可以直接说。
"""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status

from app.core.config import settings
from app.schemas import LoginIn, LoginOut

# 权限码：菜单层和按钮层共用一套
PERMS_ALL = [
    "dashboard:view",
    "shop:view",
    "product:view",
    "social:view",
    "collect:view",
    "collect:run",
    "system:admin",
]

USERS: dict[str, dict] = {
    "admin": {
        "password": "admin123",
        "display_name": "运营管理员",
        "roles": ["admin"],
        "permissions": PERMS_ALL,
    },
    "viewer": {
        "password": "viewer123",
        "display_name": "数据只读",
        "roles": ["viewer"],
        "permissions": ["dashboard:view", "shop:view", "product:view", "social:view", "collect:view"],
    },
}


def login(payload: LoginIn) -> LoginOut:
    user = USERS.get(payload.username)
    if user is None or user["password"] != payload.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="账号或密码错误"
        )
    return LoginOut(
        token=f"{settings.DEMO_TOKEN_PREFIX}{payload.username}",
        username=payload.username,
        display_name=user["display_name"],
        roles=user["roles"],
        permissions=user["permissions"],
    )


class CurrentUser:
    def __init__(self, username: str) -> None:
        self.username = username
        self.info = USERS[username]

    @property
    def permissions(self) -> list[str]:
        return self.info["permissions"]


def get_current_user(authorization: str | None = Header(default=None)) -> CurrentUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    token = authorization.removeprefix("Bearer ").strip()
    if not token.startswith(settings.DEMO_TOKEN_PREFIX):
        raise HTTPException(status_code=401, detail="token 无效")
    username = token.removeprefix(settings.DEMO_TOKEN_PREFIX)
    if username not in USERS:
        raise HTTPException(status_code=401, detail="token 无效")
    return CurrentUser(username)


def require_perm(perm: str):
    """权限码校验依赖工厂：@router.post(..., dependencies=[Depends(require_perm("collect:run"))])"""

    def _checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if perm not in user.permissions:
            raise HTTPException(status_code=403, detail=f"缺少权限：{perm}")
        return user

    return _checker
