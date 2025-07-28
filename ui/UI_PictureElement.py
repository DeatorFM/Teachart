from PyQt6 import QtWidgets, QtGui, QtCore

class PictureView:

    def setUi(self, agent: QtWidgets.QWidget):
        agent.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        agent.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
        agent.setObjectName("PictureElement")
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.main_layout.setContentsMargins(3,3,3,3)
        self.main_layout.setSpacing(0)

        self.piclabel = PictureLabel(self)
        self.piclabel.resized.connect(self.fitToPicture)
        self.main_layout.addWidget(self.piclabel)


        agent.setLayout(self.main_layout)

    def fitToPicture(self) -> None:
        self.setFixedSize(self.piclabel.width()+6, self.piclabel.height()+6)

class PictureLabel(QtWidgets.QLabel):
    resized = QtCore.pyqtSignal(int, int)
    forceRepaint = QtCore.pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setScaledContents(True)
        self.setObjectName("piclabel")

        self._resizing = False
        self._section = None
        self._points = QtCore.QPoint(0, 0)
        self._preview = None

        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        self.setStyleSheet("background: none;")

    def mouseMoveEvent(self, e: QtGui.QMouseEvent) -> None:
        # Execute Resize
        if self._resizing == False:
            self._section = self.updateCursor(e.pos())
        if e.buttons() == QtCore.Qt.MouseButton.LeftButton and self._section != None:
            self._resizing = True
            self.dragToResize(e.pos(), self._section)
            assert isinstance(self._preview, PreviewOverlay)
            self._preview.show()
            self.updateGeometry()
        super().mouseMoveEvent(e)

    def updateCursor(self, pos: QtCore.QPoint) -> str|None:
        x = self.mapToGlobal(QtCore.QPoint(0, 0)).x()
        y = self.mapToGlobal(QtCore.QPoint(0, 0)).y()
        if (pos.y() >= self.height()-5 and pos.y() <= self.height()) and (pos.x() >= self.width()-5 and pos.x() <= self.width()):
            self.setCursor(QtCore.Qt.CursorShape.SizeFDiagCursor)
            self._preview = PreviewOverlay(x, y, self)
            return "BottomRight"
        elif (pos.y() >= self.height()-5 and pos.y() <= self.height()):
            self.setCursor(QtCore.Qt.CursorShape.SizeVerCursor)
            self._preview = PreviewOverlay(x, y, self)
            return "Bottom"
        elif (pos.x() >= self.width()-5 and pos.x() <= self.width()):
            self.setCursor(QtCore.Qt.CursorShape.SizeHorCursor)
            self._preview = PreviewOverlay(x, y, self)
            return "Right"
        else:
            self.setCursor(QtCore.Qt.CursorShape.ArrowCursor)
            return None

    def dragToResize(self, pos: QtCore.QPoint, section: str) -> None:
        if section == "Right":
            newSizeX = self.width() + (pos.x() - self.width())
            newSize = QtCore.QSize(newSizeX, self.height())
        elif section == "Bottom":
            newSizeY = self.height() + (pos.y() - self.height())
            newSize = QtCore.QSize(self.width(), newSizeY)
        elif section == "BottomRight":
            newSizeX = self.width() + (pos.x() - self.width())
            newSizeY = self.height() + (pos.y() - self.height())
            newSize = QtCore.QSize(newSizeX, newSizeY)
        else: return
        if newSize.width() < 100:
            newSize.setWidth(100)
        if newSize.height() < 1:
            newSize.setHeight(1)
        assert isinstance(self._preview, PreviewOverlay)
        print(newSize)
        self._preview.setFixedSize(newSize)

    def mouseReleaseEvent(self, e: QtGui.QMouseEvent) -> None: 
        if e.button() == QtCore.Qt.MouseButton.LeftButton:
            self._resizing = False
            self._section = None
            if self._preview:
                w = self._preview.width()
                h = self._preview.height()
                self._preview.deleteLater()
                self._preview = None
                self.setFixedSize(w, h)
                self.resized.emit(w, h)
                self.forceRepaint.emit(w, h)

    def section(self) -> str|None:
        return self._section

class PreviewOverlay(QtWidgets.QWidget):
    def __init__(self, x: int, y: int, parent=None) -> None:
        super().__init__(parent)
        self.setWindowFlag(QtCore.Qt.WindowType.ToolTip, True)
        # self.setAttribute(QtCore.Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(0.4)
        self.setGeometry(x, y, parent.width(), parent.height())

    def paintEvent(self, e: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        # painter.setBackground(QtCore.Qt.GlobalColor.transparent)
        # painter.setPen(QtGui.QPen(QtCore.Qt.GlobalColor.black, 3, QtCore.Qt.PenStyle.DotLine))
        painter.drawRect(self.rect())


class CommentEdit(QtWidgets.QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.cursorPositionChanged.connect(self.fit_to_text)

    def sizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(self.parent().width(), 15)
    
    def fit_to_text(self) -> None:
        doc_height = self.document().size().height()
        if 0 <= doc_height:
            self.setMinimumHeight(int(doc_height)+20)