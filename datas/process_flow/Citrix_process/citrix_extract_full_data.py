import sys
import json
import os
import re
import time
import cv2
import pytesseract
import numpy as np
from PIL import Image, ImageGrab
from datetime import datetime
from PyQt5 import QtCore, QtGui, QtWidgets


# -------- CONFIGURATION (tweak these to tune behavior) --------
IMAGE_PATH = r"Citrix_process\screenshot.png"              # input screenshot
LOG_FILE = r"Citrix_process\pixel_click_log.json"
ANNOTATED_OUT_TEMPLATE = r"Citrix_process\annotated.png"


# OCR / detection thresholds
WORD_CONF_THRESHOLD = 40.0                 # include word boxes above this confidence as candidates
MERGE_MARGIN_PX = 8                        # expand each word box by this px before merging
MERGE_IOU_THRESH = 0.15                    # IoU threshold for merging word boxes into block
MIN_ALNUM_CHARS = 2                        # minimum alphanumeric chars in a text block
BLOCK_CONF_ACCEPT = 60.0                   # accept merged block if max OCR conf >= this
BLOCK_HEIGHT_MIN_RATIO = 0.006             # min height relative to image height
BLOCK_HEIGHT_MAX_RATIO = 0.40              # max height relative to image height
ICON_MIN_AREA = 120                        # min area to consider as icon
ICON_FILL_RATIO_MIN = 0.06                 # icon fill ratio must be >= this
ICON_SOLIDITY_MIN = 0.25                   # contour solidity threshold
ICON_MAX_GLOBAL_RATIO = 0.60               # skip super-large contours


# ---- Tesseract Path (adjust to your machine) ----
# TESSERACT_PATH = r"C:Program Files\\Tesseract-OCR\\tesseract.exe"
TESSERACT_PATH=r"C:\Droidal\Cloud_Droidal\Cluster\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH



# -------------------- Helpers --------------------
def reset_log_file():
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("Error resetting log file:", e)


def append_log_entry(log_entry):
    try:
        logs = []
        if os.path.exists(LOG_FILE):
            try:
                with open(LOG_FILE, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            except Exception:
                logs = []
        logs.append(log_entry)
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print("Error writing JSON log:", e)
        return False


# -------------------- Screenshot capture --------------------
def capture_screenshot(path=IMAGE_PATH, delay=1):
    """Wait delay seconds, then take screenshot and save to path"""
    print(f"Waiting {delay} seconds before taking screenshot...")
    time.sleep(delay)
    img = ImageGrab.grab()
    img.save(path)
    print(f"Screenshot saved to {path}")
    return path


def clean_text(s):
    return re.sub(r"\s+", " ", re.sub(r"[^\x20-\x7E]+", "", (s or ""))).strip()


def iou(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ax2, ay2 = ax + aw, ay + ah
    bx2, by2 = bx + bw, by + bh
    inter_x1, inter_y1 = max(ax, bx), max(ay, by)
    inter_x2, inter_y2 = min(ax2, bx2), min(ay2, by2)
    inter_w = max(0, inter_x2 - inter_x1)
    inter_h = max(0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h
    union = aw * ah + bw * bh - inter_area + 1e-9
    return inter_area / union


def merge_boxes(boxes, margin=MERGE_MARGIN_PX, iou_thresh=MERGE_IOU_THRESH):
    """Expand boxes with margin, then merge any boxes overlapping above iou_thresh.
       boxes = [(x,y,w,h), ...] -> returns merged list of (x,y,w,h).
    """
    if not boxes:
        return []
    # expand
    ex = []
    for (x, y, w, h) in boxes:
        ex.append((max(0, x - margin), max(0, y - margin),
                   w + 2 * margin, h + 2 * margin))
    # greedy merge
    used = [False] * len(ex)
    merged = []
    for i in range(len(ex)):
        if used[i]:
            continue
        x1, y1, w1, h1 = ex[i]
        rx1, ry1, rx2, ry2 = x1, y1, x1 + w1, y1 + h1
        used[i] = True
        changed = True
        while changed:
            changed = False
            for j in range(len(ex)):
                if used[j]:
                    continue
                bx, by, bw, bh = ex[j]
                if iou((rx1, ry1, rx2 - rx1, ry2 - ry1), (bx, by, bw, bh)) >= iou_thresh:
                    used[j] = True
                    rx1 = min(rx1, bx)
                    ry1 = min(ry1, by)
                    rx2 = max(rx2, bx + bw)
                    ry2 = max(ry2, by + bh)
                    changed = True
        merged.append((int(rx1), int(ry1), int(rx2 - rx1), int(ry2 - ry1)))
    return merged


def compute_fill_ratio(roi_gray):
    """Return proportion of dark pixels (0..1) using Otsu threshold."""
    try:
        _, th = cv2.threshold(roi_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        black_count = np.count_nonzero(th == 0)
        return black_count / max(1, th.size)
    except Exception:
        return 0.0


# -------------------- Detector class --------------------
class FullScreenImageWidget(QtWidgets.QLabel):
    def __init__(self,image_path):
        super().__init__()
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setMouseTracking(True)
        self.image_path = image_path

        self.display_pixmap = QtGui.QPixmap(image_path)
        if self.display_pixmap.isNull():
            raise FileNotFoundError(f"Could not load: {image_path}")

        try:
            pil_img = Image.open(image_path)
            self.original_width, self.original_height = pil_img.size
        except Exception:
            self.original_width = self.display_pixmap.width()
            self.original_height = self.display_pixmap.height()

        self.original_pixmap = self.display_pixmap.copy()
        self.showFullScreen()
        self.fit_image_to_screen()

        self.overlays = []
        self.all_log_entries = []  # Store all entries before writing to maintain order
        QtCore.QTimer.singleShot(600, self.start_auto_scan)

    def fit_image_to_screen(self):
        screen_geom = QtWidgets.QApplication.primaryScreen().geometry()
        scaled_pixmap = self.original_pixmap.scaled(
            screen_geom.size(),
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation
        )
        self.setPixmap(scaled_pixmap)
        self.setAlignment(QtCore.Qt.AlignCenter)

    # OCR on ROI returning combined text + max confidence
    def ocr_block(self, roi_gray):
        try:
            data = pytesseract.image_to_data(
                roi_gray,
                output_type=pytesseract.Output.DICT,
                config="--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
            )
        except Exception:
            return "", 0.0
        texts = []
        confs = []
        for i, t in enumerate(data.get("text", [])):
            txt = (t or "").strip()
            try:
                conf_val = float(data.get("conf", [])[i])
            except Exception:
                conf_val = -1.0
            if txt:
                texts.append(txt)
            if conf_val >= 0:
                confs.append(conf_val)
        return " ".join(texts).strip(), float(max(confs) if confs else 0.0)

    def detect_text_blocks(self):
        pil = Image.open(self.image_path).convert("RGB")
        img_bgr = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

        # Improved preprocessing for OCR
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 31, 2)

        try:
            data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
        except Exception:
            data = {"text": [], "conf": [], "left": [], "top": [], "width": [], "height": []}

        cand_words = []
        for i, txt in enumerate(data.get("text", [])):
            word = (txt or "").strip()
            conf_raw = data.get("conf", [])[i] if i < len(data.get("conf", [])) else "-1"
            try:
                conf_val = float(conf_raw)
            except Exception:
                conf_val = -1.0
            if not word:
                continue
            if conf_val >= WORD_CONF_THRESHOLD:
                x = int(data["left"][i])
                y = int(data["top"][i])
                w = int(data["width"][i])
                h = int(data["height"][i])
                if w < 4 or h < 4:
                    continue
                cand_words.append((x, y, w, h))

        if not cand_words:
            gray_blur = cv2.GaussianBlur(gray, (3, 3), 0)
            try:
                mser = cv2.MSER_create(5, 30, 20000)
                regions, _ = mser.detectRegions(gray_blur)
                for p in regions:
                    x, y, w, h = cv2.boundingRect(p.reshape(-1, 1, 2))
                    if w < 6 or h < 6 or w > self.original_width * 0.95:
                        continue
                    cand_words.append((x, y, w, h))
            except Exception:
                pass

        merged_blocks = merge_boxes(cand_words, margin=MERGE_MARGIN_PX, iou_thresh=MERGE_IOU_THRESH)

        accepted_blocks = []
        for (x, y, w, h) in merged_blocks:
            if h < max(8, int(BLOCK_HEIGHT_MIN_RATIO * self.original_height)) or h > int(BLOCK_HEIGHT_MAX_RATIO * self.original_height):
                continue
            roi_gray = gray[y:y + h, x:x + w]
            if roi_gray.size == 0:
                continue
            fill_ratio = compute_fill_ratio(roi_gray)
            text, conf = self.ocr_block(roi_gray)
            text = clean_text(text)
            if conf >= BLOCK_CONF_ACCEPT and len(re.findall(r"[A-Za-z0-9]", text)) >= MIN_ALNUM_CHARS:
                if fill_ratio > 0.30 and (w * h) < (self.original_width * self.original_height * 0.25):
                    continue
                accepted_blocks.append({
                    "type": "Text",
                    "text": text,
                    "coordinates": {"x": int(x), "y": int(y), "width": int(w), "height": int(h)},
                    "centroid": {"x": int(x + w // 2), "y": int(y + h // 2)},
                    "score": float(conf),
                    "fill_ratio": float(fill_ratio)
                })

        # -------- Soft-NMS instead of hard suppression --------
        if accepted_blocks:
            boxes = [(r["coordinates"]["x"], r["coordinates"]["y"],
                      r["coordinates"]["width"], r["coordinates"]["height"])
                     for r in accepted_blocks]
            scores = [r["score"] for r in accepted_blocks]

            sigma = 0.5
            Nt = 0.35
            thresh = 0.001
            keep = []
            N = len(boxes)
            suppressed = [False] * N

            for _ in range(N):
                max_idx = -1
                max_score = -1
                for i in range(N):
                    if not suppressed[i] and scores[i] > max_score:
                        max_score = scores[i]
                        max_idx = i
                if max_idx == -1:
                    break

                keep.append(max_idx)
                suppressed[max_idx] = True

                for j in range(N):
                    if suppressed[j]:
                        continue
                    iou_val = iou(boxes[max_idx], boxes[j])
                    if iou_val > Nt:
                        scores[j] *= np.exp(-(iou_val ** 2) / sigma)
                    if scores[j] < thresh:
                        suppressed[j] = True

            accepted_blocks = [accepted_blocks[i] for i in keep]

        return accepted_blocks


    def detect_icons(self, text_blocks):
        """Detect icons via contours and heuristics, skipping areas overlapping text_blocks."""
        pil = Image.open(self.image_path).convert("RGB")
        img_bgr = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

        gray = cv2.equalizeHist(gray)
        gray_blur = cv2.GaussianBlur(gray, (3, 3), 0)

        # Morphological closing to close gaps in edges for icons
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        gray_closed = cv2.morphologyEx(gray_blur, cv2.MORPH_CLOSE, kernel, iterations=1)

        edges1 = cv2.Canny(gray_closed, 50, 120)
        edges2 = cv2.Canny(gray_closed, 100, 200)
        edges = cv2.bitwise_or(edges1, edges2)

        kernel = np.ones((2, 2), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        tboxes = []
        for r in text_blocks:
            c = r["coordinates"]
            tboxes.append((c["x"], c["y"], c["width"], c["height"]))

        icons = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w * h < ICON_MIN_AREA or w < 6 or h < 6:
                continue
            if w > self.original_width * ICON_MAX_GLOBAL_RATIO and h > self.original_height * ICON_MAX_GLOBAL_RATIO:
                continue
            if any(iou((x, y, w, h), tb) > 0.25 for tb in tboxes):
                continue

            area = cv2.contourArea(cnt)
            bbox_area = max(1.0, w * h)
            solidity = area / bbox_area
            roi_gray = gray[y:y + h, x:x + w]
            if roi_gray.size == 0:
                continue
            fill_ratio = compute_fill_ratio(roi_gray)

            if solidity >= (ICON_SOLIDITY_MIN * 0.85) and fill_ratio >= (ICON_FILL_RATIO_MIN * 0.65):
                icons.append({
                    "type": "Icon",
                    "text": None,
                    "coordinates": {"x": int(x), "y": int(y), "width": int(w), "height": int(h)},
                    "centroid": {"x": int(x + w // 2), "y": int(y + h // 2)},
                    "solidity": float(solidity),
                    "fill_ratio": float(fill_ratio)
                })

        if icons:
            merged = []
            used = [False] * len(icons)
            for i in range(len(icons)):
                if used[i]:
                    continue
                xi, yi, wi, hi = icons[i]["coordinates"].values()
                rx1, ry1, rx2, ry2 = xi, yi, xi + wi, yi + hi
                used[i] = True
                for j in range(len(icons)):
                    if used[j]:
                        continue
                    xj, yj, wj, hj = icons[j]["coordinates"].values()
                    if iou((rx1, ry1, rx2 - rx1, ry2 - ry1), (xj, yj, wj, hj)) > 0.2:
                        used[j] = True
                        rx1 = min(rx1, xj)
                        ry1 = min(ry1, yj)
                        rx2 = max(rx2, xj + wj)
                        ry2 = max(ry2, yj + hj)
                merged.append({
                    "type": "Icon",
                    "text": None,
                    "coordinates": {"x": int(rx1), "y": int(ry1), "width": int(rx2 - rx1), "height": int(ry2 - ry1)},
                    "centroid": {"x": int((rx1 + rx2) // 2), "y": int((ry1 + ry2) // 2)}
                })
            icons = merged

        return icons


    def save_annotated_image(self, text_blocks, icon_blocks):
        try:
            img_bgr = cv2.imread(self.image_path)
            if img_bgr is None:
                print("Failed to load image for annotated output.")
                return None
            for r in text_blocks:
                c = r["coordinates"]
                x, y, w, h = c["x"], c["y"], c["width"], c["height"]
                cv2.rectangle(img_bgr, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.putText(img_bgr, "Text", (x, max(12, y - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1, cv2.LINE_AA)
            for r in icon_blocks:
                c = r["coordinates"]
                x, y, w, h = c["x"], c["y"], c["width"], c["height"]
                cv2.rectangle(img_bgr, (x, y), (x + w, y + h), (255, 0, 0), 2)
                cv2.putText(img_bgr, "Icon", (x, max(12, y - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 0, 0), 1, cv2.LINE_AA)

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_name = ANNOTATED_OUT_TEMPLATE
            cv2.imwrite(out_name, img_bgr)
            return out_name
        except Exception as e:
            print("Error saving annotated image:", e)
            return None


    def start_auto_scan(self):
        text_blocks = self.detect_text_blocks()
        icon_blocks = self.detect_icons(text_blocks)
        annotated_file = self.save_annotated_image(text_blocks, icon_blocks)

        combined = text_blocks + icon_blocks
        combined.sort(key=lambda r: r["centroid"]["y"] * self.original_width + r["centroid"]["x"])

        reset_log_file()
        for r in combined:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "element_type": r.get("type", ""),
                "text": r.get("text"),
                "coordinates": r.get("coordinates"),
                "centroid": r.get("centroid"),
                "confidence": float(r.get("score", 0)),
                "fill_ratio": float(r.get("fill_ratio", 0))
            }
            self.all_log_entries.append(log_entry)

        for log_entry in self.all_log_entries:
            append_log_entry(log_entry)

        print("Auto-scan complete. Results written to", LOG_FILE)
        if annotated_file:
            print("Annotated image saved as", annotated_file)
        QtCore.QTimer.singleShot(500, self.close_widget)
    
    def close_widget(self):
        """Properly close the widget and emit destroyed signal"""
        self.close()
        self.deleteLater()


# # -------------------- MAIN --------------------
def page_data_extraction():
    try:
        capture_screenshot(IMAGE_PATH, delay=3)
        
        # Check if QApplication already exists, if not create one
        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication(sys.argv)
            app_created = True
        else:
            app_created = False
        
        widget = FullScreenImageWidget(IMAGE_PATH)
        widget.show()
        
        # Only call exec_() if we created the application
        if app_created:
            app.exec_()
        else:
            # Use a local event loop for existing application
            from PyQt5.QtCore import QEventLoop
            loop = QEventLoop()
            widget.destroyed.connect(loop.quit)
            loop.exec_()
        
        image_path=ANNOTATED_OUT_TEMPLATE
        json_path=LOG_FILE
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)
                # os.remove(json_path)
        return json_data
    except Exception as e:
        print(f"Error in page_data_extraction: {e}")
        return [947,470,1294,768]

# json_data,image_path=page_data_extraction()
# print(json_data)