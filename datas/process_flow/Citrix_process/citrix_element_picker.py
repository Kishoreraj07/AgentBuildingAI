import sys
import time
import json
import os
import numpy as np
import pytesseract
import cv2
import mss
import pyautogui
from PyQt5 import QtCore, QtGui, QtWidgets


def element_picker():
    # tesseract_path=r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    tesseract_path=r"C:\Droidal\Cloud_Droidal\Cluster\Tesseract-OCR\tesseract.exe"
    # -------- CONFIGURATION --------
    SCREEN_CAPTURE_SIZE = 400
    UPDATE_INTERVAL_MS = 200
    STABILITY_FRAME_COUNT = 3
    COORDINATE_TOLERANCE = 10
    REGION_LEAVE_FRAMES = 5

    # Output folder
    OUTPUT_FOLDER = "Citrix_process"
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    LOG_FILE = os.path.join(OUTPUT_FOLDER, "single_click_log.json")

    # Disable PyAutoGUI fail-safe
    pyautogui.FAILSAFE = False
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

    def initialize_log_file():
        try:
            if os.path.exists(LOG_FILE):
                os.remove(LOG_FILE)
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error initializing log file: {e}")
            return False

    def append_log_entry(log_entry):
        try:
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            else:
                logs = []
            logs.append(log_entry)
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error writing JSON log: {e}")
            return False

    class StableBoundingBox:
        def __init__(self, rect, color=QtGui.QColor(0, 255, 0)):
            self.rect = rect
            self.color = color
            self.is_active = True
            self.widget = None
            self.create_widget()

        def create_widget(self):
            self.widget = QtWidgets.QWidget()
            self.widget.setWindowFlags(
                QtCore.Qt.FramelessWindowHint |
                QtCore.Qt.WindowStaysOnTopHint |
                QtCore.Qt.Tool |
                QtCore.Qt.WindowTransparentForInput
            )
            self.widget.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
            self.widget.setAttribute(QtCore.Qt.WA_TranslucentBackground)
            self.widget.setGeometry(self.rect)
            self.widget.paintEvent = self._paint_event
            self.widget.show()

        def _paint_event(self, event):
            painter = QtGui.QPainter(self.widget)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            pen = QtGui.QPen(self.color, 3, QtCore.Qt.SolidLine)
            painter.setPen(pen)
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawRect(0, 0, self.widget.width() - 1, self.widget.height() - 1)

        def hide(self):
            if self.widget:
                self.widget.hide()
                self.is_active = False

        def destroy(self):
            if self.widget:
                self.widget.close()
                self.widget.deleteLater()
                self.widget = None
                self.is_active = False

    class OverlayWidget(QtWidgets.QWidget):
        def __init__(self):
            super().__init__()
            self.current_box = None
            self.current_type = None
            self.is_locked = False
            self.hide()

        def update_boxes(self, boxes, box_type=None):
            if self.is_locked:
                return
            if boxes and len(boxes) > 0:
                new_rect = boxes[0]
                if box_type == "InputField":
                    color = QtGui.QColor(255, 165, 0)
                elif box_type == "Text":
                    color = QtGui.QColor(0, 255, 0)
                else:
                    color = QtGui.QColor(0, 128, 255)

                if (self.current_box is None or
                        not self.current_box.is_active or
                        self.current_box.rect != new_rect or
                        self.current_type != box_type):
                    if self.current_box:
                        self.current_box.destroy()
                    self.current_box = StableBoundingBox(new_rect, color)
                    self.current_type = box_type
            else:
                if self.current_box and self.current_box.is_active and not self.is_locked:
                    self.current_box.hide()

        def lock_region(self):
            self.is_locked = True

        def unlock_region(self):
            self.is_locked = False
            if self.current_box:
                self.current_box.destroy()
                self.current_box = None
                self.current_type = None

    class InfoOverlay(QtWidgets.QWidget):
        def __init__(self):
            super().__init__()
            self.setWindowFlags(
                QtCore.Qt.FramelessWindowHint |
                QtCore.Qt.WindowStaysOnTopHint |
                QtCore.Qt.Tool
            )
            self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
            self.label = QtWidgets.QLabel(self)
            self.label.setStyleSheet("""
                background-color: #F0F0F0DD;
                border-radius: 5px;
                padding: 6px;
                font-family: Consolas, monospace;
                font-size: 10pt;
                color: black;
            """)
            self.label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
            self.label.adjustSize()
            self.hide()
            self._last_text = None
            self._last_pos = None
            self.is_locked = False
            self.locked_text = None
            self.locked_pos = None

        def update_info(self, text, global_pos):
            if self.is_locked:
                return
            if text == self._last_text and global_pos == self._last_pos:
                return
            self._last_text = text
            self._last_pos = global_pos
            if not text:
                self.hide()
                return
            try:
                parsed = json.loads(text)
                pretty_text = json.dumps(parsed, indent=2, ensure_ascii=False)
                self.label.setText(pretty_text)
            except Exception:
                self.label.setText(text)
            self.label.adjustSize()
            self.adjustSize()
            screen_geom = QtWidgets.QApplication.primaryScreen().geometry()
            x = global_pos.x() + 20
            y = global_pos.y() + 20
            if x + self.width() > screen_geom.right():
                x = screen_geom.right() - self.width() - 10
            if y + self.height() > screen_geom.bottom():
                y = screen_geom.bottom() - self.height() - 10
            self.move(x, y)
            self.show()

        def lock_info(self, text, global_pos):
            self.is_locked = True
            self.locked_text = text
            self.locked_pos = global_pos
            try:
                parsed = json.loads(text)
                pretty_text = json.dumps(parsed, indent=2, ensure_ascii=False)
                self.label.setText(pretty_text)
            except Exception:
                self.label.setText(text)
            self.label.adjustSize()
            self.adjustSize()
            self.show()

        def unlock_info(self):
            self.is_locked = False
            self.locked_text = None
            self.locked_pos = None
            self._last_text = None
            self._last_pos = None

    class StableRegion:
        def __init__(self, region_data, capture_offset):
            self.region_type = region_data['type']
            self.text = region_data.get('text', '')
            local_x, local_y, w, h = region_data['coords']
            self.stable_coords = (
                capture_offset[0] + local_x,
                capture_offset[1] + local_y,
                w,
                h
            )
            self.stable_centroid = (
                self.stable_coords[0] + w // 2,
                self.stable_coords[1] + h // 2
            )
            self.stability_count = 1
            self.leave_count = 0

        def is_similar_to(self, region_data, capture_offset, tolerance=COORDINATE_TOLERANCE):
            if self.region_type != region_data['type']:
                return False
            local_x, local_y, w, h = region_data['coords']
            new_global_x = capture_offset[0] + local_x
            new_global_y = capture_offset[1] + local_y
            return (abs(new_global_x - self.stable_coords[0]) <= tolerance and
                    abs(new_global_y - self.stable_coords[1]) <= tolerance and
                    abs(w - self.stable_coords[2]) <= tolerance and
                    abs(h - self.stable_coords[3]) <= tolerance)

        def get_info_json(self):
            x, y, w, h = self.stable_coords
            data = {
                "type": self.region_type,
                "coordinates": {
                    "top_left": {"x": x, "y": y},
                    "top_right": {"x": x + w, "y": y},
                    "bottom_left": {"x": x, "y": y + h},
                    "bottom_right": {"x": x + w, "y": y + h}
                },
                "centroid": {"x": self.stable_centroid[0], "y": self.stable_centroid[1]}
            }
            if self.text:
                data["text"] = self.text
            return json.dumps(data, ensure_ascii=False)

        def get_qt_rect(self):
            x, y, w, h = self.stable_coords
            return QtCore.QRect(x, y, w, h)

    class MouseTracker(QtCore.QObject):
        update_signal = QtCore.pyqtSignal(list, str, QtCore.QPoint, str)

        def __init__(self):
            super().__init__()
            self.sct = mss.mss()
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.track_mouse)
            self.timer.start(UPDATE_INTERVAL_MS)
            self.current_stable_region = None
            self.is_locked = False

        def detect_regions(self, img_bgr):
            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            regions = []
            try:
                blurred = cv2.GaussianBlur(gray, (5, 5), 0)
                edges = cv2.Canny(blurred, 50, 150)
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
                dilated = cv2.dilate(edges, kernel, iterations=1)
                contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for cnt in contours:
                    x, y, w, h = cv2.boundingRect(cnt)
                    if w < 50 or h < 15 or h > 100:
                        continue
                    if w > img_bgr.shape[1] * 0.95 or h > img_bgr.shape[0] * 0.95:
                        continue
                    aspect_ratio = w / float(h)
                    if aspect_ratio < 1.5 or aspect_ratio > 15:
                        continue
                    roi = gray[y:y + h, x:x + w]
                    mean_intensity = np.mean(roi)
                    std_dev = np.std(roi)
                    if mean_intensity > 200 and std_dev < 30:
                        regions.append({
                            'type': 'InputField',
                            'text': '',
                            'center': (x + w // 2, y + h // 2),
                            'coords': (x, y, w, h)
                        })
                        continue
            except Exception as e:
                print(f"Input field detection error: {e}")
            try:
                ocr_data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
                n_boxes = len(ocr_data['level'])
                for i in range(n_boxes):
                    x, y, w, h = ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i]
                    text = ocr_data['text'][i].strip()
                    conf = ocr_data['conf'][i]
                    if w > 0 and h > 0 and text and conf > 30:
                        cx, cy = x + w // 2, y + h // 2
                        regions.append({
                            'type': 'Text',
                            'text': text,
                            'center': (cx, cy),
                            'coords': (x, y, w, h)
                        })
            except Exception as e:
                print(f"OCR error: {e}")
            try:
                edges = cv2.Canny(gray, 30, 100)
                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for cnt in contours:
                    x, y, w, h = cv2.boundingRect(cnt)
                    if w < 20 or h < 20 or w > img_bgr.shape[1] * 0.9 or h > img_bgr.shape[0] * 0.9:
                        continue
                    is_input = False
                    for r in regions:
                        if r['type'] == 'InputField':
                            rx, ry, rw, rh = r['coords']
                            if (x < rx + rw and x + w > rx and y < ry + rh and y + h > ry):
                                is_input = True
                                break
                    if is_input:
                        continue
                    cx, cy = x + w // 2, y + h // 2
                    regions.append({
                        'type': 'styles/Icon/Button',
                        'text': '',
                        'center': (cx, cy),
                        'coords': (x, y, w, h)
                    })
            except Exception as e:
                print(f"Contour detection error: {e}")
            return regions

        def lock_tracking(self):
            self.is_locked = True

        def unlock_tracking(self):
            self.is_locked = False
            self.current_stable_region = None

        def track_mouse(self):
            if self.is_locked:
                return
            try:
                x, y = pyautogui.position()
                left = max(x - SCREEN_CAPTURE_SIZE // 2, 0)
                top = max(y - SCREEN_CAPTURE_SIZE // 2, 0)
                region = {"left": left, "top": top, "width": SCREEN_CAPTURE_SIZE, "height": SCREEN_CAPTURE_SIZE}
                sct_img = np.array(self.sct.grab(region))
                img_bgr = cv2.cvtColor(sct_img, cv2.COLOR_BGRA2BGR)
                detected_regions = self.detect_regions(img_bgr)
                cursor_local_x, cursor_local_y = x - left, y - top
                hovered_region_data = None
                for r in detected_regions:
                    rx, ry, rw, rh = r['coords']
                    if rx <= cursor_local_x <= rx + rw and ry <= cursor_local_y <= ry + rh:
                        hovered_region_data = r
                        break
                capture_offset = (left, top)
                if hovered_region_data is not None:
                    if (self.current_stable_region is not None and
                            self.current_stable_region.is_similar_to(hovered_region_data, capture_offset)):
                        self.current_stable_region.stability_count += 1
                        self.current_stable_region.leave_count = 0
                        if self.current_stable_region.stability_count >= STABILITY_FRAME_COUNT:
                            bounding_boxes = [self.current_stable_region.get_qt_rect()]
                            info_json = self.current_stable_region.get_info_json()
                            region_type = hovered_region_data['type']
                            self.update_signal.emit(bounding_boxes, info_json, QtCore.QPoint(x, y), region_type)
                    else:
                        if self.current_stable_region is not None:
                            self.update_signal.emit([], "", QtCore.QPoint(x, y), "")
                        self.current_stable_region = StableRegion(hovered_region_data, capture_offset)
                else:
                    if self.current_stable_region is not None:
                        self.current_stable_region.leave_count += 1
                        if self.current_stable_region.leave_count > REGION_LEAVE_FRAMES:
                            self.current_stable_region = None
                            self.update_signal.emit([], "", QtCore.QPoint(x, y), "")
                    else:
                        self.update_signal.emit([], "", QtCore.QPoint(x, y), "")
            except Exception as e:
                print(f"Mouse tracking error: {e}")
                self.update_signal.emit([], "", QtCore.QPoint(x, y), "")

    class MaskWidget(QtWidgets.QWidget):
        should_exit = QtCore.pyqtSignal()

        def __init__(self):
            super().__init__()
            self.setWindowFlags(
                QtCore.Qt.FramelessWindowHint |
                QtCore.Qt.WindowStaysOnTopHint |
                QtCore.Qt.Tool
            )
            self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)
            self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
            self.setGeometry(QtWidgets.QApplication.primaryScreen().geometry())
            self.bounding_boxes = []
            self.info_texts = []
            self.show()

        def update_regions(self, bounding_boxes, info_texts):
            self.bounding_boxes = bounding_boxes
            self.info_texts = info_texts

        def paintEvent(self, event):
            painter = QtGui.QPainter(self)
            painter.fillRect(self.rect(), QtGui.QColor(0, 0, 0, 100))

        def mousePressEvent(self, event):
            if event.button() == QtCore.Qt.LeftButton:
                pos = event.globalPos()
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                clicked_on_region = False
                for rect, info_json in zip(self.bounding_boxes, self.info_texts):
                    if rect.contains(pos):
                        try:
                            region_info = json.loads(info_json)
                        except Exception:
                            region_info = None
                        log_entry = {
                            "timestamp": timestamp,
                            "event": "region_click",
                            "region_info": region_info
                        }
                        if append_log_entry(log_entry):
                            print(f"Logged region click at {timestamp}")
                        clicked_on_region = True
                        break
                if not clicked_on_region:
                    x, y = pos.x(), pos.y()
                    log_entry = {
                        "timestamp": timestamp,
                        "event": "generic_click",
                        "region_info": {
                            "type": "Generic",
                            "coordinates": {
                                "top_left": {"x": x, "y": y},
                                "top_right": {"x": x, "y": y},
                                "bottom_left": {"x": x, "y": y},
                                "bottom_right": {"x": x, "y": y}
                            },
                            "centroid": {"x": x, "y": y}
                        }
                    }
                    if append_log_entry(log_entry):
                        print(f"Logged generic click at {timestamp}")
                self.should_exit.emit()
            event.accept()

    class MainApp(QtWidgets.QApplication):
        def __init__(self, argv):
            super().__init__(argv)
            initialize_log_file()
            self.overlay = OverlayWidget()
            self.info_overlay = InfoOverlay()
            self.mouse_tracker = MouseTracker()
            self.mouse_tracker.update_signal.connect(self.update_ui)
            self.mask = MaskWidget()
            self.mask.should_exit.connect(self.quit)
            self.mask.lower()
            self.info_overlay.raise_()
            self.locked_state = False

        @QtCore.pyqtSlot(list, str, QtCore.QPoint, str)
        def update_ui(self, bounding_boxes, info_text, cursor_pos, box_type):
            if not self.locked_state:
                self.overlay.update_boxes(bounding_boxes, box_type)
                self.info_overlay.update_info(info_text, cursor_pos)
                if bounding_boxes and info_text:
                    self.locked_state = True
                    self.overlay.lock_region()
                    self.info_overlay.lock_info(info_text, cursor_pos)
                    self.mouse_tracker.lock_tracking()
                    self.mask.update_regions(bounding_boxes, [info_text])
                else:
                    self.mask.update_regions([], [])

        def quit(self):
            self.locked_state = False
            self.overlay.unlock_region()
            self.info_overlay.unlock_info()
            self.mouse_tracker.unlock_tracking()
            super().quit()

    app = MainApp(sys.argv)
    app.exec_()
    sys.exit(app.exec_())

    # Return final JSON content
    


# if __name__ == "__main__":
#     TESSERACT_PATH = r"C:\\Users\\Sivakumar.b\\AppData\\Local\\Programs\\Tesseract-OCR\\tesseract.exe"
#     result_json = citrix_mod_locator(TESSERACT_PATH)
#     print("Final JSON output saved in citrix_output/single_click_log.json")
#     print(json.dumps(result_json, indent=2, ensure_ascii=False))