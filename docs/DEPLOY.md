# 部署到 Render

代码仓库：https://github.com/Hyxxt/tk-shop-dashboard
部署配置：仓库根目录 `render.yaml`（Render Blueprint，一次拉起后端 + 前端）

---

## 一、最短路径（Blueprint，约 3 步）

1. 打开这个链接（仓库已经带上）：

   https://dashboard.render.com/blueprint/new?repo=https://github.com/Hyxxt/tk-shop-dashboard

2. 分支选 `main`，Blueprint 名字随便填（比如 `tk-shop`），点 **Apply**。

3. 等。会依次出现两个服务：

   | 服务名 | 类型 | 说明 |
   |---|---|---|
   | `tk-shop-api` | Web Service (Python) | FastAPI，首次启动会自动建表 + 灌模拟数据 |
   | `tk-shop-dashboard` | Static Site | Vue3 前端，构建产物 dist |

   第一个可能耗时 3-5 分钟（装 Python 依赖）。

---

## 二、部署完必须核对一件事：后端域名

`render.yaml` 里前端的环境变量写的是：

```
VITE_API_BASE = https://tk-shop-api.onrender.com/api
```

但 Render 的服务名是**全局唯一**的，`tk-shop-api` 这个名字如果被别人占了，
Render 会自动改名（比如变成 `tk-shop-api-x7k2`）。

**处理方法**：打开后端服务的页面，看顶部显示的域名，然后

> 前端服务 → Environment → 把 `VITE_API_BASE` 改成 `https://<实际后端域名>/api` → Save
> （改环境变量会自动触发重新部署，等 1-2 分钟）

改完打开前端域名，能登录、看板有曲线，就算通了。

如果打开页面一片空白或者接口 403/CORS 报错，八成就是这一步没对上。

---

## 三、常见问题

**Q：第一次打开很慢，转了半分钟才有数据？**
免费实例 15 分钟无请求会休眠，冷启动约 50 秒。这不是 bug。
正式用的话升级到 Starter（$7/月）就不会休眠。

**Q：数据会不会丢？**
演示环境用的 SQLite，容器重启后文件系统重置，启动时 `AUTO_SEED=1` 会重新灌一份模拟数据。
也就是说：**数据每次都是干净的演示数据**，这是有意设计的。
要持久化就换 Postgres —— 把 `DATABASE_URL` 指向 Render 的 Postgres 实例即可，
ORM 一行都不用改（`pymysql` 换成 `psycopg`，SQLAlchemy 的方言自动适配）。

**Q：以后改了代码怎么更新？**
`git push` 到 `main` 分支，Render 自动重新构建部署。不用手动点。

**Q：想改端口/IP 绑定？**
Render 要求监听 `0.0.0.0:$PORT`，`render.yaml` 里的 `startCommand` 已经这么配了，别改。

**Q：权限演示怎么给别人看？**
把两个账号写进演示说明：`admin/admin123`（全权限）、`viewer/viewer123`（只读）。
让对方用 viewer 登录，侧边栏会少「数据规模」、采集按钮变灰，这是权限码在起作用。

---

## 四、验收清单

部署完成后逐条点一遍，都过了再挂到作品集：

- [ ] 前端域名能打开，显示登录页
- [ ] `admin / admin123` 能登录，看板有 4 张指标卡 + 折线图 + 环形图
- [ ] 切换「7 天 / 30 天 / 90 天」，数字和曲线跟着变
- [ ] 「店铺管理」有 5 行，「单品排行」有条形图
- [ ] 「采集任务」点「立即执行」，返回成功并刷新写入行数
- [ ] 退出，用 `viewer / viewer123` 登录
- [ ] viewer 的侧边栏没有「数据规模」
- [ ] viewer 的「立即执行」按钮是灰的
- [ ] viewer 手动输入 `#/system` 会被弹回看板
- [ ] 打开 `https://<后端域名>/docs`，FastAPI 文档能访问

---

## 五、如果要迁 MySQL

本地或云上的 MySQL 都行，两步：

```bash
# 1. 建库建表
mysql -h <host> -u <user> -p < backend/sql/schema.sql

# 2. 配连接串（Render 后台加环境变量，或本地 .env）
DATABASE_URL=mysql+pymysql://user:pass@host:3306/tk_shop?charset=utf8mb4
```

第一次启动 `AUTO_SEED=1` 会往 MySQL 里灌演示数据。
生产环境记得把 `AUTO_SEED` 设成 `0`，并收紧 `CORS_ORIGINS`（别用 `*`）。
