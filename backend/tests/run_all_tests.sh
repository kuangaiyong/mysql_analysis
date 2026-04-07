#!/bin/bash
# 运行所有后端测试
echo "========================================="
echo "运行所有后端测试..."
echo "========================================="
pytest tests/ -v --tb=short --cov=app --cov-report=html

# 生成覆盖率报告
echo ""
echo "========================================="
echo "测试覆盖率报告"
echo "========================================="
pytest tests/ --cov=app --cov-report=term
