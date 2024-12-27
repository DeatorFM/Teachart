from PyQt6 import QtWidgets, QtGui, QtCore
from ui.UI_Commons import ColorMenu
from ui.StyledWidget import convertColors

class StyledHeaderItem(QtWidgets.QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("StyledHeaderItem")
        self.setUi()
        # self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.DefaultContextMenu)
        self.move(30, 30)

    def setUi(self) -> None:
        self.s_layout = QtWidgets.QStackedLayout(self)
        self.s_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.s_layout)
        
        font = QtGui.QFont()
        font.setBold(True)
        font.setPointSize(12)
        self.label = QtWidgets.QLabel(self)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.s_layout.addWidget(self.label)

        self.le_input = QtWidgets.QLineEdit(self)
        self.le_input.setObjectName("Input")
        self.s_layout.addWidget(self.le_input)
        
        colors = [
            "#ad1457", "#f4511e", "#e4c441", "#0b8043", "#3f51b5", "#8e24aa",
            "#d81b60", "#ef6c00", "#c0ca33", "#009688", "#7986cb", "#795548",
            "#d50000", "#f09300", "#7cb342", "#039be5", "#b39ddb", "#616161",
            "#e67c73", "#f6bf26", "#33b679", "#4285f4", "#9e69af", "#a79b8e"
            ]
        self.cm_colors = ColorMenu(convertColors(colors), self)
        # self.addAction(self.cm_colors)

        self.s_layout.setCurrentIndex(0)

    def contextMenuEvent(self, e: QtGui.QContextMenuEvent) -> None:
        self.cm_colors.exec(e.globalPos())

class Header(QtWidgets.QScrollArea):
    
    def __init__(self, direction: QtWidgets.QBoxLayout.Direction, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.model = None

        self.verticalScrollBar().setStyleSheet("QScrollBar {height:0px;}")
        self.horizontalScrollBar().setStyleSheet("QScrollBar {width:0px;}")
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setWidgetResizable(True)
        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.setStyleSheet("background-color: red")

        self.header_widget = QtWidgets.QWidget(self)
        self.header_widget.setStyleSheet("background-color: blue")
        self.header_widget.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)  
        self.header_layout = QtWidgets.QBoxLayout(direction)
        self.header_layout.setSpacing(0)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.header_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.header_widget.setLayout(self.header_layout)
        self.setWidget(self.header_widget)

        if direction == QtWidgets.QBoxLayout.Direction.LeftToRight:
            self.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
            self.header_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        else:
            self.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
            self.header_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)