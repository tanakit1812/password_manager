import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class CryptoManager:
    """จัดการการเข้ารหัสโดยไม่สร้างไฟล์ .key"""
    
    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        """สร้าง key จาก password โดยใช้ PBKDF2HMAC"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    @staticmethod
    def encrypt_data(data: str, password: str, salt: bytes) -> str:
        """เข้ารหัสข้อมูล"""
        key = CryptoManager.derive_key(password, salt)
        f = Fernet(key)
        return f.encrypt(data.encode()).decode()
    
    @staticmethod
    def decrypt_data(encrypted_data: str, password: str, salt: bytes) -> str:
        """ถอดรหัสข้อมูล"""
        key = CryptoManager.derive_key(password, salt)
        f = Fernet(key)
        return f.decrypt(encrypted_data.encode()).decode()
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash รหัสผ่านสำหรับการเปรียบเทียบ"""
        return hashlib.sha256(password.encode()).hexdigest()