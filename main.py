import sys
import psutil
from datetime import datetime
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtGui import QFont

class DesktopOverlay(QWidget):
    def __init__(self):
        super().__init__()

        # Флаги окна: поверх всех, без рамок, без иконки и со сквозными кликами
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.WindowTransparentForInput  # Клики проходят сквозь виджет прямо в игру
        )
        
        # Прозрачный фон
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.old_pos = None

        self.init_ui()
        
        # Принудительный системный приоритет TOPMOST в Windows
        import ctypes
        ctypes.windll.user32.SetWindowPos(int(self.winId()), -1, 0, 0, 0, 0, 0x0001 | 0x0002)

        # Обновление данных каждую секунду
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)

        font_title = QFont("Consolas", 14, QFont.Bold)
        font_stats = QFont("Consolas", 11)

        # 1. Часы
        self.time_label = QLabel("00:00:00", self)
        self.time_label.setFont(font_title)
        self.time_label.setStyleSheet("color: #00ffcc;")

        # 2. CPU
        self.cpu_label = QLabel("CPU: 0%", self)
        self.cpu_label.setFont(font_stats)
        self.cpu_label.setStyleSheet("color: #ffffff;")

        # 3. RAM
        self.ram_label = QLabel("RAM: 0%", self)
        self.ram_label.setFont(font_stats)
        self.ram_label.setStyleSheet("color: #ffffff;")

        # 4. GPU
        self.gpu_label = QLabel("GPU: N/A", self)
        self.gpu_label.setFont(font_stats)
        self.gpu_label.setStyleSheet("color: #ffffff;")

        # 5. FPS
        self.fps_label = QLabel("FPS: N/A", self)
        self.fps_label.setFont(font_stats)
        self.fps_label.setStyleSheet("color: #ffffff;")

        # Добавление всех элементов в layout
        layout.addWidget(self.time_label)
        layout.addWidget(self.cpu_label)
        layout.addWidget(self.ram_label)
        layout.addWidget(self.gpu_label)
        layout.addWidget(self.fps_label)

        self.setLayout(layout)

        # Тёмный полупрозрачный стиль блока
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(20, 20, 30, 0.85);
                border: 1px solid rgba(0, 255, 204, 0.3);
                border-radius: 12px;
            }
        """)

        self.setWindowTitle("Desktop Widget")
        self.resize(180, 140)
        self.update_stats()

    def update_stats(self):
        # Обновление времени
        now = datetime.now().strftime("%H:%M:%S")
        self.time_label.setText(now)

        # Обновление CPU и RAM
        cpu_usage = psutil.cpu_percent()
        ram_usage = psutil.virtual_memory().percent

        self.cpu_label.setText(f"CPU: {cpu_usage}%")
        self.ram_label.setText(f"RAM: {ram_usage}%")

        # Обновление FPS из RivaTuner (RTSS)
        try:
            from pyrtss import RTSS
            rtss = RTSS()
            if rtss.app_entries:
                fps = int(rtss.app_entries[0].instantaneous_frames)
                self.fps_label.setText(f"FPS: {fps}")
            else:
                self.fps_label.setText("FPS: N/A")
        except Exception:
            self.fps_label.setText("FPS: N/A")

        # Обновление GPU (загрузка видеокарты)
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu_load = int(gpus[0].load * 100)
                self.gpu_label.setText(f"GPU: {gpu_load}%")
            else:
                self.gpu_label.setText("GPU: N/A")
        except Exception:
            self.gpu_label.setText("GPU: N/A")

    # Перетаскивание окна ЛКМ
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = None

    # Закрытие окна ПКМ
    def contextMenuEvent(self, event):
        self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = DesktopOverlay()
    widget.show()
    sys.exit(app.exec_())