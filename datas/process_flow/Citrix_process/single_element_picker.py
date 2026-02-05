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
        self.hide()

    def update_boxes(self, boxes, box_type=None):
        if boxes and len(boxes) > 0:
            new_rect = boxes[0]
            if box_type == "InputField":
                color = QtGui.QColor(0, 255, 0)
            elif box_type == "Text":
                color = QtGui.QColor(0, 255, 0)
            else:
                color = QtGui.QColor(0, 255, 0)

            if (self.current_box is None or
                    not self.current_box.is_active or
                    self.current_box.rect != new_rect or
                    self.current_type != box_type):
                if self.current_box:
                    self.current_box.destroy()
                self.current_box = StableBoundingBox(new_rect, color)
                self.current_type = box_type
        else:
            if self.current_box and self.current_box.is_active:
                self.current_box.hide()


class InfoOverlay(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)

        self.label = QtWidgets.QLabel(self)
        self.label.setStyleSheet("""
            background-color: #F0F0F0CC;
            border-radius: 3px;
            padding: 2px 4px;
            font-family: Consolas, monospace;
            font-size: 6pt;
            color: black;
        """)
        self.label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.label.setWordWrap(True)
        self.label.setMaximumWidth(250)  # limit width so it's compact
        self.hide()

        self._last_text = None
        self._last_pos = None

    def update_info(self, text, global_pos):
        if text == self._last_text and global_pos == self._last_pos:
            return
        self._last_text = text
        self._last_pos = global_pos

        if not text:
            self.hide()
            return

        try:
            parsed = json.loads(text)
            pretty_text = json.dumps(parsed, indent=1, ensure_ascii=False)
            self.label.setText(pretty_text)
        except Exception:
            self.label.setText(text)

        self.label.adjustSize()
        self.adjustSize()

        screen_geom = QtWidgets.QApplication.primaryScreen().geometry()
        x = global_pos.x() + 15
        y = global_pos.y() + 15
        if x + self.width() > screen_geom.right():
            x = screen_geom.right() - self.width() - 10
        if y + self.height() > screen_geom.bottom():
            y = screen_geom.bottom() - self.height() - 10

        self.move(x, y)
        self.show()


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
        self.locked = False  # New: lock the bounding box once stable

    def is_similar_to(self, region_data, capture_offset, tolerance):
        if self.region_type != region_data['type']:
            return False
        local_x, local_y, w, h = region_data['coords']
        new_global_x = capture_offset[0] + local_x
        new_global_y = capture_offset[1] + local_y
        
        # Use centroid-based matching for better stability
        new_centroid_x = new_global_x + w // 2
        new_centroid_y = new_global_y + h // 2
        
        centroid_dist = np.sqrt(
            (new_centroid_x - self.stable_centroid[0]) ** 2 +
            (new_centroid_y - self.stable_centroid[1]) ** 2
        )
        
        # More lenient size matching for small objects
        size_tolerance = max(tolerance, min(w, h) * 0.3)
        
        return (centroid_dist <= tolerance and
                abs(w - self.stable_coords[2]) <= size_tolerance and
                abs(h - self.stable_coords[3]) <= size_tolerance)

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

    def __init__(self, capture_size, update_interval, stability_threshold, tolerance, leave_threshold):
        super().__init__()
        self.capture_size = capture_size
        self.sct = mss.mss()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.track_mouse)
        self.stability_threshold = stability_threshold
        self.tolerance = tolerance
        self.leave_threshold = leave_threshold
        self.current_stable_region = None

    def preprocess_image(self, img_bgr):
        """Enhanced preprocessing for better detection"""
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        
        # Adaptive histogram equalization for better contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        return gray, enhanced

    def detect_input_fields(self, gray, enhanced):
        """Improved input field detection for small text boxes"""
        regions = []
        try:
            # Method 1: Edge-based detection with multiple thresholds
            for low, high in [(30, 100), (50, 150), (70, 200)]:
                blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)
                edges = cv2.Canny(blurred, low, high)
                
                # Morphological operations to connect edges
                kernel_rect = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
                closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel_rect)
                
                contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for cnt in contours:
                    x, y, w, h = cv2.boundingRect(cnt)
                    
                    # Accept smaller boxes (15x15 minimum)
                    if w < 15 or h < 10 or h > 150:
                        continue
                    
                    # Skip near-fullscreen boxes
                    if w > gray.shape[1] * 0.95 or h > gray.shape[0] * 0.95:
                        continue
                    
                    aspect_ratio = w / float(h)
                    
                    # More flexible aspect ratio for small input fields
                    if aspect_ratio < 1.2 or aspect_ratio > 20:
                        continue
                    
                    roi = gray[y:y + h, x:x + w]
                    mean_intensity = np.mean(roi)
                    std_dev = np.std(roi)
                    
                    # Detect light-colored input fields
                    if mean_intensity > 180 or (mean_intensity > 150 and std_dev < 40):
                        # Check if already detected
                        is_duplicate = False
                        for existing in regions:
                            ex, ey, ew, eh = existing['coords']
                            if abs(x - ex) < 10 and abs(y - ey) < 10:
                                is_duplicate = True
                                break
                        
                        if not is_duplicate:
                            regions.append({
                                'type': 'InputField',
                                'text': '',
                                'center': (x + w // 2, y + h // 2),
                                'coords': (x, y, w, h)
                            })
            
            # Method 2: Threshold-based detection for white/light regions
            _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                
                if 15 <= w <= gray.shape[1] * 0.9 and 10 <= h <= 150:
                    aspect_ratio = w / float(h)
                    if 1.2 <= aspect_ratio <= 20:
                        # Check for duplicates
                        is_duplicate = False
                        for existing in regions:
                            ex, ey, ew, eh = existing['coords']
                            if abs(x - ex) < 10 and abs(y - ey) < 10:
                                is_duplicate = True
                                break
                        
                        if not is_duplicate:
                            regions.append({
                                'type': 'InputField',
                                'text': '',
                                'center': (x + w // 2, y + h // 2),
                                'coords': (x, y, w, h)
                            })
                            
        except Exception as e:
            print(f"Input field detection error: {e}")
        
        return regions

    def detect_text_regions(self, gray, enhanced):
        """Enhanced OCR with better preprocessing"""
        regions = []
        try:
            # Multiple OCR passes with different preprocessing
            for img in [gray, enhanced]:
                # Sharpen image
                kernel_sharpen = np.array([[-1,-1,-1],
                                          [-1, 9,-1],
                                          [-1,-1,-1]])
                sharpened = cv2.filter2D(img, -1, kernel_sharpen)
                
                # Binary threshold
                _, binary = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                
                ocr_data = pytesseract.image_to_data(binary, output_type=pytesseract.Output.DICT, config='--psm 11')
                n_boxes = len(ocr_data['level'])
                
                for i in range(n_boxes):
                    x, y, w, h = ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i]
                    text = ocr_data['text'][i].strip()
                    conf = ocr_data['conf'][i]
                    
                    if w > 0 and h > 0 and text and conf > 25:  # Lower confidence threshold
                        cx, cy = x + w // 2, y + h // 2
                        
                        # Check for duplicates
                        is_duplicate = False
                        for existing in regions:
                            ex, ey = existing['center']
                            if abs(cx - ex) < 15 and abs(cy - ey) < 15:
                                is_duplicate = True
                                break
                        
                        if not is_duplicate:
                            regions.append({
                                'type': 'Text',
                                'text': text,
                                'center': (cx, cy),
                                'coords': (x, y, w, h)
                            })
                            
        except Exception as e:
            print(f"OCR error: {e}")
        
        return regions

    def detect_icons_buttons(self, gray, enhanced, existing_regions):
        """Enhanced icon/button detection for small elements"""
        regions = []
        try:
            # Multi-scale edge detection for icons
            for scale in [1.0, 1.2]:
                if scale != 1.0:
                    scaled = cv2.resize(enhanced, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
                else:
                    scaled = enhanced
                
                edges = cv2.Canny(scaled, 40, 120)
                
                # Morphological operations
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
                edges = cv2.dilate(edges, kernel, iterations=1)
                
                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for cnt in contours:
                    x, y, w, h = cv2.boundingRect(cnt)
                    
                    if scale != 1.0:
                        x, y, w, h = int(x/scale), int(y/scale), int(w/scale), int(h/scale)
                    
                    # Accept smaller icons (10x10 minimum)
                    if w < 10 or h < 10 or w > gray.shape[1] * 0.8 or h > gray.shape[0] * 0.8:
                        continue
                    
                    # Check overlap with existing regions
                    overlaps = False
                    for r in existing_regions:
                        rx, ry, rw, rh = r['coords']
                        if not (x + w < rx or x > rx + rw or y + h < ry or y > ry + rh):
                            overlaps = True
                            break
                    
                    if overlaps:
                        continue
                    
                    cx, cy = x + w // 2, y + h // 2
                    
                    # Check for duplicates
                    is_duplicate = False
                    for existing in regions:
                        ex, ey = existing['center']
                        if abs(cx - ex) < 15 and abs(cy - ey) < 15:
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        regions.append({
                            'type': 'Icon/Button',
                            'text': '',
                            'center': (cx, cy),
                            'coords': (x, y, w, h)
                        })
                        
        except Exception as e:
            print(f"Icon detection error: {e}")
        
        return regions

    def detect_regions(self, img_bgr):
        """Main detection pipeline"""
        gray, enhanced = self.preprocess_image(img_bgr)
        
        # Detect in priority order
        input_fields = self.detect_input_fields(gray, enhanced)
        text_regions = self.detect_text_regions(gray, enhanced)
        icons_buttons = self.detect_icons_buttons(gray, enhanced, input_fields + text_regions)
        
        # Combine all regions
        all_regions = input_fields + text_regions + icons_buttons
        
        return all_regions

    def track_mouse(self):
        try:
            x, y = pyautogui.position()
            left = max(x - self.capture_size // 2, 0)
            top = max(y - self.capture_size // 2, 0)
            region = {"left": left, "top": top, "width": self.capture_size, "height": self.capture_size}
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
                        self.current_stable_region.is_similar_to(hovered_region_data, capture_offset, self.tolerance)):
                    
                    self.current_stable_region.stability_count += 1
                    self.current_stable_region.leave_count = 0
                    
                    # Lock the region after stability threshold
                    if self.current_stable_region.stability_count >= self.stability_threshold:
                        if not self.current_stable_region.locked:
                            self.current_stable_region.locked = True
                        
                        # Keep showing the SAME bounding box (no updates)
                        bounding_boxes = [self.current_stable_region.get_qt_rect()]
                        info_json = self.current_stable_region.get_info_json()
                        region_type = self.current_stable_region.region_type
                        self.update_signal.emit(bounding_boxes, info_json, QtCore.QPoint(x, y), region_type)
                else:
                    # New region detected
                    if self.current_stable_region is not None:
                        self.update_signal.emit([], "", QtCore.QPoint(x, y), "")
                    
                    self.current_stable_region = StableRegion(hovered_region_data, capture_offset)
                    
                    # Show immediately
                    bounding_boxes = [self.current_stable_region.get_qt_rect()]
                    info_json = self.current_stable_region.get_info_json()
                    region_type = hovered_region_data['type']
                    self.update_signal.emit(bounding_boxes, info_json, QtCore.QPoint(x, y), region_type)
            else:
                # Mouse left the region
                if self.current_stable_region is not None:
                    self.current_stable_region.leave_count += 1
                    
                    if self.current_stable_region.leave_count > self.leave_threshold:
                        self.current_stable_region = None
                        self.update_signal.emit([], "", QtCore.QPoint(x, y), "")
                else:
                    self.update_signal.emit([], "", QtCore.QPoint(x, y), "")
                    
        except Exception as e:
            print(f"Mouse tracking error: {e}")
            self.update_signal.emit([], "", QtCore.QPoint(x, y), "")


class MaskWidget(QtWidgets.QWidget):
    should_exit = QtCore.pyqtSignal()

    def __init__(self, append_log_func):
        super().__init__()
        self.append_log = append_log_func
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
                    
                    if self.append_log(log_entry):
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
                
                if self.append_log(log_entry):
                    print(f"Logged generic click at {timestamp}")
            
            self.should_exit.emit()
        event.accept()


class LocatorManager(QtCore.QObject):
    should_exit = QtCore.pyqtSignal()

    def __init__(self, app, standalone, append_log_func):
        super().__init__()
        self.app = app
        self.standalone = standalone
        self.append_log_func = append_log_func
        self.overlay = OverlayWidget()
        self.info_overlay = InfoOverlay()
        self.mouse_tracker = None
        self.mask = None
        self.update_ui = self._update_ui

    def initialize(self, capture_size, update_interval, stability_threshold, tolerance, leave_threshold):
        self.mouse_tracker = MouseTracker(capture_size, update_interval, stability_threshold, tolerance, leave_threshold)
        self.mouse_tracker.update_signal.connect(self.update_ui)
        self.mask = MaskWidget(self.append_log_func)
        self.mask.should_exit.connect(self.on_mask_exit)

    @QtCore.pyqtSlot(list, str, QtCore.QPoint, str)
    def _update_ui(self, bounding_boxes, info_text, cursor_pos, box_type):
        self.overlay.update_boxes(bounding_boxes, box_type)
        self.info_overlay.update_info(info_text, cursor_pos)
        info_list = [info_text] if info_text else []
        self.mask.update_regions(bounding_boxes, info_list)

    def start_tracking(self):
        self.mouse_tracker.timer.start()
        self.mask.lower()
        self.info_overlay.raise_()

    def on_mask_exit(self):
        self.cleanup()
        if self.standalone:
            self.app.quit()
        else:
            self.should_exit.emit()

    def cleanup(self):
        if self.mouse_tracker:
            self.mouse_tracker.timer.stop()
        if self.overlay.current_box:
            self.overlay.current_box.destroy()
            self.overlay.current_box = None
        self.info_overlay.hide()
        if self.mask:
            self.mask.hide()
            self.mask.close()


def citrix_mod_locator():
    # TESSERACT_PATH = r"D:\PACKAGES\Tessaract-OCR\tesseract.exe"
    TESSERACT_PATH=r"C:\Droidal\Cloud_Droidal\Cluster\Tesseract-OCR\tesseract.exe"
    # -------- OPTIMIZED CONFIGURATION --------
    SCREEN_CAPTURE_SIZE = 500  # Larger capture for better context
    UPDATE_INTERVAL_MS = 150  # Faster updates
    STABILITY_FRAME_COUNT = 2  # Quick lock after 2 frames
    COORDINATE_TOLERANCE = 15  # More lenient for small objects
    REGION_LEAVE_FRAMES = 3  # Quick removal when mouse leaves

    # Output folder
    OUTPUT_FOLDER = "citrix_output"
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    LOG_FILE = os.path.join(OUTPUT_FOLDER, "single_click_log.json")

    # Disable PyAutoGUI fail-safe
    pyautogui.FAILSAFE = False
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

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

    initialize_log_file()

    app = QtWidgets.QApplication.instance()
    standalone = False
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
        standalone = True

    manager = LocatorManager(app, standalone, append_log_entry)
    manager.initialize(SCREEN_CAPTURE_SIZE, UPDATE_INTERVAL_MS, STABILITY_FRAME_COUNT, 
                      COORDINATE_TOLERANCE, REGION_LEAVE_FRAMES)
    manager.start_tracking()

    if standalone:
        app.exec_()
    else:
        loop = QtCore.QEventLoop()
        manager.should_exit.connect(loop.quit)
        loop.exec_()

    # Return final JSON content
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# if __name__ == "__main__":
#     result_json = citrix_mod_locator()
#     print("Final JSON output saved in citrix_output/single_click_log.json")
#     print(json.dumps(result_json, indent=2, ensure_ascii=False))