#!/bin/bash

# 连接搜索功能测试执行脚本
# 测试连接的搜索、过滤和分页功能

set -e  # 遇到错误立即退出

echo "=========================================="
echo "MySQL连接搜索功能测试"
echo "=========================================="
echo ""

# 检查Python虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 错误: Python虚拟环境不存在"
    echo "请先运行: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

echo "📋 测试场景列表:"
echo "  1. 不带任何搜索参数 - 返回所有连接"
echo "  2. 带name参数搜索 - 根据连接名称模糊匹配"
echo "  3. 带host参数搜索 - 根据主机地址模糊匹配"
echo "  4. 带database参数搜索 - 根据数据库名模糊匹配"
echo "  5. 组合多个参数搜索"
echo "  6. 分页功能测试"
echo ""

# 运行测试
echo "🚀 开始运行测试..."
echo ""

# 运行搜索功能测试
pytest tests/test_connection_search.py -v --tb=short

# 检查测试结果
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 所有测试通过！"
    echo ""
    echo "📊 查看详细测试报告:"
    echo "   pytest tests/test_connection_search.py -v --cov=app --cov-report=html"
    echo ""
    echo "📄 查看覆盖率报告:"
    echo "   open htmlcov/index.html"
else
    echo ""
    echo "❌ 测试失败！请检查上面的错误信息。"
    exit 1
fi
