import sys
import os
import psutil
import ctypes
from datetime import datetime
import keyboard

from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal, QObject
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QHBoxLayout
from PyQt5.QtGui import QFont

class HotkeySignals(QObject):
    toggle_visible = pyqtSignal()
    toggle_lock = pyqtSignal()
    toggle_theme = pyqtSignal()
    quit_app = pyqtSignal()

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
        self.is_dark_theme = True
        self.old_pos = None

        self.themes = {
            "dark": {
                "container": "background-color: rgba(15, 15, 20, 0.88); border: 1px solid rgba(0, 255, 204, 0.35); border-radius: 8px;",
                "text": "color: #ffffff;",
                "accent": "color: #00ffcc;",
                "sep": "color: #555555;"
            },
            "light": {
                "container": "background-color: rgba(240, 240, 245, 0.90); border: 1px solid rgba(0, 100, 200, 0.4); border-radius: 8px;",
                "text": "color: #1a1a1a;",
                "accent": "color: #0055ff;",
                "sep": "color: #aaaaaa;"
            }
        }

        self.signals = HotkeySignals()
        self.signals.toggle_visible.connect(self.toggle_visibility)
        self.signals.toggle_lock.connect(self.toggle_click_lock)
        self.signals.toggle_theme.connect(self.toggle_theme)
        self.signals.quit_app.connect(self.force_quit)

        self.update_window_flags()
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.init_ui()

        ctypes.windll.user32.SetWindowPos(int(self.winId()), -1, 0, 0, 0, 0, 0x0001 | 0x0002)

        # Регистрация глобальных хоткеев
        keyboard.add_hotkey('ctrl+shift+h', lambda: self.signals.toggle_visible.emit())
        keyboard.add_hotkey('ctrl+shift+l', lambda: self.signals.toggle_lock.emit())
        keyboard.add_hotkey('ctrl+shift+t', lambda: self.signals.toggle_theme.emit())
        keyboard.add_hotkey('ctrl+shift+q', lambda: self.signals.quit_app.emit())

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
        layout = QHBoxLayout()
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)

        font_stats = QFont("Consolas", 10, QFont.Bold)

        self.time_label = QLabel("00:00:00", self)
        self.time_label.setFont(font_stats)

        self.cpu_label = QLabel("CPU: 0%", self)
        self.cpu_label.setFont(font_stats)

        self.ram_label = QLabel("RAM: 0%", self)
        self.ram_label.setFont(font_stats)

        self.gpu_label = QLabel("GPU: N/A", self)
        self.gpu_label.setFont(font_stats)

        self.fps_label = QLabel("FPS: N/A", self)
        self.fps_label.setFont(font_stats)

        self.status_label = QLabel("[КЛИКИ]", self)
        self.status_label.setFont(font_stats)

        self.separators = []
        for _ in range(5):
            sep = QLabel("|", self)
            sep.setFont(font_stats)
            self.separators.append(sep)

        layout.addWidget(self.time_label)
        layout.addWidget(self.separators[0])
        layout.addWidget(self.cpu_label)
        layout.addWidget(self.separators[1])
        layout.addWidget(self.ram_label)
        layout.addWidget(self.separators[2])
        layout.addWidget(self.gpu_label)
        layout.addWidget(self.separators[3])
        layout.addWidget(self.fps_label)
        layout.addWidget(self.separators[4])
        layout.addWidget(self.status_label)

        self.setLayout(layout)
        self.apply_theme()
        self.setWindowTitle("Desktop Widget Bar")
        self.adjustSize()
        self.update_stats()

    def apply_theme(self):
        theme_key = "dark" if self.is_dark_theme else "light"
        theme = self.themes[theme_key]

        self.setStyleSheet(f"QWidget {{ {theme['container']} }}")
        
        self.time_label.setStyleSheet(theme['accent'])
        self.cpu_label.setStyleSheet(theme['text'])
        self.ram_label.setStyleSheet(theme['text'])
        self.gpu_label.setStyleSheet(theme['text'])
        self.fps_label.setStyleSheet(theme['text'])

        for sep in self.separators:
            sep.setStyleSheet(theme['sep'])

        if not self.is_locked:
            self.status_label.setStyleSheet(theme['accent'])

    def toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme
        self.apply_theme()

    def update_stats(self):
        now = datetime.now().strftime("%H:%M:%S")
        self.time_label.setText(now)

        cpu_usage = psutil.cpu_percent()
        ram_usage = psutil.virtual_memory().percent

        self.cpu_label.setText(f"CPU {cpu_usage}%")
        self.ram_label.setText(f"RAM {ram_usage}%")

        fps = get_rtss_fps()
        if fps is not None and fps > 0:
            self.fps_label.setText(f"FPS {fps}")
        else:
            self.fps_label.setText("FPS N/A")

        # Безопасное получение загрузки GPU без создания фоновых процессов консоли
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            self.gpu_label.setText(f"GPU {util.gpu}%")
            pynvml.nvmlShutdown()
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
        theme_key = "dark" if self.is_dark_theme else "light"
        
        if self.is_locked:
            self.status_label.setText("[БЛОК]")
            self.status_label.setStyleSheet("color: #ff5555;")
        else:
            self.status_label.setText("[КЛИКИ]")
            self.status_label.setStyleSheet(self.themes[theme_key]['accent'])
        
        self.update_window_flags()

    def force_quit(self):
        # Жесткое и мгновенное завершение процесса без зависаний
        keyboard.unhook_all()
        QApplication.quit()
        os._exit(0)

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
            self.force_quit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = DesktopOverlay()
    widget.show()
    sys.exit(app.exec_())