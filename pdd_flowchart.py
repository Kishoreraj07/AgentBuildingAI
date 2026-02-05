import sys
import json
from PyQt5.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene, QGraphicsPolygonItem,
    QGraphicsEllipseItem, QGraphicsRectItem, QGraphicsLineItem,
    QGraphicsTextItem, QMainWindow, QAction, QMenu, QInputDialog,
    QGraphicsItem, QWidget, QVBoxLayout, QToolButton, QFrame,
    QFileDialog, QMessageBox, QColorDialog,QGraphicsPathItem
)
from PyQt5.QtGui import (
    QPen, QBrush, QColor, QFont, QPolygonF, QPainterPath,
    QCursor, QPainter, QIcon, QPixmap, QPainterPathStroker
)
from PyQt5.QtCore import Qt, QPointF, QLineF, QSize, QRectF
import math
from PyQt5.QtWidgets import QGraphicsPathItem
from PyQt5.QtGui import QPen, QBrush, QColor, QPainterPath, QFont, QPainterPathStroker, QPolygonF
from PyQt5.QtCore import Qt, QPointF, QLineF, QRectF

 
# ================================================================
# FlowNode – Resizable with perfect text centering
# ================================================================
class FlowNode(QGraphicsItem):
    Rectangle, RoundedRect, Circle, Diamond, Parallelogram, Terminator = range(6)
    _next_id = 0
 
    def __init__(self, node_type=Rectangle, text="Step", pos=QPointF(100, 100)):
        super().__init__()
        self.node_id = FlowNode._next_id
        FlowNode._next_id += 1
        self.font_size = 15           # NEW
        self.font_weight = "bold"     # NEW
 
        self.node_type = node_type
        self.setPos(pos)
        self.width = 220
        self.height = 90
        self.min_width = 80
        self.min_height = 50
        self.max_width = 600
        self.max_height = 350
 
        # Custom colors
        self.border_color = QColor("#1976D2")
        self.fill_color = QColor("#E3F2FD")
        self.selected_border_color = QColor("#0D47A1")
        self.selected_fill_color = QColor("#BBDEFB")
 
       # Text with better formatting
        self.text_item = QGraphicsTextItem(text, self)
        self.text_item.setDefaultTextColor(Qt.black)

        # ===== UPDATED: Use dynamic font size and weight =====
        font = QFont("Arial", self.font_size)
        if self.font_weight == "bold":
            font.setWeight(QFont.Bold)
        self.text_item.setFont(font)
        # ====================================================

        self.text_item.setTextInteractionFlags(Qt.NoTextInteraction)
 
        self.connections = []
        
        # Resize handle properties
        self.handle_size = 8
        self.resize_handle = None  # Will store handle rect
        self.is_resizing = False
        self.resize_start_pos = None
        self.resize_start_size = None
 
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges |
            QGraphicsItem.ItemIsFocusable
        )
        self.setAcceptHoverEvents(True)
        self.update_shape()
    def update_text_font(self):
        """Update text item font based on font_size and font_weight"""
        if hasattr(self, 'text_item'):
            font = QFont("Arial", self.font_size)
            
            if self.font_weight == "bold":
                font.setWeight(QFont.Bold)
            else:
                font.setWeight(QFont.Normal)
            
            self.text_item.setFont(font)
 
    def update_shape(self):
        path = QPainterPath()
 
        if self.node_type == self.Rectangle:
            path.addRect(-self.width/2, -self.height/2, self.width, self.height)
 
        elif self.node_type == self.RoundedRect:
            path.addRoundedRect(-self.width/2, -self.height/2, self.width, self.height, 20, 20)
 
        elif self.node_type == self.Circle:
            size = max(self.width, self.height)
            path.addEllipse(-size/2, -size/2, size, size)
            self.width = self.height = size
 
        elif self.node_type == self.Diamond:
            poly = QPolygonF([
                QPointF(0, -self.height/2),
                QPointF(self.width/2, 0),
                QPointF(0, self.height/2),
                QPointF(-self.width/2, 0),
                QPointF(0, -self.height/2)
            ])
            path.addPolygon(poly)
            path.closeSubpath()
 
        elif self.node_type == self.Parallelogram:
            skew = min(20, self.width * 0.15)
            poly = QPolygonF([
                QPointF(-self.width/2 + skew, -self.height/2),
                QPointF(self.width/2, -self.height/2),
                QPointF(self.width/2 - skew, self.height/2),
                QPointF(-self.width/2, self.height/2),
                QPointF(-self.width/2 + skew, -self.height/2)
            ])
            path.addPolygon(poly)
            path.closeSubpath()
 
        elif self.node_type == self.Terminator:
            path.addRoundedRect(-self.width/2, -self.height/2,
                                self.width, self.height,
                                self.height/2, self.height/2)
 
        self.shape_path = path
        
        # Update resize handle position (bottom-right corner)
        self.resize_handle = QRectF(
            self.width/2 - self.handle_size,
            self.height/2 - self.handle_size,
            self.handle_size * 2,
            self.handle_size * 2
        )
        
        # Update text - IMPROVED CENTERING
        self.update_text_position()
 
    def update_text_position(self):
        """Improved text centering"""
        # Set text width with padding
        text_width = self.width - 30
        if text_width < 40:
            text_width = 40
        
        self.text_item.setTextWidth(text_width)
        
        # Apply center alignment
        doc = self.text_item.document()
        option = doc.defaultTextOption()
        option.setAlignment(Qt.AlignCenter)
        doc.setDefaultTextOption(option)
        
        # Force update
        self.text_item.adjustSize()
        
        # Calculate center position
        text_rect = self.text_item.boundingRect()
        x = -text_rect.width() / 2
        y = -text_rect.height() / 2
        
        self.text_item.setPos(x, y)
 
    def boundingRect(self):
        extra = 10
        return self.shape_path.boundingRect().adjusted(-extra, -extra, extra, extra)
 
    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        
        pen = QPen(self.selected_border_color if self.isSelected() else self.border_color,
                   3 if self.isSelected() else 2)
        brush = QBrush(self.selected_fill_color if self.isSelected() else self.fill_color)
 
        painter.setPen(pen)
        painter.setBrush(brush)
        painter.drawPath(self.shape_path)
        
        # Draw resize handle when selected
        if self.isSelected():
            painter.setPen(QPen(QColor("#2196F3"), 2))
            painter.setBrush(QBrush(QColor("#FFFFFF")))
            painter.drawEllipse(self.resize_handle)
 
    def hoverMoveEvent(self, event):
        if self.isSelected() and self.resize_handle.contains(event.pos()):
            self.setCursor(Qt.SizeFDiagCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        super().hoverMoveEvent(event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.isSelected():
            if self.resize_handle and self.resize_handle.contains(event.pos()):
                self.is_resizing = True
                self.resize_start_pos = event.pos()
                self.resize_start_size = (self.width, self.height)
                event.accept()
                return
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.is_resizing:
            delta = event.pos() - self.resize_start_pos
            
            # Calculate new size
            new_width = max(self.min_width, min(self.max_width, self.resize_start_size[0] + delta.x() * 2))
            new_height = max(self.min_height, min(self.max_height, self.resize_start_size[1] + delta.y() * 2))
            
            # Keep circle/diamond proportional
            if self.node_type == self.Circle:
                size = max(new_width, new_height)
                new_width = new_height = size
            
            self.width = new_width
            self.height = new_height
            
            self.prepareGeometryChange()
            self.update_shape()
            
            # Update connected arrows
            for arrow in self.connections:
                arrow.update_position()
            
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        if self.is_resizing:
            self.is_resizing = False
            self.resize_start_pos = None
            self.resize_start_size = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)
 
    def mouseDoubleClickEvent(self, event):
        parent_widget = None
        if self.scene() and self.scene().views():
            view = self.scene().views()[0]
            parent_widget = view.window()
        
        new_text, ok = QInputDialog.getText(
            parent_widget,
            "Edit Node", 
            "Enter text:",
            text=self.text_item.toPlainText()
        )
        if ok:
            self.text_item.setPlainText(new_text)
            self.update_text_position()
    def itemChange(self, change, value):
        # Get the flag, default to False if it doesn't exist
        is_being_moved = getattr(self, '_is_being_moved_by_group', False)
        
        if change == QGraphicsItem.ItemPositionChange and not is_being_moved:
            # Handle multi-node dragging
            if self.isSelected() and self.scene():
                selected_nodes = [item for item in self.scene().selectedItems() 
                                if isinstance(item, FlowNode) and item != self 
                                and not getattr(item, '_is_being_moved_by_group', False)]
                if selected_nodes:
                    # Calculate movement delta
                    delta = value - self.pos()
                    
                    # Move all other selected nodes
                    for node in selected_nodes:
                        node._is_being_moved_by_group = True
                        node.setPos(node.pos() + delta)
                        # Update arrows for moved nodes
                        for arrow in node.connections:
                            arrow.update_position()
                        node._is_being_moved_by_group = False
        
        if change == QGraphicsItem.ItemPositionHasChanged:
            # Update arrows connected to this node
            for arrow in self.connections:
                arrow.update_position()
        
        return super().itemChange(change, value)
    
    def set_colors(self, border_color, fill_color):
        self.border_color = QColor(border_color)
        self.fill_color = QColor(fill_color)
        self.selected_border_color = self.border_color.darker(120)
        self.selected_fill_color = self.fill_color.darker(110)
        self.update()


# ================================================================\
# Arrow – grey color (customizable in future)\
# ================================================================\

class Arrow(QGraphicsPathItem):
    def __init__(self, start_node, end_node, waypoints=None, label=None):
        super().__init__()
        self.start_node = start_node
        self.end_node = end_node
        self.start_id = start_node.node_id
        self.end_id = end_node.node_id
        self.waypoints = waypoints or []
        self.label = label

        self.start_node.connections.append(self)
        self.end_node.connections.append(self)

        # Grey arrow styling
        self.setPen(QPen(QColor("#757575"), 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        self.setBrush(QBrush(QColor("#757575")))
        self.setZValue(-1)
        self.setFlag(QGraphicsPathItem.ItemIsSelectable, True)

        self.update_position()

    def update_position(self):
        """Draw path through waypoints with proper edge alignment"""
        if not self.start_node or not self.end_node:
            return

        path = QPainterPath()
        
        # Get node centers
        start_center = self.start_node.scenePos()
        end_center = self.end_node.scenePos()
        
        if not self.waypoints:
            # Direct connection - calculate edge points
            start_point = self.get_node_edge_point(self.start_node, start_center, end_center)
            end_point = self.get_node_edge_point(self.end_node, end_center, start_center)
            
            path.moveTo(start_point)
            path.lineTo(end_point)
        else:
            # Connection with waypoints
            # Calculate start edge point toward first waypoint
            first_waypoint = QPointF(self.waypoints[0]['x'], self.waypoints[0]['y'])
            start_point = self.get_node_edge_point(self.start_node, start_center, first_waypoint)
            
            path.moveTo(start_point)
            
            # Draw through all waypoints
            for wp in self.waypoints:
                path.lineTo(wp['x'], wp['y'])
            
            # Calculate end edge point from last waypoint
            last_waypoint = QPointF(self.waypoints[-1]['x'], self.waypoints[-1]['y'])
            end_point = self.get_node_edge_point(self.end_node, end_center, last_waypoint)
            
            path.lineTo(end_point)
        
        self.setPath(path)

    def get_node_edge_point(self, node, node_center, target_point):
        """
        Calculate the intersection point on the node's edge
        Works for all node shapes: Rectangle, Diamond, Circle, Terminator, Parallelogram
        """
        # Calculate direction vector
        dx = target_point.x() - node_center.x()
        dy = target_point.y() - node_center.y()
        
        # Prevent division by zero
        if abs(dx) < 0.001:
            dx = 0.001
        if abs(dy) < 0.001:
            dy = 0.001
        
        # Normalize direction
        length = math.sqrt(dx * dx + dy * dy)
        if length < 0.001:
            return node_center
        
        dx_norm = dx / length
        dy_norm = dy / length
        
        # Get node dimensions
        half_width = node.width / 2
        half_height = node.height / 2
        
        # Calculate intersection based on node type
        if node.node_type == 0:  # Rectangle
            # Calculate which edge the line intersects
            # t = distance along direction vector to reach edge
            t_x = half_width / abs(dx_norm) if abs(dx_norm) > 0.001 else float('inf')
            t_y = half_height / abs(dy_norm) if abs(dy_norm) > 0.001 else float('inf')
            t = min(t_x, t_y)
            
            edge_x = node_center.x() + dx_norm * t
            edge_y = node_center.y() + dy_norm * t
            return QPointF(edge_x, edge_y)
        
        elif node.node_type == 1:  # RoundedRect
            # Same as rectangle for simplicity
            t_x = half_width / abs(dx_norm) if abs(dx_norm) > 0.001 else float('inf')
            t_y = half_height / abs(dy_norm) if abs(dy_norm) > 0.001 else float('inf')
            t = min(t_x, t_y)
            
            edge_x = node_center.x() + dx_norm * t
            edge_y = node_center.y() + dy_norm * t
            return QPointF(edge_x, edge_y)
        
        elif node.node_type == 2:  # Circle
            # Circle radius
            radius = max(half_width, half_height)
            edge_x = node_center.x() + dx_norm * radius
            edge_y = node_center.y() + dy_norm * radius
            return QPointF(edge_x, edge_y)
        
        elif node.node_type == 3:  # Diamond
            # Diamond intersection calculation
            # Diamond vertices: top, right, bottom, left
            # Use line-line intersection with diamond edges
            angle = math.atan2(dy, dx)
            
            # Determine which diamond edge to intersect
            # Diamond has 4 edges at 45, 135, 225, 315 degrees
            if -math.pi/4 <= angle < math.pi/4:  # Right edge
                t = half_width / abs(dx_norm)
            elif math.pi/4 <= angle < 3*math.pi/4:  # Bottom edge
                t = half_height / abs(dy_norm)
            elif angle >= 3*math.pi/4 or angle < -3*math.pi/4:  # Left edge
                t = half_width / abs(dx_norm)
            else:  # Top edge
                t = half_height / abs(dy_norm)
            
            edge_x = node_center.x() + dx_norm * t
            edge_y = node_center.y() + dy_norm * t
            return QPointF(edge_x, edge_y)
        
        elif node.node_type == 4:  # Parallelogram
            # Treat as rectangle for edge calculation
            t_x = half_width / abs(dx_norm) if abs(dx_norm) > 0.001 else float('inf')
            t_y = half_height / abs(dy_norm) if abs(dy_norm) > 0.001 else float('inf')
            t = min(t_x, t_y)
            
            edge_x = node_center.x() + dx_norm * t
            edge_y = node_center.y() + dy_norm * t
            return QPointF(edge_x, edge_y)
        
        elif node.node_type == 5:  # Terminator (stadium/rounded)
            # Treat as rectangle with rounded ends
            t_x = half_width / abs(dx_norm) if abs(dx_norm) > 0.001 else float('inf')
            t_y = half_height / abs(dy_norm) if abs(dy_norm) > 0.001 else float('inf')
            t = min(t_x, t_y)
            
            edge_x = node_center.x() + dx_norm * t
            edge_y = node_center.y() + dy_norm * t
            return QPointF(edge_x, edge_y)
        
        # Default: return a point on the bounding box
        t_x = half_width / abs(dx_norm) if abs(dx_norm) > 0.001 else float('inf')
        t_y = half_height / abs(dy_norm) if abs(dy_norm) > 0.001 else float('inf')
        t = min(t_x, t_y)
        
        edge_x = node_center.x() + dx_norm * t
        edge_y = node_center.y() + dy_norm * t
        return QPointF(edge_x, edge_y)

    def paint(self, painter, option, widget=None):
        if not self.start_node or not self.end_node:
            return

        path = self.path()
        if path.isEmpty():
            return

        painter.setRenderHint(painter.Antialiasing)

        # Draw the path
        pen = QPen(QColor("#424242") if self.isSelected() else QColor("#757575"),
                   3.5 if self.isSelected() else 2.5,
                   Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        # Draw arrowhead at the end
        arrow_color = QColor("#424242") if self.isSelected() else QColor("#757575")
        self.draw_arrowhead(painter, path, arrow_color)

        # Draw label if present
        if self.label:
            self.draw_label(painter, path)

    def draw_arrowhead(self, painter, path, color):
        """Draw a clean arrowhead at the end of the path"""
        if path.length() < 1:
            return
        
        arrow_size = 12
        
        # Get the last point (end of arrow)
        end_point = path.pointAtPercent(1.0)
        
        # Get a point slightly before the end to determine direction
        if path.length() > 20:
            prev_point = path.pointAtPercent(path.percentAtLength(path.length() - 20))
        else:
            prev_point = path.pointAtPercent(0.0)
        
        # Calculate angle
        dx = end_point.x() - prev_point.x()
        dy = end_point.y() - prev_point.y()
        angle = math.atan2(dy, dx)
        
        # Calculate arrowhead points
        arrow_angle = math.pi / 6  # 30 degrees
        
        # Left point of arrowhead
        left_x = end_point.x() - arrow_size * math.cos(angle - arrow_angle)
        left_y = end_point.y() - arrow_size * math.sin(angle - arrow_angle)
        
        # Right point of arrowhead
        right_x = end_point.x() - arrow_size * math.cos(angle + arrow_angle)
        right_y = end_point.y() - arrow_size * math.sin(angle + arrow_angle)
        
        # Draw filled arrowhead
        arrow_polygon = QPolygonF([
            end_point,
            QPointF(left_x, left_y),
            QPointF(right_x, right_y)
        ])
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawPolygon(arrow_polygon)

    def draw_label(self, painter, path):
        """Draw label text (YES/NO/SKIP) on the arrow"""
        if path.length() < 20:
            return
        
        # Position label at 40% of path length (closer to start)
        mid_point = path.pointAtPercent(0.4)
        
        # Setup text drawing
        painter.setPen(QPen(QColor("#000000")))
        painter.setFont(QFont("Arial", 9, QFont.Bold))
        
        # Calculate text size
        font_metrics = painter.fontMetrics()
        text_width = font_metrics.horizontalAdvance(self.label)
        text_height = font_metrics.height()
        
        # Draw white background box
        padding = 4
        bg_rect = QRectF(
            mid_point.x() - text_width/2 - padding,
            mid_point.y() - text_height/2 - padding,
            text_width + padding * 2,
            text_height + padding * 2
        )
        
        painter.setPen(QPen(QColor("#E0E0E0"), 1))
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawRoundedRect(bg_rect, 3, 3)
        
        # Draw text
        painter.setPen(QPen(QColor("#000000")))
        painter.drawText(bg_rect, Qt.AlignCenter, self.label)

    def shape(self):
        """Make selection area wider"""
        stroker = QPainterPathStroker()
        stroker.setWidth(15)
        return stroker.createStroke(self.path())

# ================================================================
# ResizableLine – draggable endpoints like Miro
# ================================================================
class ResizableLine(QGraphicsItem):
    Line, ArrowShape = range(2)
    _next_id = 0
    
    def __init__(self, line_type=Line, start_pos=QPointF(100, 100), end_pos=QPointF(300, 100)):
        super().__init__()
        self.line_id = ResizableLine._next_id
        ResizableLine._next_id += 1
        
        self.line_type = line_type
        self.start_pos = start_pos
        self.end_pos = end_pos
        
        # Colors
        self.line_color = QColor("#757575")  # Changed from "#1976D2"
        self.selected_color = QColor("#424242")
        
        # Handle properties
        self.handle_radius = 8
        self.dragging_handle = None  # 'start', 'end', or None
        self.hover_handle = None
        
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges |
            QGraphicsItem.ItemIsFocusable
        )
        self.setAcceptHoverEvents(True)
        self.setZValue(-0.5)
        
    def boundingRect(self):
        x1, y1 = self.start_pos.x(), self.start_pos.y()
        x2, y2 = self.end_pos.x(), self.end_pos.y()
        
        extra = 25
        return QRectF(
            min(x1, x2) - extra,
            min(y1, y2) - extra,
            abs(x2 - x1) + 2 * extra,
            abs(y2 - y1) + 2 * extra
        )
    
    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw the line
        color = self.selected_color if self.isSelected() else self.line_color
        pen = QPen(color, 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        
        line = QLineF(self.start_pos, self.end_pos)
        painter.drawLine(line)
        
        # Draw arrowhead if arrow type
        if self.line_type == self.ArrowShape and line.length() > 0:
            arrow_size = 16
            
            dx = arrow_size * (line.dx() / line.length())
            dy = arrow_size * (line.dy() / line.length())
            perp_x = -dy * 0.4
            perp_y = dx * 0.4
            
            end = self.end_pos
            arrow_p1 = QPointF(end.x() - dx + perp_x, end.y() - dy + perp_y)
            arrow_p2 = QPointF(end.x() - dx - perp_x, end.y() - dy - perp_y)
            
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawPolygon(QPolygonF([end, arrow_p1, arrow_p2]))
        
        # Draw handles when selected
        if self.isSelected():
            handle_color = QColor("#2196F3")
            handle_hover = QColor("#FF9800")
            painter.setPen(QPen(Qt.white, 2))
            
            # Start handle
            painter.setBrush(QBrush(handle_hover if self.hover_handle == 'start' else handle_color))
            painter.drawEllipse(self.start_pos, self.handle_radius, self.handle_radius)
            
            # End handle
            painter.setBrush(QBrush(handle_hover if self.hover_handle == 'end' else handle_color))
            painter.drawEllipse(self.end_pos, self.handle_radius, self.handle_radius)
    
    def shape(self):
        path = QPainterPath()
        path.moveTo(self.start_pos)
        path.lineTo(self.end_pos)
        stroker = QPainterPathStroker()
        stroker.setWidth(15)
        return stroker.createStroke(path)
    
    def hoverMoveEvent(self, event):
        if self.isSelected():
            pos = event.pos()
            if self.is_near_point(pos, self.start_pos, 12):
                self.hover_handle = 'start'
                self.setCursor(Qt.SizeAllCursor)
            elif self.is_near_point(pos, self.end_pos, 12):
                self.hover_handle = 'end'
                self.setCursor(Qt.SizeAllCursor)
            else:
                self.hover_handle = None
                self.setCursor(Qt.ArrowCursor)
            self.update()
        super().hoverMoveEvent(event)
    
    def hoverLeaveEvent(self, event):
        self.hover_handle = None
        self.setCursor(Qt.ArrowCursor)
        self.update()
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.isSelected():
            pos = event.pos()
            
            # Check if clicking on handles
            if self.is_near_point(pos, self.start_pos, 12):
                self.dragging_handle = 'start'
                event.accept()
                return
            elif self.is_near_point(pos, self.end_pos, 12):
                self.dragging_handle = 'end'
                event.accept()
                return
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.dragging_handle:
            # Get scene position
            scene_pos = self.mapToScene(event.pos())
            local_pos = self.mapFromScene(scene_pos)
            
            if self.dragging_handle == 'start':
                self.start_pos = local_pos
            elif self.dragging_handle == 'end':
                self.end_pos = local_pos
            
            self.prepareGeometryChange()
            self.update()
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        if self.dragging_handle:
            self.dragging_handle = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def is_near_point(self, pos, point, threshold=10):
        """Check if position is near a point"""
        dx = pos.x() - point.x()
        dy = pos.y() - point.y()
        return (dx * dx + dy * dy) <= threshold * threshold
    
    def set_color(self, color):
        self.line_color = QColor(color)
        self.selected_color = self.line_color.darker(120)
        self.update()



class ArrowItem(QGraphicsLineItem):
    def __init__(self, start, end):
        super().__init__()
        self.setLine(QLineF(start, end))
        self.setPen(QPen(QColor("#757575"), 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setZValue(-1)

    def paint(self, painter, option, widget=None):
        if not self.start_node or not self.end_node:
            return

        path = self.path()
        if path.isEmpty():
            return

        painter.setRenderHint(QPainter.Antialiasing)

        # Draw the path
        pen = QPen(QColor("#424242") if self.isSelected() else QColor("#757575"),
                3.5 if self.isSelected() else 2.5,
                Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        # Draw arrowhead at the end
        arrow_color = QColor("#424242") if self.isSelected() else QColor("#757575")
        self.draw_arrowhead(painter, path, arrow_color)

        # Draw label if present
        if self.label:
            self.draw_label(painter, path)

    def draw_arrowhead(self, painter, path, color):
        """Draw a clean arrowhead at the end of the path"""
        if path.length() < 1:
            return
        
        arrow_size = 12
        
        # Get the last point (end of arrow)
        end_point = path.pointAtPercent(1.0)
        
        # Get a point slightly before the end to determine direction
        if path.length() > 20:
            prev_point = path.pointAtPercent(path.percentAtLength(path.length() - 20))
        else:
            prev_point = path.pointAtPercent(0.0)
        
        # Calculate angle
        dx = end_point.x() - prev_point.x()
        dy = end_point.y() - prev_point.y()
        angle = math.atan2(dy, dx)
        
        # Calculate arrowhead points
        arrow_angle = math.pi / 6  # 30 degrees
        
        # Left point of arrowhead
        left_x = end_point.x() - arrow_size * math.cos(angle - arrow_angle)
        left_y = end_point.y() - arrow_size * math.sin(angle - arrow_angle)
        
        # Right point of arrowhead
        right_x = end_point.x() - arrow_size * math.cos(angle + arrow_angle)
        right_y = end_point.y() - arrow_size * math.sin(angle + arrow_angle)
        
        # Draw filled arrowhead
        arrow_polygon = QPolygonF([
            end_point,
            QPointF(left_x, left_y),
            QPointF(right_x, right_y)
        ])
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawPolygon(arrow_polygon)

    def draw_label(self, painter, path):
        """Draw label text (YES/NO/SKIP) on the arrow"""
        if path.length() < 20:
            return
        
        # Position label at 50% of path length
        mid_point = path.pointAtPercent(0.5)
        
        # Setup text drawing
        painter.setPen(QPen(QColor("#000000")))
        painter.setFont(QFont("Arial", 9, QFont.Bold))
        
        # Calculate text size
        font_metrics = painter.fontMetrics()
        text_width = font_metrics.horizontalAdvance(self.label)
        text_height = font_metrics.height()
        
        # Draw white background box
        padding = 4
        bg_rect = QRectF(
            mid_point.x() - text_width/2 - padding,
            mid_point.y() - text_height/2 - padding,
            text_width + padding * 2,
            text_height + padding * 2
        )
        
        painter.setPen(QPen(QColor("#E0E0E0"), 1))
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawRoundedRect(bg_rect, 3, 3)
        
        # Draw text
        painter.setPen(QPen(QColor("#000000")))
        painter.drawText(bg_rect, Qt.AlignCenter, self.label)



# ================================================================\
# Custom View – connection logic + zoom + pan + grid\
# ================================================================\
class FlowView(QGraphicsView):
    def __init__(self, scene, editor):
        super().__init__(scene)
        self.editor = editor
        self.press_pos = None
        self.is_dragging = False
        self.is_panning = False
        self.pan_start = None
        self.grid_mode = 0
        self.grid_size = 20
        self.setDragMode(QGraphicsView.NoDrag)
 
    def wheelEvent(self, event):
        old_pos = self.mapToScene(event.pos())
        factor = 1.15 if event.angleDelta().y() > 0 else 1/1.15
        self.scale(factor, factor)
        new_pos = self.mapToScene(event.pos())
        self.translate(new_pos.x() - old_pos.x(), new_pos.y() - old_pos.y())
 
    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        if self.grid_mode == 0:
            return
        left = int(rect.left()) - (int(rect.left()) % self.grid_size)
        top = int(rect.top()) - (int(rect.top()) % self.grid_size)
        if self.grid_mode == 1:
            painter.setPen(QPen(QColor("#CCCCCC"), 2))
            for x in range(left, int(rect.right()), self.grid_size):
                for y in range(top, int(rect.bottom()), self.grid_size):
                    painter.drawPoint(x, y)
        elif self.grid_mode == 2:
            painter.setPen(QPen(QColor("#DDDDDD"), 1))
            for x in range(left, int(rect.right()), self.grid_size):
                painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
            for y in range(top, int(rect.bottom()), self.grid_size):
                painter.drawLine(int(rect.left()), y, int(rect.right()), y)
 
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.press_pos = event.pos()
            self.is_dragging = False
            pos = self.mapToScene(event.pos())
            items = self.scene().items(pos)
            
            # If in line/arrow drawing mode, start drawing
            if self.editor.current_tool in ("line", "arrow"):
                self.editor.temp_line = QGraphicsLineItem()
                pen = QPen(QColor("#757575"), 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)  # Changed from "#1976D2"
                self.editor.temp_line.setPen(pen)
                self.editor.temp_line.setZValue(1000)
                self.scene().addItem(self.editor.temp_line)
                self.editor.temp_line.setLine(QLineF(pos, pos))
                return
            
            clicked_node = any(isinstance(i, FlowNode) or (i.parentItem() and isinstance(i.parentItem(), FlowNode)) for i in items)
            clicked_arrow = any(isinstance(i, (Arrow, ResizableLine)) for i in items)
            
            if clicked_arrow:
                super().mousePressEvent(event)
                return
            if not clicked_node:
                self.is_panning = True
                self.pan_start = event.pos()
                self.setCursor(Qt.ClosedHandCursor)
                return
        super().mousePressEvent(event)
    def mouseMoveEvent(self, event):
        # If drawing a line/arrow, update preview
        if self.editor.temp_line:
            start = self.editor.temp_line.line().p1()
            end = self.mapToScene(event.pos())
            self.editor.temp_line.setLine(QLineF(start, end))
            return
        
        if self.is_panning and self.pan_start:
            delta = event.pos() - self.pan_start
            self.pan_start = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            return
        if self.press_pos and (event.pos() - self.press_pos).manhattanLength() > 5:
            self.is_dragging = True
        super().mouseMoveEvent(event)
    def mouseReleaseEvent(self, event):
        # Handle line/arrow drawing completion
        if self.editor.temp_line:
            start_pos = self.editor.temp_line.line().p1()
            end_pos = self.mapToScene(event.pos())
            
            # Only create if line is long enough
            if (end_pos - start_pos).manhattanLength() > 10:
                line_type = ResizableLine.ArrowShape if self.editor.current_tool == "arrow" else ResizableLine.Line
                item = ResizableLine(line_type, start_pos, end_pos)
                self.scene().addItem(item)
            
            # Clean up
            self.scene().removeItem(self.editor.temp_line)
            self.editor.temp_line = None
            self.editor.set_tool("select")
            return
        
        if self.is_panning:
            self.is_panning = False
            self.pan_start = None
            self.setCursor(Qt.ArrowCursor)
            self.press_pos = None
            self.is_dragging = False
            return
 
        if event.button() == Qt.LeftButton and not self.is_dragging and self.editor.current_tool == "select":
            pos = self.mapToScene(event.pos())
            items = self.scene().items(pos)
            arrow = next((i for i in items if isinstance(i, (Arrow, ResizableLine))), None)
            node = next((i for i in items if isinstance(i, FlowNode)), None)
            if not node and items:
                parent = items[0].parentItem()
                if isinstance(parent, FlowNode):
                    node = parent
 
            if arrow:
                super().mouseReleaseEvent(event)
                return
 
            if node:
                if event.modifiers() & Qt.ShiftModifier:
                    self.editor.auto_arrange_from_node(node)
                elif self.editor.first_node is None:
                    self.editor.first_node = node
                    node.setSelected(True)
                else:
                    if node != self.editor.first_node:
                        arrow = Arrow(self.editor.first_node, node)
                        self.scene().addItem(arrow)
                    self.editor.first_node.setSelected(False)
                    self.editor.first_node = None
 
        self.press_pos = None
        self.is_dragging = False
        super().mouseReleaseEvent(event)
# ================================================================\
# Icon helper\
# ================================================================\
def create_text_icon(text, size=32, color="#333333"):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    font = QFont("Segoe UI Emoji", int(size * 0.6))
    painter.setFont(font)
    painter.setPen(QColor(color))
    painter.drawText(pixmap.rect(), Qt.AlignCenter, text)
    painter.end()
    return QIcon(pixmap)
 
 
# ================================================================\
# Main Editor\
# ================================================================\
class FlowchartEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Professional Flowchart Editor")
        self.setGeometry(100, 50, 1200, 800)
        
        # Tool state
        self.current_tool = "select"  # "select", "line", "arrow"
        self.temp_line = None
        
        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(QBrush(QColor("#F2F2F2")))
        self.view = FlowView(self.scene, self)
        self.view.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setCentralWidget(self.view)
 
        self.nodes = []
        self.first_node = None
 
        self.create_floating_toolbar()
    def create_floating_toolbar(self):
        """Create modern floating toolbar with icons"""
        self.node_types = {
            "Process (Rectangle)": FlowNode.Rectangle,
            "Decision (Diamond)": FlowNode.Diamond,
            "Start/End (Terminator)": FlowNode.Terminator,
            "Input/Output (Parallelogram)": FlowNode.Parallelogram,
            "Circle": FlowNode.Circle,
            "Rounded Rectangle": FlowNode.RoundedRect
        }
       
        # Main toolbar container (right side)
        toolbar_container = QWidget(self)
        toolbar_container.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: 16px;
                border: 1px solid rgba(0, 0, 0, 0.1);
            }
        """)
       
        # Use vertical layout for toolbar
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)
       
        button_style = """
            QToolButton {
                background-color: rgba(255, 255, 255, 0.7);
                border: 1px solid rgba(0, 0, 0, 0.15);
                border-radius: 12px;
                padding: 0px;
                min-width: 56px;
                max-width: 56px;
                min-height: 56px;
                max-height: 56px;
            }
            QToolButton:hover {
                background-color: rgba(227, 242, 253, 0.9);
                border-color: #2196F3;
            }
            QToolButton:pressed {
                background-color: #bbdefb;
            }
        """
       
        # Color picker button
        color_btn = QToolButton()
        color_btn.setIcon(create_text_icon("🎨", 28))
        color_btn.setIconSize(QSize(28, 28))
        color_btn.setToolTip("Change Node Color")
        color_btn.setStyleSheet(button_style)
        color_btn.clicked.connect(self.change_node_color)
        layout.addWidget(color_btn)
       
        # Delete button
        delete_btn = QToolButton()
        delete_btn.setIcon(create_text_icon("🗑️", 28))
        delete_btn.setIconSize(QSize(28, 28))
        delete_btn.setToolTip("Delete Selected")
        delete_btn.setStyleSheet(button_style)
        delete_btn.clicked.connect(self.delete_selected)
        layout.addWidget(delete_btn)
       
        # Grid toggle button
        self.grid_btn = QToolButton()
        self.grid_btn.setIcon(create_text_icon("◻️", 28))
        self.grid_btn.setIconSize(QSize(28, 28))
        self.grid_btn.setToolTip("Toggle Grid")
        self.grid_btn.setStyleSheet(button_style)
        self.grid_btn.clicked.connect(self.toggle_grid)
        layout.addWidget(self.grid_btn)
       
        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setStyleSheet("background-color: #e0e0e0; max-height: 1px;")
        layout.addWidget(separator2)
       
        # Save button
        save_btn = QToolButton()
        save_btn.setIcon(create_text_icon("💾", 28))
        save_btn.setIconSize(QSize(28, 28))
        save_btn.setToolTip("Save Flowchart")
        save_btn.setStyleSheet(button_style)
        save_btn.clicked.connect(self.save_flowchart)
        layout.addWidget(save_btn)
       
        # Load button
        load_btn = QToolButton()
        load_btn.setIcon(create_text_icon("📂", 28))
        load_btn.setIconSize(QSize(28, 28))
        load_btn.setToolTip("Load Flowchart")
        load_btn.setStyleSheet(button_style)
        load_btn.clicked.connect(self.load_flowchart)
        layout.addWidget(load_btn)
       
        layout.addStretch()
       
        toolbar_container.setLayout(layout)
       
        # Position toolbar in middle-right
        self.position_toolbar()
        toolbar_container.raise_()
        self.toolbar_container = toolbar_container
       
        # Create shape panel on the left
        self.create_left_shape_panel()
 
    def create_left_shape_panel(self):
        """Create permanent shape panel on the left side"""
        shape_container = QWidget(self)
        shape_container.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: 16px;
                border: 1px solid rgba(0, 0, 0, 0.1);
            }
        """)
       
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)
       
        button_style = """
            QToolButton {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                padding: 0px;
                min-width: 56px;
                max-width: 56px;
                min-height: 56px;
                max-height: 56px;
                font-size: 32px;
                font-family: "Segoe UI Symbol", "Arial";
            }
            QToolButton:hover {
                background-color: #f0f7ff;
                border-color: #2196F3;
            }
            QToolButton:pressed {
                background-color: #e3f2fd;
            }
            QToolButton:checked {
                background-color: #bbdefb;
                border-color: #1976D2;
                border-width: 3px;
            }
        """
       
        shapes = [
            ("▭", FlowNode.Rectangle, "Rectangle", None),
            ("◇", FlowNode.Diamond, "Decision", None),
            ("⬭", FlowNode.Terminator, "Start/End", None),
            ("▱", FlowNode.Parallelogram, "I/O", None),
            ("○", FlowNode.Circle, "Circle", None),
            ("▢", FlowNode.RoundedRect, "Rounded Rect", None),
            ("─", None, "Line Tool", "line"),
            ("→", None, "Arrow Tool", "arrow"),
        ]
        
        self.tool_buttons = []
       
        for icon, node_type, tooltip, tool in shapes:
            btn = QToolButton()
            btn.setText(icon)
            btn.setToolTip(tooltip)
            btn.setStyleSheet(button_style)
            btn.setCheckable(True)
            
            if tool:
                btn.clicked.connect(lambda checked, t=tool, b=btn: self.set_tool(t, b))
                self.tool_buttons.append((tool, btn))
            else:
                btn.clicked.connect(lambda _, t=node_type, txt=tooltip: self.add_node_and_select(t, txt))
            
            layout.addWidget(btn)
       
        shape_container.setLayout(layout)
        self.shape_container = shape_container
        self.position_shape_panel()
        shape_container.raise_()
    
    
    
    
    def set_tool(self, tool_name, button=None):
        """Switch between select, line, and arrow tools"""
        self.current_tool = tool_name
        
        # Uncheck all tool buttons
        for tool, btn in self.tool_buttons:
            btn.setChecked(tool == tool_name)
        
        # Clear selection and reset state
        self.scene.clearSelection()
        self.first_node = None
        
        # Update cursor
        if tool_name == "select":
            self.view.setCursor(Qt.ArrowCursor)
        else:
            self.view.setCursor(Qt.CrossCursor)
    
    def add_node_and_select(self, node_type, default_text):
        """Add a node and switch to select tool"""
        self.set_tool("select")
        center = self.view.mapToScene(self.view.viewport().rect().center())
        node = FlowNode(node_type, default_text, center)
        self.scene.addItem(node)
        self.nodes.append(node)
        node.setSelected(True)
    
    
    def position_toolbar(self):
        if hasattr(self, 'toolbar_container'):
            w, h = 72, 380
            self.toolbar_container.setGeometry(self.width() - w - 18, (self.height() - h)//2, w, h)
 
    def position_shape_panel(self):
        if hasattr(self, 'shape_container'):
            w, h = 80, 540  # Increased height for 8 buttons
            self.shape_container.setGeometry(18, (self.height() - h)//2, w, h)
 
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.position_toolbar()
        self.position_shape_panel()
 
    def toggle_grid(self):
        self.view.grid_mode = (self.view.grid_mode + 1) % 3
        icons = ["Grid Off", "Dot Grid", "Line Grid"]
        self.grid_btn.setIcon(create_text_icon(icons[self.view.grid_mode], 28))
        self.view.viewport().update()
 
    def add_node(self, node_type, default_text="Step"):
        node = FlowNode(node_type, default_text, QPointF(300, 200))
        self.scene.addItem(node)
        self.nodes.append(node)
 
    def change_node_color(self):
        selected = [i for i in self.scene.selectedItems() if isinstance(i, (FlowNode, ResizableLine))]
        if not selected:
            QMessageBox.information(self, "No Selection", "Select nodes or lines first.")
            return
        
        if isinstance(selected[0], FlowNode):
            border = QColorDialog.getColor(selected[0].border_color, self, "Border Color")
            if not border.isValid(): return
            fill = QColorDialog.getColor(selected[0].fill_color, self, "Fill Color")
            if not fill.isValid(): return
            
            for item in selected:
                if isinstance(item, FlowNode):
                    item.set_colors(border.name(), fill.name())
                elif isinstance(item, ResizableLine):
                    item.set_color(border.name())
        else:
            color = QColorDialog.getColor(selected[0].line_color, self, "Line Color")
            if not color.isValid(): return
            
            for item in selected:
                if isinstance(item, ResizableLine):
                    item.set_color(color.name())
    def delete_selected(self):
        for item in list(self.scene.selectedItems()):
            if isinstance(item, FlowNode):
                for arrow in list(item.connections):
                    self.scene.removeItem(arrow)
                self.scene.removeItem(item)
                self.nodes.remove(item)
            elif isinstance(item, (Arrow, ResizableLine)):
                if isinstance(item, Arrow):
                    if item in item.start_node.connections:
                        item.start_node.connections.remove(item)
                    if item in item.end_node.connections:
                        item.end_node.connections.remove(item)
                self.scene.removeItem(item)
    def auto_arrange_from_node(self, start_node):
        visited = set()
        levels = {}
        def dfs(node, level=0):
            if node in visited: return
            visited.add(node)
            levels.setdefault(level, []).append(node)
            for arrow in node.connections:
                if arrow.start_node == node:
                    dfs(arrow.end_node, level + 1)
        dfs(start_node)
 
        h_space, v_space = 220, 160
        for level, nodes in levels.items():
            y = start_node.scenePos().y() + level * v_space
            total_w = (len(nodes) - 1) * h_space
            x0 = start_node.scenePos().x() - total_w / 2
            for i, n in enumerate(nodes):
                n.setPos(x0 + i * h_space, y)
        for node in visited:
            for arrow in node.connections:
                arrow.update_position()
 
    def save_flowchart(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save", "", "JSON (*.json)")
        if not path: return
        data = {"nodes": [], "arrows": []}
        for node in self.nodes:
            data["nodes"].append({
                "id": node.node_id,
                "type": node.node_type,
                "text": node.text_item.toPlainText(),
                "x": node.scenePos().x(),
                "y": node.scenePos().y(),
                "width": node.width,
                "height": node.height,
                "border": node.border_color.name(),
                "fill": node.fill_color.name()
            })
        seen = set()
        for node in self.nodes:
            for arrow in node.connections:
                if isinstance(arrow, Arrow) and id(arrow) not in seen:
                    seen.add(id(arrow))
                    arrow_data = {
                        "start_id": arrow.start_id, 
                        "end_id": arrow.end_id
                    }
                    if arrow.waypoints:  # NEW: Save waypoints if present
                        arrow_data["waypoints"] = arrow.waypoints
                    if arrow.label:  # NEW: Save label if present
                        arrow_data["label"] = arrow.label
                    data["arrows"].append(arrow_data)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            QMessageBox.information(self, "Saved", f"Saved to {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
 
    def load_flowchart(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load", "", "JSON (*.json)")
        if not path: return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Cannot load: {e}")
            return
 
        self.scene.clear()
        self.nodes.clear()
        FlowNode._next_id = 0
        id_to_node = {}
 
        for nd in data.get("nodes", []):
            node = FlowNode(nd.get("type", 0), nd.get("text", "Node"),
                            QPointF(nd.get("x", 100), nd.get("y", 100)))
            node.node_id = nd["id"]
            if node.node_id >= FlowNode._next_id:
                FlowNode._next_id = node.node_id + 1
            node.width = nd.get("width", 160)
            node.height = nd.get("height", 70)
            node.set_colors(nd.get("border", "#1976D2"), nd.get("fill", "#E3F2FD"))
            node.update_shape()
            self.scene.addItem(node)
            self.nodes.append(node)
            id_to_node[node.node_id] = node
 
        for arr in data.get("arrows", []):
            s = id_to_node.get(arr["start_id"])
            e = id_to_node.get(arr["end_id"])
            if s and e:
                waypoints = arr.get("waypoints", [])  # NEW: Load waypoints
                label = arr.get("label", None)        # NEW: Load label
                arrow = Arrow(s, e, waypoints, label)
                self.scene.addItem(arrow)
 
        QMessageBox.information(self, "Loaded", f"Loaded {path}")
 
 
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = FlowchartEditor()
    win.show()
    sys.exit(app.exec_())