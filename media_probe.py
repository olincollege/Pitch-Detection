import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtMultimedia import QMediaPlayer

app = QApplication(sys.argv)
print('App name:', app.applicationName())
print('App version:', app.applicationVersion())
print('Supported MIME types:', QMediaPlayer.supportedMimeTypes())
print('Supports MP4:', 'video/mp4' in QMediaPlayer.supportedMimeTypes())
