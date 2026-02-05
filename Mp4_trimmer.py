# Mp4_trimmer_new.py

import sys
import json
import os
import cv2
import numpy as np
import pygame
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QDialog,
    QHBoxLayout, QPushButton, QFileDialog, QLabel, QMessageBox,
    QSlider, QStyle, QFrame, QSpinBox, QStyleOptionSpinBox
)
from PyQt5.QtCore import Qt, QTimer, QRectF, pyqtSignal
from PyQt5.QtGui import QFont, QImage, QPixmap, QPainter, QPen, QBrush, QColor
import subprocess
import tempfile


# -------------------------------------------------------------------------
# Custom SpinBox with drawn arrows
# -------------------------------------------------------------------------
class CustomSpinBox(QSpinBox):
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)

        opt = QStyleOptionSpinBox()
        self.initStyleOption(opt)

        up_rect = self.style().subControlRect(QStyle.CC_SpinBox, opt, QStyle.SC_SpinBoxUp, self)
        painter.drawText(up_rect, Qt.AlignCenter, "▲")

        down_rect = self.style().subControlRect(QStyle.CC_SpinBox, opt, QStyle.SC_SpinBoxDown, self)
        painter.drawText(down_rect, Qt.AlignCenter, "▼")


from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QRectF, pyqtSignal, QPointF
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QPolygonF, QFont
import cv2

class MultiSplitTimeline(QWidget):
    splitsChanged = pyqtSignal(list)  # list of (start_ms, end_ms)
    seekRequested = pyqtSignal(int)   # Signal for seeking to a position

    def __init__(self, duration_ms=0, parent=None):
        super().__init__(parent)
        self.duration = duration_ms
        self.splits = [(0, duration_ms)]  # (start, end)
        self.active_split = 0
        self.active_handle = None  # "start", "end", or "playhead"
        self.handle_radius = 8
        self.track_height = 90
        self.setMinimumHeight(130)
        self.setMouseTracking(True)

        # Thumbnail cache
        self.thumbnails = []
        self.cap = None

        # Playhead position
        self.playhead_position = 0  # in milliseconds
        self.playhead_drag_radius = 10  # hit area around red line

    def setDuration(self, duration_ms):
        self.duration = duration_ms
        self.splits = [(0, duration_ms)]
        self.active_split = 0
        self.active_handle = None
        self.update()

    def setSplits(self, new_splits):
        self.splits = new_splits
        if self.active_split >= len(self.splits):
            self.active_split = len(self.splits) - 1
        self.update()

    def setPlayheadPosition(self, position_ms):
        """Update the playhead position on the timeline"""
        self.playhead_position = position_ms
        self.update()

    def addSplit(self):
        if not self.splits:
            self.splits = [(0, self.duration)]
            self.active_split = 0
            self.update()
            return

        last_start, last_end = self.splits[-1]
        if last_end >= self.duration:
            return

        new = (last_end, self.duration)
        self.splits.append(new)
        self.active_split = len(self.splits) - 1
        self.update()

    def generateThumbnailsFromFile(self, video_path, duration_ms, fps):
        print(f"Generating thumbnails from: {video_path}")
        print(f"Duration: {duration_ms}ms, FPS: {fps}")

        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            print("ERROR: Could not open video for thumbnails")
            return

        self.thumbnails = []
        num_thumbs = 12

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"Total frames: {total_frames}")

        for i in range(num_thumbs):
            time_ms = ((i + 0.5) / num_thumbs) * duration_ms
            frame_num = int((time_ms / 1000) * fps)
            frame_num = min(frame_num, total_frames - 1)

            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()

            if ret and frame is not None:
                try:  # NEW: Wrap thumbnail processing in try-catch
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = frame_rgb.shape

                    thumb_h = 75
                    thumb_w = int(w * (thumb_h / h))
                    if thumb_w < 40:
                        thumb_w = 40

                    thumb = cv2.resize(frame_rgb, (thumb_w, thumb_h), interpolation=cv2.INTER_AREA)

                    bytes_per_line = ch * thumb_w
                    qimg = QImage(thumb.data, thumb_w, thumb_h, bytes_per_line, QImage.Format_RGB888)
                    qimg_copy = qimg.copy()
                    pixmap = QPixmap.fromImage(qimg_copy)

                    self.thumbnails.append(pixmap)
                    print(f"Thumbnail {i+1}: {thumb_w}x{thumb_h} - Success")
                except Exception as e:
                    print(f"Thumbnail {i+1}: Error processing - {str(e)}")
                    placeholder = QPixmap(75, 75)
                    placeholder.fill(QColor(50, 50, 50))
                    self.thumbnails.append(placeholder)
            else:
                print(f"Thumbnail {i+1}: Failed to read frame {frame_num}")
                placeholder = QPixmap(75, 75)
                placeholder.fill(QColor(50, 50, 50))
                self.thumbnails.append(placeholder)

        cap.release()
        print(f"Total thumbnails generated: {len(self.thumbnails)}")
        self.update()

    def paintEvent(self, event):
        if self.duration == 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        W = self.width()
        H = self.height()
        cy = H // 2

        timeline_x = 10
        timeline_w = W - 20
        timeline_y = cy - self.track_height // 2

        # 1) Background
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(20, 20, 20)))
        painter.drawRoundedRect(timeline_x, timeline_y, timeline_w, self.track_height, 8, 8)

        # 2) Thumbnails
        if self.thumbnails:
            thumb_width = timeline_w / len(self.thumbnails)
            for i, pixmap in enumerate(self.thumbnails):
                if pixmap.isNull():
                    continue

                x = timeline_x + i * thumb_width
                y = timeline_y + 5
                h = self.track_height - 10

                aspect = pixmap.width() / pixmap.height()
                w = h * aspect

                target_rect = QRectF(x + 1, y, w - 2, h)
                painter.drawPixmap(target_rect, pixmap, QRectF(pixmap.rect()))
        else:
            painter.setPen(QPen(QColor(100, 100, 100), 1))
            painter.drawText(
                timeline_x + timeline_w // 2 - 50,
                timeline_y + self.track_height // 2,
                "Loading thumbnails..."
            )

        # 3) Split overlays
        for idx, (start, end) in enumerate(self.splits):
            start = max(0, min(self.duration, start))
            end = max(0, min(self.duration, end))
            if end <= start:
                continue

            sx = timeline_x + (start / self.duration) * timeline_w
            ex = timeline_x + (end / self.duration) * timeline_w

            if idx == self.active_split:
                overlay = QColor(0, 183, 255, 80)
            else:
                overlay = QColor(0, 120, 200, 40)

            painter.setBrush(QBrush(overlay))
            painter.drawRect(QRectF(sx, timeline_y, ex - sx, self.track_height))

        # 4) Split boundaries
        painter.setPen(QPen(QColor(0, 183, 255), 3))
        for idx, (start, end) in enumerate(self.splits):
            start = max(0, min(self.duration, start))
            end = max(0, min(self.duration, end))

            sx = timeline_x + (start / self.duration) * timeline_w
            ex = timeline_x + (end / self.duration) * timeline_w

            if idx == 0:
                painter.drawLine(int(sx), timeline_y, int(sx), timeline_y + self.track_height)
            painter.drawLine(int(ex), timeline_y, int(ex), timeline_y + self.track_height)

        # 5) Playhead (red)
        if self.duration > 0:
            playhead_x = timeline_x + (self.playhead_position / self.duration) * timeline_w
            painter.setPen(QPen(QColor(255, 50, 50), 3))
            painter.drawLine(int(playhead_x), timeline_y, int(playhead_x), timeline_y + self.track_height)

            painter.setBrush(QBrush(QColor(255, 50, 50)))
            painter.setPen(Qt.NoPen)
            triangle_size = 8
            points = [
                (playhead_x, timeline_y - 5),
                (playhead_x - triangle_size, timeline_y - triangle_size - 5),
                (playhead_x + triangle_size, timeline_y - triangle_size - 5)
            ]
            painter.drawPolygon(QPolygonF([QPointF(p[0], p[1]) for p in points]))

        # 6) Handles
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(QBrush(QColor(0, 183, 255)))

        for start, end in self.splits:
            start = max(0, min(self.duration, start))
            end = max(0, min(self.duration, end))

            sx = timeline_x + (start / self.duration) * timeline_w
            ex = timeline_x + (end / self.duration) * timeline_w

            painter.drawEllipse(
                QRectF(
                    sx - self.handle_radius,
                    cy - self.handle_radius,
                    self.handle_radius * 2,
                    self.handle_radius * 2,
                )
            )
            painter.drawEllipse(
                QRectF(
                    ex - self.handle_radius,
                    cy - self.handle_radius,
                    self.handle_radius * 2,
                    self.handle_radius * 2,
                )
            )

        # 7) Time labels
        painter.setPen(QPen(QColor(230, 230, 230), 1))
        painter.setFont(QFont("Segoe UI", 9))

        for start, end in self.splits:
            start = max(0, min(self.duration, start))
            sx = timeline_x + (start / self.duration) * timeline_w

            start_time = self.format_time(start)
            painter.drawText(int(sx - 30), timeline_y - 5, start_time)

        if self.splits:
            end = min(self.duration, self.splits[-1][1])
            ex = timeline_x + (end / self.duration) * timeline_w
            end_time = self.format_time(end)
            painter.drawText(int(ex - 30), timeline_y - 5, end_time)

    def format_time(self, ms):
        ms = int(ms)
        total_seconds = ms / 1000
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:04.1f}"

    def mousePressEvent(self, event):
        x = event.x()
        y = event.y()
        W = self.width()
        cy = self.height() // 2

        timeline_x = 10
        timeline_w = W - 20
        timeline_y = cy - self.track_height // 2

        # 1) Check split handles
        for i, (start, end) in enumerate(self.splits):
            sx = 10 + (start / self.duration) * (W - 20)
            ex = 10 + (end / self.duration) * (W - 20)

            if (x - sx) ** 2 + (y - cy) ** 2 <= self.handle_radius ** 2:
                self.active_split = i
                self.active_handle = "start"
                return

            if (x - ex) ** 2 + (y - cy) ** 2 <= self.handle_radius ** 2:
                self.active_split = i
                self.active_handle = "end"
                return

        # 2) Check playhead drag hit
        if self.duration > 0:
            playhead_x = timeline_x + (self.playhead_position / self.duration) * timeline_w
            if (abs(x - playhead_x) <= self.playhead_drag_radius and
                timeline_y <= y <= timeline_y + self.track_height):
                self.active_handle = "playhead"
                return

        # 3) Normal click seek inside track
        if (timeline_x <= x <= timeline_x + timeline_w and
                timeline_y <= y <= timeline_y + self.track_height):
            pos_ms = ((x - timeline_x) / timeline_w) * self.duration
            pos_ms = max(0, min(self.duration, pos_ms))
            self.seekRequested.emit(int(pos_ms))
            return

        self.active_handle = None

    def mouseMoveEvent(self, event):
        if self.active_handle is None:
            return

        x = event.x()
        W = self.width()

        if self.active_handle == "playhead":
            # Dragging the red playhead
            timeline_x = 10
            timeline_w = W - 20
            pos_ms = ((x - timeline_x) / timeline_w) * self.duration
            pos_ms = max(0, min(self.duration, pos_ms))

            self.playhead_position = pos_ms
            self.seekRequested.emit(int(pos_ms))
            self.update()
            return

        # Existing handle-drag logic
        pos_ms = ((x - 10) / (W - 20)) * self.duration
        pos_ms = max(0, min(self.duration, pos_ms))

        i = self.active_split
        start, end = self.splits[i]

        if self.active_handle == "start":
            prev_end = self.splits[i - 1][1] if i > 0 else 0
            pos_ms = max(pos_ms, prev_end)
            pos_ms = min(pos_ms, end - 500)
            self.splits[i] = (pos_ms, end)

        elif self.active_handle == "end":
            next_start = self.splits[i + 1][0] if i < len(self.splits) - 1 else self.duration
            pos_ms = min(pos_ms, next_start)
            pos_ms = max(pos_ms, start + 500)
            self.splits[i] = (start, pos_ms)

        self.splitsChanged.emit(self.splits)
        self.update()

    def mouseReleaseEvent(self, event):
        self.active_handle = None


# -------------------------------------------------------------------------
# Main Window
# -------------------------------------------------------------------------
class VideoTrimmer(QDialog):  
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Video Splitter Pro")
        
        self.setWindowState(Qt.WindowMaximized)
        
        self.setGeometry(200, 80, 1000, 850)
        self.setModal(True)  # Make it modal
        
        # Video data
        self.video_path = None
        self.video_duration = 0
        self.cap = None
        self.is_playing = False
        self.fps = 30
        self.total_frames = 0
        self.current_frame = 0

        # Audio handling
        self.audio_loaded = False
        self.was_playing_before_seek = False
        self.temp_audio_file = None

        # Split data
        self.splits = []
        self.active_split_index = 0

        # Timer for video frames
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        # Initialize pygame mixer for audio
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)

        self.apply_dark_theme()
        self.init_ui()

    # -------------------------------------------------------------------------
    # Styling
    # -------------------------------------------------------------------------
    def apply_dark_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #e6e6e6;
                font-family: 'Segoe UI';
                font-size: 16px;
            }

            QPushButton {
                background-color: #3a3f44;
                border: 1px solid #565a5e;
                padding: 8px 14px;
                border-radius: 6px;
                font-size: 15px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #50575d;
            }

            QPushButton:disabled {
                background-color: #2b2b2b;
                color: #8c8c8c;
            }

            QLabel {
                font-size: 15px;
            }

            QSlider::groove:horizontal {
                background: #2e2e2e;
                height: 6px;
                border-radius: 3px;
            }

            QSlider::handle:horizontal {
                background: #00b7ff;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }

            QSlider::sub-page:horizontal {
                background: #00b7ff;
            }

            QSlider::add-page:horizontal {
                background: #2e2e2e;
            }

            #videoBox {
                border: 2px solid #444;
                border-radius: 8px;
                background: #111;
            }

            #sectionHeader {
                font-size: 17px;
                font-weight: bold;
                margin-bottom: 4px;
                color: #00b7ff;
            }

            QSpinBox {
                background-color: #2e2e2e;
                border: 1px solid #565a5e;
                padding: 4px 6px;
                border-radius: 4px;
                color: #e6e6e6;
                font-weight: bold;
            }

            QSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                background-color: #3a3f44;
                border: 1px solid #565a5e;
                border-top-right-radius: 4px;
                width: 18px;
                height: 14px;
            }

            QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                background-color: #3a3f44;
                border: 1px solid #565a5e;
                border-bottom-right-radius: 4px;
                width: 18px;
                height: 14px;
            }

            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #50575d;
            }

            QSpinBox::up-button:pressed, QSpinBox::down-button:pressed {
                background-color: #00b7ff;
            }
        """)

    def init_ui(self):
        # For QDialog, we set the layout directly (no central widget needed)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(10)
        
        # Set layout directly on the dialog
        self.setLayout(main_layout)
        
        # Upload button
        self.upload_btn = QPushButton("📂 Browse and Upload Video")
        self.upload_btn.setFont(QFont("Segoe UI", 14))
        self.upload_btn.setFixedHeight(40)
        self.upload_btn.clicked.connect(self.upload_video)
        main_layout.addWidget(self.upload_btn)

        # Video name
        self.video_label = QLabel("No video loaded")
        main_layout.addWidget(self.video_label)

        # Video display (slightly reduced height to avoid scroll)
        self.video_display = QLabel()
        self.video_display.setAlignment(Qt.AlignCenter)
        self.video_display.setMinimumSize(700, 480)
        self.video_display.setObjectName("videoBox")
        main_layout.addWidget(self.video_display)

        # Playback
        playback_frame = QFrame()
        playback_layout = QVBoxLayout(playback_frame)
        playback_layout.setSpacing(6)

        controls = QHBoxLayout()
        controls.addStretch()

        # <<10s button
        self.backward_btn = QPushButton("⟲ 10s")
        self.backward_btn.setFixedWidth(100)
        self.backward_btn.clicked.connect(self.skip_backward)
        self.backward_btn.setEnabled(False)
        controls.addWidget(self.backward_btn)

        # Play/Pause button
        self.play_btn = QPushButton()
        self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_btn.setFixedWidth(80)
        self.play_btn.clicked.connect(self.play_pause)
        self.play_btn.setEnabled(False)
        controls.addWidget(self.play_btn)

        # >>30s button
        self.forward_btn = QPushButton("⟳ 30s")
        self.forward_btn.setFixedWidth(100)
        self.forward_btn.clicked.connect(self.skip_forward)
        self.forward_btn.setEnabled(False)
        controls.addWidget(self.forward_btn)

        controls.addStretch()

        # Time label centered below buttons
        time_layout = QHBoxLayout()
        time_layout.addStretch()
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("font-size: 14px; color: #00b7ff;")
        time_layout.addWidget(self.time_label)
        time_layout.addStretch()

        playback_layout.addLayout(controls)
        playback_layout.addLayout(time_layout)
        main_layout.addWidget(playback_frame)

        # Split frame
        split_frame = QFrame()
        split_layout = QVBoxLayout(split_frame)
        split_layout.setSpacing(6)

        # Split controls
        header2 = QLabel("Split/Trim Controls")
        header2.setObjectName("sectionHeader")
        split_layout.addWidget(header2)

        split_row = QHBoxLayout()

        # Start spinboxes (left)
        self.split_start_min = CustomSpinBox()
        self.split_start_sec = CustomSpinBox()
        self.split_start_min.setSuffix(" min")
        self.split_start_sec.setSuffix(" sec")
        self.split_start_min.setRange(0, 999)
        self.split_start_sec.setRange(0, 59)
        self.split_start_min.setFixedWidth(80)
        self.split_start_sec.setFixedWidth(80)

        # End spinboxes (right)
        self.split_end_min = CustomSpinBox()
        self.split_end_sec = CustomSpinBox()
        self.split_end_min.setSuffix(" min")
        self.split_end_sec.setSuffix(" sec")
        self.split_end_min.setRange(0, 999)
        self.split_end_sec.setRange(0, 59)
        self.split_end_min.setFixedWidth(80)
        self.split_end_sec.setFixedWidth(80)

        for sb in (
            self.split_start_min, self.split_start_sec,
            self.split_end_min, self.split_end_sec
        ):
            sb.setEnabled(False)
            sb.setButtonSymbols(QSpinBox.UpDownArrows)

        # Add start spinboxes to left
        split_row.addWidget(self.split_start_min)
        split_row.addWidget(self.split_start_sec)

        # Center: the custom multi-split timeline
        self.split_timeline = MultiSplitTimeline()
        self.split_timeline.seekRequested.connect(self.seek_to_position)
        split_row.addWidget(self.split_timeline, 1)

        # Add end spinboxes to right
        split_row.addWidget(self.split_end_min)
        split_row.addWidget(self.split_end_sec)

        split_layout.addLayout(split_row)

        # Connect spinbox changes -> update splits
        self.split_start_min.valueChanged.connect(self.on_split_spinbox_changed)
        self.split_start_sec.valueChanged.connect(self.on_split_spinbox_changed)
        self.split_end_min.valueChanged.connect(self.on_split_spinbox_changed)
        self.split_end_sec.valueChanged.connect(self.on_split_spinbox_changed)

        # + button row
        add_row = QHBoxLayout()
        add_row.addStretch()
        self.split_add_btn = QPushButton("+ Add Split")
        self.split_add_btn.setFixedWidth(120)
        self.split_add_btn.setEnabled(False)
        self.split_add_btn.clicked.connect(self.add_new_split)
        add_row.addWidget(self.split_add_btn)
        split_layout.addLayout(add_row)

        # List of splits (display only – currently not populated in UI)
        self.split_list_layout = QVBoxLayout()
        split_layout.addLayout(self.split_list_layout)

        main_layout.addWidget(split_frame)

        # Save button
        self.save_btn = QPushButton("💾 Save Split Timestamps")
        self.save_btn.setEnabled(False)
        self.save_btn.setFixedHeight(36)
        self.save_btn.clicked.connect(self.save_timestamps)
        main_layout.addWidget(self.save_btn)

    # -------------------------------------------------------------------------
    # Playback helpers
    # -------------------------------------------------------------------------
    def skip_backward(self):
        """Skip backward 10 seconds"""
        if not self.cap:
            return

        current_ms = int((self.current_frame / self.fps) * 1000)
        new_ms = max(0, current_ms - 10000)

        self.current_frame = int((new_ms / 1000) * self.fps)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)

        self.split_timeline.setPlayheadPosition(new_ms)

        self.time_label.setText(
            f"{self.format_time(new_ms)} / {self.format_time(self.video_duration)}"
        )

        if self.is_playing and self.audio_loaded:
            pygame.mixer.music.stop()
            pygame.mixer.music.play(start=new_ms / 1000.0)

        self.display_frame()

    def skip_forward(self):
        """Skip forward 30 seconds"""
        if not self.cap:
            return

        current_ms = int((self.current_frame / self.fps) * 1000)
        new_ms = min(self.video_duration, current_ms + 30000)

        self.current_frame = int((new_ms / 1000) * self.fps)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)

        self.split_timeline.setPlayheadPosition(new_ms)

        self.time_label.setText(
            f"{self.format_time(new_ms)} / {self.format_time(self.video_duration)}"
        )

        if self.is_playing and self.audio_loaded:
            pygame.mixer.music.stop()
            pygame.mixer.music.play(start=new_ms / 1000.0)

        self.display_frame()

    def seek_to_position(self, position_ms):
        """Seek video to specific position from timeline click"""
        if not self.cap:
            return

        self.current_frame = int((position_ms / 1000) * self.fps)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)

        self.split_timeline.setPlayheadPosition(position_ms)

        self.time_label.setText(
            f"{self.format_time(position_ms)} / {self.format_time(self.video_duration)}"
        )

        if self.is_playing and self.audio_loaded:
            pygame.mixer.music.stop()
            pygame.mixer.music.play(start=position_ms / 1000.0)

        self.display_frame()

    def add_new_split(self):
        self.split_timeline.addSplit()
        self.on_splits_updated(self.split_timeline.splits)

    def on_split_spinbox_changed(self):
        """Called when user manually edits split start/end spinboxes."""
        if not hasattr(self, "splits") or not self.splits:
            return
        if self.video_duration <= 0:
            return

        i = self.split_timeline.active_split
        if i < 0 or i >= len(self.splits):
            return

        start_ms = (self.split_start_min.value() * 60 + self.split_start_sec.value()) * 1000
        end_ms = (self.split_end_min.value() * 60 + self.split_end_sec.value()) * 1000

        prev_end = self.splits[i - 1][1] if i > 0 else 0
        next_start = self.splits[i + 1][0] if i < len(self.splits) - 1 else self.video_duration

        if start_ms < prev_end:
            start_ms = prev_end
        if end_ms > next_start:
            end_ms = next_start

        if end_ms <= start_ms:
            end_ms = min(next_start, start_ms + 1000)

        self.splits[i] = (start_ms, end_ms)

        self.split_timeline.setSplits(self.splits)
        self.split_timeline.active_split = i
        self.split_timeline.update()
        self.split_timeline.splitsChanged.emit(self.splits)

    def on_splits_updated(self, splits):
        """Called when the MultiSplitTimeline moves handles."""
        self.splits = splits
        if not self.splits:
            return

        i = self.split_timeline.active_split
        if i < 0 or i >= len(self.splits):
            i = 0

        start, end = self.splits[i]
        start = int(start)
        end = int(end)

        sbs = (
            self.split_start_min, self.split_start_sec,
            self.split_end_min, self.split_end_sec
        )
        for sb in sbs:
            sb.blockSignals(True)

        self.split_start_min.setValue((start // 1000) // 60)
        self.split_start_sec.setValue((start // 1000) % 60)
        self.split_end_min.setValue((end // 1000) // 60)
        self.split_end_sec.setValue((end // 1000) % 60)

        for sb in sbs:
            sb.blockSignals(False)

    def upload_video_programmatic(self, video_path):
        """Programmatically load a video without file dialog"""
        if not os.path.exists(video_path):
            print(f"❌ Error: Video file not found: {video_path}")
            return
        
        video_path = self.validate_and_repair_video(video_path)
        
        self.video_path = video_path
        self.video_label.setText(f"Loaded: {os.path.basename(video_path)}")
        
        self.cap = cv2.VideoCapture(video_path)
        
        if not self.cap.isOpened():
            print("❌ Error: Could not open video")
            return
        
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        if self.fps <= 0:
            self.fps = 30
        
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.video_duration = int((self.total_frames / self.fps) * 1000)
        
        # Load audio
        self.audio_loaded = False
        try:
            temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_audio_path = temp_audio.name
            temp_audio.close()
            
            ffmpeg_cmd = [
                'ffmpeg', '-i', video_path, '-vn', '-acodec', 'pcm_s16le',
                '-ar', '44100', '-ac', '2', '-y', temp_audio_path
            ]
            
            subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=30)
            pygame.mixer.music.load(temp_audio_path)
            self.audio_loaded = True
            self.temp_audio_file = temp_audio_path
        except:
            self.audio_loaded = False
        
        self.play_btn.setEnabled(True)
        self.backward_btn.setEnabled(True)
        self.forward_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        
        self.split_timeline.setDuration(self.video_duration)
        self.split_timeline.generateThumbnailsFromFile(video_path, self.video_duration, self.fps)
        
        self.split_add_btn.setEnabled(True)
        for sb in (self.split_start_min, self.split_start_sec, self.split_end_min, self.split_end_sec):
            sb.setEnabled(True)
        
        if hasattr(self, "on_splits_updated"):
            self.on_splits_updated(self.split_timeline.splits)
        
        self.current_frame = 0
        self.is_playing = False
        self.display_frame()

    # -------------------------------------------------------------------------
    # Video + Audio Handling
    # -------------------------------------------------------------------------
    def upload_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "",
            "Video Files (*.mp4 *.avi *.mkv *.mov *.flv *.wmv)"
        )

        if not file_path:
            return

        if self.audio_loaded:
            pygame.mixer.music.stop()

        if self.cap:
            self.cap.release()

        self.video_path = file_path
        self.video_label.setText(f"Loaded: {os.path.basename(file_path)}")

        self.cap = cv2.VideoCapture(file_path)

        if not self.cap.isOpened():
            print("❌ Error: Could not open video")
            return

        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        if self.fps <= 0:
            self.fps = 30

        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.video_duration = int((self.total_frames / self.fps) * 1000)

        # AUDIO via ffmpeg
        self.audio_loaded = False
        try:
            temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_audio_path = temp_audio.name
            temp_audio.close()

            ffmpeg_cmd = [
                'ffmpeg',
                '-i', file_path,
                '-vn',
                '-acodec', 'pcm_s16le',
                '-ar', '44100',
                '-ac', '2',
                '-y',
                temp_audio_path
            ]

            subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=30)

            pygame.mixer.music.load(temp_audio_path)
            self.audio_loaded = True
            self.temp_audio_file = temp_audio_path
            print("✔ Video loaded with audio (extracted)")

        except FileNotFoundError:
            try:
                pygame.mixer.music.load(file_path)
                self.audio_loaded = True
                print("✔ Video loaded with audio (direct)")
            except:
                self.audio_loaded = False
                print("⚠ Video loaded (Install FFmpeg for audio support)")
        except Exception as e:
            self.audio_loaded = False
            print(f"⚠ Video loaded (Audio error: {str(e)})")


        self.play_btn.setEnabled(True)
        self.backward_btn.setEnabled(True)
        self.forward_btn.setEnabled(True)
        self.save_btn.setEnabled(True)

        self.split_timeline.setDuration(self.video_duration)
        self.split_timeline.generateThumbnailsFromFile(file_path, self.video_duration, self.fps)

        self.split_add_btn.setEnabled(True)
        for sb in (self.split_start_min, self.split_start_sec,
                   self.split_end_min, self.split_end_sec):
            sb.setEnabled(True)

        if hasattr(self, "on_splits_updated"):
            self.on_splits_updated(self.split_timeline.splits)
        else:
            splits = self.split_timeline.splits
            if splits:
                start_ms, end_ms = splits[0]
                self.split_start_min.setValue((start_ms // 1000) // 60)
                self.split_start_sec.setValue((start_ms // 1000) % 60)
                self.split_end_min.setValue((end_ms // 1000) // 60)
                self.split_end_sec.setValue((end_ms // 1000) % 60)

        self.current_frame = 0
        self.is_playing = False

        self.display_frame()

    def validate_and_repair_video(self, video_path):
        """Re-encode video to fix corruption issues"""
        import subprocess
        import tempfile
        
        try:
            # Create temp file for repaired video
            temp_dir = tempfile.gettempdir()
            repaired_path = os.path.join(temp_dir, f"Trimmed_{os.path.basename(video_path)}")
            
            print(f"🔧 Repairing video file...")
            
            # Re-encode with FFmpeg to fix issues
            cmd = [
                'ffmpeg',
                '-err_detect', 'ignore_err',  # Ignore errors
                '-i', video_path,
                '-c:v', 'libx264',  # Re-encode video
                '-preset', 'fast',
                '-c:a', 'aac',  # Re-encode audio
                '-y',  # Overwrite
                repaired_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if os.path.exists(repaired_path) and os.path.getsize(repaired_path) > 0:
                print(f"✅ Video repaired successfully")
                return repaired_path
            else:
                print(f"⚠️ Repair failed, using original")
                return video_path
                
        except Exception as e:
            print(f"⚠️ Video repair error: {e}, using original")
            return video_path

    # -------------------------------------------------------------------------
    # Playback
    # -------------------------------------------------------------------------
    def display_frame(self):
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                return

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            target_w = self.video_display.width()
            target_h = self.video_display.height()

            scale = min(target_w / w, target_h / h)
            nw, nh = int(w * scale), int(h * scale)

            frame = cv2.resize(frame, (nw, nh))
            qimg = QImage(frame.data, nw, nh, ch * nw, QImage.Format_RGB888)
            self.video_display.setPixmap(QPixmap.fromImage(qimg))

    def update_frame(self):
        if self.cap and self.is_playing:
            self.current_frame += 1
            current_ms = int((self.current_frame / self.fps) * 1000)

            if current_ms >= self.video_duration:
                self.stop_playback()
                return

            self.time_label.setText(
                f"{self.format_time(current_ms)} / {self.format_time(self.video_duration)}"
            )

            self.split_timeline.setPlayheadPosition(current_ms)

            self.display_frame()

    def stop_playback(self):
        self.is_playing = False
        self.timer.stop()
        if self.audio_loaded:
            pygame.mixer.music.stop()
        self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def pause_for_seek(self):
        self.was_playing_before_seek = self.is_playing
        if self.is_playing:
            self.is_playing = False
            self.timer.stop()
            if self.audio_loaded:
                pygame.mixer.music.pause()

    def resume_after_seek(self):
        if self.was_playing_before_seek:
            current_ms = int((self.current_frame / self.fps) * 1000)
            self.current_frame = int((current_ms / 1000) * self.fps)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)

            if self.audio_loaded:
                pygame.mixer.music.stop()
                pygame.mixer.music.play(start=current_ms / 1000.0)

            self.is_playing = True
            self.timer.start(int(1000 / self.fps))
            self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
            self.display_frame()

    def set_position(self, pos):
        if self.cap:
            self.current_frame = int((pos / 1000) * self.fps)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
            self.time_label.setText(
                f"{self.format_time(pos)} / {self.format_time(self.video_duration)}"
            )

            self.split_timeline.setPlayheadPosition(pos)

            self.display_frame()

    def play_pause(self):
        if not self.cap or not self.cap.isOpened():
            return

        if self.is_playing:
            self.is_playing = False
            self.timer.stop()
            if self.audio_loaded:
                pygame.mixer.music.pause()
            self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        else:
            current_ms = int((self.current_frame / self.fps) * 1000)
            if self.audio_loaded:
                try:
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.unpause()
                    else:
                        pygame.mixer.music.play(start=current_ms / 1000.0)
                except Exception as e:
                    print("Audio playback error:", e)

            self.is_playing = True
            self.timer.start(int(1000 / self.fps))
            self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))

    # -------------------------------------------------------------------------
    # Utils
    # -------------------------------------------------------------------------
    def format_time(self, ms):
        ms = int(ms)
        s = ms // 1000
        m = s // 60
        s = s % 60
        m = int(m)
        s = int(s)
        return f"{m:02d}:{s:02d}"

    # Save JSON
    def save_timestamps(self):
        # Load existing JSON if it exists
        json_file = "split_timestamps.json"
        
        if os.path.exists(json_file):
            try:
                with open(json_file, "r") as f:
                    existing_data = json.load(f)
            except:
                existing_data = {"videos": []}
        else:
            existing_data = {"videos": []}
        
        # Ensure 'videos' key exists
        if "videos" not in existing_data:
            existing_data = {"videos": existing_data}  # Wrap old format
        
        # Create new video entry
        video_data = {
            "video_path": self.video_path,
            "video_name": os.path.basename(self.video_path),
            "splits": {}
        }
        
        for i, (start, end) in enumerate(self.splits, start=1):
            video_data["splits"][f"split_{i}"] = {
                "start_ms": start,
                "end_ms": end,
                "start_split": self.format_time(start),
                "end_split": self.format_time(end),
            }
        
        # Check if video already exists in JSON (update instead of duplicate)
        video_exists = False
        for idx, existing_video in enumerate(existing_data["videos"]):
            if existing_video.get("video_path") == self.video_path:
                existing_data["videos"][idx] = video_data  # Update existing
                video_exists = True
                break
        
        if not video_exists:
            existing_data["videos"].append(video_data)  # Add new
        
        # Save back to file
        with open(json_file, "w") as f:
            json.dump(existing_data, f, indent=4)

        # Show success message
        print(f"✔ Saved split data for {os.path.basename(self.video_path)}")
        print(f"   Total videos in JSON: {len(existing_data['videos'])}")
        
        # Show popup and close window
        QMessageBox.information(
            self, 
            "Success", 
            f"Split timestamps saved successfully!\n\nVideo: {os.path.basename(self.video_path)}\nSplits: {len(self.splits)}"
        )
        
        # Close the trimmer window
        self.accept()

    def closeEvent(self, event):
        if self.audio_loaded:
            pygame.mixer.music.stop()
        if self.cap:
            self.cap.release()

        if self.temp_audio_file:
            try:
                os.remove(self.temp_audio_file)
            except:
                pass

        pygame.mixer.quit()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoTrimmer()
    window.show()
    sys.exit(app.exec_())
