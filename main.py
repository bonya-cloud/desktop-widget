import sys
import psutil
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtGui import QFont

class DesktopOverlay(QWidget):
    def __init__(self):
        super().__init__()

        # Флаги окна: поверх всех окон, без рамок и без иконки на панели задач
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        
        # Делаем прозрачный фон окна
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Переменная для перетаскивания окна мышкой
        self.old_pos = None

        self.init_ui()
        
        # Таймер для обновления данных каждую секунду (1000 мс)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)

        # Кастомный шрифт
        font_title = QFont("Consolas", 14, QFont.Bold)
        font_stats = QFont("Consolas", 11)

        # Часы
        self.time_label = QLabel("00:00:00", self)
        self.time_label.setFont(font_title)
        self.time_label.setStyleSheet("color: #00ffcc;") # Неоново-бирюзовый цвет

        # Статистика CPU
        self.cpu_label = QLabel("CPU: 0%", self)
        self.cpu_label.setFont(font_stats)
        self.cpu_label.setStyleSheet("color: #ffffff;")

        # Статистика RAM
        self.ram_label = QLabel("RAM: 0%", self)
        self.ram_label.setFont(font_stats)
        self.ram_label.setStyleSheet("color: #ffffff;")

        # ФПС

        self.fps_label = QLabel("FPS: 0", self)
        self.fps_label.setFont(font_stats)
        self.fps_label.setStyleSheet("color: #ffffff;")
        

        layout.addWidget(self.time_label)
        layout.addWidget(self.cpu_label)
        layout.addWidget(self.ram_label)
        layout.addWidget(self.fps_label)

        self.setLayout(layout)

        # Стилизация самого плавающего блока (тёмная полупрозрачная карточка с закруглёнными углами)
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(20, 20, 30, 0.85);
                border: 1px solid rgba(0, 255, 204, 0.3);
                border-radius: 19px;
            }
        """)

        self.setWindowTitle("Desktop Widget")
        self.resize(180, 100)
        self.update_stats()

    def update_stats(self):
        # Обновление времени
        from datetime import datetime
        now = datetime.now().strftime("%H:%M:%S")
        self.time_label.setText(now)

        # Обновление процессора и ОЗУ
        cpu_usage = psutil.cpu_percent()
        ram_usage = psutil.virtual_memory().percent

        self.cpu_label.setText(f"CPU: {cpu_usage}%")
        self.ram_label.setText(f"RAM: {ram_usage}%")

    # --- Логика перетаскивания мышкой ---
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

    # Закрытие виджета по нажатию правой кнопкой мыши
    def contextMenuEvent(self, event):
        self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = DesktopOverlay()
    widget.show()
    sys.exit(app.exec_())