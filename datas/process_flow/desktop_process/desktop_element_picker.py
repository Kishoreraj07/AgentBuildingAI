import time
import pywinauto
from pywinauto import Desktop
import win32api
import win32con
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer, QRect, QEventLoop, QThread, QObject, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPainter, QPen, QColor
import json
import win32process
from PIL import ImageGrab
import os
from datetime import datetime
import sys
import threading
import traceback


class HoverHighlightWorker(QObject):
    """Worker thread for hover highlighting (non-blocking)"""
    highlight_ready = pyqtSignal(object)  # Emits (element, rect, process_id)
    element_lost = pyqtSignal()  # When element is no longer valid
    error = pyqtSignal(str)
    finished = pyqtSignal()  # Emitted when worker finishes
    
    def __init__(self, target_pid=None):
        super().__init__()
        self.target_pid = target_pid
        self.is_running = False
        self.stop_requested = False
        self.last_element_hash = None
        self.is_processing_click = False
        self.click_successful = False
    
    def set_processing_state(self, is_processing):
        """Set the processing state from main thread"""
        self.is_processing_click = is_processing
    
    def set_click_successful(self, success):
        """Set the click successful state from main thread"""
        self.click_successful = success
    
    @pyqtSlot()
    def find_element_at_cursor(self):
        """Find and emit element at cursor position (runs in worker thread)"""
        try:
            self.is_running = True
            self.stop_requested = False
            
            while self.is_running and not self.stop_requested:
                try:
                    # Skip highlighting if processing click or selection complete
                    if self.is_processing_click or self.click_successful:
                        self.last_element_hash = None
                        self.element_lost.emit()
                        time.sleep(0.03)
                        continue
                    
                    pos = win32api.GetCursorPos()
                    element = Desktop(backend="uia").from_point(*pos)
                    
                    # Check process match
                    target_app_match = (
                        element and
                        (not self.target_pid or element.element_info.process_id == self.target_pid)
                    )
                    
                    if element and target_app_match:
                        # Find most specific element
                        specific_element = self._find_most_specific(element, pos)
                        if specific_element:
                            element = specific_element
                        
                        element_hash = (
                            element.handle,
                            element.element_info.control_id,
                            element.element_info.name,
                            element.element_info.class_name,
                            str(element.rectangle())
                        )
                        
                        if self.last_element_hash != element_hash:
                            self.last_element_hash = element_hash
                            try:
                                rect = element.rectangle()
                                self.highlight_ready.emit((element, rect, element.element_info.process_id))
                            except:
                                self.element_lost.emit()
                    else:
                        if self.last_element_hash is not None:
                            self.last_element_hash = None
                            self.element_lost.emit()
                    
                    time.sleep(0.03)  # 30ms interval
                except Exception as e:
                    print(f"Error in hover worker: {e}")
                    time.sleep(0.05)
            
            self.is_running = False
        except Exception as e:
            print(f"Error in find_element_at_cursor: {e}")
            self.error.emit(str(e))
    
    def _find_most_specific(self, element, pos):
        """Find the most specific/smallest element at position"""
        try:
            children = element.children()
            for child in children:
                try:
                    child_rect = child.rectangle()
                    if (child_rect.left <= pos[0] <= child_rect.right and
                        child_rect.top <= pos[1] <= child_rect.bottom):
                        more_specific = self._find_most_specific(child, pos)
                        if more_specific:
                            return more_specific
                        return child
                except:
                    continue
            return element
        except:
            return element
    
    @pyqtSlot()
    def stop_finding(self):
        """Stop the worker"""
        self.stop_requested = True
        time.sleep(0.1)
        self.is_running = False
        self.finished.emit()


class ClickExtractWorker(QObject):
    """Worker thread for click extraction (non-blocking)"""
    extraction_complete = pyqtSignal(dict)  # Emits result dict
    error = pyqtSignal(str)
    finished = pyqtSignal()  # Emitted when extraction is complete
    
    def __init__(self, target_pid=None, proj_fol=None, task_fol=None, var_name=None):
        super().__init__()
        self.target_pid = target_pid
        self.proj_fol = proj_fol
        self.task_fol = task_fol
        self.var_name = var_name
        self.pos = None
    
    @pyqtSlot(tuple)
    def extract_at_position(self, pos):
        """Extract element info at given position (runs in worker thread)"""
        try:
            self.pos = pos
            element = Desktop(backend="uia").from_point(*pos)
            
            target_app_match = (
                element and
                (not self.target_pid or element.element_info.process_id == self.target_pid)
            )
            
            if element and target_app_match:
                specific_element = self._find_most_specific(element, pos)
                if specific_element:
                    element = specific_element
                
                # Extract all information
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                current_element = self._get_element_basic_info(element)
                ancestors = self._get_ancestors_info(element)
                siblings = self._get_siblings_info(element)
                children = self._get_children_info(element, max_depth=5)
                screenshot_path = self._capture_element_screenshot(element)
                
                result = {
                    "element": element,
                    "rect": element.rectangle(),
                    "current_element": current_element,
                    "ancestors": ancestors,
                    "siblings": siblings,
                    "children": children,
                    "screenshot_path": screenshot_path,
                    "timestamp": timestamp
                }
                
                self.extraction_complete.emit(result)
            else:
                self.error.emit("No valid element found at click position")
        except Exception as e:
            print(f"Error in click extraction: {e}")
            traceback.print_exc()
            self.error.emit(str(e))
        finally:
            self.finished.emit()
    
    def _find_most_specific(self, element, pos):
        """Find most specific element"""
        try:
            children = element.children()
            for child in children:
                try:
                    child_rect = child.rectangle()
                    if (child_rect.left <= pos[0] <= child_rect.right and
                        child_rect.top <= pos[1] <= child_rect.bottom):
                        more_specific = self._find_most_specific(child, pos)
                        if more_specific:
                            return more_specific
                        return child
                except:
                    continue
            return element
        except:
            return element
    
    def _get_element_basic_info(self, element):
        """Extract basic info from element"""
        try:
            info = element.element_info
            rect = None
            try:
                rect = element.rectangle()
            except:
                pass
            
            value = None
            try:
                value = element.get_value()
            except:
                pass
            if not value:
                try:
                    value = element.window_text()
                except:
                    pass
            if not value:
                try:
                    value = str(getattr(info, "name", ""))
                except:
                    pass

            basic_info = {
                "name": str(getattr(info, "name", "")),
                "control_type": str(getattr(info, "control_type", "")),
                "class_name": str(getattr(info, "class_name", "")),
                "auto_id": str(getattr(info, "automation_id", "")),
                "value": str(value) if value else "",
                "handle": str(element.handle) if hasattr(element, 'handle') else "",
                "process_id": str(getattr(info, "process_id", ""))
            }

            if rect:
                basic_info["rectangle"] = {
                    "left": rect.left,
                    "top": rect.top,
                    "right": rect.right,
                    "bottom": rect.bottom,
                    "width": rect.width(),
                    "height": rect.height()
                }

            return basic_info
        except Exception as e:
            return {"error": str(e)}
    
    def _get_siblings_info(self, element):
        """Get siblings info"""
        siblings_info = {
            "previous_sibling": None,
            "next_sibling": None
        }
        
        try:
            parent = element.parent()
            if parent:
                children = parent.children()
                current_index = -1
                
                for i, child in enumerate(children):
                    try:
                        if child.handle == element.handle:
                            current_index = i
                            break
                    except:
                        continue
                
                if current_index > 0:
                    try:
                        prev_sibling = children[current_index - 1]
                        siblings_info["previous_sibling"] = self._get_element_basic_info(prev_sibling)
                    except:
                        pass
                
                if current_index >= 0 and current_index < len(children) - 1:
                    try:
                        next_sibling = children[current_index + 1]
                        siblings_info["next_sibling"] = self._get_element_basic_info(next_sibling)
                    except:
                        pass
        except:
            pass
        
        return siblings_info
    
    def _get_children_info(self, element, max_depth=5, current_depth=0):
        """Get children info recursively"""
        children_info = []
        
        if current_depth >= max_depth:
            return children_info
        
        try:
            children = element.children()
            for child in children:
                try:
                    child_info = self._get_element_basic_info(child)
                    
                    if current_depth + 1 < max_depth:
                        child_info["children"] = self._get_children_info(child, max_depth, current_depth + 1)
                    
                    children_info.append(child_info)
                except Exception as e:
                    children_info.append({"error": str(e)})
        except:
            pass
        
        return children_info
    
    def _get_ancestors_info(self, element, max_levels=10):
        """Get ancestors info"""
        ancestors = []
        
        try:
            ancestor = element.parent()
            level = 0
            
            while ancestor and level < max_levels:
                try:
                    ancestor_info = self._get_element_basic_info(ancestor)
                    ancestors.append(ancestor_info)
                    ancestor = ancestor.parent()
                    level += 1
                except:
                    break
        except:
            pass
        
        return ancestors[::-1]
    
    def _capture_element_screenshot(self, element):
        """Capture screenshot of element"""
        try:
            rect = element.rectangle()
            
            padding = 5
            bbox = (
                rect.left - padding,
                rect.top - padding,
                rect.right + padding,
                rect.bottom + padding
            )
            
            screenshot = ImageGrab.grab(bbox)
            if self.proj_fol and self.task_fol and self.var_name:
                save_dir = os.path.join(self.proj_fol, self.task_fol, "desktop", "images")
                os.makedirs(save_dir, exist_ok=True)
                image_path = os.path.join(save_dir, f"{self.var_name}.png")
            else:
                image_path = "element_screenshot.png"

            screenshot.save(image_path)
            return {"screenshot_path": image_path}
            
        except Exception as e:
            print(f"Screenshot failed: {e}")
            return None


class OverlayWidget(QWidget):
    """Transparent overlay widget for drawing rectangles"""
    def __init__(self, color="red", width=5):
        super().__init__()
        self.color = QColor(color)
        self.width = width
        self.rect = None
        self.is_painting = False
        self.pending_rect = None
        
        # Make window transparent and frameless
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.hide()
    
    def set_rectangle(self, left, top, width, height):
        """Set the rectangle to draw (thread-safe)"""
        # Store pending update while painting
        if self.is_painting:
            self.pending_rect = (left, top, width, height)
            return
        
        self.setGeometry(left, top, width, height)
        self.rect = QRect(0, 0, width, height)
        self.update()
    
    def paintEvent(self, event):
        """Draw the rectangle"""
        try:
            self.is_painting = True
            if self.rect:
                painter = QPainter(self)
                painter.setRenderHint(QPainter.Antialiasing)
                pen = QPen(self.color, self.width)
                painter.setPen(pen)
                painter.drawRect(self.rect.adjusted(
                    self.width//2, 
                    self.width//2, 
                    -self.width//2, 
                    -self.width//2
                ))
        finally:
            self.is_painting = False
            # Apply pending update if any
            if self.pending_rect:
                rect_data = self.pending_rect
                self.pending_rect = None
                self.set_rectangle(*rect_data)


class ClickOverlayWidget(QWidget):
    """Overlay for clicked element with double border"""
    def __init__(self):
        super().__init__()
        self.rect_width = 0
        self.rect_height = 0
        self.is_painting = False
        self.pending_rect = None
        
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.hide()
    
    def set_rectangle(self, left, top, width, height):
        """Set the rectangle to draw (thread-safe)"""
        # Store pending update while painting
        if self.is_painting:
            self.pending_rect = (left, top, width, height)
            return
        
        self.setGeometry(left, top, width, height)
        self.rect_width = width
        self.rect_height = height
        self.update()
    
    def paintEvent(self, event):
        """Draw double border (red outer, lime inner)"""
        try:
            self.is_painting = True
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Outer red border
            pen_red = QPen(QColor("red"), 6)
            painter.setPen(pen_red)
            painter.drawRect(1, 1, self.rect_width-2, self.rect_height-2)
            
            # Inner lime border
            pen_lime = QPen(QColor("lime"), 2)
            painter.setPen(pen_lime)
            painter.drawRect(2, 2, self.rect_width-4, self.rect_height-4)
        finally:
            self.is_painting = False
            # Apply pending update if any
            if self.pending_rect:
                rect_data = self.pending_rect
                self.pending_rect = None
                self.set_rectangle(*rect_data)


class ElementSelector:
    def __init__(self, app, target_window_title=None, proj_fol=None, task_fol=None, var_name=None, auto_quit=False):
        self.app = app
        self.target_window_title = target_window_title
        self.target_handle = None
        self.target_pid = None
        self.click_successful = False
        self.is_processing_click = False
        self.picked_element = None
        self.last_element_hash = None
        self.last_rect = None
        self.overlay_visible = False
        self.last_hovered_element_info = None
        self.element_info_data = None
        self.child_info_data = None
        self.screenshot_path = None
        self.proj_fol = proj_fol
        self.task_fol = task_fol
        self.var_name = var_name
        self.auto_quit = auto_quit
        self._paint_lock = threading.Lock()  # Lock for paint operations

        if target_window_title:
            self.target_handle, self.target_pid = self.find_window_by_title(target_window_title)

        # Create overlay widgets on main thread
        self.hover_overlay = None
        self.click_overlay = None
        QTimer.singleShot(0, self._create_overlay_widgets)

        # Initialize worker threads for element detection
        self.hover_worker = None
        self.hover_thread = None
        self.click_worker = None
        self.click_thread = None
        self._setup_hover_worker()

        # Setup timer for mouse tracking (Ctrl+Click detection)
        self.timer = QTimer()
        self.timer.timeout.connect(self.mouse_event_loop)
        self.timer.start(30)  # 30ms interval for Ctrl+Click detection

        if self.target_window_title:
            print(f"Targeting Window: \"{self.target_window_title}\"")
        else:
            print("Targeting: Any application")
        print("Waiting for Ctrl+Click...")
    
    def _create_overlay_widgets(self):
        """Create overlay widgets on main thread"""
        try:
            self.hover_overlay = OverlayWidget(color="red", width=5)
            self.click_overlay = ClickOverlayWidget()
        except Exception as e:
            print(f"Error creating overlay widgets: {e}")
            traceback.print_exc()

    def _setup_hover_worker(self):
        """Setup hover detection worker thread"""
        try:
            self.hover_thread = QThread()
            self.hover_worker = HoverHighlightWorker(target_pid=self.target_pid)
            self.hover_worker.moveToThread(self.hover_thread)
            
            # Connect signals
            self.hover_thread.started.connect(self.hover_worker.find_element_at_cursor)
            self.hover_worker.highlight_ready.connect(self._on_hover_highlight_ready)
            self.hover_worker.element_lost.connect(self._on_element_lost)
            self.hover_worker.error.connect(self._on_hover_error)
            self.hover_worker.finished.connect(self.hover_thread.quit)
            
            # Start thread
            self.hover_thread.start()
            print("Hover detection thread started")
        except Exception as e:
            print(f"Error setting up hover worker: {e}")
            traceback.print_exc()
    
    def _on_hover_highlight_ready(self, data):
        """Handle hover highlight signal from worker thread"""
        try:
            if self.hover_overlay is None:
                return
            
            element, rect, process_id = data
            
            # Skip if clicking or selection complete
            if self.is_processing_click or self.click_successful:
                return
            
            # Draw red outline for hover on main thread (UI operations must be on main thread)
            if self.draw_rectangle(self.hover_overlay, rect, color="red", width=5):
                # Schedule show on main thread with lock
                QTimer.singleShot(0, lambda: self._safe_show_overlay(self.hover_overlay))
                self.overlay_visible = True
                self.last_hovered_element_info = {
                    "element": element,
                    "rect": rect,
                    "process_id": process_id
                }
        except Exception as e:
            print(f"Error in hover highlight handler: {e}")
            traceback.print_exc()
    
    def _safe_show_overlay(self, overlay):
        """Show overlay safely with lock"""
        try:
            with self._paint_lock:
                if overlay and overlay.isVisible() is False:
                    overlay.show()
        except:
            pass
    
    def _on_element_lost(self):
        """Handle element lost signal from worker thread"""
        try:
            if self.hover_overlay is None:
                return
            
            self.overlay_visible = False
            self.last_hovered_element_info = None
            # Schedule hide on main thread with lock
            QTimer.singleShot(0, lambda: self._safe_hide_overlay(self.hover_overlay))
        except Exception as e:
            print(f"Error in element lost handler: {e}")
    
    def _safe_hide_overlay(self, overlay):
        """Hide overlay safely with lock"""
        try:
            with self._paint_lock:
                if overlay and overlay.isVisible():
                    overlay.hide()
        except:
            pass
    
    def _on_hover_error(self, error_msg):
        """Handle error signal from hover worker"""
        print(f"Hover worker error: {error_msg}")
    
    def _setup_click_worker(self):
        """Setup click extraction worker thread"""
        try:
            self.click_thread = QThread()
            self.click_worker = ClickExtractWorker(
                target_pid=self.target_pid,
                proj_fol=self.proj_fol,
                task_fol=self.task_fol,
                var_name=self.var_name
            )
            self.click_worker.moveToThread(self.click_thread)
            
            # Connect signals
            self.click_worker.extraction_complete.connect(self._on_click_extraction_complete)
            self.click_worker.error.connect(self._on_click_error)
            self.click_worker.finished.connect(self.click_thread.quit)
            self.click_thread.finished.connect(lambda: print("Click worker thread finished"))
            
            return True
        except Exception as e:
            print(f"Error setting up click worker: {e}")
            traceback.print_exc()
            return False
    
    def _on_click_extraction_complete(self, result):
        """Handle extraction complete signal from worker thread"""
        try:
            element = result["element"]
            rect = result["rect"]
            current_element = result["current_element"]
            ancestors = result["ancestors"]
            siblings = result["siblings"]
            children = result["children"]
            screenshot_path = result["screenshot_path"]
            timestamp = result["timestamp"]
            
            # Draw click outline (RED outer + LIME inner)
            self._draw_click_outline(rect)
            
            # Store extracted data with JSON serialization (for compatibility with main_desktop_element_picker)
            element_info_data = {
                "current_element": current_element,
                "ancestors": ancestors,
                "siblings": siblings,
                "timestamp": timestamp
            }
            child_info_data = {
                "children": children,
                "timestamp": timestamp
            }
            
            # JSON serialize for return
            self.element_info_data = json.dumps(element_info_data, indent=2, ensure_ascii=False)
            self.child_info_data = json.dumps(child_info_data, indent=2, ensure_ascii=False)
            self.screenshot_path = screenshot_path
            self.picked_element = element
            
            # Export JSON files if directories provided
            if self.proj_fol and self.task_fol and self.var_name:
                self._export_element_json(current_element, ancestors, siblings, children)
            
            self.click_successful = True
            
            # Notify hover worker that click is complete
            if self.hover_worker:
                self.hover_worker.set_click_successful(True)
            
            print("Element extraction complete")
            
            # Auto-quit if requested
            if self.auto_quit:
                self.cleanup_and_quit()
        except Exception as e:
            print(f"Error handling click extraction: {e}")
            traceback.print_exc()
        finally:
            self.is_processing_click = False
    
    def _on_click_error(self, error_msg):
        """Handle error signal from click worker"""
        print(f"Click worker error: {error_msg}")
        self.is_processing_click = False
    
    def _draw_click_outline(self, rect):
        """Draw double border outline for click"""
        try:
            # Schedule click overlay update on main thread
            QTimer.singleShot(0, lambda: self._update_click_overlay(rect))
        except Exception as e:
            print(f"Error drawing click outline: {e}")
    
    def _update_click_overlay(self, rect):
        """Update click overlay (runs on main thread)"""
        try:
            if self.click_overlay is None:
                return
            
            with self._paint_lock:
                # RED outer border (width 5)
                self.click_overlay.set_rectangle(rect.left - 5, rect.top - 5, rect.width() + 10, rect.height() + 10)
                self.click_overlay.outer_color = "red"
                
                # LIME inner border (width 3) - handled by ClickOverlayWidget
                self.click_overlay.inner_color = "lime"
                self.click_overlay.show()
        except Exception as e:
            print(f"Error updating click overlay: {e}")

    def find_window_by_title(self, title):
        """Finds a window by its title and returns its handle and process ID."""
        try:
            windows = pywinauto.findwindows.find_windows(title_re=f".*{title}.*", backend="uia")
            if windows:
                handle = windows[0]
                app = pywinauto.Application(backend="uia").connect(handle=handle)
                window = app.window(handle=handle)
                window.set_focus()
                _, pid = win32process.GetWindowThreadProcessId(handle)
                return handle, pid
        except Exception as e:
            print(f"Could not find window with title containing: '{title}'. Error: {e}")
        return None, None

    def draw_rectangle(self, overlay, rect, color="red", width=5):
        """Draws a highlighted rectangle on an overlay window (thread-safe)."""
        try:
            if overlay is None:
                return False
            
            if rect.width() <= 0 or rect.height() <= 0:
                QTimer.singleShot(0, lambda: self._safe_hide_overlay(overlay))
                return False

            current_rect = (rect.left, rect.top, rect.width(), rect.height())
            if self.last_rect == current_rect and self.overlay_visible:
                return True

            self.last_rect = current_rect
            # Use QTimer to ensure thread safety for UI updates with lock
            QTimer.singleShot(0, lambda: self._safe_set_rectangle(overlay, rect.left, rect.top, rect.width(), rect.height()))
            return True
        except Exception as e:
            print(f"Draw rectangle failed: {e}")
            try:
                QTimer.singleShot(0, lambda: self._safe_hide_overlay(overlay))
            except:
                pass
            return False
    
    def _safe_set_rectangle(self, overlay, left, top, width, height):
        """Set rectangle safely with lock"""
        try:
            with self._paint_lock:
                if overlay:
                    overlay.set_rectangle(left, top, width, height)
        except:
            pass

    def find_most_specific_element(self, element):
        """Find the most specific/smallest element at the cursor position."""
        try:
            children = element.children()
            cursor_pos = win32api.GetCursorPos()
            for child in children:
                try:
                    child_rect = child.rectangle()
                    if (child_rect.left <= cursor_pos[0] <= child_rect.right and
                        child_rect.top <= cursor_pos[1] <= child_rect.bottom):
                        more_specific = self.find_most_specific_element(child)
                        if more_specific:
                            return more_specific
                        return child
                except:
                    continue
            return element
        except:
            return element

    def get_element_basic_info(self, element):
        """Extract basic information from an element safely."""
        try:
            info = element.element_info
            rect = None
            try:
                rect = element.rectangle()
            except:
                pass
            
            value = None
            try:
                value = element.get_value()
            except:
                pass
            if not value:
                try:
                    value = element.window_text()
                except:
                    pass
            if not value:
                try:
                    value = str(getattr(info, "name", ""))
                except:
                    pass

            basic_info = {
                "name": str(getattr(info, "name", "")),
                "control_type": str(getattr(info, "control_type", "")),
                "class_name": str(getattr(info, "class_name", "")),
                "auto_id": str(getattr(info, "automation_id", "")),
                "value": str(value) if value else "",
                "handle": str(element.handle) if hasattr(element, 'handle') else "",
                "process_id": str(getattr(info, "process_id", ""))
            }

            if rect:
                basic_info["rectangle"] = {
                    "left": rect.left,
                    "top": rect.top,
                    "right": rect.right,
                    "bottom": rect.bottom,
                    "width": rect.width(),
                    "height": rect.height()
                }

            return basic_info
        except Exception as e:
            return {"error": str(e)}

    def get_siblings_info(self, element):
        """Get information about previous and next siblings."""
        siblings_info = {
            "previous_sibling": None,
            "next_sibling": None
        }
        
        try:
            parent = element.parent()
            if parent:
                children = parent.children()
                current_index = -1
                
                for i, child in enumerate(children):
                    try:
                        if child.handle == element.handle:
                            current_index = i
                            break
                    except:
                        continue
                
                if current_index > 0:
                    try:
                        prev_sibling = children[current_index - 1]
                        siblings_info["previous_sibling"] = self.get_element_basic_info(prev_sibling)
                    except:
                        pass
                
                if current_index >= 0 and current_index < len(children) - 1:
                    try:
                        next_sibling = children[current_index + 1]
                        siblings_info["next_sibling"] = self.get_element_basic_info(next_sibling)
                    except:
                        pass
        except:
            pass
        
        return siblings_info

    def get_children_info(self, element, max_depth=5, current_depth=0):
        """Get information about all children recursively with depth limit."""
        children_info = []
        
        if current_depth >= max_depth:
            return children_info
        
        try:
            children = element.children()
            for child in children:
                try:
                    child_info = self.get_element_basic_info(child)
                    
                    if current_depth + 1 < max_depth:
                        child_info["children"] = self.get_children_info(child, max_depth, current_depth + 1)
                    
                    children_info.append(child_info)
                except Exception as e:
                    children_info.append({"error": str(e)})
        except:
            pass
        
        return children_info

    def get_ancestors_info(self, element, max_levels=10):
        """Get information about all ancestor elements up the hierarchy."""
        ancestors = []
        
        try:
            ancestor = element.parent()
            level = 0
            
            while ancestor and level < max_levels:
                try:
                    ancestor_info = self.get_element_basic_info(ancestor)
                    ancestors.append(ancestor_info)
                    ancestor = ancestor.parent()
                    level += 1
                except:
                    break
        except:
            pass
        
        return ancestors[::-1]

    def capture_element_screenshot(self, element, filename="element_screenshot.png"):
        """Capture screenshot of the element"""
        try:
            rect = element.rectangle()
            
            padding = 5
            bbox = (
                rect.left - padding,
                rect.top - padding,
                rect.right + padding,
                rect.bottom + padding
            )
            
            screenshot = ImageGrab.grab(bbox)
            if self.proj_fol and self.task_fol and self.var_name:
                save_dir = os.path.join(self.proj_fol, self.task_fol, "desktop", "images")
                os.makedirs(save_dir, exist_ok=True)
                image_path = os.path.join(save_dir, f"{self.var_name}.png")
            else:
                image_path = "element_screenshot.png"

            screenshot.save(image_path)
            return image_path
            
        except Exception as e:
            print(f"\n✗ Screenshot failed: {e}")
            return None

    def hover_highlight(self, pos):
        """Highlights the element under the cursor with optimizations (DEPRECATED - now handled by worker thread)."""
        # This method is now handled by the HoverHighlightWorker thread
        # Kept for backward compatibility but no longer called
        pass

    def click_extract(self, pos):
        """Extracts and returns comprehensive attributes of the clicked element."""
        self.is_processing_click = True
        if self.overlay_visible and self.hover_overlay:
            QTimer.singleShot(0, lambda: self._safe_hide_overlay(self.hover_overlay))
            self.overlay_visible = False
        if self.click_overlay:
            QTimer.singleShot(0, lambda: self._safe_hide_overlay(self.click_overlay))
        time.sleep(0.05)

        try:
            element = Desktop(backend="uia").from_point(*pos)

            is_internal_window = False
            target_app_match = (
                element and
                (not self.target_pid or element.element_info.process_id == self.target_pid)
            )

            if element and not is_internal_window and target_app_match:
                specific_element = self.find_most_specific_element(element)
                if specific_element:
                    element = specific_element

                rect = element.rectangle()
                self.picked_element = element

                # Show click overlay
                self.click_overlay.set_rectangle(rect.left, rect.top, rect.width(), rect.height())
                self.click_overlay.show()
                self.click_overlay.raise_()

                self.click_successful = True
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                self.screenshot_path = {"screenshot_path": self.capture_element_screenshot(element)}
                
                current_element = self.get_element_basic_info(element)
                ancestors = self.get_ancestors_info(element)
                siblings = self.get_siblings_info(element)
                children = self.get_children_info(element, max_depth=5)
                
                element_info_data = {
                    "current_element": current_element,
                    "ancestors": ancestors,
                    "siblings": siblings,
                    "timestamp": timestamp
                }
                element_info_filename = "element_info.json"
    
                try:
                    with open(element_info_filename, "w", encoding="utf-8") as f:
                        json.dump(element_info_data, f, indent=2, ensure_ascii=False)
                    print(f"\n✓ Element info exported to: {element_info_filename}")
                except Exception as e:
                    print(f"\n✗ Element info export failed: {e}")
                
                child_info_data = {
                    "Current_element_info": {
                        "name": current_element.get("name", ""),
                        "control_type": current_element.get("control_type", ""),
                        "handle": current_element.get("handle", "")
                    },
                    "children": children,
                    "total_children": len(children),
                    "timestamp": timestamp
                }

                child_info_filename = "child_info.json"
    
                try:
                    with open(child_info_filename, "w", encoding="utf-8") as f:
                        json.dump(child_info_data, f, indent=2, ensure_ascii=False)
                    print(f"\n✓ Children info exported to: {child_info_filename}")
                    print(f"  - Direct children: {len(children)}")
                except Exception as e:
                    print(f"\n✗ Children info export failed: {e}")
                
                self.element_info_data = json.dumps(element_info_data, indent=2, ensure_ascii=False)
                self.child_info_data = json.dumps(child_info_data, indent=2, ensure_ascii=False)
                
                print("\n" + "=" * 60)
                print("EXPORT SUMMARY:")
                print("=" * 60)
                print("1. Element Info JSON: (returned as string)")
                print("2. Children Info JSON: (returned as string)")
                print("3. Screenshot: {self.screenshot_path}")
                print("=" * 60)
                
                print("\n" + "=" * 60)
                print("ELEMENT INFO JSON:")
                print("=" * 60)
                print(self.element_info_data)
                print("=" * 60)
                
                print("\n" + "=" * 60)
                print("CHILD INFO JSON:")
                print("=" * 60)
                print(self.child_info_data)
                print("=" * 60)
                
                print("\n" + "="*50)
                print("Extraction complete!")
                print("="*50 + "\n")
                
                # Hide click overlay after 2 seconds
                QTimer.singleShot(2000, self.click_overlay.hide)
                # Quit application after extraction only if this picker created the app
                if self.auto_quit:
                    QTimer.singleShot(2500, self.app.quit)
            else:
                self.click_overlay.hide()
        except Exception as e:
            print(f"Error during click extraction: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.is_processing_click = False

    def mouse_event_loop(self):
        """Mouse event loop: detect Ctrl+Click and trigger element extraction on worker thread."""
        if self.click_successful:
            self.timer.stop()
            return
        
        # Detect Ctrl + Left Click
        ctrl_pressed = win32api.GetAsyncKeyState(win32con.VK_CONTROL) & 0x8000
        left_click = win32api.GetAsyncKeyState(win32con.VK_LBUTTON) & 0x8000

        if ctrl_pressed and left_click and not self.is_processing_click:
            print("\n>>> Ctrl + Click detected - Starting extraction on worker thread...")
            pos = win32api.GetCursorPos()
            self._trigger_click_extraction(pos)
            # Don't perform actual click - just extract data
            time.sleep(0.2)
    
    def _trigger_click_extraction(self, pos):
        """Trigger click extraction on worker thread"""
        try:
            if not self.is_processing_click:
                self.is_processing_click = True
                
                # Notify hover worker to stop highlighting
                if self.hover_worker:
                    self.hover_worker.set_processing_state(True)
                
                # Schedule hide on main thread with lock
                if self.hover_overlay:
                    QTimer.singleShot(0, lambda: self._safe_hide_overlay(self.hover_overlay))
                
                # Setup and start click worker
                if self._setup_click_worker():
                    self.click_thread.start()
                    self.click_worker.extract_at_position(pos)
        except Exception as e:
            print(f"Error triggering click extraction: {e}")
            traceback.print_exc()
            self.is_processing_click = False
    
    def _export_element_json(self, current_element, ancestors, siblings, children):
        """Export element information to JSON files"""
        try:
            save_dir = os.path.join(self.proj_fol, self.task_fol, "desktop")
            os.makedirs(save_dir, exist_ok=True)
            
            # Element info JSON
            element_json_path = os.path.join(save_dir, f"{self.var_name}_element_info.json")
            element_data = {
                "current_element": current_element,
                "ancestors": ancestors,
                "siblings": siblings
            }
            with open(element_json_path, 'w', encoding='utf-8') as f:
                json.dump(element_data, f, indent=2, ensure_ascii=False)
            print(f"Element info saved: {element_json_path}")
            
            # Children info JSON
            children_json_path = os.path.join(save_dir, f"{self.var_name}_children_info.json")
            with open(children_json_path, 'w', encoding='utf-8') as f:
                json.dump(children, f, indent=2, ensure_ascii=False)
            print(f"Children info saved: {children_json_path}")
        except Exception as e:
            print(f"Error exporting JSON: {e}")
            traceback.print_exc()
    
    def cleanup_and_quit(self):
        """Cleanup and quit the application"""
        try:
            # Stop hover worker
            if self.hover_worker:
                self.hover_worker.stop_finding()
                if self.hover_thread:
                    self.hover_thread.quit()
                    self.hover_thread.wait(2000)
                    if self.hover_thread.isRunning():
                        self.hover_thread.terminate()
                        self.hover_thread.wait()
            
            # Stop click worker if running
            if self.click_thread and self.click_thread.isRunning():
                self.click_thread.quit()
                self.click_thread.wait(2000)
                if self.click_thread.isRunning():
                    self.click_thread.terminate()
                    self.click_thread.wait()
            
            # Stop timer
            if self.timer.isActive():
                self.timer.stop()
            
            # Hide and cleanup overlays safely
            try:
                with self._paint_lock:
                    if self.hover_overlay:
                        try:
                            self.hover_overlay.hide()
                            self.hover_overlay.setParent(None)
                            self.hover_overlay.deleteLater()
                        except:
                            pass
                    
                    if self.click_overlay:
                        try:
                            self.click_overlay.hide()
                            self.click_overlay.setParent(None)
                            self.click_overlay.deleteLater()
                        except:
                            pass
            except:
                pass
            
            print("Cleanup complete")
            
            # Quit application only if we created it
            if self.auto_quit and QApplication.instance():
                QApplication.quit()
        except Exception as e:
            print(f"Error during cleanup: {e}")
            traceback.print_exc()


def main_desktop_element_picker(target_window_title=None, proj_fol=None, task_fol=None, var_name=None):
    """
    Main function to start the element picker.
    
    Args:
        target_window_title: Optional window title to target specific application
        proj_fol: Project folder path
        task_fol: Task folder name
        var_name: Variable name for screenshot
    
    Returns:
        tuple: (element_info_json_dict, child_info_json_dict, screenshot_path) if successful, else (None, None, None)
    """
    app = QApplication.instance()
    # QApplication.processEvents()
    created_app = False
    if app is None:
        app = QApplication(sys.argv)
        created_app = True
    else:
        created_app = False
    
    selector = ElementSelector(app, target_window_title, proj_fol, task_fol, var_name, auto_quit=created_app)
    
    if created_app:
        # Run full event loop we created and let selector schedule app.quit
        app.exec_()
    else:
        # Use a local event loop to wait until selection completes without quitting the main app
        loop = QEventLoop()
        checker = QTimer()
        checker.setInterval(50)
        def _check_done():
            if selector.click_successful:
                checker.stop()
                loop.quit()
        checker.timeout.connect(_check_done)
        checker.start()
        loop.exec_()
    
    if selector.click_successful and selector.element_info_data:
        element_info_dict = json.loads(selector.element_info_data)
        child_info_dict = json.loads(selector.child_info_data)
        return (element_info_dict, child_info_dict, selector.screenshot_path)
    else:
        return (None, None, None)


# if __name__ == "__main__":
#     application_name = None  # Change to your target application name
    
#     print("\n" + "="*60)
#     print("Enhanced Element Picker - PyQt5 Version")
#     print("="*60)
#     print("Instructions:")
#     print("1. Hover over any UI element (red highlight appears)")
#     print("2. Press Ctrl + Left Click to extract information")
#     print("3. Function returns: (element_info_json_dict, child_info_json_dict, screenshot_path)")
#     print("   - Element properties, ancestors, siblings (in element_info_json_dict)")
#     print("   - Children (up to 5 levels deep, in child_info_json_dict)")
#     print("   - Screenshot path (screenshot_path)")
#     print("="*60 + "\n")
    
#     outputs = main_desktop_element_picker(application_name)
    
#     if outputs[0] is not None:
#         print("\nReturned outputs:")
#         print(f"Screenshot Path: {outputs[2]}")
#     else:
#         print("No element was clicked. No outputs generated.")