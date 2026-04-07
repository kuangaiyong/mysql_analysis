"""
WebSocket服务测试
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import WebSocket
from app.services.websocket_service import (
    ConnectionManager,
    websocket_endpoint,
    handle_client_message,
    start_metrics_collection,
    stop_metrics_collection,
    start_collection_for_connection,
    collection_tasks,
    manager,
)


class TestConnectionManager:
    """测试连接管理器"""

    @pytest.fixture
    def manager_instance(self):
        """创建新的管理器实例"""
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        """创建Mock WebSocket"""
        ws = AsyncMock(spec=WebSocket)
        ws.send_json = AsyncMock()
        ws.accept = AsyncMock()
        ws.receive_text = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect_without_connection_id(
        self, manager_instance, mock_websocket
    ):
        """测试无connection_id的连接"""
        await manager_instance.connect(mock_websocket, None)

        assert mock_websocket in manager_instance.active_connections
        assert manager_instance.active_connections[mock_websocket] is None
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_with_connection_id(self, manager_instance, mock_websocket):
        """测试有connection_id的连接"""
        connection_id = 123
        await manager_instance.connect(mock_websocket, connection_id)

        assert mock_websocket in manager_instance.active_connections
        assert manager_instance.active_connections[mock_websocket] == connection_id
        assert connection_id in manager_instance.connection_subscribers
        assert mock_websocket in manager_instance.connection_subscribers[connection_id]

    def test_disconnect_without_subscription(self, manager_instance, mock_websocket):
        """测试无订阅的断开连接"""
        manager_instance.active_connections[mock_websocket] = None
        manager_instance.disconnect(mock_websocket)

        assert mock_websocket not in manager_instance.active_connections

    def test_disconnect_with_subscription(self, manager_instance, mock_websocket):
        """测试有订阅的断开连接"""
        connection_id = 123
        manager_instance.active_connections[mock_websocket] = connection_id
        manager_instance.connection_subscribers[connection_id] = {mock_websocket}

        manager_instance.disconnect(mock_websocket)

        assert mock_websocket not in manager_instance.active_connections
        assert connection_id not in manager_instance.connection_subscribers

    def test_disconnect_with_alert_queue_flush(self, manager_instance, mock_websocket):
        """测试断开连接时刷新告警队列"""
        connection_id = 123
        manager_instance.active_connections[mock_websocket] = connection_id
        manager_instance.connection_subscribers[connection_id] = set()
        manager_instance.alert_queue[connection_id] = [
            {"type": "test_alert", "message": "Test"}
        ]

        with patch.object(manager_instance, "flush_alert_queue") as mock_flush:
            manager_instance.disconnect(mock_websocket)
            mock_flush.assert_called_once_with(connection_id)

    @pytest.mark.asyncio
    async def test_send_personal_message(self, manager_instance, mock_websocket):
        """测试发送个人消息"""
        message = {"type": "test", "data": "hello"}
        await manager_instance.send_personal_message(message, mock_websocket)

        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_personal_message_error(self, manager_instance, mock_websocket):
        """测试发送消息失败"""
        mock_websocket.send_json.side_effect = Exception("Connection closed")
        message = {"type": "test"}

        # 应该捕获异常而不抛出
        await manager_instance.send_personal_message(message, mock_websocket)

    @pytest.mark.asyncio
    async def test_broadcast_to_connection(self, manager_instance, mock_websocket):
        """测试向特定连接广播"""
        connection_id = 123
        manager_instance.connection_subscribers[connection_id] = {mock_websocket}
        message = {"type": "broadcast", "data": "test"}

        await manager_instance.broadcast_to_connection(connection_id, message)

        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_to_connection_no_subscribers(self, manager_instance):
        """测试无订阅者的广播"""
        connection_id = 999
        message = {"type": "broadcast"}

        # 应该不抛出异常
        await manager_instance.broadcast_to_connection(connection_id, message)

    @pytest.mark.asyncio
    async def test_broadcast_to_connection_with_failure(self, manager_instance):
        """测试广播时有连接失败"""
        connection_id = 123
        ws1 = AsyncMock(spec=WebSocket)
        ws1.send_json = AsyncMock()
        ws2 = AsyncMock(spec=WebSocket)
        ws2.send_json = AsyncMock(side_effect=Exception("Failed"))

        manager_instance.connection_subscribers[connection_id] = {ws1, ws2}
        message = {"type": "broadcast"}

        with patch.object(manager_instance, "disconnect") as mock_disconnect:
            await manager_instance.broadcast_to_connection(connection_id, message)
            mock_disconnect.assert_called_once_with(ws2)

    @pytest.mark.asyncio
    async def test_broadcast_all(self, manager_instance, mock_websocket):
        """测试广播给所有连接"""
        manager_instance.active_connections[mock_websocket] = None
        message = {"type": "global", "data": "test"}

        await manager_instance.broadcast_all(message)

        mock_websocket.send_json.assert_called_once_with(message)

    def test_subscribe_to_connection(self, manager_instance, mock_websocket):
        """测试订阅特定connection"""
        old_connection_id = 100
        new_connection_id = 200
        manager_instance.active_connections[mock_websocket] = old_connection_id
        manager_instance.connection_subscribers[old_connection_id] = {mock_websocket}

        manager_instance.subscribe_to_connection(mock_websocket, new_connection_id)

        assert manager_instance.active_connections[mock_websocket] == new_connection_id
        assert mock_websocket not in manager_instance.connection_subscribers.get(
            old_connection_id, set()
        )
        assert (
            mock_websocket in manager_instance.connection_subscribers[new_connection_id]
        )

    @pytest.mark.asyncio
    async def test_send_config_alert_with_deduplication(
        self, manager_instance, mock_websocket
    ):
        """测试告警去重"""
        connection_id = 123
        manager_instance.connection_subscribers[connection_id] = {mock_websocket}
        now = datetime.now(timezone.utc)
        manager_instance.alert_deduplication[connection_id] = now

        await manager_instance.send_config_alert(
            connection_id=connection_id,
            analysis_id=1,
            health_score=80,
            critical_count=1,
            top_issue="test_issue",
        )

        # 由于去重，不应该发送消息
        mock_websocket.send_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_config_alert_without_subscribers(self, manager_instance):
        """测试无订阅者时缓存告警"""
        connection_id = 123
        now = datetime.now(timezone.utc)
        # 清除去重记录
        manager_instance.alert_deduplication = {}

        await manager_instance.send_config_alert(
            connection_id=connection_id,
            analysis_id=1,
            health_score=80,
            critical_count=1,
            top_issue="test_issue",
        )

        assert connection_id in manager_instance.alert_queue
        assert len(manager_instance.alert_queue[connection_id]) == 1

    @pytest.mark.asyncio
    async def test_send_config_alert_queue_limit(self, manager_instance):
        """测试告警队列限制"""
        connection_id = 123
        manager_instance.alert_deduplication = {}
        manager_instance.alert_queue[connection_id] = [{"type": "old"}] * 10

        await manager_instance.send_config_alert(
            connection_id=connection_id,
            analysis_id=1,
            health_score=80,
            critical_count=1,
        )

        assert len(manager_instance.alert_queue[connection_id]) == 10

    @pytest.mark.asyncio
    async def test_send_config_completion(self, manager_instance, mock_websocket):
        """测试发送配置完成通知"""
        connection_id = 123
        manager_instance.connection_subscribers[connection_id] = {mock_websocket}

        await manager_instance.send_config_completion(
            connection_id=connection_id,
            analysis_id=1,
            health_score=85,
        )

        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "config_completion"
        assert call_args["connection_id"] == connection_id
        assert call_args["health_score"] == 85

    @pytest.mark.asyncio
    async def test_flush_alert_queue(self, manager_instance, mock_websocket):
        """测试刷新告警队列"""
        connection_id = 123
        manager_instance.connection_subscribers[connection_id] = {mock_websocket}
        manager_instance.alert_queue[connection_id] = [
            {"type": "alert1", "data": "test1"},
            {"type": "alert2", "data": "test2"},
        ]

        manager_instance.flush_alert_queue(connection_id)
        # 给异步任务一点时间
        await asyncio.sleep(0.1)

        # 队列应该被清空
        assert len(manager_instance.alert_queue[connection_id]) == 0

    def test_flush_alert_queue_empty(self, manager_instance):
        """测试刷新空队列"""
        connection_id = 123

        # 不应该抛出异常
        manager_instance.flush_alert_queue(connection_id)


class TestWebSocketEndpoint:
    """测试WebSocket端点"""

    @pytest.fixture
    def mock_websocket(self):
        """创建Mock WebSocket"""
        ws = AsyncMock(spec=WebSocket)
        ws.send_json = AsyncMock()
        ws.accept = AsyncMock()
        ws.receive_text = AsyncMock(return_value='{"type": "heartbeat"}')
        ws.query_params = {"token": "valid_token"}  # 模拟有效的token参数
        ws.headers = {}
        ws.close = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_websocket_endpoint_with_heartbeat(self, mock_websocket):
        """测试WebSocket端点心跳"""
        # 模拟接收3次消息后断开
        mock_websocket.receive_text.side_effect = [
            '{"type": "heartbeat"}',
            '{"type": "ping"}',
            Exception("Connection closed"),
        ]

        with patch("app.services.websocket_service.manager") as mock_manager:
            with patch("app.services.websocket_service.decode_access_token") as mock_decode:
                mock_decode.return_value = {"sub": "test_user"}  # 模拟有效的token解码
                mock_manager.connect = AsyncMock()
                mock_manager.disconnect = Mock()

                try:
                    await websocket_endpoint(mock_websocket)
                except Exception:
                    pass

                mock_manager.connect.assert_called_once()
                mock_manager.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_endpoint_invalid_json(self, mock_websocket):
        """测试WebSocket端点收到无效JSON"""
        mock_websocket.receive_text.side_effect = [
            "invalid json",
            Exception("Connection closed"),
        ]

        with patch("app.services.websocket_service.manager") as mock_manager:
            with patch("app.services.websocket_service.decode_access_token") as mock_decode:
                mock_decode.return_value = {"sub": "test_user"}  # 模拟有效的token解码
                mock_manager.connect = AsyncMock()
                mock_manager.disconnect = Mock()

                try:
                    await websocket_endpoint(mock_websocket)
                except Exception:
                    pass

                mock_manager.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_endpoint_missing_token(self, mock_websocket):
        """测试WebSocket端点缺少token"""
        mock_websocket.query_params = {}  # 没有token
        mock_websocket.headers = {}

        with patch("app.services.websocket_service.decode_access_token") as mock_decode:
            await websocket_endpoint(mock_websocket)

            # 应该发送错误消息并关闭连接
            mock_websocket.send_json.assert_called_once()
            call_args = mock_websocket.send_json.call_args[0][0]
            assert call_args["type"] == "error"
            assert call_args["code"] == "MISSING_TOKEN"
            mock_websocket.close.assert_called_once()
            # decode_access_token不应该被调用
            mock_decode.assert_not_called()

    @pytest.mark.asyncio
    async def test_websocket_endpoint_invalid_token(self, mock_websocket):
        """测试WebSocket端点无效token"""
        mock_websocket.query_params = {"token": "invalid_token"}

        with patch("app.services.websocket_service.decode_access_token") as mock_decode:
            mock_decode.return_value = None  # 模拟无效token

            await websocket_endpoint(mock_websocket)

            # 应该发送错误消息并关闭连接
            mock_websocket.send_json.assert_called_once()
            call_args = mock_websocket.send_json.call_args[0][0]
            assert call_args["type"] == "error"
            assert call_args["code"] == "INVALID_TOKEN"
            mock_websocket.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_endpoint_token_from_header(self, mock_websocket):
        """测试WebSocket端点从header获取token"""
        mock_websocket.query_params = {}  # 没有query参数token
        mock_websocket.headers = {"authorization": "Bearer header_token"}
        mock_websocket.receive_text.side_effect = [
            '{"type": "heartbeat"}',
            Exception("Connection closed"),
        ]

        with patch("app.services.websocket_service.manager") as mock_manager:
            with patch("app.services.websocket_service.decode_access_token") as mock_decode:
                mock_decode.return_value = {"sub": "test_user"}
                mock_manager.connect = AsyncMock()
                mock_manager.disconnect = Mock()

                try:
                    await websocket_endpoint(mock_websocket)
                except Exception:
                    pass

                # 验证token是从header中提取的
                mock_decode.assert_called_once_with("header_token")
                mock_manager.connect.assert_called_once()

class TestHandleClientMessage:
    """测试客户端消息处理"""

    @pytest.fixture
    def mock_websocket(self):
        """创建Mock WebSocket"""
        ws = AsyncMock(spec=WebSocket)
        ws.send_json = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_handle_subscribe_message(self, mock_websocket):
        """测试处理订阅消息"""
        message = {"type": "subscribe", "connection_id": 123}

        with patch("app.services.websocket_service.manager") as mock_manager:
            mock_manager.subscribe_to_connection = Mock()
            mock_manager.send_personal_message = AsyncMock()

            await handle_client_message(mock_websocket, message)

            mock_manager.subscribe_to_connection.assert_called_once_with(
                mock_websocket, 123
            )

    @pytest.mark.asyncio
    async def test_handle_heartbeat_message(self, mock_websocket):
        """测试处理心跳消息"""
        message = {"type": "heartbeat"}

        with patch("app.services.websocket_service.manager") as mock_manager:
            mock_manager.send_personal_message = AsyncMock()

            await handle_client_message(mock_websocket, message)

            mock_manager.send_personal_message.assert_called_once_with(
                {"type": "pong"}, mock_websocket
            )

    @pytest.mark.asyncio
    async def test_handle_ping_message(self, mock_websocket):
        """测试处理ping消息"""
        message = {"type": "ping"}

        with patch("app.services.websocket_service.manager") as mock_manager:
            mock_manager.send_personal_message = AsyncMock()

            await handle_client_message(mock_websocket, message)

            mock_manager.send_personal_message.assert_called_once_with(
                {"type": "pong"}, mock_websocket
            )


class TestMetricsCollection:
    """测试性能指标收集"""

    @pytest.mark.asyncio
    async def test_start_metrics_collection_connection_not_found(self):
        """测试连接不存在的情况"""
        with patch(
            "app.services.websocket_service.get_connection"
        ) as mock_get_connection:
            mock_get_connection.return_value = None

            await start_metrics_collection(999, 5)

            mock_get_connection.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_metrics_collection(self):
        """测试停止指标收集"""
        connection_id = 123
        mock_task = Mock()
        mock_task.cancel = Mock()
        collection_tasks[connection_id] = mock_task

        await stop_metrics_collection(connection_id)

        mock_task.cancel.assert_called_once()
        assert connection_id not in collection_tasks

    @pytest.mark.asyncio
    async def test_stop_metrics_collection_not_running(self):
        """测试停止未运行的收集"""
        connection_id = 999

        # 不应该抛出异常
        await stop_metrics_collection(connection_id)

    @pytest.mark.asyncio
    async def test_start_collection_for_connection(self):
        """测试为连接启动收集"""
        connection_id = 123

        with patch(
            "app.services.websocket_service.stop_metrics_collection"
        ) as mock_stop:
            with patch(
                "app.services.websocket_service.start_metrics_collection"
            ) as mock_start:
                mock_stop.return_value = None
                mock_start.return_value = None

                await start_collection_for_connection(connection_id, 10)

                mock_stop.assert_called_once_with(connection_id)


class TestGlobalManager:
    """测试全局管理器"""

    def test_global_manager_exists(self):
        """测试全局管理器实例存在"""
        assert manager is not None
        assert isinstance(manager, ConnectionManager)
