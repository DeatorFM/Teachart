from typing import Iterable, Any
from PyQt6.QtCore import QModelIndex
from PyQt6.QtWidgets import QWidget
from elements.baseelement import BaseElement
from ui.UI_Table import CellWidget
from PyQt6 import QtCore, QtGui, QtWidgets
from dataclasses import dataclass, field
import itertools


class CellModel(QtCore.QAbstractListModel):
    contentsChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._elements: list[BaseElement] = []  

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self._elements)

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self._elements[index.row()]
        elif role == QtCore.Qt.ItemDataRole.UserRole:
            return self._elements[index.row()].model()
    
    def add_element(self, element: BaseElement) -> None:
        self.beginInsertRows(self.createIndex(self.rowCount(), 0), self.rowCount(), self.rowCount())
        self._elements.append(element)
        self.endInsertRows()

    def moveRows(self, sourceParent: QModelIndex, sourceRow: int, count: int, destinationParent: QModelIndex, destinationChild: int) -> bool:
        if count == 1:
            try:
                self.beginMoveRows(sourceParent, sourceRow, sourceRow, destinationParent, destinationChild)
                self._elements.insert(destinationChild, self._elements.pop(sourceRow))
                self.endMoveRows()
                return True
            except IndexError:
                return False
        else:
            return False

    def removeRows(self, row: int, count: int, parent: QModelIndex = ...) -> bool:
        if count == 1:
            try:
                self.beginRemoveRows(parent, row, row)
                del self._elements[row]
                self.endRemoveRows()
                return True
            except IndexError:
                return False
        else:
            return False
        
    def __sizeof__(self) -> int:
        return self.rowCount()
        

class CellView(QtWidgets.QListView):
    def __init__(self, parent: QWidget | None = ...) -> None:
        super().__init__(parent)
        self.setResizeMode(QtWidgets.QListView.ResizeMode.Adjust)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)

    def dataChanged(self, topLeft: QModelIndex, bottomRight: QModelIndex, roles: Iterable[int] = ...) -> None:
        if topLeft == bottomRight:
            for role in roles:
                match role:
                    case QtCore.Qt.ItemDataRole.DisplayRole:
                        self.setIndexWidget(topLeft, topLeft.data(role))

    def setSelected(self, selected: bool):
        if selected == True:
            self.setFrameShape(QtWidgets.QFrame.Shape.Box)
        else:
            self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.style().polish(self)


class Cell(CellWidget):
    resized = QtCore.pyqtSignal(int, int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet("background-color: #f8f9fa;")
        self.setAutoFillBackground(True)
        # self.model = CellModel(self)
        # self.model.contentsChanged.connect(self.update_cell)

    # def set_model(self, model: CellModel):
    #     self.model = model
   
    def clear(self) -> None:
        for i in reversed(range(self.element_layout.count())):
            w = self.element_layout.takeAt(i).widget()
            self.element_layout.removeWidget(w)
    
    def update_cell(self, model: CellModel) -> None:
        self.clear()
        for element in model:
            self.element_layout.addWidget(element)

    def setSelected(self, selected: bool):
        if selected == True:
            self.setFrameShape(QtWidgets.QFrame.Shape.Box)
        else:
            self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.style().polish(self)

    def resizeEvent(self, a0: QtGui.QResizeEvent | None) -> None:
        if a0 is not None:
            self.resized.emit(a0.size().width(), a0.size().height())
        super().resizeEvent(a0)

@dataclass
class HeaderDataItem:
    orientation: QtCore.Qt.Orientation
    section_size: int
    editable: bool = field(default=True)
    text: str = field(default="")

    @classmethod
    def horizontal(cls) -> "HeaderDataItem":
        return cls(QtCore.Qt.Orientation.Horizontal, 100)

    @classmethod
    def vertical(cls) -> "HeaderDataItem":
        return cls(QtCore.Qt.Orientation.Vertical, 30, False)

class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data: list, parent=None) -> None:
        super().__init__(parent)
        self.cell_parent = parent
        self._data: list[list[CellModel]] = data #Im Programm nicht unterstützte Änderung
        self._header_data: dict[QtCore.Qt.Orientation, list[HeaderDataItem]] = self.init_header_data()

        self.header_index: tuple[int, int] = (0, 0)

        self.init_header_data()

    def rowCount(self, parent=QtCore.QModelIndex()) -> int:
        return len(self._data)
    
    def columnCount(self, parent=QtCore.QModelIndex()) -> int:
        return len(max(self._data, key=len))
    
    def index(self, row: int, column: int, parent=QtCore.QModelIndex()) -> QtCore.QModelIndex:
        return self.createIndex(row, column)
    
    def insert_row(self, row: int) -> bool:
        try:
            self.beginInsertRows(QtCore.QModelIndex(), row, row)
            self._data.insert(row, [Cell(self.cell_parent) for _ in range(self.columnCount())])
            self._header_data[QtCore.Qt.Orientation.Vertical].insert(row, HeaderDataItem.vertical())
            self.endInsertRows()
            return True
        except IndexError:
            return False

    def insert_column(self, column: int) -> bool:
        try:
            self.beginInsertColumns(QtCore.QModelIndex(), column, column)
            for row in self._data:
                row.insert(column, Cell(self.cell_parent))
            self._header_data[QtCore.Qt.Orientation.Horizontal].insert(column, HeaderDataItem.horizontal())
            self.endInsertColumns()
            return True
        except IndexError:
            return False

    def remove_row(self, row: int) -> bool:
        if self.rowCount() > 1:
            try:
                self.beginRemoveRows(QtCore.QModelIndex(), row, row)
                del self._data[row]
                self._header_data[QtCore.Qt.Orientation.Vertical].pop(row)
                print(self._header_data)
                self.endRemoveRows()
                return True
            except IndexError:
                return False
        else:
            return False
       
    def remove_column(self, column: int) -> bool:
        if self.columnCount() > 1:
            try:
                self.beginRemoveColumns(QtCore.QModelIndex(), column, column)
                for row in self._data:
                    del row[column]
                self._header_data[QtCore.Qt.Orientation.Horizontal].pop(column)
                print(self._header_data)
                self.endRemoveColumns()
                return True
            except IndexError:
                return False
        else:
            return False
        
    def moveRows(self, sourceParent: QModelIndex, sourceRow: int, count: int, destinationParent: QModelIndex, destinationChild: int) -> bool:
        try:
            self.beginMoveRows(sourceParent, sourceRow, sourceRow+count, destinationParent, destinationChild)
            self._data.insert(destinationChild, self._data.pop(sourceRow))
            self._header_data[QtCore.Qt.Orientation.Vertical].insert(destinationChild, self._header_data[QtCore.Qt.Orientation.Vertical].pop(sourceRow))
            print("Ended Move Operation successfully")
            self.endMoveRows()
            return True
        except IndexError:
            return False
        
    def moveColumns(self, sourceParent: QModelIndex, sourceColumn: int, count: int, destinationParent: QModelIndex, destinationChild: int) -> bool:
        try:
            self.beginMoveColumns(sourceParent, sourceColumn, sourceColumn+count, destinationParent, destinationChild)
            for row in self._data:
                row.insert(destinationChild, row.pop(sourceColumn))
            self._header_data[QtCore.Qt.Orientation.Horizontal].insert(destinationChild, self._header_data[QtCore.Qt.Orientation.Horizontal].pop(sourceColumn))
            self.endMoveRows()
            return True
        except IndexError:
            return False

    def init_header_data(self) -> dict[QtCore.Qt.Orientation, list[HeaderDataItem]]:
        header_data = {}
        header_data[QtCore.Qt.Orientation.Horizontal] = [HeaderDataItem.horizontal() for _ in range(self.columnCount())]
        header_data[QtCore.Qt.Orientation.Vertical] = [HeaderDataItem.vertical() for _ in range(self.rowCount())]
        return header_data

    def header(self, orientation: QtCore.Qt.Orientation) -> list[HeaderDataItem]:
        return self._header_data[orientation]
    
    def header_count(self, orientation: QtCore.Qt.Orientation) -> int:
        if orientation == QtCore.Qt.Orientation.Horizontal:
            return self.columnCount()
        else:
            return self.rowCount()

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = ...) -> Any:
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            print(orientation, self.header_index[1])
            if not self.header_index[1] > self.header_count(orientation) - 1:
                if self._header_data[orientation][self.header_index[1]].text:
                    return self._header_data[orientation][self.header_index[1]].text
                else:
                    return str(self.header_index[1] + 1)
            else:
                return "ERROR"
        elif role == QtCore.Qt.ItemDataRole.FontRole:
            font = QtGui.QFont()
            font.setFamily("Segoe UI Semibold")
            return font
        elif role == QtCore.Qt.ItemDataRole.TextAlignmentRole:
            return QtCore.Qt.AlignmentFlag.AlignCenter
        elif role == QtCore.Qt.ItemDataRole.UserRole:
            return self._header_data[orientation][section]

    def setHeaderData(self, section: int, orientation: QtCore.Qt.Orientation, value: Any, role: int = ...) -> bool:
        try:    
            item = self._header_data[orientation][section]
            if role == QtCore.Qt.ItemDataRole.DisplayRole and isinstance(value, str):
                item.text = value
                self.headerDataChanged.emit(orientation, section, section)
                return True
            elif role == QtCore.Qt.ItemDataRole.SizeHintRole and isinstance(value, int):
                item.section_size = value
                self.headerDataChanged.emit(orientation, section, section)
                return True
            else:
                return False
            
        except (IndexError, TypeError):
            return False
    
    def data(self, row: int, column: int) -> Cell | None:
        try:
            return self._data[row][column]
        except IndexError:
            return None
            
    def set_data(self, row: int, column: int, value: Cell) -> bool|None:
        if not value: return False
        try:
            self._data[row][column] = value
            self.dataChanged.emit(row, column)
            return True
        except IndexError:
            return False
            
    def cells(self) -> list[Cell]:
        return [cell for cell in itertools.chain.from_iterable(self._data)]
            
    def cell_of(self, element: BaseElement) -> CellModel | None:
        for cell in self.cells():
            if element in cell.model:
                return cell.model
            
    # def cell_coordinates(self, cell: Cell) -> tuple[int, int|str] | None:
    #     """Returns coordinates of the cell inside the table. The column may be the text inside."""
    #     for irow, row in enumerate(self._data):
    #         if cell in row:
    #             for icolumn, item in enumerate(row):
    #                 if cell == item:
    #                     column = self._header_data[QtCore.Qt.Orientation.Horizontal][icolumn].text
    #                     return irow+1, column

    def structure(self) -> list[list[Cell]]:
        return self._data

    def xml(self, stream: QtCore.QXmlStreamWriter) -> QtCore.QXmlStreamWriter:
        stream.writeStartElement("h", "table")
        stream.writeAttribute("h", "rows", str(self.rowCount()))
        stream.writeAttribute("h", "columns", str(self.columnCount()))
        for hitem in self._header_data[QtCore.Qt.Orientation.Horizontal]:
            stream.writeStartElement("h", "header")
            stream.writeAttribute("h", "width", str(hitem.model.section_size))
            stream.writeAttribute("h", "color", hitem.model.color.name())
            stream.writeCharacters(hitem.model.text)
            stream.writeEndElement()
        return stream