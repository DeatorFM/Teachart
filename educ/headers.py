from PyQt6 import QtCore, QtGui, QtWidgets

class DelegateHeader(QtWidgets.QWidget):
    resized = QtCore.pyqtSignal(QtCore.Qt.Orientation, int, int)

    def __init__(self, orientation: QtCore.Qt.Orientation, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.orientation: QtCore.Qt.Orientation = orientation
        self.i: int = 0
        self.setStyleSheet("QWidget {background-color: blue;}")
        self._block_emit = False

        if self.orientation == QtCore.Qt.Orientation.Horizontal:
            self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        else:
            self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Expanding)
    
    def sizeHint(self) -> QtCore.QSize:
        if self.orientation == QtCore.Qt.Orientation.Horizontal:
            return QtCore.QSize(100, 5)
        else:
            return QtCore.QSize(5, 30)

    def try_resize(self, size: int) -> None:
        print("Trying to resize")
        self._block_emit = True
        if self.orientation == QtCore.Qt.Orientation.Horizontal:
            self.setMinimumWidth(size)
        else:
            self.setMinimumHeight(size)
        self._block_emit = False

        
class HeaderView(QtWidgets.QHeaderView):

    def __init__(self, orientation: QtCore.Qt.Orientation, parent: QtWidgets.QWidget | None = ...) -> None:
        super().__init__(orientation, parent)
        self.line_edit = QtWidgets.QLineEdit(self)

        self._last_section = 0

        self.setSectionsClickable(True)
        self.line_edit.hide()
        self.line_edit.editingFinished.connect(self.on_editing_finished)
        self.sectionDoubleClicked.connect(self.activate_editor)
        self.sectionMoved.connect(self.on_section_moved)

        if orientation is QtCore.Qt.Orientation.Horizontal:
            self.setDefaultSectionSize(100)
            self.setMinimumSectionSize(100)
        else:
            self.setDefaultSectionSize(30)
            self.setMinimumSectionSize(30)
        self.setMaximumHeight(30)

    def paintSection(self, painter: QtGui.QPainter | None, rect: QtCore.QRect, logicalIndex: int) -> None:
        # print("Paint Section", self.orientation(), logicalIndex, self.visualIndex(logicalIndex))
        self.model().header_index = (logicalIndex, self.visualIndex(logicalIndex))
        super().paintSection(painter, rect, logicalIndex)

    def sections(self) -> dict[int, int]:
        if self.orientation() == QtCore.Qt.Orientation.Horizontal:
            return {self.logicalIndex(i) : i for i in range(self.model().columnCount())}
        else:
            return {self.logicalIndex(i) : i for i in range(self.model().rowCount())}
        
    def sectionPositions(self) -> list[int]:
        if self.orientation() == QtCore.Qt.Orientation.Horizontal:
            return [self.sectionPosition(i) for i in range(self.model().columnCount())]
        else:
            return [self.sectionPosition(i) for i in range(self.model().rowCount())]

    def count_for_orientation(self) -> int:
        if self.orientation() == QtCore.Qt.Orientation.Horizontal:
            return self.model().columnCount()
        else:
            return self.model().rowCount()

    def on_section_moved(self, section: int, source: int, destination: int) -> None:
        if self.orientation() == QtCore.Qt.Orientation.Horizontal:
            source_mindex = self.model().index(0, source)
            destination_mindex = self.model().index(0, destination)
            self.model().moveColumn(source_mindex, source, destination_mindex, destination)
        else:
            source_mindex = self.model().index(source, 0)
            destination_mindex = self.model().index(destination, 0)
            self.model().moveRow(source_mindex, source, destination_mindex, destination)

    def activate_editor(self, section: int) -> None:
        if self.orientation() == QtCore.Qt.Orientation.Horizontal:
            text = self.model().headerData(self.visualIndex(section), self.orientation(), QtCore.Qt.ItemDataRole.UserRole).text
            self.line_edit.setText(text)
            self.line_edit.show()
            self._last_section = self.visualIndex(section)
            rect = self.rect()
            pos = self.sectionPosition(section)
            self.line_edit.setGeometry(rect.x() + pos, rect.y(), self.sectionSize(section), rect.height())

    def on_editing_finished(self) -> None:
        text = self.line_edit.text()
        self.model().setHeaderData(self._last_section, self.orientation(), text, QtCore.Qt.ItemDataRole.DisplayRole)
        self.line_edit.hide()