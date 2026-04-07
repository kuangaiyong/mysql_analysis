# 用户登录增强功能设计

**日期**: 2026-02-27
**版本**: 1.0
**状态**: 已批准

---

## 概述

增强现有的用户登录功能，实现「记住我」机制、完善测试覆盖、优化用户体验。

## 功能需求

### 1. 「记住我」功能
- 支持用户勾选「记住我」后，7天内无需重新登录
- 使用 Refresh Token + Access Token 双 Token 机制
- Access Token: 30分钟有效期
- Refresh Token: 7天有效期

### 2. 测试覆盖
- 后端认证逻辑测试覆盖率 ≥98%
- 前端组件测试覆盖率 ≥85%
- 完整的集成测试

### 3. 用户体验改进
- 密码强度指示器（弱/中/强）
- 登录/注册加载动画
- 优化的错误提示
- 键盘 Enter 键提交支持

---

## 设计方案

### Token 机制

**双 Token 认证流程：**

1. 用户登录 → 服务器返回 `{ access_token, refresh_token, token_type }`
2. Access Token 过期（30分钟）→ 前端使用 Refresh Token 自动刷新
3. Refresh Token 过期（7天）→ 用户需重新登录

**安全措施：**
- Refresh Token 使用随机 UUID + 用户 ID 哈希
- Refresh Token 一次性使用，刷新后旧 Token 失效
- 支持撤销（登出时删除 Refresh Token）

**配置项（config.py）：**
```python
access_token_expire_minutes: int = 30
refresh_token_expire_days: int = 7
```

---

### 数据模型

#### 新增 RefreshToken 模型

**文件**: `backend/app/models/refresh_token.py`

```python
class RefreshToken(Base):
    """Refresh Token 表"""

    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(255), unique=True, nullable=False, index=True, comment="Refresh Token")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    expires_at = Column(DateTime, nullable=False, comment="过期时间")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    is_revoked = Column(Boolean, default=False, comment="是否已撤销")

    user = relationship("User", back_populates="refresh_tokens")
```

#### 修改 User 模型

**文件**: `backend/app/models/user.py`

```python
class User(Base):
    # ... 现有字段 ...

    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
```

#### Schema 更新

**文件**: `backend/app/schemas/user.py`

```python
class TokenResponse(BaseModel):
    """Token响应模型"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """刷新Token请求模型"""
    refresh_token: str
```

---

### API 设计

#### 修改端点

**POST /api/v1/auth/login**
- 新增请求参数：`remember_me: boolean`
- 响应变更：返回 `{ access_token, refresh_token, token_type }`

```json
Request: { "username": "...", "password": "...", "remember_me": true }
Response: {
  "access_token": "eyJ...",
  "refresh_token": "uuid...",
  "token_type": "bearer"
}
```

#### 新增端点

**POST /api/v1/auth/refresh**
- 使用 Refresh Token 刷新 Access Token

```json
Request: { "refresh_token": "uuid..." }
Response: { "access_token": "eyJ...", "token_type": "bearer" }
```

**POST /api/v1/auth/logout**
- 撤销 Refresh Token

```json
Request: { "refresh_token": "uuid..." }
Response: { "message": "登出成功" }
```

#### AuthMiddleware 更新

**文件**: `backend/app/middleware/auth.py`

公开路由新增：
```python
PUBLIC_PATHS = {
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",  # 新增
    "/api/docs",
    "/api/redoc",
    "/openapi.json",
    "/api/health",
}
```

---

### 前端改动

#### 1. 登录页面

**文件**: `frontend/src/view/login/index.vue`

**新增功能：**
- 「记住我」复选框
- 密码强度指示器（实时显示 弱/中/强，颜色：红/黄/绿）
- 加载动画（登录/注册时按钮显示 loading 状态）
- 键盘支持（Enter 键提交表单）
- 错误提示优化

**表单数据：**
```typescript
const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  rememberMe: false  // 新增
})
```

#### 2. Auth API

**文件**: `frontend/src/api/auth.ts`

```typescript
export const authApi = {
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const formData = new FormData()
    formData.append('username', data.username)
    formData.append('password', data.password)
    formData.append('remember_me', String(data.rememberMe))
    const response = await service.post<LoginResponse>('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
    return response.data
  },

  refresh: async (refreshToken: string): Promise<TokenResponse> => {
    const response = await service.post<TokenResponse>('/auth/refresh', { refresh_token: refreshToken })
    return response.data
  },

  logout: async (refreshToken: string): Promise<void> => {
    await service.post('/auth/logout', { refresh_token: refreshToken })
  }
}
```

#### 3. Token 存储

**文件**: `frontend/src/types/auth.ts`

```typescript
export const ACCESS_TOKEN_KEY = 'mysql_analysis_access_token'
export const REFRESH_TOKEN_KEY = 'mysql_analysis_refresh_token'

export const setAccessToken = (token: string): void => {
  localStorage.setItem(ACCESS_TOKEN_KEY, token)
}

export const setRefreshToken = (token: string): void => {
  localStorage.setItem(REFRESH_TOKEN_KEY, token)
}

export const getRefreshToken = (): string | null => {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export const clearTokens = (): void => {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}
```

#### 4. Axios 拦截器

**文件**: `frontend/src/api/client.ts`

**响应拦截器 - 自动刷新 Token：**
```typescript
service.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { status, config } = error.response || {}

    if (status === 401 && config.url !== '/auth/refresh') {
      const refreshToken = getRefreshToken()
      if (refreshToken) {
        try {
          const { access_token } = await authApi.refresh(refreshToken)
          setAccessToken(access_token)
          config.headers.Authorization = `Bearer ${access_token}`
          return service.request(config)
        } catch {
          clearTokens()
          window.location.href = '/#/login'
        }
      } else {
        window.location.href = '/#/login'
      }
    }
    return Promise.reject(error)
  }
)
```

#### 5. 用户登出

**文件**: `frontend/src/view/layout/header/UserDropdown.vue`

```typescript
const handleLogout = async () => {
  const refreshToken = getRefreshToken()
  if (refreshToken) {
    await authApi.logout(refreshToken)
  }
  clearTokens()
  ElMessage.success('已退出登录')
  router.push('/login')
}
```

---

### 测试策略

#### 后端测试

**目标覆盖率**: 认证逻辑 ≥98%

**测试文件结构：**
```
backend/tests/
├── test_auth.py              # 认证路由测试
├── test_auth_service.py       # Auth核心服务测试
├── test_refresh_token.py      # Refresh Token CRUD测试
└── crud/
    └── test_user.py          # 用户CRUD测试（补充）
```

**核心测试用例：**

**test_auth.py**
- 登录成功（remember_me=true/false）
- 登录失败（用户名错误/密码错误）
- 刷新 Access Token（成功/过期/已撤销）
- 登出成功
- 注册成功/用户名重复

**test_auth_service.py**
- create_access_token - 正确生成JWT
- decode_access_token - 正确解码/过期检测
- verify_password - bcrypt验证
- get_password_hash - bcrypt哈希生成

**test_refresh_token.py**
- 创建 Refresh Token
- 验证 Token（有效/过期/已撤销）
- 撤销 Token
- 清理过期 Token

**crud/test_user.py**
- authenticate_user - 认证成功/失败

#### 前端测试

**目标覆盖率**: 组件 ≥85%

**测试文件结构：**
```
frontend/src/__tests__/
├── view/
│   └── login.spec.ts        # 登录页面测试
├── api/
│   └── auth.spec.ts         # Auth API测试
└── utils/
    └── auth.spec.ts         # Token存储工具测试
```

**核心测试用例：**

**login.spec.ts**
- 渲染登录表单
- 记住我复选框交互
- 密码强度指示器（弱/中/强）
- 表单验证（必填/长度/密码匹配）
- 键盘Enter提交
- 加载状态显示
- 错误提示显示

**auth.spec.ts (API)**
- login - 成功/失败
- refresh - 成功/失败
- logout - 成功
- axios interceptor刷新token

**auth.spec.ts (Utils)**
- setToken/getToken/removeToken
- setAccessToken/setRefreshToken
- clearTokens

#### 集成测试

**文件**: `backend/tests/test_auth_integration.py`

**测试场景：**
- 完整登录流程 → 存储 token → 访问受保护资源
- Token过期 → 自动刷新 → 重试请求
- Refresh Token过期 → 强制重新登录
- 登出 → Token撤销 → 访问受保护资源失败

#### 测试覆盖率命令

```bash
# 后端
pytest tests/ -m "auth" --cov=app.core.auth --cov=app.crud.user --cov=app.routers.auth --cov-report=html

# 前端
npm run test:coverage -- src/__tests__/view/login.spec.ts src/__tests__/api/auth.spec.ts
```

---

## 实施步骤

### 阶段1：后端基础
1. 创建 RefreshToken 模型
2. 更新 User 模型关联
3. 实现 RefreshToken CRUD
4. 更新认证服务（生成/验证 Refresh Token）

### 阶段2：API 实现
1. 修改 /login 接口支持 remember_me
2. 实现 /refresh 接口
3. 实现 /logout 接口
4. 更新 AuthMiddleware

### 阶段3：前端实现
1. 更新 Auth API（login/refresh/logout）
2. 实现 Token 存储工具
3. 更新 Axios 拦截器（自动刷新）
4. 更新登录页面（记住我、密码强度、UX改进）
5. 更新登出逻辑

### 阶段4：测试
1. 后端单元测试（auth_service, refresh_token）
2. 后端路由测试（auth）
3. 后端集成测试
4. 前端组件测试（login）
5. 前端 API 测试（auth）
6. 前端集成测试

### 阶段5：验证与部署
1. 运行所有测试，确保覆盖率达标
2. 手动测试完整登录流程
3. 代码审查
4. 部署到测试环境
5. 生产环境部署

---

## 预期成果

- ✅ 用户可勾选「记住我」，7天内无需重新登录
- ✅ Access Token 30分钟自动刷新，无感知体验
- ✅ 完整的测试覆盖（后端≥98%、前端≥85%）
- ✅ 优化的用户体验（密码强度、加载动画、错误提示、键盘支持）
- ✅ 安全的双 Token 认证机制

---

## 风险与注意事项

1. **Token 安全**: Refresh Token 必须使用 HTTPS 传输
2. **数据库迁移**: Refresh Token 表需要创建（生产环境使用 Alembic）
3. **向后兼容**: 旧版本 Token 将无法刷新，需要重新登录
4. **并发刷新**: 多个请求同时过期可能导致多次刷新，需要加锁或去重

---

## 参考资料

- FastAPI OAuth2 文档
- JWT RFC 7519
- Refresh Token 最佳实践
- Element Plus 组件文档
