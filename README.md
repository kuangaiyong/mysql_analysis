# MySQL 性能诊断与优化系统

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Vue 3](https://img.shields.io/badge/vue-3.5+-brightgreen.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.109+-teal.svg)](https://fastapi.tiangolo.com/)

一个功能强大、易于使用的 MySQL 性能监控、诊断和优化建议系统。基于 FastAPI + Vue3 + Element Plus 构建，提供实时监控、智能分析、自动告警等功能，帮助开发者快速定位和解决数据库性能问题。

## 📋 目录

- [项目简介](#项目简介)
- [核心功能](#核心功能)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [开发指南](#开发指南)
- [配置说明](#配置说明)
- [API 文档](#api-文档)
- [测试](#测试)
- [部署](#部署)
- [常见问题](#常见问题)
- [故障排除](#故障排除)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

## 🎯 项目简介

本系统旨在为数据库管理员和开发者提供一个全面的 MySQL 性能监控和优化工具。通过实时采集性能指标、分析慢查询、检测 SQL 反模式、提供智能优化建议，帮助用户快速发现和解决数据库性能瓶颈，提升数据库运行效率。

### 核心价值

- 🎯 **全面监控** - 覆盖 MySQL 运行状态的 20+ 性能指标
- 🔍 **智能诊断** - 自动识别性能问题并提供优化建议
- 📊 **可视化分析** - 直观的图表展示性能趋势和模式
- 🚨 **实时告警** - 灵活的告警规则，及时发现异常
- 💡 **优化建议** - 基于最佳实践的索引和查询优化方案

## ✨ 核心功能

### 已实现功能

#### 连接管理
- ✅ 支持多个 MySQL 连接配置
- ✅ 连接测试和状态监控
- ✅ 连接信息的增删改查

#### 性能监控
- ✅ 实时性能指标采集（QPS、TPS、连接数等）
- ✅ WebSocket 实时数据推送
- ✅ Prometheus 指标导出

#### EXPLAIN 分析
- ✅ SQL 执行计划分析
- ✅ 执行成本评估
- ✅ 索引使用情况检测

#### 索引管理
- ✅ 索引列表查看
- ✅ 索引使用统计
- ✅ 冗余索引检测

#### 慢查询分析
- ✅ 慢查询日志解析
- ✅ 慢查询模式识别
- ✅ 优化建议生成

#### 查询趋势
- ✅ 查询模式趋势分析
- ✅ 历史数据对比
- ✅ 异常查询检测

#### 索引建议
- ✅ 智能索引优化建议
- ✅ 基于查询模式的索引推荐
- ✅ 索引收益评估

#### 等待事件分析
- ✅ Wait Events 监控
- ✅ 瓶颈事件识别
- ✅ 资源争用分析

#### 告警管理
- ✅ 告警规则配置
- ✅ 告警历史记录
- ✅ 多渠道告警通知

#### 性能报告
- ✅ 性能分析报告生成
- ✅ 多格式导出（PDF、Excel）
- ✅ 定时报告任务

#### 表结构分析
- ✅ 表结构优化建议
- ✅ 字段类型检查
- ✅ 存储引擎分析

#### 配置分析
- ✅ MySQL 配置参数分析
- ✅ 配置优化建议
- ✅ 参数变更追踪

#### 复制监控
- ✅ 主从复制状态监控
- ✅ 复制延迟检测
- ✅ 复制错误告警

#### sys schema 分析
- ✅ MySQL sys 库数据查询
- ✅ 系统视图分析
- ✅ 性能洞察

#### 调优建议
- ✅ 综合性能调优建议
- ✅ 优先级排序
- ✅ 可执行方案

#### SQL 反模式检测
- ✅ 常见 SQL 问题识别
- ✅ 反模式模式匹配
- ✅ 改进建议

#### Optimizer 分析
- ✅ 查询优化器分析
- ✅ 执行计划对比
- ✅ 优化器 hint 建议

#### 事务分析
- ✅ 事务锁监控
- ✅ 死锁检测
- ✅ 长事务识别

#### 执行计划回归检测
- ✅ 计划变更追踪
- ✅ 性能回归检测
- ✅ 计划对比分析

#### 会话管理
- ✅ 当前会话监控
- ✅ 会话详情查看
- ✅ 异常会话终止

#### 规则引擎
- ✅ 自定义分析规则
- ✅ 规则 DSL 支持
- ✅ 规则执行引擎

#### 锁分析
- ✅ 锁等待分析
- ✅ 死锁分析
- ✅ 锁冲突检测

#### 认证与授权
- ✅ 用户注册与登录
- ✅ JWT Token 认证
- ✅ 权限管理

## 🛠 技术栈

### 后端

| 技术 | 版本 | 说明 |
|------|------|------|
| FastAPI | 0.109.0+ | 现代化 Python Web 框架 |
| SQLAlchemy | 2.0.25+ | Python ORM 库 |
| PyMySQL | 1.1.0+ | MySQL 驱动 |
| Pydantic | 2.5.3+ | 数据验证和设置管理 |
| Uvicorn | 0.27.0+ | ASGI 服务器 |
| Alembic | 1.13.1+ | 数据库迁移工具 |
| Redis | 5.0.1+ | 缓存和消息队列 |
| Celery | 5.3.6+ | 异步任务队列 |
| APScheduler | 3.10.4+ | 定时任务调度 |
| Loguru | 0.7.2+ | 日志库 |
| Prometheus Client | 0.19.0+ | 监控指标导出 |

### 前端

| 技术 | 版本 | 说明 |
|------|------|------|
| Vue | 3.5.24 | 渐进式 JavaScript 框架 |
| Vue Router | 4.6.4 | 官方路由管理器 |
| Pinia | 3.0.4 | 状态管理库 |
| Element Plus | 2.10.2 | Vue 3 UI 组件库 |
| TypeScript | 5.9.3 | JavaScript 超集 |
| Vite | 6.0.5 | 下一代前端构建工具 |
| Axios | 1.13.2 | HTTP 客户端 |
| ECharts | 6.0.0 | 数据可视化库 |
| UnoCSS | 66.5.0 | 原子化 CSS 引擎 |

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Node.js 18+
- MySQL 5.7+ 或 8.0+
- Redis 6.0+（可选，用于缓存和任务队列）

### 后端安装

```bash
# 1. 克隆仓库
git clone https://github.com/yourusername/mysql_analysis.git
cd mysql_analysis

# 2. 创建虚拟环境
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置必要的配置项

# 5. 初始化数据库
python3 -m alembic upgrade head

# 6. 启动开发服务器
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

后端服务将在 http://localhost:8000 运行

API 文档地址：http://localhost:8000/api/docs

### 前端安装

```bash
# 1. 安装依赖
cd frontend
npm install

# 2. 配置环境变量
cp .env.development.example .env.development
# 根据需要修改 .env.development 中的配置

# 3. 启动开发服务器
npm run dev
```

前端服务将在 http://localhost:5173 运行

### 验证安装

访问以下地址验证系统是否正常运行：

- 前端页面：http://localhost:5173
- API 文档：http://localhost:8000/api/docs
- 健康检查：http://localhost:8000/api/health

## 📁 项目结构

```
mysql_analysis/
├── backend/                         # FastAPI 后端
│   ├── app/
│   │   ├── main.py                # 应用入口
│   │   ├── config.py              # 配置管理
│   │   ├── database.py            # 数据库连接
│   │   ├── core/                  # 核心功能
│   │   │   ├── logging_config.py  # 日志配置
│   │   │   └── security.py        # 安全相关
│   │   ├── models/                # SQLAlchemy ORM 模型
│   │   │   ├── connection.py      # 连接模型
│   │   │   ├── performance_metric.py  # 性能指标
│   │   │   └── ...
│   │   ├── schemas/               # Pydantic 数据模型
│   │   ├── routers/               # API 路由
│   │   │   ├── connections.py     # 连接管理
│   │   │   ├── monitoring.py      # 性能监控
│   │   │   ├── explain.py         # EXPLAIN 分析
│   │   │   └── ...
│   │   ├── crud/                  # 数据库操作层
│   │   ├── services/              # 业务逻辑层
│   │   ├── tasks/                 # 后台任务
│   │   │   └── metrics_collector.py  # 指标采集
│   │   └── middleware/            # 中间件
│   ├── tests/                     # 测试文件
│   │   ├── test_connections.py   # 连接测试
│   │   ├── conftest.py           # pytest 配置
│   │   └── ...
│   ├── alembic/                   # 数据库迁移
│   │   └── versions/
│   ├── requirements.txt           # Python 依赖
│   ├── .env                       # 环境变量（需手动创建）
│   ├── .env.example               # 环境变量示例
│   └── alembic.ini                # Alembic 配置
│
├── frontend/                       # Vue3 前端
│   ├── src/
│   │   ├── api/                   # API 客户端
│   │   │   ├── connections.ts     # 连接 API
│   │   │   └── index.ts           # API 配置
│   │   ├── components/            # Vue 组件
│   │   │   ├── common/            # 通用组件
│   │   │   └── ...
│   │   ├── hooks/                 # Composition Hooks
│   │   ├── pinia/                 # Pinia 状态管理
│   │   │   ├── stores/            # Store 定义
│   │   │   └── index.ts           # Pinia 配置
│   │   ├── router/                # Vue Router
│   │   │   └── index.ts           # 路由配置
│   │   ├── types/                 # TypeScript 类型定义
│   │   ├── views/                 # 页面组件
│   │   │   ├── Dashboard.vue     # 仪表盘
│   │   │   ├── Connections.vue   # 连接管理
│   │   │   └── ...
│   │   ├── style/                 # 全局样式
│   │   │   ├── variables.scss     # CSS 变量
│   │   │   └── utilities.scss     # 工具类
│   │   ├── App.vue                # 根组件
│   │   └── main.ts                # 入口文件
│   ├── public/                    # 静态资源
│   ├── package.json               # Node 依赖
│   ├── vite.config.ts             # Vite 配置
│   ├── tsconfig.json              # TypeScript 配置
│   ├── vitest.config.ts           # Vitest 配置
│   └── .env.development           # 开发环境变量
│
├── docs/                          # 文档
├── e2e/                           # E2E 测试
├── logs/                          # 日志文件
├── reports/                       # 测试报告
├── .gitignore
├── AGENTS.md                      # Agent 开发指南
└── README.md                      # 本文件
```

## 📖 开发指南

### 代码风格

#### Python 代码规范

- **导入顺序**：标准库 → 第三方库 → 本地应用
- **命名规范**：
  - 类名：PascalCase（如 `Connection`）
  - 函数名：snake_case（如 `get_connection`）
  - 常量：UPPER_SNAKE_CASE（如 `MAX_CONNECTIONS`）
  - 私有变量：_snake_case（如 `_internal_var`）
- **注释**：使用中文注释，关键函数添加 docstring
- **错误处理**：使用 FastAPI 的 `HTTPException`

示例：

```python
from datetime import datetime  # 1. 标准库
from fastapi import APIRouter   # 2. 第三方库
from app.database import Base   # 3. 本地应用

class Connection(Base):
    """连接模型"""
    alert_rules = relationship("AlertRule", back_populates="connection",
                               cascade="all, delete-orphan")

def get_connection(connection_id: int):
    """
    获取连接详情

    Args:
        connection_id: 连接 ID

    Returns:
        Connection 对象
    """
    from fastapi import HTTPException, status

    connection = db.query(Connection).filter(Connection.id == connection_id).first()
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="连接不存在"
        )
    return connection

MAX_CONNECTIONS = 100
```

#### TypeScript/Vue3 代码规范

- **导入顺序**：Vue → Element Plus → 本地
- **命名规范**：
  - 组件名：PascalCase（如 `ConnectionList`）
  - 变量名：camelCase（如 `connectionList`）
  - 类型名：PascalCase（如 `Connection`）
  - 常量：UPPER_SNAKE_CASE（如 `API_BASE_URL`）
- **样式**：优先使用工具类（`utilities.scss`），避免内联样式
- **TypeScript**：严格模式，禁止使用 `any` 类型

示例：

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { Connection } from '@/types/connection'

const connections = ref<Connection[]>([])
const loading = ref(false)

const fetchData = async () => {
  loading.value = true
  try {
    connections.value = await connectionsApi.getAll()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '请求失败')
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>

<template>
  <div class="page-container">
    <!-- 使用工具类 -->
    <el-input class="input-lg" />
    <div class="u-mb-20">内容</div>
  </div>
</template>

<style scoped>
/* 仅必要时使用 scoped 样式 */
</style>
```

#### CSS/SCSS 样式规范

**优先使用工具类（utilities.scss）**：

```html
<!-- 推荐 -->
<el-input class="input-lg" />
<div class="u-mb-20">内容</div>
<div class="page-container">页面内容</div>

<!-- 不推荐 -->
<el-input style="width: 200px" />
```

**常用工具类**：

| 类名 | 用途 |
|------|------|
| `.page-container` | 页面容器，padding: 20px |
| `.search-form` | 搜索表单，margin-bottom: 20px |
| `.card-margin` | 卡片间距，margin-bottom: 20px |
| `.card-header` | flex布局，space-between |
| `.input-sm/md/lg/xl` | 输入框宽度 120/150/200/280px |
| `.w-full` | width: 100% |
| `.u-mb-20`, `.u-mt-20` | margin-bottom/top: 20px |
| `.flex`, `.items-center`, `.justify-between` | Flex布局 |
| `.gap-4` | gap: 16px |

### 开发环境配置

#### 后端开发

```bash
# 进入后端目录
cd backend

# 激活虚拟环境
source venv/bin/activate

# 安装开发依赖
pip install -r requirements.txt

# 启动开发服务器（支持热重载）
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 运行测试
pytest tests/

# 运行测试并生成覆盖率报告
pytest tests/ --cov=app --cov-report=html
```

#### 前端开发

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器（支持热更新）
npm run dev

# 类型检查
npm run type-check

# 运行测试
npm run test

# 运行测试并生成覆盖率报告
npm run test:coverage

# 构建
npm run build
```

### 数据库迁移

```bash
cd backend

# 创建迁移
alembic revision --autogenerate -m "描述信息"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1

# 查看迁移历史
alembic history
```

### 测试策略

#### 测试覆盖率目标

- 核心业务逻辑：≥98%
- API 路由：≥90%
- 前端组件：≥85%

#### 后端测试

```bash
# 运行所有测试
pytest tests/

# 运行单个测试文件
pytest tests/test_connections.py

# 运行单个测试函数
pytest tests/test_connections.py::test_create_connection

# 按标记运行
pytest tests/ -m "connection"

# 匹配模式运行
pytest tests/ -k "connection"

# 生成覆盖率报告
pytest tests/ --cov=app --cov-report=html
```

**可用 Fixtures**（在 `conftest.py` 中）：

- `client`: FastAPI 测试客户端
- `test_connection`: 测试用连接对象
- `mock_mysql_connector`: Mock MySQL 连接器
- `sample_connection_data`: 示例连接数据
- `sample_alert_rule_data`: 示例告警规则数据

#### 前端测试

```bash
# 运行所有测试
npm run test

# 运行单个测试文件
npm test -- ConnectionList.spec.ts

# 运行特定目录的测试
npm test -- src/__tests__/api/

# 运行测试并生成覆盖率报告
npm run test:coverage

# UI 模式运行测试
npm run test:ui
```

**测试示例**：

```typescript
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { ElMessage } from 'element-plus'

describe('ConnectionList', () => {
  it('应该显示连接列表', () => {
    const wrapper = mount(ConnectionList)
    expect(wrapper.find('.connection-list').exists()).toBe(true)
  })
})
```

## ⚙️ 配置说明

### 环境变量

#### 后端配置（`backend/.env`）

```bash
# ==================== 应用信息 ====================
APP_NAME=MySQL性能诊断系统
APP_VERSION=1.0.0
DEBUG=true

# ==================== 数据库配置 ====================
# 系统自己的数据库（存储配置、指标、分析结果等）
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/mysql_analysis

# ==================== 目标MySQL数据库配置（被监控的数据库）====================
TARGET_MYSQL_HOST=localhost
TARGET_MYSQL_PORT=3306
TARGET_MYSQL_USER=root
TARGET_MYSQL_PASSWORD=your_password
TARGET_MYSQL_DATABASE=your_database

# ==================== Redis配置 ====================
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=
REDIS_CACHE_TTL=3600

# ==================== CORS配置 ====================
BACKEND_CORS_ORIGINS=http://localhost:5173,http://localhost:5174,http://localhost:3000

# ==================== 密码加密配置 ====================
PASSWORD_ENCRYPTION_KEY=your_encryption_key_min_32_chars

# ==================== JWT配置 ====================
SECRET_KEY=your_secret_key_min_32_chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ==================== Celery配置 ====================
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# ==================== 性能采集配置 ====================
METRICS_COLLECTION_INTERVAL=60
SLOW_QUERY_THRESHOLD=1.0
SLOW_QUERY_LOG_PATH=/var/log/mysql/slow-query.log

# ==================== 日志配置 ====================
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# ==================== 邮件配置 ====================
SMTP_HOST=localhost
SMTP_PORT=25
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=noreply@example.com
SMTP_USE_TLS=true
```

#### 前端配置（`frontend/.env.development`）

```bash
# API 基础路径
VITE_API_BASE_URL=http://localhost:8000/api/v1

# WebSocket 地址
VITE_WS_BASE_URL=ws://localhost:8000/ws

# 应用标题
VITE_APP_TITLE=MySQL性能诊断系统

# 分页大小
VITE_PAGE_SIZE=20

# 上传文件大小限制（MB）
VITE_MAX_UPLOAD_SIZE=10
```

### 安全配置建议

1. **生产环境必须设置**：
   - `DEBUG=false`
   - 强密码（`SECRET_KEY`、`PASSWORD_ENCRYPTION_KEY`）
   - 使用 HTTPS
   - 配置防火墙

2. **敏感信息保护**：
   - 不要将 `.env` 文件提交到版本控制
   - 使用密钥管理服务（如 AWS Secrets Manager）
   - 定期轮换密钥

3. **数据库安全**：
   - 使用强密码
   - 限制数据库用户权限
   - 启用 SSL 连接
   - 定期备份数据

## 📚 API 文档

系统提供两种 API 文档格式：

### Swagger UI（推荐）

访问地址：http://localhost:8000/api/docs

特点：
- 交互式 API 测试
- 完整的请求/响应示例
- 自动生成的参数说明
- 支持 OAuth2 认证测试

### ReDoc

访问地址：http://localhost:8000/api/redoc

特点：
- 美观的文档展示
- 清晰的结构
- 适合作为正式文档

### API 端点示例

#### 连接管理

```bash
# 获取连接列表
GET /api/v1/connections/

# 创建连接
POST /api/v1/connections/
{
  "name": "生产数据库",
  "host": "localhost",
  "port": 3306,
  "username": "root",
  "password": "encrypted_password",
  "database": "production"
}

# 测试连接
POST /api/v1/connections/{id}/test

# 更新连接
PUT /api/v1/connections/{id}

# 删除连接
DELETE /api/v1/connections/{id}
```

#### 性能监控

```bash
# 获取性能指标
GET /api/v1/monitoring/metrics?connection_id=1

# 获取慢查询列表
GET /api/v1/slow-queries/?connection_id=1&limit=100

# 分析 SQL
POST /api/v1/explain/
{
  "connection_id": 1,
  "sql": "SELECT * FROM users WHERE email = 'test@example.com'"
}
```

## 🧪 测试

### 后端测试

```bash
cd backend

# 运行所有测试
pytest tests/

# 运行特定标记的测试
pytest tests/ -m "not slow"

# 运行测试并显示详细输出
pytest tests/ -v

# 运行测试并生成覆盖率报告
pytest tests/ --cov=app --cov-report=html --cov-report=term

# 只在最近失败的测试上运行
pytest tests/ --lf

# 并行运行测试（需要 pytest-xdist）
pytest tests/ -n auto
```

### 前端测试

```bash
cd frontend

# 运行所有测试
npm run test

# 运行测试并生成覆盖率报告
npm run test:coverage

# 在监听模式下运行测试
npm run test:watch

# UI 模式运行测试
npm run test:ui
```

### E2E 测试

```bash
# 运行 E2E 测试
npm run test:e2e

# UI 模式运行 E2E 测试
npm run test:e2e:ui

# 调试模式运行 E2E 测试
npm run test:e2e:debug
```

## 🚀 部署

### 生产环境部署建议

#### 后端部署

1. **使用 Gunicorn + Uvicorn**：

```bash
# 安装 Gunicorn
pip install gunicorn

# 启动服务
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

2. **使用 Docker**：

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=mysql+pymysql://user:password@db:3306/mysql_analysis
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

  db:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=rootpassword
      - MYSQL_DATABASE=mysql_analysis
    volumes:
      - mysql_data:/var/lib/mysql

  redis:
    image: redis:6.2-alpine
    volumes:
      - redis_data:/data

volumes:
  mysql_data:
  redis_data:
```

3. **使用 Nginx 反向代理**：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端
    location / {
        root /var/www/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

#### 前端部署

```bash
# 构建生产版本
cd frontend
npm run build

# 部署到 Nginx
cp -r dist/* /var/www/frontend/
```

### 监控和日志

1. **使用 Prometheus + Grafana** 监控应用指标
2. **使用 ELK Stack** 或 **Loki** 收集日志
3. **配置告警规则** 及时发现问题

### 备份策略

1. **数据库备份**：定期备份系统数据库和目标数据库
2. **配置备份**：备份配置文件和环境变量
3. **代码备份**：使用 Git 版本控制

## ❓ 常见问题

### Q1: 如何添加新的 MySQL 连接？

**A**: 在前端"连接管理"页面，点击"添加连接"按钮，填写连接信息后点击"测试连接"，确认无误后保存。

### Q2: 慢查询日志在哪里配置？

**A**: 需要在目标 MySQL 服务器上配置慢查询日志：

```sql
-- 开启慢查询日志
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;  -- 超过 1 秒的查询记录为慢查询
SET GLOBAL slow_query_log_file = '/var/log/mysql/slow-query.log';
```

### Q3: 如何配置告警通知？

**A**: 在"告警管理"页面创建告警规则，配置触发条件和通知方式（邮件、Webhook 等）。需要在 `.env` 文件中配置 SMTP 相关参数。

### Q4: 系统支持哪些 MySQL 版本？

**A**: 支持 MySQL 5.7+ 和 MySQL 8.0+。

### Q5: 如何重置用户密码？

**A**: 目前系统提供注册功能，用户可以通过注册重置密码。如需管理员重置，请直接在数据库中修改 `users` 表的 `password_hash` 字段。

### Q6: 系统的性能开销如何？

**A**: 系统对被监控数据库的性能开销很小，主要开销来自：
- 定期采集性能指标（默认每 60 秒一次）
- 执行 EXPLAIN 分析
- 读取慢查询日志

可以通过调整 `METRICS_COLLECTION_INTERVAL` 参数来降低采集频率。

### Q7: 如何导出性能报告？

**A**: 在"性能报告"页面选择报告类型和时间范围，点击"生成报告"，生成后可导出为 PDF 或 Excel 格式。

## 🔧 故障排除

### 后端启动失败

**问题**: `ModuleNotFoundError: No module named 'xxx'`

**解决方案**:
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

**问题**: `OperationalError: Unable to connect to database`

**解决方案**:
1. 检查 `.env` 文件中的 `DATABASE_URL` 配置
2. 确认数据库服务已启动
3. 验证数据库用户名和密码
4. 检查防火墙设置

### 前端启动失败

**问题**: `npm install` 失败

**解决方案**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

**问题**: API 请求失败（CORS 错误）

**解决方案**:
1. 检查后端 `BACKEND_CORS_ORIGINS` 配置
2. 确认前端和后端地址匹配
3. 检查浏览器控制台具体错误信息

### 数据库连接失败

**问题**: "连接测试失败"

**解决方案**:
1. 验证目标 MySQL 服务器是否运行
2. 检查网络连接和防火墙
3. 确认用户权限是否足够
4. 检查 MySQL 配置（`max_connections`）

### 性能指标不更新

**问题**: 仪表盘数据不刷新

**解决方案**:
1. 检查 Celery worker 是否运行
2. 查看 Redis 连接状态
3. 检查任务日志：`tail -f logs/celery.log`
4. 确认 `METRICS_COLLECTION_INTERVAL` 配置

### 慢查询分析为空

**问题**: 慢查询列表为空

**解决方案**:
1. 确认目标 MySQL 已开启慢查询日志
2. 检查 `long_query_time` 设置
3. 验证慢查询日志文件路径
4. 确认系统有权限读取日志文件

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

### 开发流程

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -m "Add some feature"`
4. 推送到分支：`git push origin feature/your-feature`
5. 提交 Pull Request

### 代码规范

- 遵循项目的代码风格指南（见 [AGENTS.md](./AGENTS.md)）
- 所有输出必须使用中文
- 添加适当的注释和文档
- 编写测试用例
- 确保测试通过

### Commit 消息规范

使用语义化提交消息：

```
feat: 添加新功能
fix: 修复问题
docs: 文档更新
style: 代码格式（不影响功能）
refactor: 重构
test: 测试相关
chore: 构建/工具相关
```

示例：

```
feat(connections): 支持批量连接测试

- 添加批量测试接口
- 优化测试逻辑性能
- 更新前端界面支持批量操作

Closes #123
```

### Pull Request 要求

1. 描述清晰的 PR 标题和说明
2. 关联相关的 Issue
3. 通过所有测试
4. 代码审查通过
5. 更新相关文档

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](./LICENSE) 文件。

## 📮 联系方式

- 问题反馈：[GitHub Issues](https://github.com/yourusername/mysql_analysis/issues)
- 功能建议：[GitHub Discussions](https://github.com/yourusername/mysql_analysis/discussions)
- 邮箱：your-email@example.com

## 🙏 致谢

感谢以下开源项目：

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Python Web 框架
- [Vue.js](https://vuejs.org/) - 渐进式 JavaScript 框架
- [Element Plus](https://element-plus.org/) - Vue 3 UI 组件库
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python ORM 库
- [ECharts](https://echarts.apache.org/) - 数据可视化库

---

**⭐ 如果这个项目对你有帮助，请给个 Star 支持一下！**
