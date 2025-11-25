from pathlib import Path
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QTextEdit, QMessageBox,
                               QFileDialog, QApplication, QComboBox, QStyle)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QIcon
from utils.telegram import TelegramNotifier
from utils.crypto import CryptoManager
import csv
import chardet

class SetupDialog(QDialog):
    """หน้าต่างตั้งค่าเริ่มต้น"""
    def showEvent(self, event):
        super().showEvent(event)
        self.center_on_screen()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ตั้งค่ารหัสผ่านหลัก")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.set_window_icon()
        self.setup_ui()
        self.apply_style()
    
    def set_window_icon(self):
        icon_path = Path("info.png")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
    
    def center_on_screen(self):
        screen = QApplication.primaryScreen().availableGeometry()
        window_geo = self.frameGeometry()
        center_point = screen.center()
        window_geo.moveCenter(center_point)
        self.move(window_geo.topLeft())
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("🔐 สร้างรหัสผ่านหลัก")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        desc = QLabel("รหัสผ่านนี้จะใช้ในการเข้าถึงโปรแกรม\nกรุณาจดจำรหัสผ่านนี้ไว้")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(desc)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("ใส่รหัสผ่านหลัก")
        self.password_input.setMinimumHeight(40)
        layout.addWidget(self.password_input)
        
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setPlaceholderText("ยืนยันรหัสผ่านหลัก")
        self.confirm_input.setMinimumHeight(40)
        layout.addWidget(self.confirm_input)
        
        btn_layout = QHBoxLayout()
        
        self.create_btn = QPushButton("สร้างรหัสผ่าน")
        self.create_btn.setMinimumHeight(40)
        self.create_btn.clicked.connect(self.create_password)
        btn_layout.addWidget(self.create_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def apply_style(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
            }
            QLineEdit {
                padding: 10px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #667eea;
            }
            QPushButton {
                background-color: #667eea;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5568d3;
            }
            QPushButton:pressed {
                background-color: #4c51bf;
            }
        """)
    
    def create_password(self):
        password = self.password_input.text()
        confirm = self.confirm_input.text()
        
        if not password:
            QMessageBox.warning(self, "คำเตือน", "กรุณาใส่รหัสผ่าน")
            return
        
        if len(password) < 6:
            QMessageBox.warning(self, "คำเตือน", "รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร")
            return
        
        if password != confirm:
            QMessageBox.warning(self, "คำเตือน", "รหัสผ่านไม่ตรงกัน")
            return
        
        self.master_password = password
        self.accept()

class LoginDialog(QDialog):
    """หน้าต่างเข้าสู่ระบบ"""
    def showEvent(self, event):
        super().showEvent(event)
        self.center_on_screen()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("เข้าสู่ระบบ")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.attempts = 0
        self.set_window_icon()
        self.setup_ui()
        self.apply_style()
    
    def set_window_icon(self):
        icon_path = Path("info.png")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
    
    def center_on_screen(self):
        screen = QApplication.primaryScreen().availableGeometry()
        window_geo = self.frameGeometry()
        center_point = screen.center()
        window_geo.moveCenter(center_point)
        self.move(window_geo.topLeft())
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("🔒 Password Manager")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        desc = QLabel("ใส่รหัสผ่านหลักเพื่อเข้าใช้งาน")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(desc)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("รหัสผ่านหลัก")
        self.password_input.setMinimumHeight(40)
        self.password_input.returnPressed.connect(self.login)
        layout.addWidget(self.password_input)
        
        self.login_btn = QPushButton("เข้าสู่ระบบ")
        self.login_btn.setMinimumHeight(40)
        self.login_btn.clicked.connect(self.login)
        layout.addWidget(self.login_btn)
        
        self.setLayout(layout)
    
    def apply_style(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
            }
            QLineEdit {
                padding: 10px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #667eea;
            }
            QPushButton {
                background-color: #667eea;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5568d3;
            }
        """)
    
    def login(self):
        self.entered_password = self.password_input.text()
        if self.entered_password:
            self.accept()

class PasswordEntryDialog(QDialog):
    """หน้าต่างเพิ่ม/แก้ไขรหัสผ่าน"""
    def showEvent(self, event):
        super().showEvent(event)
        self.center_on_screen()

    def __init__(self, parent=None, entry_data=None, folder_name=None):
        super().__init__(parent)
        self.setWindowTitle("เพิ่มรหัสผ่าน" if entry_data is None else "แก้ไขรหัสผ่าน")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.entry_data = entry_data
        self.folder_name = folder_name
        self.set_window_icon()
        self.setup_ui()
        self.apply_style()

    
    def set_window_icon(self):
        icon_path = Path("info.png")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
    
    def center_on_screen(self):
        screen = QApplication.primaryScreen().availableGeometry()
        window_geo = self.frameGeometry()
        center_point = screen.center()
        window_geo.moveCenter(center_point)
        self.move(window_geo.topLeft())
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("ชื่อ (เช่น Facebook, Gmail)")
        layout.addWidget(QLabel("ชื่อ:"))
        layout.addWidget(self.title_input)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("ชื่อผู้ใช้หรืออีเมล")
        layout.addWidget(QLabel("ชื่อผู้ใช้:"))
        layout.addWidget(self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("รหัสผ่าน")
        layout.addWidget(QLabel("รหัสผ่าน:"))
        layout.addWidget(self.password_input)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("URL (ถ้ามี)")
        layout.addWidget(QLabel("URL:"))
        layout.addWidget(self.url_input)
        
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("หมายเหตุ (ถ้ามี)")
        self.notes_input.setMaximumHeight(80)
        layout.addWidget(QLabel("หมายเหตุ:"))
        layout.addWidget(self.notes_input)
        
        if self.entry_data:
            self.title_input.setText(self.entry_data.get('title', ''))
            self.username_input.setText(self.entry_data.get('username', ''))
            self.password_input.setText(self.entry_data.get('password', ''))
            self.url_input.setText(self.entry_data.get('url', ''))
            self.notes_input.setText(self.entry_data.get('notes', ''))
        
        btn_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("บันทึก")
        self.save_btn.clicked.connect(self.save_entry)
        btn_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("ยกเลิก")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def apply_style(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
            }
            QLabel {
                color: #333;
                font-weight: bold;
                margin-top: 5px;
            }
            QLineEdit, QTextEdit {
                padding: 8px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                background-color: white;
                font-size: 13px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border-color: #667eea;
            }
            QPushButton {
                background-color: #667eea;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #5568d3;
            }
            QPushButton#cancel_btn {
                background-color: #e0e0e0;
                color: #333;
            }
            QPushButton#cancel_btn:hover {
                background-color: #d0d0d0;
            }
        """)
        self.cancel_btn.setObjectName("cancel_btn")
    
    def save_entry(self):
        if not self.title_input.text() or not self.username_input.text() or not self.password_input.text():
            QMessageBox.warning(self, "คำเตือน", "กรุณากรอกข้อมูลให้ครบ (ชื่อ, ชื่อผู้ใช้, รหัสผ่าน)")
            return
        
        self.result = {
            'title': self.title_input.text(),
            'username': self.username_input.text(),
            'password': self.password_input.text(),
            'url': self.url_input.text(),
            'notes': self.notes_input.toPlainText()
        }
        self.accept()

class PasswordDetailDialog(QDialog):
    """หน้าต่างแสดงรายละเอียดรหัสผ่าน - เวอร์ชันสมบูรณ์เต็มรูปแบบ"""

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self.center_on_screen)

    def __init__(self, parent=None, password_entries=None):
        super().__init__(parent)
        self.setWindowTitle("รายละเอียดรหัสผ่าน")
        self.setModal(True)
        self.setMinimumWidth(560)
        self.password_entries = password_entries or []
        self.current_index = 0
        self.password_visible = False
        self.set_window_icon()
        self.setup_ui()
        self.apply_style()
        self.load_entry()

    def set_window_icon(self):
        icon_path = Path("info.png")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    def center_on_screen(self):
        screen = QApplication.primaryScreen().availableGeometry()
        window_geo = self.frameGeometry()
        center_point = screen.center()
        window_geo.moveCenter(center_point)
        self.move(window_geo.topLeft())

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Title
        self.title_label = QLabel()
        self.title_label.setFont(QFont("Arial", 18, QFont.Bold))
        self.title_label.setStyleSheet("color: #2c3e50;")
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        # ComboBox + Navigation (ถ้ามีหลายรายการ)
        if len(self.password_entries) > 1:
            top_layout = QHBoxLayout()
            top_layout.addWidget(QLabel("เลือกบัญชี:"))

            self.combo = QComboBox()
            self.combo.setMinimumWidth(300)
            for i, entry in enumerate(self.password_entries):
                username = entry.get('username', '') or 'ไม่มีชื่อผู้ใช้'
                self.combo.addItem(f"{entry['title']} — {username}", i)
            self.combo.setCurrentIndex(0)
            self.combo.currentIndexChanged.connect(self.combo_changed)
            top_layout.addWidget(self.combo)
            top_layout.addStretch()
            layout.addLayout(top_layout)

            # Navigation buttons
            nav_layout = QHBoxLayout()
            self.entry_label = QLabel()
            self.entry_label.setAlignment(Qt.AlignCenter)
            self.entry_label.setStyleSheet("font-weight: bold; color: #3498db;")
            nav_layout.addWidget(self.entry_label)



        # Username
        layout.addWidget(QLabel("ชื่อผู้ใช้:"))
        self.username_label = QLabel()
        self.username_label.setStyleSheet("padding: 12px; background: #ecf0f1; border-radius: 8px; font-family: Consolas;")
        layout.addWidget(self.username_label)

        copy_user_layout = QHBoxLayout()
        self.copy_username_btn = QPushButton("คัดลอกชื่อผู้ใช้")
        self.copy_username_btn.clicked.connect(self.copy_username)
        copy_user_layout.addWidget(self.copy_username_btn)
        copy_user_layout.addStretch()
        layout.addLayout(copy_user_layout)

        # Password
        layout.addWidget(QLabel("รหัสผ่าน:"))
        password_layout = QHBoxLayout()
        self.password_label = QLabel("••••••••••••")
        self.password_label.setStyleSheet("padding: 12px; background: #ecf0f1; border-radius: 8px; font-family: Consolas;")
        password_layout.addWidget(self.password_label)

        self.toggle_password_btn = QPushButton("แสดง")
        self.toggle_password_btn.setCheckable(True)
        self.toggle_password_btn.setFixedWidth(90)
        self.toggle_password_btn.clicked.connect(self.toggle_password)
        password_layout.addWidget(self.toggle_password_btn)
        layout.addLayout(password_layout)

        copy_pass_layout = QHBoxLayout()
        self.copy_password_btn = QPushButton("คัดลอกรหัสผ่าน")
        self.copy_password_btn.clicked.connect(self.copy_password)
        copy_pass_layout.addWidget(self.copy_password_btn)
        copy_pass_layout.addStretch()
        layout.addLayout(copy_pass_layout)

        # URL
        layout.addWidget(QLabel("URL:"))
        self.url_label = QLabel("-")
        self.url_label.setStyleSheet("padding: 12px; background: #ecf0f1; border-radius: 8px;")
        self.url_label.setOpenExternalLinks(True)
        self.url_label.setWordWrap(True)
        layout.addWidget(self.url_label)

        # Notes
        layout.addWidget(QLabel("หมายเหตุ:"))
        self.notes_label = QLabel("-")
        self.notes_label.setStyleSheet("padding: 12px; background: #ecf0f1; border-radius: 8px;")
        self.notes_label.setWordWrap(True)
        layout.addWidget(self.notes_label)

        # Action Buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(12)

        self.edit_btn = QPushButton("แก้ไขบัญชีนี้")
        self.edit_btn.setStyleSheet("background-color: #3498db; color: white; padding: 12px; border-radius: 8px; font-weight: bold;")
        self.edit_btn.clicked.connect(self.edit_current_entry)
        action_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("ลบบัญชีนี้")
        self.delete_btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 12px; border-radius: 8px; font-weight: bold;")
        self.delete_btn.clicked.connect(self.delete_current_entry)
        action_layout.addWidget(self.delete_btn)

        action_layout.addStretch()

        close_btn = QPushButton("ปิด")
        close_btn.setStyleSheet("background-color: #95a5a6; color: white; padding: 12px 30px; border-radius: 8px; font-weight: bold;")
        close_btn.clicked.connect(self.accept)
        action_layout.addWidget(close_btn)

        layout.addLayout(action_layout)
        self.setLayout(layout)

    def apply_style(self):
        self.setStyleSheet("""
            QDialog { background-color: #f8fafc; }
            QLabel { color: #2d3436; font-size: 14px; }
            QPushButton {
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { opacity: 0.9; }
            QComboBox {
                padding: 8px;
                border: 2px solid #dfe6e9;
                border-radius: 8px;
                background: white;
            }
            QComboBox:focus { border-color: #3498db; }
        """)

    def load_entry(self):
        if not self.password_entries:
            return

        entry = self.password_entries[self.current_index]

        self.title_label.setText(f"{entry['title']}")
        self.username_label.setText(entry.get('username', '-') or '-')

        # Password
        if self.password_visible:
            self.password_label.setText(entry.get('password', ''))
            self.toggle_password_btn.setText("ซ่อน")
        else:
            pwd = entry.get('password', '')
            self.password_label.setText("•" * max(8, len(pwd)))
            self.toggle_password_btn.setText("แสดง")

        # URL
        url = entry.get('url', '').strip()
        if url and url != '':
            self.url_label.setText(f'<a href="{url}">{url}</a>')
        else:
            self.url_label.setText("-")

        # Notes
        notes = entry.get('notes', '').strip()
        self.notes_label.setText(notes if notes else "-")

        # Update navigation
        if len(self.password_entries) > 1:
            self.entry_label.setText(f"{self.current_index + 1} / {len(self.password_entries)}")
            self.combo.blockSignals(True)
            self.combo.setCurrentIndex(self.current_index)
            self.combo.blockSignals(False)

    def combo_changed(self, index):
        if index >= 0:
            self.current_index = index
            self.password_visible = False
            self.load_entry()

    def toggle_password(self):
        self.password_visible = not self.password_visible
        self.load_entry()

    def prev_entry(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.password_visible = False
            self.load_entry()

    def next_entry(self):
        if self.current_index < len(self.password_entries) - 1:
            self.current_index += 1
            self.password_visible = False
            self.load_entry()

    def copy_username(self):
        entry = self.password_entries[self.current_index]
        QApplication.clipboard().setText(entry.get('username', ''))
        QMessageBox.information(self, "สำเร็จ", "คัดลอกชื่อผู้ใช้เรียบร้อย")

    def copy_password(self):
        entry = self.password_entries[self.current_index]
        QApplication.clipboard().setText(entry.get('password', ''))
        QMessageBox.information(self, "สำเร็จ", "คัดลอกรหัสผ่านเรียบร้อย")

    def edit_current_entry(self):
        entry = self.password_entries[self.current_index]
        dialog = PasswordEntryDialog(self, entry_data=entry)
        if dialog.exec():
            updated = dialog.result
            self.password_entries[self.current_index] = updated

            # อัปเดตข้อมูลจริงในหน้าหลัก
            main = self.parent()
            if main and hasattr(main, 'data') and main.current_folder:
                folder_data = main.data['folders'][main.current_folder]
                for i, item in enumerate(folder_data):
                    if item is entry:  # อ้างอิงเดียวกัน
                        folder_data[i] = updated
                        main.save_data()
                        break

            self.load_entry()
            QMessageBox.information(self, "สำเร็จ", "แก้ไขบัญชีเรียบร้อย")

    def delete_current_entry(self):
        entry = self.password_entries[self.current_index]
        reply = QMessageBox.question(
            self, "ยืนยันการลบ",
            f"คุณแน่ใจหรือไม่ที่จะลบ\n\"{entry['title']}\" ({entry.get('username', 'ไม่มีชื่อผู้ใช้')})",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            main = self.parent()
            if main and hasattr(main, 'data') and main.current_folder:
                folder_data = main.data['folders'][main.current_folder]
                if entry in folder_data:
                    folder_data.remove(entry)
                    main.save_data()

            self.password_entries.pop(self.current_index)
            if not self.password_entries:
                self.accept()
            else:
                if self.current_index >= len(self.password_entries):
                    self.current_index = len(self.password_entries) - 1
                self.load_entry()
                if hasattr(main, 'load_passwords'):
                    main.load_passwords()

class SettingsDialog(QDialog):
    """หน้าต่างตั้งค่า (เต็ม)"""
    def showEvent(self, event):
        super().showEvent(event)
        self.center_on_screen()

    def __init__(self, parent=None, bot_id="", chat_id="", master_password="", storage=None):
        super().__init__(parent)
        self.setWindowTitle("ตั้งค่า")
        self.setModal(True)
        self.setMinimumWidth(500)

        # ค่าเริ่มต้นจากผู้เรียก
        self.parent_window = parent
        self.bot_id = bot_id or ""
        self.chat_id = chat_id or ""
        self.master_password = master_password or ""
        self.storage = storage

        # ผลลัพธ์ที่ caller จะอ่าน
        self.result_bot = self.bot_id
        self.result_chat = self.chat_id
        self.new_master_password = None

        self.set_window_icon()
        self.setup_ui()
        self.apply_style()

    def set_window_icon(self):
        icon_path = Path("info.png")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    def center_on_screen(self):
        screen = QApplication.primaryScreen().availableGeometry()
        window_geo = self.frameGeometry()
        center_point = screen.center()
        window_geo.moveCenter(center_point)
        self.move(window_geo.topLeft())

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Telegram Settings
        title = QLabel("⚙️ ตั้งค่า Telegram")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)

        layout.addWidget(QLabel("Bot Token:"))
        self.bot_input = QLineEdit()
        self.bot_input.setText(self.bot_id)
        self.bot_input.setPlaceholderText("ใส่ Bot Token จาก @BotFather")
        layout.addWidget(self.bot_input)

        layout.addWidget(QLabel("Chat ID:"))
        self.chat_input = QLineEdit()
        self.chat_input.setText(self.chat_id)
        self.chat_input.setPlaceholderText("ใส่ Chat ID ของคุณ")
        layout.addWidget(self.chat_input)

        info = QLabel("💡 วิธีหา Chat ID: ส่งข้อความไปที่บอทแล้วเข้า\nhttps://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates")
        info.setStyleSheet("color: #666; font-size: 11px; margin: 10px 0;")
        layout.addWidget(info)

        # Master Password Change
        title2 = QLabel("🔐 เปลี่ยนรหัสผ่านหลัก")
        title2.setFont(QFont("Arial", 16, QFont.Bold))
        title2.setStyleSheet("margin-top: 20px;")
        layout.addWidget(title2)

        layout.addWidget(QLabel("รหัสผ่านหลักปัจจุบัน:"))
        self.current_password_input = QLineEdit()
        self.current_password_input.setEchoMode(QLineEdit.Password)
        self.current_password_input.setPlaceholderText("ใส่รหัสผ่านหลักปัจจุบัน")
        layout.addWidget(self.current_password_input)

        layout.addWidget(QLabel("รหัสผ่านหลักใหม่:"))
        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.Password)
        self.new_password_input.setPlaceholderText("ใส่รหัสผ่านหลักใหม่")
        layout.addWidget(self.new_password_input)

        layout.addWidget(QLabel("ยืนยันรหัสผ่านหลักใหม่:"))
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setPlaceholderText("ยืนยันรหัสผ่านหลักใหม่")
        layout.addWidget(self.confirm_password_input)

        # Buttons: Backup, Test, Save, Cancel
        btn_layout = QHBoxLayout()

        self.backup_btn = QPushButton("สำรองข้อมูล")
        self.backup_btn.setToolTip("สร้าง CSV และส่งไปยัง Telegram")
        self.backup_btn.clicked.connect(self.on_backup_clicked)
        btn_layout.addWidget(self.backup_btn)

        self.test_btn = QPushButton("ทดสอบ Telegram")
        self.test_btn.clicked.connect(self.test_telegram)
        btn_layout.addWidget(self.test_btn)

        btn_layout.addStretch(1)

        self.save_btn = QPushButton("บันทึก")
        self.save_btn.clicked.connect(self.save_settings)
        btn_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("ยกเลิก")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def apply_style(self):
        self.setStyleSheet("""
            QDialog { background-color: #f5f7fa; }
            QLabel { color: #333; }
            QLineEdit {
                padding: 8px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                background-color: white;
                font-size: 13px;
            }
            QLineEdit:focus { border-color: #667eea; }
            QPushButton {
                background-color: #667eea;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 15px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #5568d3; }
            QPushButton#cancel_btn {
                background-color: #e0e0e0;
                color: #333;
            }
            QPushButton#cancel_btn:hover { background-color: #d0d0d0; }
        """)
        self.cancel_btn.setObjectName("cancel_btn")

    def on_backup_clicked(self):
        parent = self.parent_window
        if parent and hasattr(parent, "backup_now"):
            try:
                parent.backup_now()
            except Exception:
                QMessageBox.warning(self, "สำรองล้มเหลว", "ไม่สามารถสำรองข้อมูลได้ในขณะนี้")
        else:
            QMessageBox.warning(self, "ไม่สามารถ", "ฟังก์ชันสำรองข้อมูลไม่พร้อมใช้งาน")

    def test_telegram(self):
        bot_token = self.bot_input.text().strip()
        chat_id = self.chat_input.text().strip()
        if not bot_token or not chat_id:
            QMessageBox.warning(self, "คำเตือน", "กรุณากรอก Bot Token และ Chat ID")
            return
        TelegramNotifier.send_message(bot_token, chat_id, "🔔 ทดสอบการส่งข้อความจาก Password Manager")
        QMessageBox.information(self, "สำเร็จ", "ส่งข้อความทดสอบแล้ว กรุณาตรวจสอบ Telegram")

    def save_settings(self):
        self.result_bot = self.bot_input.text().strip()
        self.result_chat = self.chat_input.text().strip()
        self.new_master_password = None

        current_pwd = self.current_password_input.text()
        new_pwd = self.new_password_input.text()
        confirm_pwd = self.confirm_password_input.text()

        if current_pwd or new_pwd or confirm_pwd:
            if new_pwd != confirm_pwd:
                QMessageBox.warning(self, "คำเตือน", "รหัสผ่านใหม่และยืนยันไม่ตรงกัน")
                return
            # ถ้าไม่มี master_password เดิม ให้ปฏิเสธการเปลี่ยน
            if not self.master_password:
                QMessageBox.warning(self, "คำเตือน", "ไม่สามารถเปลี่ยนรหัสผ่านได้ (ไม่มีรหัสผ่านหลักเดิม)")
                return
            # ตรวจสอบรหัสผ่านปัจจุบันตรงกับที่ถูกส่งมาเป็นค่าเริ่มต้น
            if current_pwd != self.master_password:
                QMessageBox.warning(self, "คำเตือน", "รหัสผ่านหลักปัจจุบันไม่ถูกต้อง")
                return
            if len(new_pwd) < 6:
                QMessageBox.warning(self, "คำเตือน", "รหัสผ่านใหม่ต้องมีอย่างน้อย 6 ตัวอักษร")
                return
            self.new_master_password = new_pwd

        self.accept()

class ImportCSVDialog(QDialog):
    """นำเข้า CSV — รองรับภาษาไทย 100% + สร้างโฟลเดอร์อัตโนมัติ"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("นำเข้าข้อมูลจาก CSV")
        self.setModal(True)
        self.setMinimumWidth(680)
        self.setMinimumHeight(580)
        self.csv_file = None
        self.imported_data = []
        self.set_window_icon()
        self.setup_ui()
        self.apply_style()

    def set_window_icon(self):
        icon_path = Path("info.png")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    def showEvent(self, event):
        super().showEvent(event)
        self.center_on_screen()

    def center_on_screen(self):
        screen = QApplication.primaryScreen().availableGeometry()
        window_geo = self.frameGeometry()
        center_point = screen.center()
        window_geo.moveCenter(center_point)
        self.move(window_geo.topLeft())

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        title = QLabel("นำเข้าข้อมูลจาก CSV")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        info = QLabel("""
<h3>รูปแบบ CSV ที่รองรับ</h3>

<p><b>มีคอลัมน์ folder (แนะนำ)</b></p>
<code style="background:#f0f0f0; padding:8px; border-radius:4px; display:block;">
folder,title,username,password,url,notes
</code>

<hr>

<h4>ตัวอย่างข้อมูล:</h4>
<code style="background:#e8f5e9; padding:12px; border-left:4px solid #4caf50; display:block; font-family: Consolas; white-space: pre;">
folder,title,username,password,url,notes
test1,Facebook,xxx@gmail.com,123456,https://facebook.com,บัญชีหลัก
test2,Email,xxx@gmail.com,123456,,
</code>

<p style="color:#7f8c8d; font-size:12px; margin-top:10px;">
หมายเหตุ:<br>
• ถ้าไม่มีคอลัมน์ <b>folder</b> → จะใส่ในโฟลเดอร์ "<b>ทั่วไป</b>" อัตโนมัติ<br>
• คอลัมน์ <b>url</b> และ <b>notes</b> สามารถเว้นว่างได้<br>
• รองรับทั้งไฟล์ .csv
</p>
""")
        info.setWordWrap(True)
        info.setStyleSheet("background: #e8f4f8; padding: 15px; border-radius: 8px; border: 1px solid #b3e0ea; font-family: Consolas;")
        layout.addWidget(info)

        file_layout = QHBoxLayout()
        self.file_label = QLabel("ยังไม่ได้เลือกไฟล์")
        self.file_label.setStyleSheet("padding: 10px; background: white; border: 2px dashed #bdc3c7; border-radius: 6px; min-height: 20px;")
        self.file_label.setAlignment(Qt.AlignCenter)
        file_layout.addWidget(self.file_label, 1)

        select_btn = QPushButton("เลือกไฟล์ CSV")
        select_btn.setIcon(QApplication.style().standardIcon(QStyle.SP_DialogOpenButton))
        select_btn.clicked.connect(self.select_file)
        file_layout.addWidget(select_btn)
        layout.addLayout(file_layout)

        layout.addWidget(QLabel("<b>ตัวอย่างข้อมูลที่จะนำเข้า:</b>"))
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(260)
        self.preview_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.preview_text)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.import_btn = QPushButton("นำเข้า")
        self.import_btn.setEnabled(False)
        self.import_btn.setMinimumWidth(120)
        self.import_btn.clicked.connect(self.import_data)
        cancel_btn = QPushButton("ยกเลิก")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.import_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def apply_style(self):
        self.setStyleSheet("""
            QDialog { background-color: #f8fafc; }
            QPushButton { background-color: #667eea; color: white; border: none; border-radius: 8px; padding: 12px 20px; font-weight: bold; font-size: 14px; }
            QPushButton:hover { background-color: #5a6fd8; }
            QPushButton:disabled { background-color: #b2bec3; color: #636e72; }
        """)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "เลือกไฟล์ CSV", "", "CSV Files (*.csv);;All Files (*)")
        if file_path:
            self.csv_file = file_path
            self.file_label.setText(Path(file_path).name)
            self.file_label.setStyleSheet("padding: 10px; background: #dff9fb; border: 2px solid #00d2d3; border-radius: 6px; color: #006266; font-weight: bold;")
            self.load_preview()

    def load_preview(self):
        if not self.csv_file:
            return

        self.imported_data = []
        preview_lines = []
        folders = set()

        try:
            # ลองหลาย encoding
            encodings = ['utf-8', 'utf-8-sig', 'cp874', 'tis-620', 'windows-1252']
            content = None
            used_encoding = None
            for enc in encodings:
                try:
                    with open(self.csv_file, 'r', encoding=enc) as f:
                        content = f.read()
                    used_encoding = enc
                    break
                except:
                    continue
            if content is None:
                raise Exception("ไม่สามารถอ่านไฟล์ได้ทุกรูปแบบ")

            lines = content.splitlines()
            if not lines:
                raise Exception("ไฟล์ว่าง")

            dialect = csv.Sniffer().sniff(content[:2048])
            reader = csv.DictReader(lines, dialect=dialect)
            fieldnames = [name.strip().lower() for name in reader.fieldnames]

            required = ['title', 'username', 'password']
            missing = [c for c in required if c not in fieldnames]
            if missing:
                QMessageBox.critical(self, "รูปแบบผิด", f"ไม่พบคอลัมน์: {', '.join(missing)}")
                self.reset_preview()
                return

            for i, row in enumerate(reader):
                cleaned = {k.strip().lower(): v.strip() for k, v in row.items()}
                folder_name = cleaned.get('folder', '').strip() or "ทั่วไป"
                folders.add(folder_name)

                if i < 6:
                    preview_lines.append(f"รายการที่ {i+1} → <b>[{folder_name}]</b>")
                    preview_lines.append(f"   ชื่อ: {cleaned.get('title', '-')}")
                    preview_lines.append(f"   ผู้ใช้: {cleaned.get('username', '-')}")
                    preview_lines.append(f"   รหัสผ่าน: {'*' * (len(cleaned.get('password', '')) or 8)}")
                    preview_lines.append("")

                self.imported_data.append({
                    'folder': folder_name,
                    'title': cleaned.get('title', ''),
                    'username': cleaned.get('username', ''),
                    'password': cleaned.get('password', ''),
                    'url': cleaned.get('url', ''),
                    'notes': cleaned.get('notes', '')
                })

            summary = f"<b>พบ {len(self.imported_data)} รายการ</b> (encoding: {used_encoding})"
            folder_text = "<br><b>โฟลเดอร์ที่จะสร้าง:</b> " + ", ".join(sorted(folders))
            self.preview_text.setHtml(f"{summary}{folder_text}<hr>" + "<br>".join(preview_lines))
            self.import_btn.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "อ่านไม่ได้", f"ข้อผิดพลาด: {str(e)}")
            self.reset_preview()

    def reset_preview(self):
        self.preview_text.clear()
        self.imported_data = []
        self.import_btn.setEnabled(False)
        self.file_label.setText("ยังไม่ได้เลือกไฟล์")
        self.file_label.setStyleSheet("padding: 10px; background: white; border: 2px dashed #bdc3c7; border-radius: 6px;")

    def import_data(self):
        if self.imported_data:
            self.accept()

    def get_imported_data(self):
        """ฟังก์ชันนี้ถูกเรียกจาก PasswordManager — คืนค่าที่เตรียมไว้แล้ว"""
        return self.imported_data

class RenameFolderDialog(QDialog):
    """หน้าต่างเปลี่ยนชื่อโฟลเดอร์"""
    def showEvent(self, event):
        super().showEvent(event)
        self.center_on_screen()

    def __init__(self, parent=None, current_name=""):
        super().__init__(parent)
        self.setWindowTitle("เปลี่ยนชื่อโฟลเดอร์")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.current_name = current_name
        self.set_window_icon()
        self.setup_ui()
        self.apply_style()

    
    def set_window_icon(self):
        icon_path = Path("info.png")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
    
    def center_on_screen(self):
        screen = QApplication.primaryScreen().availableGeometry()
        window_geo = self.frameGeometry()
        center_point = screen.center()
        window_geo.moveCenter(center_point)
        self.move(window_geo.topLeft())
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("📝 เปลี่ยนชื่อโฟลเดอร์")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        layout.addWidget(QLabel("ชื่อใหม่:"))
        self.name_input = QLineEdit()
        self.name_input.setText(self.current_name)
        self.name_input.setPlaceholderText("ใส่ชื่อโฟลเดอร์ใหม่")
        self.name_input.setMinimumHeight(40)
        self.name_input.selectAll()
        layout.addWidget(self.name_input)
        
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("บันทึก")
        save_btn.clicked.connect(self.save_name)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("ยกเลิก")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def apply_style(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
            }
            QLabel {
                color: #333;
            }
            QLineEdit {
                padding: 10px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #667eea;
            }
            QPushButton {
                background-color: #667eea;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5568d3;
            }
        """)
    
    def save_name(self):
        new_name = self.name_input.text().strip()
        if not new_name:
            QMessageBox.warning(self, "คำเตือน", "กรุณาใส่ชื่อโฟลเดอร์")
            return
        
        self.new_folder_name = new_name
        self.accept()