import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QPalette, QColor, QIcon
from ui.main_windows import PasswordManager

def main():
    app = QApplication(sys.argv)
    
    # ตั้งค่า icon
    icon_path = Path("info.png")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # ตั้งค่า font ทั่วทั้งแอป
    font = QFont("Arial", 10)
    app.setFont(font)
    
    # ตั้งค่า palette
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(236, 240, 241))
    palette.setColor(QPalette.WindowText, QColor(44, 62, 80))
    app.setPalette(palette)
    
    window = PasswordManager()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()