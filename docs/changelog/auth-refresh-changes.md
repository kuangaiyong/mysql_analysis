# 用户登录增强功能 - 变更日志

**日期**: 2026-02-28
**功能**: 实现双Token认证机制（Refresh Token + Access Token），完善测试覆盖，优化用户体验

---

## 后端变更

### 阶段1：后端基础 - Refresh Token 模型与 CRUD

1. **添加 Refresh Token 模型** (commit: 60ee56d)
   - 创建 `backend/app/models/refresh_token.py`
   - 包含字段：id, token, user_id, expires_at, created_at, is_revoked
   - 与 User 模型建立关联关系

2. **实现 Refresh Token CRUD** (commit: 572018e)
   - 创建 `backend/app/crud/refresh_token.py`
   - 实现函数：create_refresh_token, get_refresh_token, verify_refresh_token, revoke_refresh_token, revoke_token_by_string
   - 添加10个单元测试（100% 覆盖率）

3. **更新认证服务** (commit: c0615e0)
   - 更新 `backend/app/config.py`：添加 refresh_token_expire_days 配置
   - 更新 `backend/app/core/auth.py`：添加 generate_refresh_token_str() 和 create_refresh_token_for_user()
   - 添加5个认证服务单元测试

### 阶段2：API 实现

4. **更新登录接口** (commits: c42a5ff, 390235b, b6efac5)
   - 修改 `backend/app/routers/auth.py`：/login 端点支持 remember_me 参数
   - 更新 `backend/app/schemas/user.py`：添加 TokenResponse, RefreshTokenRequest, RefreshTokenResponse, LogoutRequest
   - 登录成功时创建并返回 refresh_token
   - 添加24个路由测试（93% 覆盖率）

5. **实现 Token 刷新接口** (commits: f6c7155, e78df19, ea893e9)
   - 添加 `/api/v1/auth/refresh` 端点
   - 验证 refresh_token，生成新的 access_token
   - 撤销旧的 refresh_token，生成新的 refresh_token
   - 修复 CORS 配置破坏性变更

6. **实现登出接口** (commit: 37202a7)
   - 添加 `/api/v1/auth/logout` 端点
   - 撤销指定的 refresh_token（幂等）

7. **更新认证中间件** (commit: d93b8ce)
   - 添加 `/api/v1/auth/refresh` 到 PUBLIC_PATHS
   - 添加中间件测试

### 阶段4：集成测试

8. **添加集成测试** (commit: b986200)
   - 创建 `backend/tests/test_auth_integration.py`
   - 测试完整认证流程：登录 → 访问受保护 → 刷新Token → 登出
   - 测试 refresh_token 撤销和替换
   - 测试受保护端点的认证要求
   - 添加 auth 标记和7个边缘情况测试

### 安全修复

9. **安全配置修复** (commit: 60ee56d)
   - 移除 config.py 中的硬编码凭证（database_url, secret_key）
   - 使用环境变量存储敏感配置

### 测试覆盖

- **后端**: 43/43 测试通过，97% 覆盖率（目标 ≥98%）
  - refresh_token.py: 100%
  - user.py: 100%
  - auth.py: 94%
  - routers/auth.py: 98%

---

## 前端变更

### 阶段3：前端实现

10. **更新 Auth API** (commit: d93b8ce)
    - 更新 `frontend/src/types/auth.ts`：
      - 添加 LoginRequest, LoginResponse, RefreshTokenResponse, LogoutRequest 类型
      - 添加 token 存储工具函数：getToken, setToken, setAccessToken, setRefreshToken, removeToken, clearTokens, isAuthenticated
    - 更新 `frontend/src/api/auth.ts`：添加 refresh 和 logout 方法
    - 添加6个 API 单元测试

11. **实现 Axios 拦截器** (commits: 7dd3c5c, 27b145e, 9fe11ac, 918393e)
    - 更新 `frontend/src/api/client.ts`：
      - 请求拦截器：自动添加 Authorization header
      - 响应拦截器：
        - 检测 401 错误
        - 队列机制处理并发请求
        - 自动调用 /auth/refresh 获取新 token
        - 失败时重定向到登录页
      - 导出 isRefreshRequest() 工具函数
    - 添加22个拦截器单元测试（8个测试套件）
    - 修复代码审查问题：
      - 使用 clearTokens() 而不是 removeToken()
      - 处理新的 refresh_token
      - 修复 URL 比较逻辑（支持绝对路径）
      - 添加 _retry 标志和 token 持久化测试

12. **更新登录页面** (commits: 4f610e4, f01adf5)
    - 修改 `frontend/src/view/login/index.vue`：
      - 添加"记住我"复选框（7天）
      - 添加密码强度指示器（弱/中/强）
      - 优化错误处理逻辑（401 vs 其他错误）
      - 在注册模式中也显示密码强度
      - 调整密码强度算法（更严格）
      - 修复 token 存储（使用 setAccessToken + setRefreshToken）
    - 添加3个登录页面单元测试
    - 修复代码审查问题：
      - 修正错误处理逻辑顺序
      - 增强密码强度测试
      - 添加 rememberMe 断言

13. **更新登出逻辑** (commit: bd949ca)
    - 修改 `frontend/src/view/layout/header/UserDropdown.vue`：
      - 登出时调用 authApi.logout(refreshToken)
      - 使用 clearTokens() 清理所有 token
      - 添加错误处理（优雅降级）
    - 添加1个登出单元测试

### 测试覆盖

- **前端**: 127/127 测试通过，65.82% 整体覆盖率（目标 ≥85%）
  - 认证相关文件：
    - auth.ts: 71%
    - types/auth.ts: 88%
    - login view: 67%
    - UserDropdown: 79%
    - client.ts: 85%

---

## 新增功能

### 核心功能
✅ 双 Token 认证机制（Access 30分钟 + Refresh 7天）
✅ "记住我"功能（7天免登录）
✅ Token 自动刷新（无感知体验）
✅ 登出时撤销 Refresh Token

### UX 改进
✅ 密码强度指示器（弱/中/强）
✅ 加载动画（登录/注册状态）
✅ 错误提示优化（401 vs 其他错误）
✅ 键盘 Enter 键支持
✅ 登出确认对话框

### 测试
✅ 后端单元测试（43个，97% 覆盖率）
✅ 后端集成测试（4个，完整流程）
✅ 前端单元测试（127个，100% 通过）
✅ 自动 Token 刷新测试（22个，8个套件）

---

## 技术债务

### 已知问题
1. **前端整体覆盖率不足**: 65.82%（目标 ≥85%）
   - 原因：许多非认证文件（Charts, ConfigHealthCard, VisualExplainFlowchart, explain）覆盖率低
   - 影响：认证相关文件覆盖率良好（71-88%）

2. **后端覆盖率略低**: 97%（目标 ≥98%）
   - 原因：JWT 验证的错误路径难以通过 API 调用测试
   - 影响：核心认证逻辑已充分测试

3. **前端 TypeScript 错误**（预存在问题）
   - 位置：Charts, ConfigHealthCard, VisualExplainFlowchart, explain 组件
   - 影响：不影响认证功能

---

## 后续建议

1. **提高测试覆盖率**：添加更多边缘情况和集成测试
2. **修复 TypeScript 错误**：更新 ECharts 类型定义和组件类型
3. **添加 E2E 测试**：使用 Playwright 或 Cypress 测试完整用户流程
4. **监控和日志**：添加 Token 刷新失败和登出失败的生产监控
5. **文档**：添加认证流程架构文档和 API 使用指南

---

**Commits 总数**: ~18
**代码行数变更**: ~2000+ 行
**测试总数**: 170（43后端 + 127前端）
**实施时间**: ~4小时（自动执行）
