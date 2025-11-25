import sys
from pathlib import Path
from collections import defaultdict
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QLineEdit, QPushButton, QListWidget, 
                               QMessageBox, QInputDialog, QFrame, QApplication,
                               QMenu, QListWidgetItem, QDialog, QStyle)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from utils.storage import DataStorage
from utils.crypto import CryptoManager
from utils.telegram import TelegramNotifier
from ui.dialogs import (SetupDialog, LoginDialog, PasswordEntryDialog, 
                        PasswordDetailDialog, SettingsDialog, ImportCSVDialog,
                        RenameFolderDialog)
from PySide6.QtCore import QDateTime
import platform
import tempfile
from datetime import datetime

class PasswordManager(QMainWindow):
    """หน้าต่างหลักของโปรแกรม"""
    
    def __init__(self):
        super().__init__()
        self.storage = DataStorage()
        self.master_password = None
        self.data = {
            'master_hash': None,
            'telegram_bot': '',
            'telegram_chat': '',
            'folders': {},
            'login_attempts': 0
        }
        self.current_folder = None
        
        self.set_window_icon()
        self.init_login()
    
    def set_window_icon(self):
        icon_path = Path("info.png")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
    
    def find_or_create_folder(self, folder_name: str):
        """
        ค้นหาหรือสร้างโฟลเดอร์ใน QTreeWidget
        รองรับชื่อ tree_widget หลายแบบที่คนนิยมใช้
        """
        from PySide6.QtWidgets import QTreeWidgetItem
        from PySide6.QtGui import QIcon
        from PySide6.QtCore import Qt

        # --- ตรวจจับ QTreeWidget อัตโนมัติ ไม่ว่าจะชื่ออะไร ---
        tree = None
        possible_names = ['tree_widget', 'treeWidget', 'password_tree', 'tree_view', 'treeView', 'entries_tree']
        for name in possible_names:
            if hasattr(self, name):
                tree = getattr(self, name)
                break
    
        if tree is None:
            raise AttributeError("ไม่พบ QTreeWidget ในคลาส PasswordManager "
                           "(ลองตั้งชื่อว่า tree_widget, treeWidget, หรือ password_tree)")
        # --------------------------------------------------------

        # ถ้าชื่อโฟลเดอร์ว่าง → ใส่ที่ root
        if not folder_name or folder_name.strip() in ["", "Imported", "Root"]:
            return tree  # root คือตัว QTreeWidget เอง

        folder_name = folder_name.strip()

        # ค้นหาโฟลเดอร์ที่มีชื่อนี้อยู่แล้ว
        for i in range(tree.topLevelItemCount()):
            item = tree.topLevelItem(i)
            if (item.text(0) == folder_name and 
                item.data(0, Qt.UserRole) == "folder"):
                return item

     # ถ้าไม่เจอ → สร้างใหม่
        new_folder = QTreeWidgetItem([folder_name])
    
        # ใช้ไอคอนโฟลเดอร์จากระบบ (ไม่ต้องมีไฟล์ก็ได้)
        new_folder.setIcon(0, self.style().standardIcon(QStyle.StandardPixmap.SP_DirClosedIcon))
        new_folder.setData(0, Qt.UserRole, "folder")
        new_folder.setExpanded(True)

        tree.addTopLevelItem(new_folder)
        return new_folder

    def center_on_screen(self):
        screen = QApplication.primaryScreen().availableGeometry()
        window_geo = self.frameGeometry()
        center_point = screen.center()
        window_geo.moveCenter(center_point)
        self.move(window_geo.topLeft())
    
    def init_login(self):
        """เริ่มต้นการ login"""
        loaded_data = self.try_load_existing_data()

        if loaded_data is not None:
            try:
                meta = self.storage.load_metadata()
                if meta:
                    self.data['telegram_bot'] = meta.get('telegram_bot', '')
                    self.data['telegram_chat'] = meta.get('telegram_chat', '')
            except Exception:
                pass
        
        if loaded_data is None:
            dialog = SetupDialog(self)
            if dialog.exec():
                self.master_password = dialog.master_password
                self.data['master_hash'] = CryptoManager.hash_password(self.master_password)
                self.data['folders'] = {'ทั่วไป': []}
                self.save_data()
                self.init_ui()
                self.center_on_screen()
                self.show()
            else:
                sys.exit()
        else:
            login_dialog = LoginDialog(self)
            if login_dialog.exec():
                entered_password = login_dialog.entered_password
                loaded = self.storage.load_data(entered_password)
                
                if loaded and loaded.get('master_hash') == CryptoManager.hash_password(entered_password):
                    self.master_password = entered_password
                    self.data = loaded
                    self.data['login_attempts'] = 0
                    self.save_data()
                    self.init_ui()
                    self.center_on_screen()
                    self.show()
                else:
                    self.handle_failed_login()
            else:
                sys.exit()
    
    def try_load_existing_data(self):
        """ลองโหลดข้อมูลที่มีอยู่"""
        if not self.storage.filename.exists():
            return None
        return True
    
    def handle_failed_login(self):
        attempts = (self.data.get('login_attempts', 0) + 1)
        self.data['login_attempts'] = attempts

        bot = self.data.get('telegram_bot', '')
        chat = self.data.get('telegram_chat', '')

        if bot and chat:
            msg = f"พยายามเข้าสู่ระบบล้มเหลว \nเวลา: {QDateTime.currentDateTime().toString('dd/MM/yyyy hh:mm')}\nเครื่อง: {platform.node()}"
            try:
                TelegramNotifier.send_message(bot, chat, msg)
            except Exception:
                # ไม่แสดง logging ตามที่ร้องขอ — เงียบไว้
                pass

        if attempts >= 3:
            if bot and chat:
                try:
                    tmp_dir = Path(tempfile.gettempdir())
                    csv_name = f"backup_before_delete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    csv_path = tmp_dir / csv_name

                    # ถ้า self.data ว่าง ให้ลองโหลดสำรองจาก storage (ถ้ามี)
                    data_to_export = self.data
                    try:
                        if not data_to_export.get('folders'):
                            if hasattr(self.storage, "decrypt_backup_with_master"):
                                backup = self.storage.decrypt_backup_with_master() or {}
                            elif hasattr(self.storage, "load_plaintext_backup"):
                                backup = self.storage.load_plaintext_backup() or {}
                            else:
                                backup = {}
                            if backup and backup.get('folders'):
                                data_to_export = backup
                    except Exception:
                        # เงียบไว้ตามคำขอ (ไม่ใช้ logging)
                        pass
                except Exception:
                    pass

            # ลบข้อมูลทั้งหมดแล้วลบ metadata/ไฟล์ที่เกี่ยวข้อง (รวม secure_data.meta หากมี)
            try:
                # ลบไฟล์ข้อมูลหลัก
                try:
                    self.storage.delete_all_data()
                except Exception:
                    pass

                # พยายามลบไฟล์ metadata / key / backup ทุกชนิดที่อาจถูกสร้าง
                try:
                    candidates = [
                        self.storage.filename.with_suffix('.meta'),
                        self.storage.filename.with_suffix('.meta.json'),
                        self.storage.filename.with_suffix('.meta.bin'),
                        self.storage.filename.with_suffix('.mkey.bin'),
                        self.storage.filename.with_suffix('.backup.enc'),
                        self.storage.filename.with_suffix('.backup.bin'),
                        # ถ้ามีไฟล์ชื่อ secure_data.meta อยู่โดยตรง ในโฟลเดอร์เดียวกัน ให้ลบทิ้งด้วย
                        Path(self.storage.filename.parent) / 'secure_data.meta'
                    ]
                    for p in candidates:
                        try:
                            if p.exists():
                                p.unlink(missing_ok=True)
                        except Exception:
                            # เงียบ — ล้างพยายามต่อไป
                            pass
                except Exception:
                    pass

            except Exception:
                pass

            QMessageBox.critical(None, "ล็อคระบบ", "ลบข้อมูลทั้งหมดแล้ว")
            sys.exit()
        else:
            QMessageBox.warning(None, "ผิด", f"รหัสผ่านผิด!")
            self.init_login()
    
    def init_ui(self):
        """สร้าง UI หลัก"""
        self.setWindowTitle("Password Manager")
        self.setMinimumSize(1000, 600)
        
        central_widget = QWidget()
        main_layout = QHBoxLayout()
        
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-right: 1px solid #34495e;
            }
        """)
        
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(15, 20, 15, 20)
        sidebar_layout.setSpacing(10)
        
        logo = QLabel("🔐 Password Manager")
        logo.setStyleSheet("color: white; font-size: 18px; font-weight: bold; margin-bottom: 20px;")
        sidebar_layout.addWidget(logo)
        
        self.add_folder_btn = QPushButton("+ เพิ่มโฟลเดอร์")
        self.add_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.add_folder_btn.clicked.connect(self.add_folder)
        sidebar_layout.addWidget(self.add_folder_btn)
        
        self.folder_list = QListWidget()
        self.folder_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                color: white;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 12px;
                border-radius: 6px;
                margin: 2px 0;
            }
            QListWidget::item:hover {
                background-color: #34495e;
            }
            QListWidget::item:selected {
                background-color: #3498db;
            }
        """)
        self.folder_list.itemClicked.connect(self.select_folder)
        self.folder_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.folder_list.customContextMenuRequested.connect(self.show_folder_context_menu)
        sidebar_layout.addWidget(self.folder_list)
        
        sidebar_layout.addStretch()
        
        # Import CSV Button
        self.import_btn = QPushButton("📥 นำเข้า CSV")
        self.import_btn.setStyleSheet("""
            QPushButton {
                background-color: #16a085;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #138d75;
            }
        """)
        self.import_btn.clicked.connect(self.import_csv)
        sidebar_layout.addWidget(self.import_btn)
        
        self.settings_btn = QPushButton("⚙️ ตั้งค่า")
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #34495e;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #4a5f7f;
            }
        """)
        self.settings_btn.clicked.connect(self.open_settings)
        sidebar_layout.addWidget(self.settings_btn)
        
        sidebar.setLayout(sidebar_layout)
        main_layout.addWidget(sidebar)
        
        # Main content
        content = QWidget()
        content.setStyleSheet("background-color: #ecf0f1;")
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.folder_title = QLabel("เลือกโฟลเดอร์")
        self.folder_title.setFont(QFont("Arial", 16, QFont.Bold))
        self.folder_title.setStyleSheet("color: #2c3e50;")
        header_layout.addWidget(self.folder_title)
        
        header_layout.addStretch()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 ค้นหา...")
        self.search_input.setFixedWidth(300)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #bdc3c7;
                border-radius: 20px;
                background-color: white;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        self.search_input.textChanged.connect(self.search_passwords)
        header_layout.addWidget(self.search_input)
        
        self.add_password_btn = QPushButton("+ เพิ่มรหัสผ่าน")
        self.add_password_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        self.add_password_btn.clicked.connect(self.add_password)
        header_layout.addWidget(self.add_password_btn)
        
        content_layout.addLayout(header_layout)
        
        # Password list
        self.password_list = QListWidget()
        self.password_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 15px;
                border-bottom: 1px solid #ecf0f1;
                border-radius: 8px;
                margin: 5px 0;
                color: #2c3e50;
            }
            QListWidget::item:hover {
                background-color: #f0f8ff;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd !important;
                color: #1976d2 !important;
                border: 2px solid #3498db;
                font-weight: bold;
            }
        """)
        self.password_list.itemDoubleClicked.connect(self.view_password_details)
        self.password_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.password_list.customContextMenuRequested.connect(self.show_password_context_menu)
        content_layout.addWidget(self.password_list)
        
        # Button bar
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(10)
        
        self.edit_btn = QPushButton("✏️ แก้ไข")
        self.edit_btn.clicked.connect(self.edit_password)
        self.edit_btn.setStyleSheet(self.get_button_style("#3498db"))
        btn_bar.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("🗑️ ลบ")
        self.delete_btn.clicked.connect(self.delete_password)
        self.delete_btn.setStyleSheet(self.get_button_style("#e74c3c"))
        btn_bar.addWidget(self.delete_btn)
        
        btn_bar.addStretch()
        
        content_layout.addLayout(btn_bar)
        
        content.setLayout(content_layout)
        main_layout.addWidget(content)
        
        central_widget.setLayout(main_layout)
        
        self.load_folders()
        self.apply_main_style()
    
    def get_button_style(self, color):
        """สร้าง style สำหรับปุ่ม"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 15px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {color};
                opacity: 0.8;
            }}
            QPushButton:disabled {{
                background-color: #bdc3c7;
                color: #7f8c8d;
            }}
        """
    
    def apply_main_style(self):
        """ใช้ style กับหน้าต่างหลัก"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ecf0f1;
            }
        """)
    
    def show_folder_context_menu(self, position):
        """แสดงเมนูคลิกขวาสำหรับโฟลเดอร์"""
        item = self.folder_list.itemAt(position)
        if not item:
            return
        
        folder_name = item.text().replace("📁 ", "")
        
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 20px;
            }
            QMenu::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        
        rename_action = menu.addAction("✏️ เปลี่ยนชื่อ")
        delete_action = menu.addAction("🗑️ ลบ")
        
        action = menu.exec(self.folder_list.mapToGlobal(position))
        
        if action == rename_action:
            self.rename_folder(folder_name)
        elif action == delete_action:
            self.delete_folder(folder_name)
    
    def show_password_context_menu(self, position):
        """แสดงเมนูคลิกขวาสำหรับรหัสผ่าน"""
        item = self.password_list.itemAt(position)
        if not item:
            return
        
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 20px;
            }
            QMenu::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        
        view_action = menu.addAction("👁 ดูรายละเอียด")
        edit_action = menu.addAction("✏️ แก้ไข")
        delete_action = menu.addAction("🗑️ ลบ")
        
        action = menu.exec(self.password_list.mapToGlobal(position))
        
        if action == view_action:
            self.view_password_details(item)
        elif action == edit_action:
            self.edit_password()
        elif action == delete_action:
            self.delete_password()
    
    def load_folders(self):
        """โหลดรายการโฟลเดอร์"""
        self.folder_list.clear()
        for folder_name in self.data['folders'].keys():
            self.folder_list.addItem(f"📁 {folder_name}")
        
        if self.folder_list.count() > 0:
            self.folder_list.setCurrentRow(0)
            self.select_folder(self.folder_list.item(0))
    
    def select_folder(self, item):
        """เลือกโฟลเดอร์"""
        if item:
            folder_name = item.text().replace("📁 ", "")
            self.current_folder = folder_name
            self.folder_title.setText(f"📁 {folder_name}")
            self.load_passwords()
    
    def group_passwords_by_title(self, passwords):
        """จัดกลุ่มรหัสผ่านตามชื่อ"""
        grouped = defaultdict(list)
        for pwd in passwords:
            grouped[pwd['title']].append(pwd)
        return grouped
    
    def load_passwords(self, search_term=""):
        """โหลดรายการรหัสผ่าน"""
        self.password_list.clear()
        
        if not self.current_folder:
            return
        
        passwords = self.data['folders'].get(self.current_folder, [])
        
        # Filter by search term
        if search_term:
            passwords = [pwd for pwd in passwords if 
                        search_term.lower() in pwd['title'].lower() or 
                        search_term.lower() in pwd['username'].lower()]
        
        # Group by title
        grouped = self.group_passwords_by_title(passwords)
        
        for title, entries in grouped.items():
            if len(entries) == 1:
                pwd = entries[0]
                display_text = f"🔐 {pwd['title']}\n   👤 {pwd['username']}"
                if pwd.get('url'):
                    display_text += f"\n   🌐 {pwd['url']}"
            else:
                display_text = f"🔐 {title}\n   👥 {len(entries)} บัญชี"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, {'title': title, 'entries': entries})
            self.password_list.addItem(item)
    
    def search_passwords(self):
        """ค้นหารหัสผ่าน"""
        search_term = self.search_input.text()
        self.load_passwords(search_term)
    
    def add_folder(self):
        """เพิ่มโฟลเดอร์ใหม่"""
        folder_name, ok = QInputDialog.getText(self, "เพิ่มโฟลเดอร์", "ชื่อโฟลเดอร์:")
        
        if ok and folder_name:
            if folder_name in self.data['folders']:
                QMessageBox.warning(self, "คำเตือน", "มีโฟลเดอร์นี้อยู่แล้ว")
                return
            
            self.data['folders'][folder_name] = []
            self.save_data()
            self.load_folders()
            QMessageBox.information(self, "สำเร็จ", f"เพิ่มโฟลเดอร์ '{folder_name}' แล้ว")
            self.maybe_prompt_backup("เพิ่มโฟลเดอร์")
    
    def rename_folder(self, folder_name):
        """เปลี่ยนชื่อโฟลเดอร์"""
        dialog = RenameFolderDialog(self, folder_name)
        if dialog.exec():
            new_name = dialog.new_folder_name
            
            if new_name == folder_name:
                return
            
            if new_name in self.data['folders']:
                QMessageBox.warning(self, "คำเตือน", "มีโฟลเดอร์ชื่อนี้อยู่แล้ว")
                return
            
            self.data['folders'][new_name] = self.data['folders'][folder_name]
            del self.data['folders'][folder_name]
            
            if self.current_folder == folder_name:
                self.current_folder = new_name
            
            self.save_data()
            self.load_folders()
            QMessageBox.information(self, "สำเร็จ", f"เปลี่ยนชื่อเป็น '{new_name}' แล้ว")
            self.maybe_prompt_backup("เปลี่ยนชื่อโฟลเดอร์")
    
    def delete_folder(self, folder_name):
        """ลบโฟลเดอร์"""
        self.maybe_prompt_backup("ลบโฟลเดอร์")
        if len(self.data['folders']) == 1:
            QMessageBox.warning(self, "คำเตือน", "ต้องมีอย่างน้อย 1 โฟลเดอร์")
            return
        
        passwords_count = len(self.data['folders'][folder_name])
        reply = QMessageBox.question(
            self,
            "ยืนยันการลบ",
            f"ต้องการลบโฟลเดอร์ '{folder_name}' ใช่หรือไม่?\n(มีรหัสผ่าน {passwords_count} รายการ)",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            del self.data['folders'][folder_name]
            self.save_data()
            self.load_folders()
            QMessageBox.information(self, "สำเร็จ", f"ลบโฟลเดอร์ '{folder_name}' แล้ว")
    
    def add_password(self):
        """เพิ่มรหัสผ่านใหม่"""
        if not self.current_folder:
            QMessageBox.warning(self, "คำเตือน", "กรุณาเลือกโฟลเดอร์ก่อน")
            return
        
        dialog = PasswordEntryDialog(self, folder_name=self.current_folder)
        if dialog.exec():
            self.data['folders'][self.current_folder].append(dialog.result)
            self.save_data()
            self.load_passwords()
            QMessageBox.information(self, "สำเร็จ", "เพิ่มรหัสผ่านแล้ว")
            self.maybe_prompt_backup("เพิ่มรหัสผ่าน")
    
    def get_selected_password_data(self):
        """ดึงข้อมูลรหัสผ่านที่เลือก"""
        current_item = self.password_list.currentItem()
        if not current_item:
            return None
        
        data = current_item.data(Qt.UserRole)
        return data
    
    def view_password_details(self, item):
        """แสดงรายละเอียดรหัสผ่าน"""
        data = self.get_selected_password_data()
        if not data:
            return
        
        entries = data['entries']
        dialog = PasswordDetailDialog(self, entries)
        dialog.exec()
    
    def edit_password(self):
        """แก้ไขรหัสผ่าน"""
        data = self.get_selected_password_data()
        if not data:
            QMessageBox.warning(self, "คำเตือน", "กรุณาเลือกรหัสผ่านที่ต้องการแก้ไข")
            return
        
        entries = data['entries']
        
        if len(entries) == 1:
            # Edit single entry
            password_entry = entries[0]
            passwords = self.data['folders'][self.current_folder]
            idx = passwords.index(password_entry)
            
            dialog = PasswordEntryDialog(self, password_entry, self.current_folder)
            if dialog.exec():
                self.data['folders'][self.current_folder][idx] = dialog.result
                self.save_data()
                self.load_passwords()
                QMessageBox.information(self, "สำเร็จ", "แก้ไขรหัสผ่านแล้ว")
                self.maybe_prompt_backup("แก้ไขรหัสผ่าน")
        else:
            # Multiple entries - show detail dialog first
            dialog = PasswordDetailDialog(self, entries)
            dialog.exec()
    
    def delete_password(self):
        """ลบรหัสผ่าน"""
        self.maybe_prompt_backup("ลบรหัสผ่าน")
        data = self.get_selected_password_data()
        if not data:
            QMessageBox.warning(self, "คำเตือน", "กรุณาเลือกรหัสผ่านที่ต้องการลบ")
            return
        
        title = data['title']
        entries = data['entries']
        
        reply = QMessageBox.question(
            self,
            "ยืนยันการลบ",
            f"คุณต้องการลบ '{title}' ({len(entries)} รายการ) ใช่หรือไม่?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            passwords = self.data['folders'][self.current_folder]
            for entry in entries:
                if entry in passwords:
                    passwords.remove(entry)
            
            self.save_data()
            self.load_passwords()
            QMessageBox.information(self, "สำเร็จ", "ลบรหัสผ่านแล้ว")
    
    def import_csv(self):
        """นำเข้าข้อมูลจาก CSV และสร้างโฟลเดอร์อัตโนมัติ"""
        dialog = ImportCSVDialog(self)
        if dialog.exec() == QDialog.Accepted:
            imported_data = dialog.get_imported_data()
            if not imported_data:
                QMessageBox.warning(self, "ไม่มีข้อมูล", "ไม่พบข้อมูลที่จะนำเข้า")
                return

            count = 0
            folders_created = set()
            
            for item in imported_data:
                try:
                    # ดึงชื่อโฟลเดอร์จาก CSV
                    folder_name = item.get('folder', '').strip()
                    
                    # ถ้าไม่มีชื่อโฟลเดอร์ ให้ใช้ "Imported"
                    if not folder_name:
                        folder_name = "Imported"
                    
                    # สร้างโฟลเดอร์ถ้ายังไม่มี
                    if folder_name not in self.data['folders']:
                        self.data['folders'][folder_name] = []
                        folders_created.add(folder_name)
                    
                    # สร้างข้อมูลรหัสผ่าน
                    password_entry = {
                        'title': item.get('title', '').strip(),
                        'username': item.get('username', '').strip(),
                        'password': item.get('password', '').strip(),
                        'url': item.get('url', '').strip(),
                        'notes': item.get('notes', '').strip()
                    }
                    
                    # เพิ่มเข้าไปในโฟลเดอร์
                    self.data['folders'][folder_name].append(password_entry)
                    count += 1
                    
                except Exception as e:
                    # ข้ามรายการที่มีปัญหา
                    continue
            
            # บันทึกข้อมูล
            self.save_data()
            
            # โหลดโฟลเดอร์ใหม่
            self.load_folders()
            
            # แสดงผลสำเร็จ
            msg = f"นำเข้าข้อมูลเรียบร้อย {count} รายการ"
            if folders_created:
                msg += f"\n\nสร้างโฟลเดอร์ใหม่:\n" + "\n".join(f"📁 {f}" for f in folders_created)
            
            QMessageBox.information(self, "นำเข้าสำเร็จ", msg)
            self.maybe_prompt_backup("นำเข้าข้อมูล")
    
    def open_settings(self):
        """เปิดหน้าตั้งค่า"""
        dialog = SettingsDialog(
            self,
            self.data.get('telegram_bot', ''),
            self.data.get('telegram_chat', ''),
            self.master_password,
            self.storage
        )
        
        if dialog.exec():
            # เก็บค่าใหม่จาก dialog (เหมือนเดิม)
            self.data['telegram_bot'] = dialog.result_bot
            self.data['telegram_chat'] = dialog.result_chat
            
            if dialog.new_master_password:
                old_password = self.master_password
                new_password = dialog.new_master_password
                self.master_password = new_password
                self.data['master_hash'] = CryptoManager.hash_password(new_password)
                QMessageBox.information(self, "สำเร็จ", "เปลี่ยนรหัสผ่านหลักแล้ว")
            
            self.save_data()

            # บันทึก metadata (ไม่เข้ารหัส) ถ้ามีเมทอด
            try:
                if hasattr(self.storage, "save_metadata"):
                    self.storage.save_metadata({
                        'telegram_bot': self.data.get('telegram_bot', ''),
                        'telegram_chat': self.data.get('telegram_chat', '')
                    })
            except Exception:
                pass

            QMessageBox.information(self, "สำเร็จ", "บันทึกการตั้งค่าแล้ว")

            # หลังจากบันทึกการตั้งค่า ให้เสนอปุ่มสำรองข้อมูล (ย้ายจาก UI หลักมาอยู่ที่นี่)
            reply = QMessageBox.question(
                self,
                "สำรองข้อมูล",
                "ต้องการสำรองข้อมูลและส่งไฟล์ไปยัง Telegram ตอนนี้หรือไม่?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.backup_now()

    def maybe_prompt_backup(self, action_desc: str = ""):
        """
        ถามผู้ใช้ก่อนทำการเพิ่ม/แก้/ลบ ว่าต้องการสำรองข้อมูลก่อนหรือไม่
        (ถ้า Yes จะเรียก backup_now(), ถ้า No จะทำต่อไปเลย)
        """
        try:
            text = f"ต้องการสำรองข้อมูล{action_desc}หรือไม่?"
            resp = QMessageBox.question(self, "สำรองข้อมูล", text, QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if resp == QMessageBox.Yes:
                self.backup_now()
        except Exception:
            pass  # เงียบตามคำขอ

    def backup_now(self):
        """
        สร้าง CSV ชั่วคราวจากข้อมูล (หรือจาก backup ที่ถอดได้) และส่งไฟล์ไปที่ Telegram
        แจ้งผลสำเร็จ/ล้มเหลวให้ผู้ใช้ทราบ
        """
        bot = self.data.get('telegram_bot', '') or ''
        chat = self.data.get('telegram_chat', '') or ''

        if not bot or not chat:
            QMessageBox.warning(self, "ไม่สามารถสำรอง", "ยังไม่ได้ตั้งค่า Telegram (bot token / chat id)")
            return

        try:
            tmp_dir = Path(tempfile.gettempdir())
            csv_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            csv_path = tmp_dir / csv_name

            # เลือกข้อมูลที่จะ export: ถ้า self.data ไม่มี folders ให้ลองโหลด backup ที่ถอดได้
            data_to_export = self.data
            if not data_to_export.get('folders'):
                try:
                    backup = {}
                    if hasattr(self.storage, "decrypt_backup_with_master"):
                        backup = self.storage.decrypt_backup_with_master() or {}
                    elif hasattr(self.storage, "load_plaintext_backup"):
                        backup = self.storage.load_plaintext_backup() or {}
                    if backup and backup.get('folders'):
                        data_to_export = backup
                except Exception:
                    pass

            # สร้างไฟล์ CSV
            try:
                self.storage.export_data_to_csv(data_to_export, csv_path)
            except Exception:
                pass

            # ตรวจสอบไฟล์
            if not csv_path.exists() or csv_path.stat().st_size == 0:
                try:
                    csv_path.unlink(missing_ok=True)
                except Exception:
                    pass
                QMessageBox.warning(self, "สำรองไม่สำเร็จ", "ไม่สามารถสร้างไฟล์สำรองได้ (ไฟล์ว่างหรือไม่ถูกสร้าง)")
                return

            # ส่งไฟล์ผ่าน Telegram
            try:
                sent = False
                if hasattr(TelegramNotifier, "send_file"):
                    sent = TelegramNotifier.send_file(bot, chat, str(csv_path), "Password Manager backup")
                if sent:
                    QMessageBox.information(self, "สำรองเรียบร้อย", "ส่งไฟล์สำรองไปยัง Telegram เรียบร้อยแล้ว")
                else:
                    QMessageBox.warning(self, "ส่งไฟล์ล้มเหลว", "ไม่สามารถส่งไฟล์ไปยัง Telegram ได้ — ตรวจสอบ token/chat/การเชื่อมต่อ")
            except Exception:
                QMessageBox.warning(self, "ส่งไฟล์ล้มเหลว", "เกิดข้อผิดพลาดขณะส่งไฟล์ไปยัง Telegram")
            finally:
                try:
                    csv_path.unlink(missing_ok=True)
                except Exception:
                    pass
        except Exception:
            QMessageBox.warning(self, "สำรองล้มเหลว", "เกิดข้อผิดพลาดไม่คาดคิดขณะสำรองข้อมูล")
    
    def save_data(self):
        """บันทึกข้อมูลแบบเข้ารหัส"""
        if self.master_password:
            self.storage.save_data(self.data, self.master_password)
            # อัปเดต metadata ไฟล์ด้วย (ปลอดภัยสำหรับค่า telegram ที่ไม่สำคัญต่อความลับหลัก)
            try:
                self.storage.save_metadata({
                    'telegram_bot': self.data.get('telegram_bot', ''),
                    'telegram_chat': self.data.get('telegram_chat', '')
                })
            except Exception:
                pass
    
    def closeEvent(self, event):
        """เมื่อปิดโปรแกรม"""
        self.save_data()
        event.accept()
