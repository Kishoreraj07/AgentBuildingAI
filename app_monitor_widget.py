import sys
import time
import ctypes
import threading

from PIL import Image
import io

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QScrollArea, QFrame, QSizePolicy, QGridLayout, QCheckBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap, QImage, QColor, QFont

import style_loader

import win32gui
import win32process
import win32ui
import win32con

try:
    import dxcam
    DXCAM_AVAILABLE = True
except Exception:
    DXCAM_AVAILABLE = False


def pil_image_to_qimage(pil_img: Image.Image) -> QImage:
    if pil_img.mode != "RGB":
        pil_img = pil_img.convert("RGB")
    w, h = pil_img.size
    data = pil_img.tobytes("raw", "RGB")
    qimg = QImage(data, w, h, 3 * w, QImage.Format_RGB888)
    return qimg.copy()


class ThumbnailWidget(QFrame):
    clicked = pyqtSignal(int)

    def __init__(self, hwnd: int, title: str, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self.hwnd = hwnd
        self.setFrameShape(QFrame.StyledPanel)
        self.setLineWidth(1)
        self.setProperty('class', 'AppMonitorThumbnail')
        style_loader.apply_stylesheet(self)

        v = QVBoxLayout(self)
        self.thumb_label = QLabel(self)
        self.thumb_label.setPixmap(pixmap)
        self.thumb_label.setAlignment(Qt.AlignCenter)
        self.thumb_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        v.addWidget(self.thumb_label)

        self.title_label = QLabel(title, self)
        self.title_label.setWordWrap(True)
        self.title_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.title_label.setFont(QFont("Segoe UI", 9))
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.title_label.setMaximumHeight(60)
        v.addWidget(self.title_label)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.hwnd)

    def set_selected(self, sel: bool):
        if sel:
            self.setProperty('class', 'AppMonitorThumbnailSelected')
        else:
            self.setProperty('class', 'AppMonitorThumbnail')
        style_loader.apply_stylesheet(self)


class CaptureThread(QThread):
    frame_ready = pyqtSignal(QImage)
    error = pyqtSignal(str)
    finished_monitoring = pyqtSignal()

    def __init__(self, hwnd: int, camera, method: str, parent=None):
        super().__init__(parent)
        self.hwnd = hwnd
        self._running = True
        self.camera = camera
        self.method = method

    def stop(self):
        self._running = False

    def run(self):
        try:
            while self._running:
                if not win32gui.IsWindow(self.hwnd):
                    self._running = False
                    continue

                if self.method.startswith("DXCam") and self.camera:
                    try:
                        frame = self.camera.get_latest_frame()
                        if frame is not None:
                            self.frame_ready.emit(pil_image_to_qimage(Image.fromarray(frame, "RGB")))
                    except Exception:
                        pass
                else:
                    pil_img = CaptureHelpers.capture_printwindow_pil(self.hwnd)
                    if pil_img is not None:
                        self.frame_ready.emit(pil_image_to_qimage(pil_img))
                time.sleep(0.03)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished_monitoring.emit()

class CaptureHelpers:
    @staticmethod
    def capture_printwindow_pil(hwnd):
        try:
            if not win32gui.IsWindow(hwnd) or win32gui.IsIconic(hwnd): return None
            rect = win32gui.GetWindowRect(hwnd)
            width, height = rect[2] - rect[0], rect[3] - rect[1]
            if width <= 0 or height <= 0: return None

            hwnd_dc = win32gui.GetWindowDC(hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()
            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(save_bitmap)
            ctypes.windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 3)
            
            bmp_info = save_bitmap.GetInfo()
            bmp_str = save_bitmap.GetBitmapBits(True)
            img = Image.frombuffer('RGB', (bmp_info['bmWidth'], bmp_info['bmHeight']), bmp_str, 'raw', 'BGRX', 0, 1)
            
            win32gui.DeleteObject(save_bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwnd_dc)
            return img
        except Exception:
            return None

    @staticmethod
    def capture_thumbnail_qpixmap(hwnd, target_width=300):
        pil_img = CaptureHelpers.capture_printwindow_pil(hwnd)
        if pil_img is None: return None
        w, h = pil_img.size
        if w <= 0: return None
        pil_img.thumbnail((target_width, int(h * target_width / w)), Image.Resampling.LANCZOS)
        return QPixmap.fromImage(pil_image_to_qimage(pil_img))


class AppMonitorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.camera = None
        if DXCAM_AVAILABLE:
            try:
                self.camera = dxcam.create(output_color="RGB")
            except Exception:
                self.camera = None

        self.selected_hwnd = None
        self.capture_thread = None
        self.thumb_map = {}
        self.init_ui()
        self.populate_app_list()

    def init_ui(self):
        h_layout = QHBoxLayout(self)
        h_layout.setContentsMargins(10, 10, 10, 10)

        # Left Pane (Thumbnails and Controls)
        left_pane = QWidget()
        left_layout = QVBoxLayout(left_pane)
        left_pane.setFixedWidth(400)
        h_layout.addWidget(left_pane)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setProperty('class', 'AppMonitorScrollArea')
        style_loader.apply_stylesheet(self.scroll_area)
        left_container = QWidget()
        self.grid_layout = QGridLayout(left_container)
        self.grid_layout.setSpacing(8)
        self.scroll_area.setWidget(left_container)
        left_layout.addWidget(self.scroll_area)

        controls = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh List")
        self.refresh_button.clicked.connect(self.populate_app_list)
        controls.addWidget(self.refresh_button)

        self.stop_button = QPushButton("Stop Monitoring")
        self.stop_button.clicked.connect(self.stop_monitoring)
        controls.addWidget(self.stop_button)
        left_layout.addLayout(controls)

        # Right Pane (Live Preview)
        right_pane = QVBoxLayout()
        h_layout.addLayout(right_pane)

        self.info_label = QLabel("Click a thumbnail on the left to start monitoring.")
        self.info_label.setAlignment(Qt.AlignCenter)
        right_pane.addWidget(self.info_label)

        self.preview_label = QLabel()
        self.preview_label.setProperty('class', 'AppMonitorPreviewLabel')
        style_loader.apply_stylesheet(self.preview_label)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        right_pane.addWidget(self.preview_label, 1)

    def populate_app_list(self):
        self.stop_monitoring()
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().deleteLater()
        self.thumb_map.clear()
        
        windows = []
        win32gui.EnumWindows(lambda hwnd, lparam: lparam.append((hwnd, win32gui.GetWindowText(hwnd))), windows)

        cols = 2
        thumb_width = 180
        for i, (hwnd, title) in enumerate(filter(lambda item: item[1] and win32gui.IsWindowVisible(item[0]), windows)):
            pix = CaptureHelpers.capture_thumbnail_qpixmap(hwnd, target_width=thumb_width)
            if not pix:
                pix = QPixmap(thumb_width, int(thumb_width * 0.6))
                pix.fill(QColor("#555"))
            thumb = ThumbnailWidget(hwnd, title, pix)
            thumb.clicked.connect(self.on_thumbnail_clicked)
            self.grid_layout.addWidget(thumb, i // cols, i % cols)
            self.thumb_map[hwnd] = thumb

    def on_thumbnail_clicked(self, hwnd):
        self.stop_monitoring()
        self.selected_hwnd = hwnd
        for h, widget in self.thumb_map.items():
            widget.set_selected(h == hwnd)

        capture_method = "PrintWindow"
        if self.camera:
            try:
                self.camera.start(target_hwnd=hwnd)
                capture_method = "DXCam (WGC)"
            except Exception:
                pass
        
        self.info_label.setText(f"Monitoring: {win32gui.GetWindowText(hwnd)}")
        self.capture_thread = CaptureThread(hwnd, self.camera, capture_method)
        self.capture_thread.frame_ready.connect(self.update_preview)
        self.capture_thread.finished.connect(self.on_capture_finished)
        self.capture_thread.start()

    def update_preview(self, qimg: QImage):
        if self.preview_label.width() > 1 and self.preview_label.height() > 1:
            pixmap = QPixmap.fromImage(qimg).scaled(
                self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.preview_label.setPixmap(pixmap)

    def on_capture_finished(self):
        self.info_label.setText("Monitoring stopped. Click a thumbnail to begin.")
        if self.preview_label: self.preview_label.clear()

    def stop_monitoring(self):
        if self.capture_thread and self.capture_thread.isRunning():
            self.capture_thread.stop()
            self.capture_thread.wait(500)
        if self.camera and DXCAM_AVAILABLE:
            try: self.camera.stop()
            except Exception: pass
        for widget in self.thumb_map.values():
            widget.set_selected(False)
        self.selected_hwnd = None

    def cleanup_on_close(self):
        self.stop_monitoring()
        if self.camera:
            self.camera.release()