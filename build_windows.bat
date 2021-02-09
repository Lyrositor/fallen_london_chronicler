@echo off
rmdir /Q /S dist
pyinstaller pyinstaller.spec
cd dist
tar -c -a -f fallen_london_chronicler-win64.zip fallen_london_chronicler
cd ..
