from PyQt6 import QtCore, QtGui, QtWidgets
from educ.headers import HeaderView
from ui.StyledWidget import fromStyle

class Table(QtWidgets.QScrollArea):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setUi()
        self.setObjectName("Table")
        self.setStyleSheet(fromStyle("Table"))
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)       
    
    def setUi(self):
        self.setWidgetResizable(True)
        self.grid_widget = GridWidget(self)
        self.grid_widget.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)  
        self.grid_widget.setContentsMargins(0, 0, 0, 0)
        self.grid_widget.resized.connect(self.on_resized)

        self.grid = QtWidgets.QGridLayout(self)
        self.grid.setContentsMargins(1, 1, 0, 0)
        self.grid.setSpacing(0)
        self.grid.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.grid_widget.setLayout(self.grid)
        self.setWidget(self.grid_widget)

        self.margins = QtCore.QMargins(30, 30, 0, 0)
        self.setViewportMargins(self.margins)

        self.sa_hheaders = QtWidgets.QScrollArea(self)
        self.sa_hheaders.setWidgetResizable(True)
        self.sa_hheaders.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)        
        self.sa_hheaders.horizontalScrollBar().setStyleSheet("QScrollBar {width:0px;}")
        self.sa_hheaders.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.sa_hheaders.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)

        self.hheaders = HeaderView(QtCore.Qt.Orientation.Horizontal, self)
        self.hheaders.setDefaultSectionSize(100)
        self.hheaders.setAutoFillBackground(True)
        self.hheaders.setSectionsMovable(True)
        self.hheaders.setMinimumSectionSize(100)
        self.hheaders.setMaximumHeight(30)
        self.sa_hheaders.setWidget(self.hheaders)

        self.sa_vheaders = QtWidgets.QScrollArea(self)
        self.sa_vheaders.setWidgetResizable(True)
        self.sa_vheaders.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.sa_vheaders.verticalScrollBar().setStyleSheet("QScrollBar {height:0px;}")
        self.sa_vheaders.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.sa_vheaders.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)

        self.vheaders = HeaderView(QtCore.Qt.Orientation.Vertical,  self)
        self.vheaders.setAutoFillBackground(True)
        self.vheaders.setSectionsMovable(True)
        self.vheaders.setDefaultSectionSize(30)
        self.vheaders.setMinimumSectionSize(30)
        self.vheaders.setMaximumWidth(30)
        self.vheaders.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Fixed)

        self.sa_vheaders.setWidget(self.vheaders)

        self.horizontalScrollBar().valueChanged.connect(self.on_scroll_bar_moved)
        self.verticalScrollBar().valueChanged.connect(self.on_scroll_bar_moved)

    def on_resized(self) -> None:
        self.hheaders.setMinimumWidth(self.grid_widget.width())
        self.vheaders.setMinimumHeight(self.grid_widget.height())
        self.updateGeometry()

    def on_scroll_bar_moved(self) -> None:
        self.sa_hheaders.horizontalScrollBar().setValue(self.horizontalScrollBar().value())
        self.sa_vheaders.verticalScrollBar().setValue(self.verticalScrollBar().value())

    def scrollContentsBy(self, dx: int, dy: int) -> None:
        self.hheaders.scrollDirtyRegion(dx, 0)
        self.vheaders.scrollDirtyRegion(0, dy)
        super().scrollContentsBy(dx, dy)

    def resizeEvent(self, a0: QtGui.QResizeEvent | None) -> None:
        rect = self.viewport().geometry()
        self.sa_hheaders.setGeometry(
            rect.x() +1, rect.y() - self.margins.top(), rect.width(), self.margins.top()
        )
        self.sa_vheaders.setGeometry(
            rect.x()  - self.margins.left(), rect.y() + 1, self.margins.left(), rect.height()
        )
        super().resizeEvent(a0)

class GridWidget(QtWidgets.QWidget):
    resized = QtCore.pyqtSignal(int, int)
    resized2 = QtCore.pyqtSignal()

    def resizeEvent(self, event: QtGui.QResizeEvent | None) -> None:
        super().resizeEvent(event)
        self.resized.emit(self.width(), self.height())
        self.resized2.emit()


class CellWidget(QtWidgets.QFrame):
    resized = QtCore.pyqtSignal()
    selected = QtCore.pyqtSignal(QtWidgets.QFrame)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setUi()
        self.setObjectName("CellWidget")
        self.setProperty("selected", False)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.MinimumExpanding)
        self.setBaseSize(100, 30)

    def setUi(self) -> None:
        self.element_layout = QtWidgets.QVBoxLayout(self)
        self.element_layout.setContentsMargins(3, 3, 3, 3)
        self.element_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.element_layout)

        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)

    def sizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(100, 30)

