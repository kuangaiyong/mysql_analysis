#!/bin/bash
# 运行测试并生成覆盖率报告
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing --cov-report=xml
