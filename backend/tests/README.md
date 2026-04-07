# 后端测试文档

## 运行测试

### 运行所有测试
```bash
cd backend
pytest tests/ -v
```

### 运行特定模块测试
```bash
pytest tests/test_connections.py -v
pytest tests/test_monitoring.py -v
pytest tests/test_slow_queries.py -v
pytest tests/test_explain.py -v
pytest tests/test_indexes.py -v
pytest tests/test_tables.py -v
pytest tests/test_alerts.py -v
pytest tests/test_reports.py -v
```

### 运行带覆盖率的测试
```bash
pytest tests/ --cov=app --cov-report=html
```

### 查看覆盖率报告
```bash
pytest tests/ --cov=app --cov-report=term
```

### 使用脚本运行测试
```bash
# 运行所有测试
./tests/run_all_tests.sh

# 运行覆盖率报告
./tests/run_coverage.sh
```

### 测试标记
```bash
# 只运行连接管理测试
pytest tests/ -m connection -v

# 只运行API测试
pytest tests/ -m api -v

# 只运行单元测试
pytest tests/ -m unit -v

# 只运行集成测试
pytest tests/ -m integration -v
```

## 测试覆盖范围

| 模块 | 测试文件 | 端点数 | 测试用例数 | 覆盖率目标 |
|------|---------|--------|-----------|-------------|
| 连接管理 | test_connections.py | 7 | 10+ | 90% |
| 性能监控 | test_monitoring.py | 5 | 10+ | 85% |
| 慢查询 | test_slow_queries.py | 9 | 15+ | 90% |
| EXPLAIN | test_explain.py | 4 | 10+ | 85% |
| 索引管理 | test_indexes.py | 5 | 10+ | 85% |
| 表结构 | test_tables.py | 7 | 15+ | 85% |
| 告警管理 | test_alerts.py | 10 | 20+ | 90% |
| 性能报告 | test_reports.py | 7 | 15+ | 85% |

**总体覆盖率目标：87%**

## 测试数据

测试使用SQLite内存数据库进行快速测试，避免依赖外部MySQL服务。

### Fixtures说明

#### db_session
创建测试数据库会话，每个测试函数独立事务，测试结束后自动回滚。

#### client
创建FastAPI测试客户端，使用测试数据库会话覆盖依赖注入。

#### test_connection, test_alert_rule, test_slow_query等
创建测试数据对象，自动管理数据库生命周期。

### Mock对象

- **mock_mysql_connector**: Mock MySQL连接器，避免真实数据库连接
- **mock_performance_collector**: Mock性能采集器
- **mock_redis_cache**: Mock Redis缓存

## 测试命名规范

- `test_<action>_<scenario>`: 测试特定功能在特定场景下
- 使用参数化测试(`@pytest.mark.parametrize`)减少重复代码
- 测试函数名使用下划线分隔，描述清晰

## 编写新测试

1. 在对应测试文件中添加测试函数
2. 使用`client` fixture进行API调用
3. 断言响应状态码和数据结构
4. 使用mock避免外部依赖
5. 确保测试独立，可重复运行

## 覆盖率报告

运行 `pytest tests/ --cov=app --cov-report=html` 后，在 `htmlcov/index.html` 查看详细覆盖率报告。
