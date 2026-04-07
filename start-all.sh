#!/bin/bash

# MySQL性能诊断系统启动脚本
# 用法: ./start-all.sh

echo "🚀 启动 MySQL 性能诊断系统..."

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否在项目根目录
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 启动后端
echo -e "${YELLOW}📡 启动后端服务...${NC}"
cd backend

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "⚠️  警告: backend/.env 文件不存在"
    if [ -f .env.example ]; then
        echo "📋 从 .env.example 创建 .env..."
        cp .env.example .env
        echo "⚠️  请编辑 backend/.env 配置数据库连接"
    fi
fi

# 启动后端（后台运行）
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✅ 后端服务已启动 (PID: $BACKEND_PID)${NC}"
echo "   API: http://localhost:8000"
echo "   文档: http://localhost:8000/api/docs"
echo "   日志: logs/backend.log"

cd ..

# 等待后端启动
sleep 3

# 启动前端
echo -e "${YELLOW}🎨 启动前端服务...${NC}"
cd frontend

# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
fi

# 启动前端（后台运行）
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}✅ 前端服务已启动 (PID: $FRONTEND_PID)${NC}"
echo "   前端: http://localhost:5173"
echo "   日志: logs/frontend.log"

cd ..

# 保存PID到文件
mkdir -p logs
echo $BACKEND_PID > logs/backend.pid
echo $FRONTEND_PID > logs/frontend.pid

echo ""
echo -e "${GREEN}✅ 所有服务已启动！${NC}"
echo ""
echo "📝 快速访问："
echo "   前端首页: http://localhost:5173"
echo "   Dashboard: http://localhost:5173/#/dashboard"
echo "   Monitoring: http://localhost:5173/#/monitoring"
echo "   API文档: http://localhost:8000/api/docs"
echo ""
echo "🛑 停止服务: ./stop-all.sh"
echo "📋 查看日志: tail -f logs/backend.log 或 tail -f logs/frontend.log"
