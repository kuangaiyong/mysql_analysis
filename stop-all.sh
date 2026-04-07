#!/bin/bash

# MySQL性能诊断系统停止脚本
# 用法: ./stop-all.sh

echo "🛑 停止 MySQL 性能诊断系统..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# 停止后端
if [ -f logs/backend.pid ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        kill $BACKEND_PID
        echo -e "${GREEN}✅ 后端服务已停止 (PID: $BACKEND_PID)${NC}"
    else
        echo -e "${RED}⚠️  后端服务未运行${NC}"
    fi
    rm logs/backend.pid
else
    echo -e "${RED}⚠️  未找到后端PID文件${NC}"
fi

# 停止前端
if [ -f logs/frontend.pid ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID
        echo -e "${GREEN}✅ 前端服务已停止 (PID: $FRONTEND_PID)${NC}"
    else
        echo -e "${RED}⚠️  前端服务未运行${NC}"
    fi
    rm logs/frontend.pid
else
    echo -e "${RED}⚠️  未找到前端PID文件${NC}"
fi

# 额外清理：杀死所有相关进程
echo "🧹 清理残留进程..."
pkill -f "uvicorn app.main:app" && echo "   已清理后端进程"
pkill -f "vite.*5173" && echo "   已清理前端进程"

echo -e "${GREEN}✅ 所有服务已停止${NC}"
