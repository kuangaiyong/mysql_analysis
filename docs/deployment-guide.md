# MySQL 性能诊断与优化系统 — 部署手册

> 版本：2.0 | 最后更新：2026-04-16
>
> 本手册覆盖 **Linux、macOS、Windows** 三平台的手动部署流程（不涉及 Docker）。

---

## 目录

1. [系统架构概览](#1-系统架构概览)
2. [环境要求](#2-环境要求)
3. [获取源码](#3-获取源码)
4. [后端部署](#4-后端部署)
5. [前端部署](#5-前端部署)
6. [启动与停止](#6-启动与停止)
7. [生产环境构建](#7-生产环境构建)
8. [Nginx 反向代理配置（推荐）](#8-nginx-反向代理配置推荐)
9. [配置详解](#9-配置详解)
10. [数据库初始化与迁移](#10-数据库初始化与迁移)
11. [常见问题](#11-常见问题)

---

## 1. 系统架构概览

```
┌──────────────┐       ┌──────────────────┐       ┌──────────────────┐
│              │  HTTP  │                  │  SQL   │                  │
│   前端 (Vue) │ ────►  │   后端 (FastAPI)  │ ────►  │   MySQL 数据库    │
│   :5173      │  /api  │   :8000          │        │   :3306          │
│              │  /ws   │                  │        │                  │
└──────────────┘       └──────┬───────────┘       └──────────────────┘
                              │
                         HTTP/HTTPS
                              │
                       ┌──────▼───────────┐
                       │   LLM AI 服务     │
                       │ (智谱/Kimi/OpenAI) │
                       └──────────────────┘
```

| 组件 | 技术栈 | 默认端口 | 说明 |
|------|--------|---------|------|
| 前端 | Vue 3 + Vite + Element Plus + ECharts | 5173 | 开发服务器；生产环境构建为静态文件 |
| 后端 | Python 3.10+ / FastAPI / Uvicorn | 8000 | REST API + WebSocket |
| 数据库 | MySQL 8.0+ | 3306 | 系统自身数据库 + 被诊断的目标数据库 |
| AI 服务 | 智谱 GLM-5（默认）/ Kimi / OpenAI / Claude | — | 外部 LLM API |

---

## 2. 环境要求

### 2.1 必需软件

| 软件 | 最低版本 | 推荐版本 | 说明 |
|------|---------|---------|------|
| **Python** | 3.10 | 3.12 | 后端运行时 |
| **Node.js** | 18.0 | 20 LTS | 前端构建与开发 |
| **npm** | 9.0 | 10+ | 包管理器（随 Node.js 安装） |
| **MySQL** | 8.0 | 8.0+ | 系统数据库 + 被诊断数据库 |

### 2.2 可选软件

| 软件 | 说明 |
|------|------|
| **Redis** | 缓存 + Celery 任务队列（可选，不装不影响核心功能） |
| **Nginx** | 生产环境反向代理（推荐） |
| **Git** | 源码拉取 |

### 2.3 版本检查命令

```bash
# 所有平台通用
python3 --version    # 或 python --version (Windows)
node --version
npm --version
mysql --version
```

---

## 3. 获取源码

```bash
git clone https://github.com/kuangaiyong/mysql_analysis.git
cd mysql_analysis
```

项目目录结构：

```
mysql_analysis/
├── backend/                  # 后端（FastAPI）
│   ├── app/                  # 应用源码
│   │   ├── main.py           # 入口
│   │   ├── config.py         # 配置
│   │   ├── database.py       # 数据库连接
│   │   ├── routers/          # API 路由
│   │   ├── services/         # 业务逻辑
│   │   │   ├── ai/           # AI 诊断服务
│   │   │   └── sql_executor.py
│   │   └── ...
│   ├── alembic/              # 数据库迁移
│   ├── alembic.ini
│   ├── requirements.txt      # Python 依赖
│   └── .env.example          # 环境变量模板
├── frontend/                 # 前端（Vue 3）
│   ├── src/
│   │   ├── api/              # API 调用
│   │   ├── view/             # 页面组件
│   │   ├── pinia/            # 状态管理
│   │   └── components/       # 公共组件
│   ├── package.json
│   └── vite.config.ts
├── start-all.sh              # Linux/macOS 一键启动
├── stop-all.sh               # Linux/macOS 一键停止
└── docs/                     # 文档
```

---

## 4. 后端部署

### 4.1 创建 Python 虚拟环境

**Linux / macOS：**

```bash
cd mysql_analysis/backend

# 创建虚拟环境
python3 -m venv venv

# 激活
source venv/bin/activate
```

**Windows（CMD）：**

```cmd
cd mysql_analysis\backend

python -m venv venv

venv\Scripts\activate
```

**Windows（PowerShell）：**

```powershell
cd mysql_analysis\backend

python -m venv venv

.\venv\Scripts\Activate.ps1
```

> **提示**：如果 PowerShell 报执行策略错误，先运行：
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

### 4.2 安装 Python 依赖

```bash
# 确保虚拟环境已激活
pip install -r requirements.txt
```

如果安装 `cryptography` 或 `pymysql` 失败，可能需要先安装编译工具：

- **Linux (Ubuntu/Debian)**：`sudo apt-get install build-essential libssl-dev libffi-dev python3-dev`
- **Linux (CentOS/RHEL)**：`sudo yum install gcc openssl-devel libffi-devel python3-devel`
- **macOS**：`xcode-select --install`
- **Windows**：安装 [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

### 4.3 创建 MySQL 数据库

登录 MySQL 后执行：

```sql
-- 创建系统数据库（存储连接配置、分析结果等）
CREATE DATABASE mysql_analysis DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建专用用户（推荐）
CREATE USER 'mysql_analysis'@'%' IDENTIFIED BY 'YOUR_STRONG_PASSWORD';
GRANT ALL PRIVILEGES ON mysql_analysis.* TO 'mysql_analysis'@'%';
FLUSH PRIVILEGES;
```

> **注意**：系统还需要访问**被诊断的目标 MySQL 数据库**。目标数据库的连接信息在系统启动后通过前端页面配置（连接管理），不需要提前写入配置文件。

### 4.4 配置环境变量

```bash
cd backend
cp .env.example .env
```

编辑 `backend/.env`，**必须修改**以下配置项：

```ini
# ==================== 必须配置 ====================

# 系统数据库连接（上面创建的数据库）
DATABASE_URL=mysql+pymysql://mysql_analysis:YOUR_STRONG_PASSWORD@localhost:3306/mysql_analysis

# JWT 密钥（用下面的命令生成）
# python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=粘贴上面命令生成的随机字符串

# ==================== AI 服务配置（至少配一个）====================

# 智谱 GLM（默认）
ZHIPU_API_KEY=你的智谱API密钥

# 或使用 Kimi
# KIMI_API_KEY=你的Kimi密钥

# 或使用 OpenAI
# OPENAI_API_KEY=你的OpenAI密钥
```

### 4.5 初始化数据库表

```bash
cd backend

# 方式一：使用 Alembic 迁移（推荐）
alembic upgrade head

# 方式二：自动建表（开发环境可用，启动时自动执行）
# 无需额外操作，后端启动时会自动创建表（database.py 中的 init_db()）
```

### 4.6 验证后端

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

看到以下输出表示启动成功：

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

访问 http://localhost:8000/api/health ，返回 `{"status":"healthy",...}` 即成功。

访问 http://localhost:8000/api/docs 可查看完整 API 文档（Swagger UI）。

---

## 5. 前端部署

### 5.1 安装 Node.js 依赖

```bash
cd mysql_analysis/frontend
npm install
```

### 5.2 开发模式启动

```bash
npm run dev
```

看到以下输出表示启动成功：

```
  VITE v6.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.x.x:5173/
```

开发模式下，Vite 会自动将 `/api` 和 `/ws` 请求代理到后端 `http://127.0.0.1:8000`（已在 `vite.config.ts` 中配置），无需额外设置跨域。

### 5.3 验证前端

浏览器访问 http://localhost:5173 ，看到登录页面即成功。

---

## 6. 启动与停止

### 6.1 Linux / macOS — 一键脚本

**启动（后台运行）：**

```bash
cd mysql_analysis

# 首次使用需赋予执行权限
chmod +x start-all.sh stop-all.sh

./start-all.sh
```

输出示例：

```
🚀 启动 MySQL 性能诊断系统...
📡 启动后端服务...
✅ 后端服务已启动 (PID: 12345)
   API: http://localhost:8000
   文档: http://localhost:8000/api/docs
   日志: logs/backend.log

🎨 启动前端服务...
✅ 前端服务已启动 (PID: 12346)
   前端: http://localhost:5173
   日志: logs/frontend.log

✅ 所有服务已启动！
```

**停止：**

```bash
./stop-all.sh
```

**查看日志：**

```bash
tail -f logs/backend.log    # 后端日志
tail -f logs/frontend.log   # 前端日志
```

### 6.2 Linux / macOS — 手动启动

**方式一：前台运行（适合调试）**

终端 1（后端）：

```bash
cd mysql_analysis/backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

终端 2（前端）：

```bash
cd mysql_analysis/frontend
npm run dev
```

**方式二：后台运行（nohup）**

```bash
# 后端
cd mysql_analysis/backend
source venv/bin/activate
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
echo $! > ../logs/backend.pid

# 前端
cd mysql_analysis/frontend
nohup npm run dev > ../logs/frontend.log 2>&1 &
echo $! > ../logs/frontend.pid

# 停止
kill $(cat logs/backend.pid)
kill $(cat logs/frontend.pid)
```

### 6.3 Windows — 手动启动

打开两个终端窗口：

**终端 1（后端，CMD）：**

```cmd
cd mysql_analysis\backend
venv\Scripts\activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**终端 2（前端，CMD）：**

```cmd
cd mysql_analysis\frontend
npm run dev
```

**停止**：分别在两个终端按 `Ctrl + C`。

---

## 7. 生产环境构建

生产环境下，前端构建为静态文件，由后端直接托管或由 Nginx 反向代理。

### 7.1 后端 — 生产启动参数

```bash
cd backend
source venv/bin/activate   # Linux/macOS
# venv\Scripts\activate    # Windows

# 多 worker 启动（推荐 4 个 worker，根据 CPU 核数调整）
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

> **注意**：生产环境不要使用 `--reload` 参数。

建议使用 **systemd**（Linux）或 **PM2** 管理后端进程。

**systemd 服务文件示例**（`/etc/systemd/system/mysql-analysis.service`）：

```ini
[Unit]
Description=MySQL Analysis Backend
After=network.target mysql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/mysql_analysis/backend
ExecStart=/opt/mysql_analysis/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=5
Environment=ENVIRONMENT=production

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable mysql-analysis
sudo systemctl start mysql-analysis
sudo systemctl status mysql-analysis
```

### 7.2 前端 — 构建静态文件

```bash
cd frontend
npm run build
```

构建完成后，静态文件输出到 `frontend/dist/` 目录。

生产环境的 API 和 WebSocket 地址在 `frontend/.env.production` 中配置：

```ini
# 相对路径（通过 Nginx 代理时使用）
VITE_BASE_API=/api/v1
VITE_WS_URL=/ws
```

如果前后端不在同一域名下，改为绝对路径：

```ini
VITE_BASE_API=https://your-server.com/api/v1
VITE_WS_URL=wss://your-server.com/ws
```

### 7.3 后端托管前端静态文件

编辑 `backend/app/main.py`，在启动事件后添加静态文件挂载：

```python
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# 在 app.include_router(...) 之后添加：
frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
```

> **注意**：这行必须在所有 `include_router` 之后，否则会拦截 API 路由。

---

## 8. Nginx 反向代理配置（推荐）

生产环境推荐使用 Nginx 统一入口，同时托管前端静态文件和代理后端 API。

### 8.1 Nginx 配置示例

```nginx
server {
    listen 80;
    server_name your-server.com;

    # 前端静态文件
    root /opt/mysql_analysis/frontend/dist;
    index index.html;

    # Vue Router history 模式 — 所有未匹配的路径返回 index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # AI 接口需要较长超时（最大 15 分钟）
        location /api/v1/ai/ {
            proxy_pass http://127.0.0.1:8000;
            proxy_read_timeout 900s;
            proxy_send_timeout 900s;
        }
    }

    # WebSocket 代理
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 3600s;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 日志
    access_log /var/log/nginx/mysql_analysis_access.log;
    error_log /var/log/nginx/mysql_analysis_error.log;
}
```

### 8.2 启用 HTTPS（推荐）

使用 [Let's Encrypt](https://letsencrypt.org/) 免费证书：

```bash
# 安装 certbot
sudo apt-get install certbot python3-certbot-nginx   # Ubuntu/Debian
# sudo yum install certbot python3-certbot-nginx      # CentOS/RHEL

# 自动配置 HTTPS
sudo certbot --nginx -d your-server.com

# 自动续期（certbot 会自动添加 cron）
sudo certbot renew --dry-run
```

---

## 9. 配置详解

所有后端配置通过 `backend/.env` 文件管理。完整配置项说明：

### 9.1 核心配置

| 配置项 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `DATABASE_URL` | **是** | — | 系统数据库连接串 |
| `SECRET_KEY` | **是** | — | JWT 签名密钥 |
| `DEBUG` | 否 | `True` | 调试模式，生产环境设为 `False` |
| `LOG_LEVEL` | 否 | `INFO` | 日志级别：DEBUG/INFO/WARNING/ERROR |

### 9.2 AI 服务配置

| 配置项 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `AI_ENABLED` | 否 | `True` | AI 诊断总开关 |
| `AI_PROVIDER` | 否 | `zhipu` | 默认 AI 提供商：`zhipu`/`kimi`/`openai`/`claude` |
| `ZHIPU_API_KEY` | 按需 | — | 智谱 API 密钥 |
| `ZHIPU_MODEL` | 否 | `GLM-5` | 智谱模型 |
| `KIMI_API_KEY` | 按需 | — | Kimi API 密钥 |
| `OPENAI_API_KEY` | 按需 | — | OpenAI API 密钥 |
| `ANTHROPIC_API_KEY` | 按需 | — | Claude API 密钥 |
| `AI_TIMEOUT` | 否 | `900` | AI 请求超时（秒） |
| `AI_TEMPERATURE` | 否 | `0.3` | 生成温度 |

### 9.3 CORS 配置

| 配置项 | 说明 |
|--------|------|
| `BACKEND_CORS_ORIGINS` | 允许的前端来源，逗号分隔。开发环境默认包含 `http://localhost:5173` |

### 9.4 前端配置

通过 `frontend/.env.development`（开发）和 `frontend/.env.production`（生产）配置：

| 变量 | 说明 |
|------|------|
| `VITE_BASE_API` | 后端 API 基础路径 |
| `VITE_WS_URL` | WebSocket 连接地址 |

---

## 10. 数据库初始化与迁移

### 10.1 首次部署

后端首次启动时会自动创建所需数据表（`database.py` → `init_db()`）。

也可以使用 Alembic 迁移工具：

```bash
cd backend
alembic upgrade head
```

### 10.2 版本升级

拉取新代码后，执行数据库迁移：

```bash
cd backend
source venv/bin/activate   # Linux/macOS
alembic upgrade head
```

### 10.3 查看迁移状态

```bash
alembic current        # 当前版本
alembic history        # 迁移历史
```

---

## 11. 常见问题

### Q1: `pip install` 失败，提示 `cryptography` 编译错误

**Linux**：安装编译依赖
```bash
# Ubuntu/Debian
sudo apt-get install build-essential libssl-dev libffi-dev python3-dev

# CentOS/RHEL
sudo yum install gcc openssl-devel libffi-devel python3-devel
```

**macOS**：
```bash
xcode-select --install
```

**Windows**：安装 [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)，勾选"桌面开发 with C++"工作负载。

### Q2: 前端启动报 `npm install` 失败

- 检查 Node.js 版本是否 >= 18：`node --version`
- 清除缓存重试：`npm cache clean --force && rm -rf node_modules && npm install`
- 如遇网络问题，使用国内镜像：`npm config set registry https://registry.npmmirror.com`

### Q3: 后端启动报 `DATABASE_URL` 错误

- 确认 `backend/.env` 文件存在且已正确配置
- 确认 MySQL 服务正在运行
- 测试连接：`mysql -u mysql_analysis -p -h localhost mysql_analysis`

### Q4: 前端页面空白或 API 404

- 确认后端已启动：`curl http://localhost:8000/api/health`
- 开发模式下 Vite 会自动代理 API；生产环境需配置 Nginx 或修改 `.env.production`

### Q5: AI 诊断功能不工作

- 确认 `AI_ENABLED=True`
- 确认至少配置了一个 AI 提供商的 API Key
- 检查后端日志中的 AI 请求错误：`tail -f logs/backend.log | grep -i "ai\|llm"`

### Q6: WebSocket 连接失败

- 确认后端 WebSocket 路径为 `/ws`
- Nginx 需要配置 WebSocket 代理（见第 8 节）
- 检查防火墙是否放行对应端口

### Q7: Windows PowerShell 执行策略报错

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### Q8: 如何更换 AI 提供商

编辑 `backend/.env`：

```ini
# 切换到 Kimi
AI_PROVIDER=kimi
KIMI_API_KEY=你的密钥

# 切换到 OpenAI
AI_PROVIDER=openai
OPENAI_API_KEY=你的密钥
OPENAI_BASE_URL=https://api.openai.com/v1   # 或自定义代理地址
```

修改后重启后端即可生效。

---

> 部署完成后，访问系统首页，使用默认账号登录，然后在「连接管理」中添加要诊断的 MySQL 数据库连接即可开始使用。
