# MySQL性能诊断与优化系统 - Agent开发指南

AI代理在此代码库工作的完整指南。遵循最小化修改原则。

## 语言规约（强制）

**所有输出必须使用中文**，代码之外的任何内容都使用中文。

### 文档与说明
- README、CHANGELOG、CONTRIBUTING 等文档
- API 文档、接口说明
- 架构设计文档、技术方案

### 代码相关
- 代码注释（单行、多行、文档字符串 docstring）
- TODO、FIXME、NOTE、HACK 等标记注释
- commit message（提交信息）
- PR 标题和描述
- 变量、函数、类的说明性注释
- 测试用例的描述字符串（describe/it 的说明文字）

### 用户界面
- 前端页面文字、提示信息
- 错误消息、警告信息
- 表单验证提示
- 成功/失败反馈信息
- API 返回的错误详情（detail）

### 配置与日志
- 配置文件中的说明性注释
- 日志输出信息
- 环境变量说明

### 沟通交流
- 与用户的对话、回答
- 思考过程、分析说明
- 草稿、计划、方案

---

## 项目结构

```
mysql_analysis/
├── backend/                    # FastAPI后端
│   ├── app/{main,config,database}.py
│   ├── app/{models,schemas,routers,crud,services,tasks}/
│   ├── tests/                  # pytest测试
│   └── pytest.ini
└── frontend/                   # Vue3前端
    ├── src/{api,components,hooks,pinia,router,types,view}/
    ├── src/style/              # 全局样式
    │   ├── variables.scss      # CSS变量定义
    │   └── utilities.scss      # 工具类（优先使用）
    └── vitest.config.ts
```

---

## 构建、测试命令

### 后端

```bash
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 测试
pytest tests/                           # 所有测试
pytest tests/test_connections.py        # 单个文件
pytest tests/test_connections.py::test_create_connection  # 单个函数
pytest tests/ -m "connection"           # 按标记
pytest tests/ -k "connection"           # 匹配模式
pytest tests/ --cov=app --cov-report=html  # 带覆盖率
```

### 前端

```bash
cd frontend
npm run dev                 # 开发服务器
npm run type-check          # 类型检查
npm run build               # 构建
npm run test                # 所有测试
npm test -- ConnectionList.spec.ts     # 单个文件
npm test -- src/__tests__/api/         # 特定目录
npm run test:coverage       # 带覆盖率
```

---

## Python代码风格

### 导入顺序：标准库 → 第三方库 → 本地应用

```python
from datetime import datetime  # 1. 标准库
from fastapi import APIRouter  # 2. 第三方库
from app.database import Base  # 3. 本地应用
```

### 命名：类PascalCase，函数snake_case，常量UPPER_SNAKE_CASE

```python
class Connection(Base):
    alert_rules = relationship("AlertRule", back_populates="connection", cascade="all, delete-orphan")

def get_connection(): ...
MAX_CONNECTIONS = 100

# 错误处理
from fastapi import HTTPException, status
raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="连接不存在")
```

---

## TypeScript/Vue3代码风格

### 导入顺序：Vue → Element Plus → 本地

```typescript
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { Connection } from '@/types/connection'
```

### 命名：组件PascalCase，变量camelCase，类型PascalCase

### 组件模板

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

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
  <div class="page-container"><!-- 内容 --></div>
</template>

<style scoped>
</style>
```

---

## CSS/SCSS样式规范

### 优先使用工具类（utilities.scss）

```html
<!-- 推荐 -->
<el-input class="input-lg" />
<div class="u-mb-20">内容</div>
<div class="page-container">页面内容</div>

<!-- 不推荐 -->
<el-input style="width: 200px" />
```

### 常用工具类

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

### CSS变量

```scss
// 颜色
--primary-color: #409eff;
--success-color: #67c23a;
--warning-color: #e6a23c;
--danger-color: #f56c6c;
// 间距
--spacing-xs: 4px; --spacing-sm: 8px; --spacing-md: 12px; --spacing-lg: 16px; --spacing-xl: 20px;
```

---

## 重要规则

### 安全
- 不将密码、密钥提交到代码仓库
- 使用环境变量存储敏感配置
- 使用`password_encrypted`存储加密密码

### 数据库
- 所有操作通过CRUD层
- 使用`db.commit()`和`db.refresh()`确保持久化

### API
- 所有路由包含响应模型
- 使用依赖注入获取数据库会话
- 返回404给不存在的资源

### 前端
- 所有API调用必须异步
- 使用`scoped`样式
- **优先使用工具类（utilities.scss）替代内联样式**

---

## 测试

### 后端Fixtures（conftest.py）

- `client`: FastAPI测试客户端
- `test_connection`: 测试用连接对象
- `mock_mysql_connector`: Mock MySQL连接器
- `sample_connection_data`, `sample_alert_rule_data`: 示例数据

### 前端测试

```typescript
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
// Element Plus已在setup.ts中mock
```

---

## 测试覆盖目标

- 核心业务逻辑：≥98%
- API路由：≥90%
- 前端组件：≥85%

---

最后更新：2026年3月
