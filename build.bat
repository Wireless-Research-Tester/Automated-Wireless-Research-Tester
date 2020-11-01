pyinstaller -F mainWindow_app.py
:: add -w option later
move dist\mainWindow_app.exe mainWindow_app.exe
rmdir /S/Q dist
rmdir /S/Q build
del mainWindow_app.spec
