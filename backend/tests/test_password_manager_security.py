"""
测试密码管理器安全修复
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from cryptography.fernet import Fernet

from app.core.password_manager import PasswordManager


class TestPasswordManagerSecurity:
    """密码管理器安全测试"""

    def test_password_manager_requires_key(self):
        """测试密码管理器在没有配置密钥时抛出异常"""
        # 清除环境变量
        with patch.dict(os.environ, {}, clear=True):
            # 模拟配置没有设置密钥
            with patch("app.core.password_manager._get_settings") as mock_settings:
                mock_config = MagicMock()
                mock_config.password_encryption_key = ""
                mock_settings.return_value = mock_config

                with pytest.raises(ValueError) as exc_info:
                    PasswordManager()

                assert "密码加密密钥未配置" in str(exc_info.value)

    def test_password_manager_with_env_key(self):
        """测试密码管理器从环境变量读取密钥"""
        # 生成有效的密钥
        valid_key = Fernet.generate_key().decode()

        with patch.dict(os.environ, {"PASSWORD_ENCRYPTION_KEY": valid_key}, clear=True):
            with patch("app.core.password_manager._get_settings") as mock_settings:
                mock_config = MagicMock()
                mock_config.password_encryption_key = ""
                mock_settings.return_value = mock_config

                # 应该成功创建
                manager = PasswordManager()
                assert manager.fernet is not None

    def test_password_manager_with_config_key(self):
        """测试密码管理器从配置读取密钥"""
        # 生成有效的密钥
        valid_key = Fernet.generate_key().decode()

        with patch.dict(os.environ, {}, clear=True):
            with patch("app.core.password_manager._get_settings") as mock_settings:
                mock_config = MagicMock()
                mock_config.password_encryption_key = valid_key
                mock_settings.return_value = mock_config

                # 应该成功创建
                manager = PasswordManager()
                assert manager.fernet is not None

    def test_encrypt_decrypt_roundtrip(self):
        """测试加密解密往返"""
        valid_key = Fernet.generate_key().decode()

        with patch.dict(os.environ, {}, clear=True):
            with patch("app.core.password_manager._get_settings") as mock_settings:
                mock_config = MagicMock()
                mock_config.password_encryption_key = valid_key
                mock_settings.return_value = mock_config

                manager = PasswordManager()

                # 测试加密解密
                original_password = "my_secret_password_123!"
                encrypted = PasswordManager.encrypt_password(original_password)
                decrypted = PasswordManager.decrypt_password(encrypted)

                assert decrypted == original_password
                assert encrypted != original_password

    def test_generate_key_returns_valid_fernet_key(self):
        """测试生成的密钥是有效的 Fernet 密钥"""
        key = PasswordManager.generate_key()

        # 验证密钥可以创建 Fernet 实例
        fernet = Fernet(key.encode())
        assert fernet is not None

        # 验证可以加密解密
        test_data = b"test data"
        encrypted = fernet.encrypt(test_data)
        decrypted = fernet.decrypt(encrypted)
        assert decrypted == test_data
