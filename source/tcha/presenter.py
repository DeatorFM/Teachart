from math import sqrt

from PyQt6.QtCore import QT_TR_NOOP as tr
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QPainter, QPainterPath, QPen, QPolygonF, QScreen
from PyQt6.QtWidgets import (
    QDialog,
    QGraphicsItem,
    QGraphicsScene,
    QGraphicsSceneMouseEvent,
    QGraphicsView,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from tcha.consts import CanvasTool
from tcha.error import StandardLogger


class ArrowPath(QPainterPath):
    def __init__(self, p1: QPointF, p2: QPointF, pen: QPen = QPen()):
        super().__init__()
        self.pen = pen
        self.pen.setWidthF(1.0)
        self.brush = QBrush(Qt.BrushStyle.SolidPattern)
        self.brush.setColor(self.pen.color())
        self.mode = QPainter.CompositionMode.CompositionMode_SourceOver

        # Sorry I'm bad at maths so I made an AI write the vector calculations for me

        # Draw line from p1 to p2
        self.moveTo(p1)
        self.lineTo(p2)

        # Calculate direction vector from p1 to p2
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        length = sqrt(dx**2 + dy**2)

        # If points are the same, just return (no arrow to draw)
        if length == 0:
            return

        # Normalize direction vector
        dx_norm = dx / length
        dy_norm = dy / length

        # Arrow head height (0.25 of the line length)
        arrow_height = length * 0.25

        # For equilateral triangle: side = 2 * height / sqrt(3)
        side_length = 2 * arrow_height / sqrt(3)

        # Calculate base center point (0.25 length back from p2)
        base_x = p2.x() - arrow_height * dx_norm
        base_y = p2.y() - arrow_height * dy_norm

        # Perpendicular vector (rotated 90 degrees counter-clockwise)
        perp_x = -dy_norm
        perp_y = dx_norm

        # Two base points of the triangle (half side length on each side)
        half_side = side_length / 2
        a1 = QPointF(base_x + half_side * perp_x, base_y + half_side * perp_y)
        a2 = QPointF(base_x - half_side * perp_x, base_y - half_side * perp_y)

        # Create equilateral triangle with p2 as the apex
        head = QPolygonF()
        head.append(p2)
        head.append(a1)
        head.append(a2)
        head.append(p2)

        self.addPolygon(head)


class FormattedLine(QPolygonF):
    def __init__(self):
        super().__init__()
        self.pen = QPen()
        self.mode = QPainter.CompositionMode.CompositionMode_SourceOver

    def contains(self, value: QPointF):
        return self.containsPoint(value, Qt.FillRule.OddEvenFill)


class PointerPen(QPen):
    def __init__(self):
        super().__init__()
        self.setWidthF(2.0)
        self.setColor(Qt.GlobalColor.red)


class CanvasScene(QGraphicsScene):
    def __init__(self):
        super().__init__()
        self._lines: list[FormattedLine | ArrowPath] = []

        self.pen = QPen()
        self.pen.setWidthF(3.0)
        self.pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.tool = CanvasTool.Pointer

        self._start = QPointF(0.0, 0.0)
        self._end = QPointF(0.0, 0.0)
        self._current_pos = QPointF(0.0, 0.0)

        self._painting = False

    @property
    def lines(self) -> list[QPolygonF]:
        return self._lines

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        # self._current_pos == event.scenePos()

        if event.buttons() == Qt.MouseButton.LeftButton:
            if self._painting:
                pointf = event.scenePos()

                if self.tool == CanvasTool.Pen and self._lines:
                    self._lines[-1].append(pointf)
                    self.update()
                elif self.tool == CanvasTool.Rubber:
                    for i, line in enumerate(self._lines):
                        if line.contains(pointf):
                            del self._lines[i]
                            break

                    self.update()

        event.accept()

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self._painting = bool(self.items())
            if self.tool == CanvasTool.Pen:
                new_line = FormattedLine()
                new_line.pen = QPen(self.pen)
                self._lines.append(new_line)
                pointf = event.scenePos()
                new_line.append(pointf)
            elif self.tool == CanvasTool.Arrow:
                self._start = event.scenePos()

        event.accept()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        self._painting = False
        self._eraser_path = None
        if self._start != event.scenePos():
            self._end = event.scenePos()
            if self.tool == CanvasTool.Arrow:
                path = ArrowPath(self._start, self._end, QPen(self.pen))
                self._lines.append(path)
                self.update()
        event.accept()

    def drawForeground(self, painter: QPainter, rect: QRectF):
        for line in self._lines:
            painter.setPen(line.pen)
            painter.setCompositionMode(line.mode)
            if isinstance(line, QPolygonF):
                painter.drawPolyline(line)
                continue
            painter.setBrush(line.brush)
            painter.drawPath(line)

        if self.tool == CanvasTool.Pointer:
            painter.setPen(PointerPen())
            painter.drawEllipse(self._current_pos, 2.0, 2.0)


class PresenterCanvas(QGraphicsView):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        scene = CanvasScene()
        self.setScene(scene)

        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing, True)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing, False)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)

    def change_item(self, item: QGraphicsItem):

        self.scene().lines.clear()
        self.scene().clear()
        self.scene().addItem(item)
        StandardLogger.debug(f"Changed current item to {item}", extra={"sender": "PRESENTERCANVAS"})

        self.rescale()

    def clear(self) -> None:
        self.scene().clear()

    def rescale(self) -> None:
        for item in self.scene().items():
            self.fitInView(item, Qt.AspectRatioMode.KeepAspectRatio)

    def set_color(self, button: QToolButton) -> None:
        color: Qt.GlobalColor = button.property("color")
        self.scene().pen.setColor(color)

    def set_tool(self, button: QToolButton) -> None:
        tool: CanvasTool = button.property("tool")
        self.scene().tool = tool

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.rescale()


class PresenterView(QDialog):
    def __init__(self, scene: QGraphicsScene, editor: "Editor", parent=None):
        super().__init__(parent, Qt.WindowType.Dialog)
        lo = QVBoxLayout(self)
        self._view = QGraphicsView(scene)
        self._my_editor = editor
        self.setWindowTitle(tr("Presentation View - Teachart"))
        lo.addWidget(self._view)
        self.setLayout(lo)
        self.rescale()

        self._view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self._view.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self._view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self._view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)
        self._view.setInteractive(False)

        self._view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scene.changed.connect(self.rescale)

    @property
    def scene(self) -> QGraphicsScene:
        return self.view.scene()

    @property
    def editor(self) -> "Editor":
        return self._my_editor

    @property
    def view(self) -> QGraphicsView:
        return self._view

    def rescale(self) -> None:
        for item in self.scene.items():
            self.view.fitInView(item, Qt.AspectRatioMode.KeepAspectRatio)

    def set_current_editor(self, editor: "Editor") -> None:
        self.my_editor = editor

    def showFullScreen(self):
        editor_screen: QScreen = self._my_editor.windowHandle().screen()
        other_screens = [s for s in editor_screen.virtualSiblings() if s != editor_screen]
        if other_screens:
            target_screen = other_screens[0]
            self.setGeometry(target_screen.geometry())
            super().showFullScreen()
            self.rescale()
