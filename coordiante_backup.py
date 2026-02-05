import sys
import time
import json
import numpy as np
import pytesseract
import cv2
import mss
import pyautogui
from PyQt5 import QtCore, QtGui, QtWidgets

# --- Bounding Box Class ---
# Draws the actual highlight box
class StableBoundingBox:
    def __init__(self, rect, color = QtGui.QColor(65, 105, 225)): # Darker Cyan
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
        pen = QtGui.QPen(self.color, 3, QtCore.Qt.SolidLine) # Use self.color
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

# --- Overlay Controller ---
# Manages creating/destroying highlight boxes
class OverlayWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.current_box = None
        self.current_type = None
        self.hide()

    def update_boxes(self, boxes, box_type=None):
        if boxes and len(boxes) > 0:
            new_rect = boxes[0]
            
            # Set all box colors to Darker Cyan
            color = QtGui.QColor(0, 180, 180) 

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

# --- InfoOverlay Class Removed ---
# No more JSON popup on hover

# --- Region Stability Logic ---
# (Used by MouseTracker)
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
        self.locked = False

    def is_similar_to(self, region_data, capture_offset, tolerance):
        if self.region_type != region_data['type']:
            return False
        local_x, local_y, w, h = region_data['coords']
        new_global_x = capture_offset[0] + local_x
        new_global_y = capture_offset[1] + local_y
        
        new_centroid_x = new_global_x + w // 2
        new_centroid_y = new_global_y + h // 2
        
        centroid_dist = np.sqrt(
            (new_centroid_x - self.stable_centroid[0]) ** 2 +
            (new_centroid_y - self.stable_centroid[1]) ** 2
        )
        
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

# --- Mouse Tracker & CV Engine ---
# Follows mouse, captures screen, finds elements
class MouseTracker(QtCore.QObject):
    # Signal now only sends data needed by OverlayWidget and MaskWidget
    update_signal = QtCore.pyqtSignal(list, str, str) # (boxes, info_json, box_type)

    def __init__(self, capture_size, update_interval, stability_threshold, tolerance, leave_threshold):
        super().__init__()
        self.capture_size = capture_size
        self.sct = mss.mss()
        self.timer = QtCore.QTimer()
        self.timer.setInterval(update_interval) # Use passed-in interval
        self.timer.timeout.connect(self.track_mouse)
        self.stability_threshold = stability_threshold
        self.tolerance = tolerance
        self.leave_threshold = leave_threshold
        self.current_stable_region = None

    # --- OpenCV / Tesseract Detection Logic (Unchanged) ---
    def preprocess_image(self, img_bgr):
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        return gray, enhanced

    def detect_input_fields(self, gray, enhanced):
        regions = []
        try:
            for low, high in [(30, 100), (50, 150), (70, 200)]:
                blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)
                edges = cv2.Canny(blurred, low, high)
                kernel_rect = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
                closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel_rect)
                contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for cnt in contours:
                    x, y, w, h = cv2.boundingRect(cnt)
                    if w < 15 or h < 10 or h > 150: continue
                    if w > gray.shape[1] * 0.95 or h > gray.shape[0] * 0.95: continue
                    aspect_ratio = w / float(h)
                    if aspect_ratio < 1.2 or aspect_ratio > 20: continue
                    
                    roi = gray[y:y + h, x:x + w]
                    mean_intensity = np.mean(roi)
                    std_dev = np.std(roi)
                    
                    if mean_intensity > 180 or (mean_intensity > 150 and std_dev < 40):
                        is_duplicate = False
                        for existing in regions:
                            ex, ey, ew, eh = existing['coords']
                            if abs(x - ex) < 10 and abs(y - ey) < 10:
                                is_duplicate = True
                                break
                        if not is_duplicate:
                            regions.append({'type': 'InputField', 'text': '', 'center': (x + w // 2, y + h // 2), 'coords': (x, y, w, h)})
            
            _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                if 15 <= w <= gray.shape[1] * 0.9 and 10 <= h <= 150:
                    aspect_ratio = w / float(h)
                    if 1.2 <= aspect_ratio <= 20:
                        is_duplicate = False
                        for existing in regions:
                            ex, ey, ew, eh = existing['coords']
                            if abs(x - ex) < 10 and abs(y - ey) < 10:
                                is_duplicate = True
                                break
                        if not is_duplicate:
                            regions.append({'type': 'InputField', 'text': '', 'center': (x + w // 2, y + h // 2), 'coords': (x, y, w, h)})
        except Exception as e:
            print(f"Input field detection error: {e}")
        return regions

    def detect_text_regions(self, gray, enhanced):
        regions = []
        try:
            for img in [gray, enhanced]:
                kernel_sharpen = np.array([[-1,-1,-1], [-1, 9,-1], [-1,-1,-1]])
                sharpened = cv2.filter2D(img, -1, kernel_sharpen)
                _, binary = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                
                ocr_data = pytesseract.image_to_data(binary, output_type=pytesseract.Output.DICT, config='--psm 11')
                n_boxes = len(ocr_data['level'])
                
                for i in range(n_boxes):
                    x, y, w, h = ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i]
                    text = ocr_data['text'][i].strip()
                    conf = ocr_data['conf'][i]
                    
                    if w > 0 and h > 0 and text and conf > 25:
                        cx, cy = x + w // 2, y + h // 2
                        is_duplicate = False
                        for existing in regions:
                            ex, ey = existing['center']
                            if abs(cx - ex) < 15 and abs(cy - ey) < 15:
                                is_duplicate = True
                                break
                        if not is_duplicate:
                            regions.append({'type': 'Text', 'text': text, 'center': (cx, cy), 'coords': (x, y, w, h)})
        except Exception as e:
            print(f"OCR error: {e}")
        return regions

    def detect_icons_buttons(self, gray, enhanced, existing_regions):
        regions = []
        try:
            for scale in [1.0, 1.2]:
                if scale != 1.0:
                    scaled = cv2.resize(enhanced, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
                else:
                    scaled = enhanced
                
                edges = cv2.Canny(scaled, 40, 120)
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
                edges = cv2.dilate(edges, kernel, iterations=1)
                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for cnt in contours:
                    x, y, w, h = cv2.boundingRect(cnt)
                    if scale != 1.0:
                        x, y, w, h = int(x/scale), int(y/scale), int(w/scale), int(h/scale)
                    
                    if w < 10 or h < 10 or w > gray.shape[1] * 0.8 or h > gray.shape[0] * 0.8:
                        continue
                    
                    overlaps = False
                    for r in existing_regions:
                        rx, ry, rw, rh = r['coords']
                        if not (x + w < rx or x > rx + rw or y + h < ry or y > ry + rh):
                            overlaps = True
                            break
                    if overlaps: continue
                    
                    cx, cy = x + w // 2, y + h // 2
                    is_duplicate = False
                    for existing in regions:
                        ex, ey = existing['center']
                        if abs(cx - ex) < 15 and abs(cy - ey) < 15:
                            is_duplicate = True
                            break
                    if not is_duplicate:
                        regions.append({'type': 'styles/Icon/Button', 'text': '', 'center': (cx, cy), 'coords': (x, y, w, h)})
        except Exception as e:
            print(f"Icon detection error: {e}")
        return regions

    def detect_general_contours(self, gray, enhanced, existing_regions):
        """Finds any other 'box-like' regions as a fallback."""
        regions = []
        try:
            edges = cv2.Canny(enhanced, 30, 100)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            dilated = cv2.dilate(edges, kernel, iterations=1)
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                if w < 8 or h < 8 or w > gray.shape[1] * 0.95 or h > gray.shape[0] * 0.95:
                    continue
                overlaps = False
                for r in existing_regions:
                    rx, ry, rw, rh = r['coords']
                    if not (x + w < rx or x > rx + rw or y + h < ry or y > ry + rh):
                        overlaps = True
                        break
                if overlaps:
                    continue
                regions.append({
                    'type': 'Region', # Generic type
                    'text': '',
                    'center': (x + w // 2, y + h // 2),
                    'coords': (x, y, w, h)
                })
        except Exception as e:
            print(f"General contour detection error: {e}")
        return regions

    def detect_regions(self, img_bgr):
        """Main detection pipeline"""
        gray, enhanced = self.preprocess_image(img_bgr)
        input_fields = self.detect_input_fields(gray, enhanced)
        text_regions = self.detect_text_regions(gray, enhanced)
        icons_buttons = self.detect_icons_buttons(gray, enhanced, input_fields + text_regions)
        all_smart_regions = input_fields + text_regions + icons_buttons
        general_regions = self.detect_general_contours(gray, enhanced, all_smart_regions)
        all_regions = all_smart_regions + general_regions
        return all_regions
    # --- End of Detection Logic ---

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
            
            min_area = float('inf')
            for r in detected_regions:
                rx, ry, rw, rh = r['coords']
                if rx <= cursor_local_x <= rx + rw and ry <= cursor_local_y <= ry + rh:
                    area = rw * rh
                    if area < min_area:
                        min_area = area
                        hovered_region_data = r
            
            capture_offset = (left, top)
            
            if hovered_region_data is not None:
                if (self.current_stable_region is not None and
                        self.current_stable_region.is_similar_to(hovered_region_data, capture_offset, self.tolerance)):
                    
                    self.current_stable_region.stability_count += 1
                    self.current_stable_region.leave_count = 0
                    
                    if self.current_stable_region.stability_count >= self.stability_threshold:
                        if not self.current_stable_region.locked:
                            self.current_stable_region.locked = True
                        
                        bounding_boxes = [self.current_stable_region.get_qt_rect()]
                        info_json = self.current_stable_region.get_info_json()
                        region_type = self.current_stable_region.region_type
                        # Emit signal without cursor position
                        self.update_signal.emit(bounding_boxes, info_json, region_type)
                else:
                    if self.current_stable_region is not None:
                        self.update_signal.emit([], "", "")
                    
                    self.current_stable_region = StableRegion(hovered_region_data, capture_offset)
                    
                    bounding_boxes = [self.current_stable_region.get_qt_rect()]
                    info_json = self.current_stable_region.get_info_json()
                    region_type = hovered_region_data['type']
                    # Emit signal without cursor position
                    self.update_signal.emit(bounding_boxes, info_json, region_type)
            else:
                if self.current_stable_region is not None:
                    self.current_stable_region.leave_count += 1
                    
                    if self.current_stable_region.leave_count > self.leave_threshold:
                        self.current_stable_region = None
                        self.update_signal.emit([], "", "")
                else:
                    self.update_signal.emit([], "", "")
                    
        except Exception as e:
            print(f"Mouse tracking error: {e}")
            self.update_signal.emit([], "", "")

# --- Full Screen Mask Widget ---
# Covers screen, intercepts click, and stores data
class MaskWidget(QtWidgets.QWidget):
    should_exit = QtCore.pyqtSignal() # Signal to tell manager to stop

    def __init__(self):
        super().__init__()
        # Store the click data here
        self.clicked_log_entry = None
        self.clicked_bounds = None
        self.clicked_position = None  # Store the exact [x, y] click position
        
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool |
            QtCore.Qt.X11BypassWindowManagerHint
        )
        # CRITICAL: Must receive mouse events
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating, False)  # Allow activation to receive events
        self.setGeometry(QtWidgets.QApplication.primaryScreen().geometry())
        self.bounding_boxes = []
        self.info_texts = []

        
        # Ensure widget is shown and can receive events
        self.show()
        self.raise_()
        self.activateWindow()

    def update_regions(self, bounding_boxes, info_texts):
        # Keep track of the currently highlighted region
        self.bounding_boxes = bounding_boxes
        self.info_texts = info_texts

    def paintEvent(self, event):
        # Draw the semi-transparent mask
        painter = QtGui.QPainter(self)
        painter.fillRect(self.rect(), QtGui.QColor(0, 0, 0, 100))

    def mousePressEvent(self, event):
        print(f"MaskWidget: mousePressEvent called - button: {event.button()}")
        if event.button() == QtCore.Qt.LeftButton:
            pos = event.globalPos()
            click_x, click_y = pos.x(), pos.y()
            print(f"MaskWidget: Left click detected at {click_x}, {click_y}")
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            clicked_on_region = False
            
            # Check if click was inside the currently highlighted box
            for rect, info_json in zip(self.bounding_boxes, self.info_texts):
                if rect.contains(pos):
                    try:
                        region_info = json.loads(info_json)
                    except Exception:
                        region_info = None
                    
                    # This is the data format you wanted
                    log_entry = {
                        "timestamp": timestamp,
                        "event": "region_click",
                        "region_info": region_info
                    }
                    
                    # Store the log entry, bounds, and click position
                    self.clicked_log_entry = log_entry
                    self.clicked_position = [click_x, click_y]  # Store exact click position
                    if region_info:
                        l = region_info['coordinates']['top_left']['x']
                        r = region_info['coordinates']['top_right']['x']
                        t = region_info['coordinates']['top_left']['y']
                        b = region_info['coordinates']['bottom_left']['y']
                        self.clicked_bounds = [l, r, t, b]
                        print(f"MaskWidget: Stored region bounds: {self.clicked_bounds}")
                        print(f"MaskWidget: Stored click position: {self.clicked_position}")
                    
                    clicked_on_region = True
                    break
            
            if not clicked_on_region:
                # Fallback for a generic click on the mask
                x, y = click_x, click_y
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
                # Store the generic log entry, bounds, and click position
                self.clicked_log_entry = log_entry
                self.clicked_bounds = [x, x, y, y]
                self.clicked_position = [click_x, click_y]  # Store exact click position
                print(f"MaskWidget: Stored generic click bounds: {self.clicked_bounds}")
                print(f"MaskWidget: Stored click position: {self.clicked_position}")
            
            # Tell the manager to stop and clean up
            print("MaskWidget: Emitting should_exit signal...")
            self.should_exit.emit()
            print("MaskWidget: Signal emitted")
        else:
            print(f"MaskWidget: Ignoring non-left button click: {event.button()}")
        event.accept()

# --- Main Controller ---
# Ties all widgets and trackers together
class LocatorManager(QtCore.QObject):
    should_exit = QtCore.pyqtSignal()

    def __init__(self, app, standalone):
        super().__init__()
        self.app = app
        self.standalone = standalone
        self.overlay = OverlayWidget()
        # InfoOverlay removed
        self.mouse_tracker = None
        self.mask = None
        self.update_ui = self._update_ui

    def initialize(self, capture_size, update_interval, stability_threshold, tolerance, leave_threshold):
        self.mouse_tracker = MouseTracker(capture_size, update_interval, stability_threshold, tolerance, leave_threshold)
        self.mouse_tracker.update_signal.connect(self.update_ui)
        self.mask = MaskWidget() # Create mask
        self.mask.should_exit.connect(self.on_mask_exit) # Connect exit signal

    # Updated slot to match new signal
    @QtCore.pyqtSlot(list, str, str)
    def _update_ui(self, bounding_boxes, info_text, box_type):
        self.overlay.update_boxes(bounding_boxes, box_type)
        # info_overlay.update_info call removed
        
        # We still pass info_text to the mask (invisibly) so it can be saved on click
        info_list = [info_text] if info_text else []
        self.mask.update_regions(bounding_boxes, info_list)

    def start_tracking(self):
        self.mouse_tracker.timer.start()
        # CRITICAL: Ensure mask is absolutely on top and can receive events
        # The mask MUST be above everything to intercept clicks
        self.mask.show()
        self.mask.raise_()
        self.mask.activateWindow()
        self.mask.setFocus()
        # Force window to front
        self.mask.setWindowState(self.mask.windowState() | QtCore.Qt.WindowActive)
        # Process events to ensure mask is on top
        self.app.processEvents()
        # Double-check mask is visible and on top
        if not self.mask.isVisible():
            print("WARNING: Mask widget is not visible!")
        print(f"Mask widget visible: {self.mask.isVisible()}, geometry: {self.mask.geometry()}")
        # info_overlay.raise_() removed

    def on_mask_exit(self):
        # Called when MaskWidget is clicked
        print("LocatorManager: on_mask_exit called")
        self.cleanup()
        if self.standalone:
            print("LocatorManager: Standalone mode - quitting app")
            self.app.quit()
        else:
            print("LocatorManager: Non-standalone mode - emitting should_exit signal")
            self.should_exit.emit()
            print("LocatorManager: should_exit signal emitted")

    def cleanup(self):
        # Stop timer and hide all overlays
        if self.mouse_tracker:
            self.mouse_tracker.timer.stop()
        if self.overlay.current_box:
            self.overlay.current_box.destroy()
            self.overlay.current_box = None
        # info_overlay.hide() removed
        if self.mask:
            self.mask.hide()
            self.mask.close()

# --- Main Function To Call ---
def select_element():
    """
    Activates a full-screen mask to select a UI element.
    
    - Masks the screen.
    - Highlights hovered elements in a DARKER CYAN.
    - On click, deactivates and returns the clicked element's data.

    Returns:
        tuple: (clicked_event_log, clicked_bounds)
        
        - clicked_event_log (list): A list containing one dictionary 
                                    with the clicked element's data.
        - clicked_bounds (list): A list of bounds [left, right, top, bottom].
    """
    
    # --- IMPORTANT ---
    # Set this to your Tesseract-OCR executable path
    # !! This path MUST be correct for text detection to work !!
    TESSERACT_PATH = r"C:\Droidal\Cloud_Droidal\Cluster\Tesseract-OCR\tesseract.exe"
    # TESSERACT_PATH = r"D:\PACKAGES\Tessaract-OCR\tesseract.exe" # Alt path
    
    # --- UPDATED CONFIGURATION ---
    SCREEN_CAPTURE_SIZE = 500
    UPDATE_INTERVAL_MS = 50   # FASTER: Was 150. (20 updates/sec)
    STABILITY_FRAME_COUNT = 1 # FASTER: Was 2. (Instant highlight)
    COORDINATE_TOLERANCE = 15
    REGION_LEAVE_FRAMES = 1   # FASTER: Was 3. (Instant hide)

    # Setup
    pyautogui.FAILSAFE = False
    try:
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
        pytesseract.get_tesseract_version() 
    except Exception as e:
        print(f"Tesseract Error: {e}")
        print(f"Please ensure Tesseract is installed at: {TESSERACT_PATH}")
        print("Continuing without text detection...")

    # Get or create the PyQt Application instance
    app = QtWidgets.QApplication.instance()
    standalone = False
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
        standalone = True

    manager = LocatorManager(app, standalone)
    manager.initialize(SCREEN_CAPTURE_SIZE, UPDATE_INTERVAL_MS, STABILITY_FRAME_COUNT,
                       COORDINATE_TOLERANCE, REGION_LEAVE_FRAMES)
    manager.start_tracking()

    # Run the event loop to wait for the user's click
    if standalone:
        app.exec_()
    else:
        # When called from within another event loop (like a dialog),
        # nested QEventLoop.exec_() doesn't process events correctly.
        # Use a combination of processEvents and timer-based checking
        print("Coordinate picker: Waiting for user click (non-standalone mode)...")
        
        # Use a flag to track if we should exit
        should_exit = False
        
        def on_exit_signal():
            nonlocal should_exit
            should_exit = True
            print("Coordinate picker: Exit signal received")
        
        # Connect the exit signal
        manager.should_exit.connect(on_exit_signal, QtCore.Qt.QueuedConnection)
        
        # Poll for clicks with aggressive event processing
        # This ensures events are processed even when called from nested event loops
        max_iterations = 60000  # Maximum 60 seconds (60000 * 1ms)
        iteration = 0
        
        # Ensure mask is on top before starting polling
        if manager.mask:
            manager.mask.raise_()
            manager.mask.activateWindow()
            app.processEvents()
        
        # Use Windows API to detect mouse clicks as backup
        # This works even when Qt events aren't processed correctly in nested event loops
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            # GetAsyncKeyState checks if left mouse button is pressed (bit 0x8000)
            VK_LBUTTON = 0x01
            last_mouse_state = (user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000) != 0
        except Exception as e:
            print(f"Warning: Could not initialize Windows API for click detection: {e}")
            user32 = None
            last_mouse_state = False
        
        while iteration < max_iterations:
            # CRITICAL: Process ALL events including input events
            # Process events multiple times to ensure mouse events are handled
            for _ in range(3):
                app.processEvents(QtCore.QEventLoop.AllEvents)
            
            # Backup: Check mouse button state using Windows API
            # This detects clicks even if Qt events aren't processed in nested loops
            click_detected = False
            click_position = None
            if user32:
                try:
                    current_mouse_state = (user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000) != 0
                    # Detect mouse button press (transition from not pressed to pressed)
                    # This indicates a click started
                    if current_mouse_state and not last_mouse_state:
                        # Mouse button was just pressed - wait for release to confirm click
                        # We'll detect the release in the next iteration
                        pass
                    # Detect mouse button release (transition from pressed to not pressed)
                    # This confirms a complete click
                    elif not current_mouse_state and last_mouse_state:
                        # Mouse button was just released - this is a complete click
                        click_position = pyautogui.position()
                        print(f"Coordinate picker: Click detected via Windows API (button release) at {click_position}")
                        click_detected = True
                        # Try to send event to mask widget first
                        if manager.mask:
                            from PyQt5.QtCore import QPoint
                            from PyQt5.QtGui import QMouseEvent
                            global_pos = QtCore.QPoint(click_position[0], click_position[1])
                            local_pos = manager.mask.mapFromGlobal(global_pos)
                            # Send both press and release events
                            press_event = QMouseEvent(
                                QtCore.QEvent.MouseButtonPress,
                                local_pos,
                                global_pos,
                                QtCore.Qt.LeftButton,
                                QtCore.Qt.LeftButton,
                                QtCore.Qt.NoModifier
                            )
                            release_event = QMouseEvent(
                                QtCore.QEvent.MouseButtonRelease,
                                local_pos,
                                global_pos,
                                QtCore.Qt.LeftButton,
                                QtCore.Qt.LeftButton,
                                QtCore.Qt.NoModifier
                            )
                            # Post events to mask widget
                            QtWidgets.QApplication.postEvent(manager.mask, press_event)
                            QtWidgets.QApplication.postEvent(manager.mask, release_event)
                            # Process events to handle the posted events
                            for _ in range(10):
                                app.processEvents()
                    last_mouse_state = current_mouse_state
                except Exception as e:
                    print(f"Error checking mouse state: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Check if mask was clicked (primary check - Qt events)
            if manager.mask and manager.mask.clicked_log_entry:
                print("Coordinate picker: Click detected via mask widget, exiting...")
                should_exit = True
                break
            
            # If click was detected via Windows API but mask didn't process it
            if click_detected and click_position:
                # Wait a bit more for Qt to process
                for _ in range(10):
                    app.processEvents()
                # Check again
                if manager.mask and manager.mask.clicked_log_entry:
                    print("Coordinate picker: Click processed after Windows API detection, exiting...")
                    should_exit = True
                    break
                else:
                    # Fallback: Manually set the bounds using click position
                    print("Coordinate picker: Using Windows API click position as fallback")
                    x, y = click_position
                    if manager.mask:
                        import time
                        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                        # Try to get region info from current stable region if available
                        bounds = [x, x, y, y]
                        region_info = None
                        
                        if manager.mouse_tracker and manager.mouse_tracker.current_stable_region:
                            # Use the stable region's bounds
                            coords = manager.mouse_tracker.current_stable_region.stable_coords
                            bounds = [coords[0], coords[0] + coords[2], coords[1], coords[1] + coords[3]]
                            print(f"Coordinate picker: Using stable region bounds: {bounds}")
                            # Get region info as dict, not JSON string
                            try:
                                region_info_str = manager.mouse_tracker.current_stable_region.get_info_json()
                                region_info = json.loads(region_info_str)
                            except:
                                region_info = None
                        
                        if not region_info:
                            # Create generic region info
                            region_info = {
                                "type": "Generic",
                                "coordinates": {
                                    "top_left": {"x": bounds[0], "y": bounds[2]},
                                    "top_right": {"x": bounds[1], "y": bounds[2]},
                                    "bottom_left": {"x": bounds[0], "y": bounds[3]},
                                    "bottom_right": {"x": bounds[1], "y": bounds[3]}
                                },
                                "centroid": {"x": (bounds[0] + bounds[1]) // 2, "y": (bounds[2] + bounds[3]) // 2}
                            }
                        
                        log_entry = {
                            "timestamp": timestamp,
                            "event": "region_click" if manager.mouse_tracker and manager.mouse_tracker.current_stable_region else "generic_click",
                            "region_info": region_info
                        }
                        manager.mask.clicked_log_entry = log_entry
                        manager.mask.clicked_bounds = bounds
                        manager.mask.clicked_position = [x, y]  # Store exact click position
                        print(f"Coordinate picker: Manually set bounds: {bounds}")
                        print(f"Coordinate picker: Manually set click position: {[x, y]}")
                        # Trigger cleanup
                        manager.cleanup()
                        should_exit = True
                        break
            
            # Check if exit signal was received (backup check)
            if should_exit:
                print("Coordinate picker: Exit requested, exiting...")
                break
            
            # Small sleep to prevent 100% CPU usage
            # But keep it very short for responsive click detection
            QtCore.QThread.msleep(1)  # 1ms sleep for responsive detection
            iteration += 1
            
            # Debug output every 5 seconds
            if iteration % 5000 == 0:
                print(f"Coordinate picker: Still waiting for click... (iteration {iteration})")
                if manager.mask:
                    print(f"  Mask visible: {manager.mask.isVisible()}")
                    print(f"  Mask geometry: {manager.mask.geometry()}")
                # Force mask to front periodically
                if manager.mask:
                    manager.mask.raise_()
                    manager.mask.activateWindow()
        
        if iteration >= max_iterations:
            print("WARNING: Coordinate picker timed out after 60 seconds!")
        
        print("Coordinate picker: Exited polling loop")
        
        # Verify click was detected
        if manager.mask and manager.mask.clicked_log_entry:
            print(f"Coordinate picker: Confirmed click detected, bounds: {manager.mask.clicked_bounds}")
        else:
            print("WARNING: Coordinate picker exited but no click was detected!")

    # --- Retrieve and Return Data ---
    log_data = []
    bounds_data = []
    position_data = []

    if manager.mask and manager.mask.clicked_log_entry:
        log_data = [manager.mask.clicked_log_entry]  # Return as list
        bounds_data = manager.mask.clicked_bounds     # [left, right, top, bottom]
        position_data = manager.mask.clicked_position # [x, y] - exact click position
    
    # Return format: {
    #   'bounds': [left, right, top, bottom],
    #   'position': [x, y]
    # }
    # return {
    #     'bounds': bounds_data,
    #     'position': position_data
    # }
    return position_data

# # --- Example Usage ---
# if __name__ == "__main__":
#     print("Starting element selector...")
#     print("Move your mouse over an element and click it.")
    
#     clicked_bounds_list = select_element()
    
#     print(clicked_bounds_list)