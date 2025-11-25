@echo off
python -m nuitka ^
  --standalone ^
  --mingw64 ^
  --output-dir=dist ^
  --windows-console-mode=disable ^
  --enable-plugin=pyside6 ^
  --follow-imports ^
  --noinclude-qt-plugins=qml ^
  --include-package=utils ^
  --include-package=ui ^
  --include-data-files=info.png=info.png ^
  --include-data-files=info.ico=info.ico ^
  --windows-icon-from-ico=info.ico ^
  --output-dir=dist ^
  "Password Manager.py"
pause
