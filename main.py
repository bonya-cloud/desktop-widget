import sys
import psutil
import ctypes
from datetime import datetime
import keyboard

from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal, QObject
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QHBoxLayout
from PyQt5.QtGui import QFont

# Сигналы для безопасного вызова функций Qt из потока горячих клавиш
class HotkeySignals(QObject):
    toggle_visible = pyqtSignal()
    toggle_lock = pyqtSignal()
    quit_app = pyqtSignal()

# Чтение FPS напрямую из RivaTuner Statistics Server
def get_rtss_fps():
    try:
        FILE_MAP_READ = 0x0004
        handle = ctypes.windll.kernel32.OpenFileMappingW(FILE_MAP_READ, False, "RTSSSharedMemoryV2")
        if not handle:
            return None
        buf = ctypes.windll.kernel32.MapViewOfFile(handle, FILE_MAP_READ, 0, 0, 0)
        if not buf:
            ctypes.windll.kernel32.CloseHandle(handle)
            return None
        
        app_entry_offset = 256
        fps_offset = app_entry_offset + 12
        fps = ctypes.cast(buf + fps_offset, ctypes.POINTER(ctypes.c_uint32)).contents.value
        
        ctypes.windll.kernel32.UnmapViewOfFile(buf)
        ctypes.windll.kernel32.CloseHandle(handle)
        return fps
    except Exception:
        return None

class DesktopOverlay(QWidget):
    def __init__(self):
        super().__init__()

        self.is_locked = False
        self.old_pos = None

        # Настройка сигналов горячих клавиш
        self.signals = HotkeySignals()
        self.signals.toggle_visible.connect(self.toggle_visibility)
        self.signals.toggle_lock.connect(self.toggle_click_lock)
        self.signals.quit_app.connect(self.close)

        self.update_window_flags()
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.init_ui()

        # Принудительный системный приоритет TOPMOST
        ctypes.windll.user32.SetWindowPos(int(self.winId()), -1, 0, 0, 0, 0, 0x0001 | 0x0002)

        # Хоткеи
        keyboard.add_hotkey('ctrl+shift+h', lambda: self.signals.toggle_visible.emit())
        keyboard.add_hotkey('ctrl+shift+l', lambda: self.signals.toggle_lock.emit())
        keyboard.add_hotkey('ctrl+shift+q', lambda: self.signals.quit_app.emit())

        # Обновление данных каждую секунду
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)

    def update_window_flags(self):
        flags = Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool
        if self.is_locked:
            flags |= Qt.WindowTransparentForInput
        
        self.setWindowFlags(flags)
        self.show()

    def init_ui(self):
        # Используем горизонтальный Layout вместо вертикального
        layout = QHBoxLayout()
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)

        font_stats = QFont("Consolas", 10, QFont.Bold)
        style_text = "color: #ffffff;"
        style_sep = "color: #555555; font-weight: bold;"

        # Часы
        self.time_label = QLabel("00:00:00", self)
        self.time_label.setFont(font_stats)
        self.time_label.setStyleSheet("color: #00ffcc;")

        # CPU
        self.cpu_label = QLabel("CPU: 0%", self)
        self.cpu_label.setFont(font_stats)
        self.cpu_label.setStyleSheet(style_text)

        # RAM
        self.ram_label = QLabel("RAM: 0%", self)
        self.ram_label.setFont(font_stats)
        self.ram_label.setStyleSheet(style_text)

        # GPU
        self.gpu_label = QLabel("GPU: N/A", self)
        self.gpu_label.setFont(font_stats)
        self.gpu_label.setStyleSheet(style_text)

        # FPS
        self.fps_label = QLabel("FPS: N/A", self)
        self.fps_label.setFont(font_stats)
        self.fps_label.setStyleSheet(style_text)

        # Статус кликов
        self.status_label = QLabel("[КЛИКИ]", self)
        self.status_label.setFont(font_stats)
        self.status_label.setStyleSheet("color: #00ffcc;")

        # Собираем горизонтальную строку с разделителями "|"
        layout.addWidget(self.time_label)
        layout.addWidget(self.create_sep(style_sep))
        layout.addWidget(self.cpu_label)
        layout.addWidget(self.create_sep(style_sep))
        layout.addWidget(self.ram_label)
        layout.addWidget(self.create_sep(style_sep))
        layout.addWidget(self.gpu_label)
        layout.addWidget(self.create_sep(style_sep))
        layout.addWidget(self.fps_label)
        layout.addWidget(self.create_sep(style_sep))
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        # Стилизация узкой полосы
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(15, 15, 20, 0.88);
                border: 1px solid rgba(0, 255, 204, 0.35);
                border-radius: 8px;
            }
        """)

        self.setWindowTitle("Desktop Widget Bar")
        self.adjustSize()  # Автоматический подгон ширины под текст
        self.update_stats()

    def create_sep(self, style):
        sep = QLabel("|", self)
        sep.setFont(QFont("Consolas", 10))
        sep.setStyleSheet(style)
        return sep

    def update_stats(self):
        # Время
        now = datetime.now().strftime("%H:%M:%S")
        self.time_label.setText(now)

        # CPU и RAM
        cpu_usage = psutil.cpu_percent()
        ram_usage = psutil.virtual_memory().percent

        self.cpu_label.setText(f"CPU {cpu_usage}%")
        self.ram_label.setText(f"RAM {ram_usage}%")

        # FPS
        fps = get_rtss_fps()
        if fps is not None and fps > 0:
            self.fps_label.setText(f"FPS {fps}")
        else:
            self.fps_label.setText("FPS N/A")

        # GPU
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu_load = int(gpus[0].load * 100)
                self.gpu_label.setText(f"GPU {gpu_load}%")
            else:
                self.gpu_label.setText("GPU N/A")
        except Exception:
            self.gpu_label.setText("GPU N/A")

        self.adjustSize()

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()

    def toggle_click_lock(self):
        self.is_locked = not self.is_locked
        if self.is_locked:
            self.status_label.setText("[БЛОК]")
            self.status_label.setStyleSheet("color: #ff5555;")
        else:
            self.status_label.setText("[КЛИКИ]")
            self.status_label.setStyleSheet("color: #00ffcc;")
        
        self.update_window_flags()

    # Перетаскивание
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.is_locked:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.old_pos and not self.is_locked:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = None

    def contextMenuEvent(self, event):
        if not self.is_locked:
            self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = DesktopOverlay()
    widget.show()
    sys.exit(app.exec_())