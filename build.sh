python -O -m PyInstaller \
 --exclude-module PyQt5 \
 --exclude-module debug_ui \
 -n panic-panda \
 --windowed \
 src/app.py 