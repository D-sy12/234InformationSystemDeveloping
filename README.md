# 234InformationSystemDeveloping

图书管理系统 —— 信息系统开发实践小组作业

## 功能总览

- **游客**：在线浏览电子图书（封面 + 基本信息 + 在线阅读全文），无法预约实体书
- **注册用户**：预约借阅实体图书（每本借阅上限 7 天）；个人中心（我的借阅/预约记录、到期倒计时、自助归还）
- **登录 / 注册**：行为式（滑块）验证码 + QQ 邮箱验证码
- **管理员**（默认 `admin` / `admin`，可在 `.env` 修改）：
  - 添加新图书、管理实体图书馆藏数量
  - 查看全部借阅记录：谁借了哪本书、何时到期
  - 到期前 1 天自动邮件提醒（每条记录只提醒一次，防轰炸）
  - 逾期记录**自动标红**，可一键发送催还邮件
  - 数据统计（ECharts：分类分布 / 借阅状态分布 / 热门借阅 TOP5）

## 技术栈

| 端 | 技术 |
|---|---|
| 前端 | Vue3 + Vite + Element Plus + ECharts + 自研滑块行为验证组件 |
| 后端 | Python Flask + Flask-SQLAlchemy + PyJWT + smtplib（QQ 邮箱） |
| 数据库 | MySQL 8.0 |

## 环境要求

- Python >= 3.10
- Node.js >= 18
- MySQL >= 8.0

## 快速开始

### 1. 初始化数据库

```bash
mysql -uroot -p < database/init.sql
```

> 后端首次启动也会自动建库建表并写入样例图书，此步可选。

### 2. 下载图书数据（可选，公版书来自 Project Gutenberg）

```bash
python scripts/download_books.py
```

生成 `backend/static/books/*.txt` 与 `backend/static/covers/*.svg`；有 ISBN 的书会尝试从 Open Library 拉取真实封面并生成 `scripts/update_covers.sql`。图书文件已提交到 git，克隆后可跳过此步。

### 3. 启动后端

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows；Linux/Mac 用 source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env       # Windows；Linux/Mac 用 cp
# 编辑 .env：填 MySQL 密码、QQ 邮箱授权码、管理员账号密码
python app.py                # 运行在 http://127.0.0.1:5000
```

首次启动自动创建管理员账号（默认 `admin` / `admin`）。

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev                  # 运行在 http://localhost:5173
```

管理员登录后访问 `/admin` 进入管理后台。

## 借阅状态规则

| 判定 | 状态 | 用户/管理员页面表现 |
|---|---|---|
| 距到期 > 1 天 | 借阅中 | 正常显示 |
| 距到期 <= 1 天 | 即将到期 | 黄色提示 + 自动邮件提醒（每条只提醒一次） |
| 超过应还时间 | 逾期 | **标红** + 一键邮件催还 |

## QQ 邮箱 SMTP 配置（发验证码 / 催还邮件）

1. 网页版 QQ 邮箱 → 设置 → 账号 → 开启「SMTP 服务」
2. 按提示用手机发短信获取**授权码**（不是 QQ 密码）
3. 将 `QQ号@qq.com` 和授权码填入 `backend/.env` 的 `SMTP_USER` / `SMTP_PASSWORD`

## 目录结构

```
backend/    后端 Flask（app.py 入口；static/books 图书全文；static/covers 封面）
frontend/   前端 Vue3（/ 图书浏览；/profile 个人中心；/admin 管理后台）
database/   MySQL 建库脚本 init.sql
scripts/    公版图书下载脚本 download_books.py
```

## 常见问题

- **MySQL 报认证错误**：MySQL 8 默认 `caching_sha2_password`，需安装 cryptography（requirements.txt 已包含）。
- **SMTP 报 535**：授权码错误，或未开启 SMTP 服务。
- **收不到验证码**：检查垃圾邮箱；确认 `.env` 里 SMTP 配置正确。
- **前端 401 跳转**：登录态过期属正常，重新登录即可。

## 注意

`backend/.env` 含密码，已被 `.gitignore` 排除，**不要提交**；克隆后从 `.env.example` 复制创建。
