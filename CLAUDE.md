# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Language Requirement

All output outside of code (comments, docstrings, commit messages, PR descriptions, UI text, error messages, logs) must be in Chinese. Variable/function/class names remain in English.

## Commands

### Backend (from `backend/`)

```bash
# Dev server
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Tests
pytest tests/                                              # all
pytest tests/test_connections.py                           # single file
pytest tests/test_connections.py::test_create_connection   # single function
pytest tests/ -k "connection"                              # pattern match
pytest tests/ --cov=app --cov-report=html                  # with coverage

# Database migrations
alembic revision --autogenerate -m "描述信息"
alembic upgrade head
alembic downgrade -1
```

### Frontend (from `frontend/`)

```bash
npm run dev              # dev server (port 5173)
npm run build            # production build
npm run type-check       # TypeScript check
npm run test             # all tests (vitest)
npm test -- auth.spec.ts # single file
npm run test:coverage    # with coverage
```

### E2E (from `e2e/`)

```bash
npm test                 # Playwright tests
```

## Architecture

This is a MySQL performance diagnostic system built with FastAPI + Vue 3 + Element Plus. The system has been simplified to focus on AI-powered diagnostics — many original monitoring/analysis modules have been removed. What remains:

### Backend (FastAPI + SQLAlchemy 2.x + Pydantic v2)

Three active routers registered in `main.py`:
- `/api/v1/connections/` — MySQL connection CRUD
- `/api/v1/auth/` — JWT authentication (access + refresh tokens)
- `/api/v1/ai/` — AI diagnostic endpoints (the core feature)

Middleware stack (applied bottom-up): `AuthMiddleware` → `CORSMiddleware` → `JSONSerializationMiddleware`

There's a global monkey-patch in `main.py` replacing `json.dumps` and `jsonable_encoder` to handle `Decimal` serialization from SQLAlchemy.

Models: `Connection`, `User`, `RefreshToken` — that's it. Tables are created via `Base.metadata.create_all()` on startup (Alembic exists but isn't the primary migration path).

Config: `pydantic-settings` based (`backend/app/config.py`), reads from `.env`. AI providers supported: zhipu (default, GLM-5), openai (gpt-4o), claude.

### AI Service Layer (`backend/app/services/ai/`)

Clean layered architecture:
- `llm_adapter.py` — abstract `LLMAdapter` with `ZhipuAdapter`, `OpenAIAdapter`, `ClaudeAdapter` implementations using `httpx.AsyncClient`. Factory: `get_llm_adapter(provider)`
- `context_builder.py` — `AIContextBuilder` collects live MySQL data (global status, variables, performance_schema, EXPLAIN, table structure)
- `prompts.py` — system/user prompt templates for diagnosis, SQL optimization, EXPLAIN interpretation. 8 quick-question presets
- `ai_diagnostic_service.py` — orchestrator with `diagnose()`, `optimize_sql()`, `explain_interpret()`, `quick_diagnosis()` etc.
- `llm_logger.py` — structured LLM interaction logging (INFO summaries, DEBUG full content)
- `cache.py` — in-memory AI response cache

SSE streaming protocol: events follow `status → context → analysis → result` (or `error`).

### Frontend (Vue 3 + TypeScript + Vite 6 + Element Plus + Pinia)

Hash-based routing (`createWebHashHistory`). Auth guard redirects unauthenticated users to `/login`.

Active routes:
- `/login`
- `/connections` — connection management
- `/ai-diagnostic` — AI diagnosis chat (default after login)
- `/sql-optimizer` — AI SQL optimization
- `/explain-interpret` — AI EXPLAIN interpretation

API client in `frontend/src/api/client.ts` (axios). Dev proxy in `vite.config.ts` forwards `/api` → `http://127.0.0.1:8000`.

## Code Style

### Python
- Import order: stdlib → third-party → local (`from app.xxx`)
- Classes: PascalCase. Functions: snake_case. Constants: UPPER_SNAKE_CASE
- Errors: `raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="连接不存在")`
- All DB operations go through the CRUD layer

### TypeScript/Vue
- Import order: Vue → Element Plus → local
- Components: PascalCase. Variables: camelCase. Types: PascalCase
- Use `<script setup lang="ts">` with Composition API
- Prefer utility classes from `style/utilities.scss` over inline styles (`.page-container`, `.input-lg`, `.u-mb-20`, `.card-header`, etc.)
- Use `scoped` styles

### Commit Messages

Semantic format in Chinese:
```
feat(scope): 添加新功能
fix(scope): 修复问题
docs: 文档更新
refactor: 重构
test: 测试相关
```

## Test Setup

### Backend
- pytest + pytest-cov + pytest-asyncio + factory_boy
- Key fixtures in `conftest.py`: `client` (FastAPI TestClient), `test_connection`, `mock_mysql_connector`, `sample_connection_data`
- Coverage targets: core logic ≥98%, API routes ≥90%

### Frontend
- vitest + @vue/test-utils
- Element Plus is mocked in test setup
- Coverage target: components ≥85%

### E2E
- Playwright (chromium/firefox/webkit), separate package in `e2e/`
