from PyQt6 import QtWidgets, QtCore, QtGui
from ui.StyledWidget import *

class IconButton(QtWidgets.QPushButton):
    def __init__(self, icon: str, parent=None, width=20, height=20):
        super().__init__(parent)
        ic = QtGui.QIcon()
        ic.addPixmap(QtGui.QPixmap(icon))
        self.setIcon(ic)
        self.setIconSize(QtCore.QSize(width, height))
        self.setProperty("borderless", True)

class SplitButton(QtWidgets.QFrame):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.button_layout = QtWidgets.QHBoxLayout(self)
        self.button_layout.setSpacing(0)
        self.button_layout.setContentsMargins(2, 0, 2, 0)
        self.lbutton = QtWidgets.QPushButton()
        self.lbutton.setObjectName("lbutton")
        self.button_layout.addWidget(self.lbutton)
        self.rbutton = QtWidgets.QPushButton()
        self.rbutton.setObjectName("rbutton")
        self.button_layout.addWidget(self.rbutton)
        self.setStyleSheet(fromStyle("SplitButton"))

class PrettyButton(QtWidgets.QPushButton):
    def __init__(self, title, iconpath: str, iconpathhover: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName(title)
        self.default_icon = QtGui.QIcon()
        self.default_icon.addPixmap(QtGui.QPixmap(f"{iconpath}"))
        self.hover_icon = QtGui.QIcon()
        self.hover_icon.addPixmap(QtGui.QPixmap(f"{iconpathhover}"))
        self.setIcon(self.default_icon)
        self.setIconSize(QtCore.QSize(20, 20))
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.installEventFilter(self)

    def eventFilter(self, a0: 'QObject', event: 'QEvent') -> bool:
        if event.type() == QtCore.QEvent.Type.HoverEnter:
            self.setIcon(self.hover_icon)
            self.setIconSize(QtCore.QSize(20, 20))
        elif event.type() == QtCore.QEvent.Type.HoverLeave:
            self.setIcon(self.default_icon)
        super().eventFilter(a0, event)
    
class SwitchButton(QtWidgets.QPushButton):
    stateChanged = QtCore.pyqtSignal(int)

    def __init__(self, icon1: str, icon2: str, parent= None) -> None:
        super().__init__(parent)
        self.icon1 = QtGui.QIcon()
        self.icon1.addPixmap(QtGui.QPixmap(f"{icon1}"))
        self.icon2 = QtGui.QIcon()
        self.icon2.addPixmap(QtGui.QPixmap(f"{icon2}"))
        self.setIcon(self.icon1)
        self.setIconSize(QtCore.QSize(20, 20))
        self._state = 1
        self.clicked.connect(self.switchState)

    def switchState(self) -> None:
        if self._state == 1:
            self.setIcon(self.icon2)
            self.style().polish(self)
            self._state = 2
        else:
            self.setIcon(self.icon1)
            self.style().polish(self)
            self._state = 1
        self.stateChanged.emit(self.state())

    def changeState(self, state: int) -> None:
        if state == 1:
            self.setIcon(self.icon1)
            self.style().polish(self)
            self._state = 1
        elif state == 2:
            self.setIcon(self.icon2)
            self.style().polish(self)
            self._state = 2

    def state(self) -> int:
        return self._state

class DoubleClickButton(QtWidgets.QPushButton):
    doubleClicked = QtCore.pyqtSignal()

    def mouseDoubleClickEvent(self, a0: QtGui.QMouseEvent) -> None:
        self.doubleClicked.emit()

class ColorAction(QtWidgets.QWidgetAction):
    colorSelected = QtCore.pyqtSignal(QtGui.QColor)

    def __init__(self, colors: list[QtGui.QColor], parent=None) -> None:
        super().__init__(parent)
        widget = QtWidgets.QWidget(parent)
        layout = QtWidgets.QGridLayout(widget)
        layout.setSpacing(0)
        layout.setContentsMargins(2, 2, 2, 2)
        palette = colors
        count = len(palette)
        rows = count // round(count ** .5)
        for row in range(rows):
            for column in range(count // rows):
                color = palette.pop(0)
                # print(color.name(QtGui.QColor.NameFormat.HexRgb))
                button = QtWidgets.QToolButton(widget)
                button.setAutoRaise(True)
                button.clicked.connect(lambda state, color=color: self.handleButton(color))
                pixmap = QtGui.QPixmap(16, 16)
                pixmap.fill(color)
                button.setIcon(QtGui.QIcon(pixmap))
                layout.addWidget(button, row, column)
        self.setDefaultWidget(widget)

    def handleButton(self, color: QtGui.QColor):
        self.parent().hide()
        self.colorSelected.emit(color)
        # print(color.name(QtGui.QColor.NameFormat.HexRgb))

class ColorMenu(QtWidgets.QMenu):
    colorChanged = QtCore.pyqtSignal(QtGui.QColor)

    def __init__(self, colors: list[QtGui.QColor], parent=None) -> None:
        QtWidgets.QMenu.__init__(self, parent)
        self.ac_color = ColorAction(colors, self)
        self.ac_color.colorSelected.connect(self.changeColor)
        self.addAction(self.ac_color)
        self.addSeparator()
        self.ac_CustomColor = self.addAction('Custom Color')
        self.ac_CustomColor.triggered.connect(self.from_color_dialog)

    def changeColor(self, color: QtGui.QColor) -> None:
        self.colorChanged.emit(color)

    def from_color_dialog(self) -> None:
        color = QtWidgets.QColorDialog.getColor()
        self.changeColor(color)

class PointSpacer(QtWidgets.QLabel):
    def __init__(self, spaces: int, parent=None) -> None:
        super().__init__(parent)
        self.setText(""*spaces)