"""
密码加密/解密工具
"""

from cryptography.fernet import Fernet
from typing import Optional
import base64
import os

# 延迟导入避免循环依赖
_settings = None


def _get_settings():
    """延迟加载配置"""
    global _settings
    if _settings is None:
        from app.config import settings
        _settings = settings
    return _settings

class PasswordManager:
    """密码管理器 - 使用Fernet加密"""

    def __init__(self, key: Optional[bytes] = None):
        """
        初始化密码管理器

        Args:
            key: 加密密钥（32字节URL安全的base64编码字符串）
        """
        if key:
            self.fernet = Fernet(key)
        else:
            # 从配置或环境变量加载密钥
            settings = _get_settings()
            config_key = settings.password_encryption_key
            
            if config_key:
                self.fernet = Fernet(config_key.encode())
            else:
                # 开发环境：尝试从环境变量获取，否则抛出异常
                env_key = os.environ.get("PASSWORD_ENCRYPTION_KEY")
                if env_key:
                    self.fernet = Fernet(env_key.encode())
                else:
                    raise ValueError(
                        "密码加密密钥未配置。请设置 PASSWORD_ENCRYPTION_KEY 环境变量 "
                        "或在配置文件中设置 password_encryption_key"
                    )

    @staticmethod
    def generate_key() -> str:
        """
        生成加密密钥

        Returns:
            Base64编码的密钥字符串
        """
        key = Fernet.generate_key()
        return key.decode()

    @staticmethod
    def encrypt_password(password: str, key: Optional[str] = None) -> str:
        """
        加密密码

        Args:
            password: 明文密码
            key: 加密密钥（可选，如不提供则使用默认）

        Returns:
            加密后的密码（Base64编码）
        """
        if key:
            fernet = Fernet(key.encode())
        else:
            manager = PasswordManager()
            fernet = manager.fernet

        encrypted = fernet.encrypt(password.encode())
        return base64.b64encode(encrypted).decode()

    @staticmethod
    def decrypt_password(encrypted_password: str, key: Optional[str] = None) -> str:
        """
        解密密码

        Args:
            encrypted_password: 加密后的密码（Base64编码）
            key: 加密密钥（可选）

        Returns:
            明文密码
        """
        if key:
            fernet = Fernet(key.encode())
        else:
            manager = PasswordManager()
            fernet = manager.fernet

        encrypted = base64.b64decode(encrypted_password.encode())
        decrypted = fernet.decrypt(encrypted)
        return decrypted.decode()
