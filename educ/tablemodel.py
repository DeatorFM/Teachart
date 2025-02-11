from PyQt6.QtCore import QAbstractTableModel, QAbstractListModel, QObject, QModelIndex, Qt, QSize, QMimeData, QDataStream, QIODevice, QByteArray
from PyQt6.QtGui import QFont

from typing import Any, Protocol
from dataclasses import dataclass, field

class BaseModel(Protocol):
    ...

class CellModel(QAbstractListModel):
    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._data: list[BaseModel] = []
        # self.rects: list[QRect] = []
        self.height: int = 30
        self.cell_index = (-1, -1)

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self._data)
        
    def add_model(self, model: BaseModel) -> None:
        self._data.append(model)
        self.dataChanged.emit(self.index(0), self.index(len(self._data) - 1))

    def removeRows(self, row, count, parent = ...) -> bool:
        try:
            self.beginRemoveRows(parent, row, row + count - 1)
            for _ in range(count):
                del self._data[row]
            self.endRemoveRows()
            return True
        except IndexError:
            return False

    def pop_model(self, row: int) -> BaseModel:
        model = self._data.pop(row)
        self.layoutChanged.emit()
        return model

    def index(self, row: int, column: int = 0, parent: QModelIndex = ...) -> QModelIndex:
        return self.createIndex(row, column)

    def data(self, index: QModelIndex, role: int = 1) -> BaseModel:
        # print("Data called from row:", index.row(), self._data[index.row()], "with role", role)# Model
        return self._data[index.row()]
            
    def setData(self, index: QModelIndex, value: Any, role: int = ...) -> bool:
        if index.isValid():
            self._data[index.row()] = value
            return True
        else:
            print("The data could not be saved into model.")
            return False

    def mimeData(self, indexes):
        mimedata = QMimeData()
        encoded_data = QByteArray()
        stream = QDataStream(encoded_data, QIODevice.OpenModeFlag.WriteOnly)

        # Write source info
        index = indexes[0]
        stream.writeInt32(self.cell_index[0])    # Table row
        stream.writeInt32(self.cell_index[1])    # Table column
        stream.writeInt32(index.row())           # Item index in cell
        stream.writeInt32(1)                     # map_items
        stream.writeQString('CellEditor')        # Source identifier

        mimedata.setData('application/x-qabstractitemmodeldatalist', encoded_data)
        return mimedata

    def dropMimeData(self, data, action, row, column, parent):
        if not data.hasFormat('application/x-qabstractitemmodeldatalist'):
            return False

        encoded_data = data.data('application/x-qabstractitemmodeldatalist')
        stream = QDataStream(encoded_data, QIODevice.OpenModeFlag.ReadOnly)
        
        source_table_row = stream.readInt32()
        source_table_column = stream.readInt32()
        source_item_row = stream.readInt32()
        map_items = stream.readInt32()
        source_type = stream.readQString()
        
        if source_type != 'CellEditor':
            return False
            
        # If same cell, move rows internally
        if (source_table_row, source_table_column) == self.cell_index:
            return self.moveRows(QModelIndex(), source_item_row, 1, 
                            QModelIndex(), parent.row())
                           
        return False

    def moveRows(self, sourceParent: QModelIndex, sourceRow: int, count: int, destinationParent: QModelIndex, destinationChild: int) -> bool:
        try:
            if sourceRow == self.rowCount() - 1 and destinationChild == self.rowCount() or destinationChild == -1:
                return False
            if sourceRow > destinationChild:
                self.beginMoveRows(sourceParent, sourceRow, sourceRow + count - 1, destinationParent, destinationChild)
            else:
                self.beginMoveRows(sourceParent, sourceRow, sourceRow + count - 1, destinationParent, destinationChild + 1)
            
            self._data.insert(destinationChild, self._data.pop(sourceRow))
            self.endMoveRows()
            print("Moved successfully")
            return True
        except IndexError:
            return False

    def change_on_mouse_hover(self) -> bool:
        for row in self:
            if row.change_on_mouse_hover():
                return True
            else:
                return False

    def __iter__(self):
        return iter(self._data)

    def __repr__(self) -> str:
        return str(self._data)
    
    def expected_cell_height(self, width: int) -> int:
        if self._data:
            height = sum([model.expected_size(width).height() for model in self._data])
            return height
        else:
            return 30
        
    def flags(self, index: QModelIndex):
        return Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
    
    def __str__(self):
        return str(self._data)
    

@dataclass
class HeaderDataItem:
    orientation: Qt.Orientation
    section_size: int
    editable: bool = field(default=True)
    text: str = field(default="")

    @classmethod
    def horizontal(cls) -> "HeaderDataItem":
        return cls(Qt.Orientation.Horizontal, 100)

    @classmethod
    def vertical(cls) -> "HeaderDataItem":
        return cls(Qt.Orientation.Vertical, 30, False)
    

class TableModel(QAbstractTableModel):
    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._data: list[list[CellModel]]
        self._header_data: dict[Qt.Orientation, list[HeaderDataItem]] = {Qt.Orientation.Horizontal: [], Qt.Orientation.Vertical: []}
        self.header_index: tuple[int, int] = (0, 0)

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self._data)
        
    def columnCount(self, parent: QModelIndex = ...) -> int:
        return len(max(self._data, key=len))
    
    def supportedDropActions(self):
        return Qt.DropAction.MoveAction
    
    def new(self, rows: int, columns: int):
        data = []
        for row in range(rows):
            column_list = []
            for column in range(columns):
                cell = CellModel(self)
                model_index = self.index(row, column)
                cell.dataChanged.connect(lambda: self.dataChanged.emit(model_index, model_index))
                column_list.append(cell)
            data.append(column_list)
        self._data = data
        self._header_data[Qt.Orientation.Horizontal] = [HeaderDataItem.horizontal() for i in range(columns)]
        self._header_data[Qt.Orientation.Vertical] = [HeaderDataItem.vertical() for i in range(rows)]
    
    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        # print("Index called!")
        return self.createIndex(row, column)
        
    def data(self, index: QModelIndex, role: int = ...) -> Any:
        return self._data[index.row()][index.column()] 
    
    def header_count(self, orientation: Qt.Orientation) -> int:
        if orientation == Qt.Orientation.Horizontal:
            return self.columnCount()
        else:
            return self.rowCount()
        
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> Any:
        try:
            if role == Qt.ItemDataRole.DisplayRole:
                if self._header_data[orientation][section].text:
                    return self._header_data[orientation][section].text
                else:
                    return str(section + 1)
            elif role == Qt.ItemDataRole.FontRole:
                font = QFont()
                font.setFamily("Segoe UI Semibold")
                return font
            elif role == Qt.ItemDataRole.TextAlignmentRole:
                return Qt.AlignmentFlag.AlignCenter  
            elif role == Qt.ItemDataRole.SizeHintRole:
                if orientation == Qt.Orientation.Horizontal:
                    return QSize(self._header_data[orientation][section].section_size, 30)
        except IndexError:
            pass

    def setHeaderData(self, section, orientation, value, role = ...) -> bool:
        try:
            if role == Qt.ItemDataRole.DisplayRole and isinstance(value, str):
                self._header_data[orientation][section].text = value
                self.headerDataChanged.emit(orientation, section, section)
                return True
            elif role == Qt.ItemDataRole.SizeHintRole and isinstance(value, QSize):
                self._header_data[orientation][section].section_size = value.width()
                self.headerDataChanged.emit(orientation, section, section)
                return True
            else:
                return False
        except IndexError:
            return False
        
    def insertRows(self, row: int, count: int, parent: QModelIndex = QModelIndex()) -> bool:
        try:
            self.beginInsertRows(QModelIndex(), row + 1, row + 1)
            self._data.insert(row + 1, [CellModel(self) for _ in range(self.columnCount())])
            self._header_data[Qt.Orientation.Vertical].insert(row, HeaderDataItem.vertical())
            self.endInsertRows()
            return True
        except IndexError:
            return False

    def insertColumns(self, column: int, count: int, parent: QModelIndex = QModelIndex()) -> bool:
        try:
            self.beginInsertColumns(parent, column + 1, column + 1)
            for row in self._data:
                row.insert(column + 1, CellModel(self))
            self._header_data[Qt.Orientation.Horizontal].insert(column, HeaderDataItem.horizontal())
            self.endInsertColumns()
            return True
        except IndexError:
            return False
        
    def removeRows(self, row: int, count: int, parent: QModelIndex = QModelIndex()) -> bool:
        if row < 0 or row >= len(self._data) or self.rowCount() == 1:
            return False
        self.beginRemoveRows(parent, row, row + count - 1)
        for _ in range(count):
            del self._data[row]
        del self._header_data[Qt.Orientation.Vertical][row]
        self.endRemoveRows()
        return True

    def removeColumns(self, column: int, count: int, parent: QModelIndex = QModelIndex()) -> bool:
        if column < 0 or column >= self.columnCount() or self.columnCount() == 1:
            return False
        self.beginRemoveColumns(parent, column, column + count - 1)
        for row in self._data:
            for _ in range(count):
                del row[column]
        del self._header_data[Qt.Orientation.Horizontal][column]
        self.endRemoveColumns()
        return True

    def moveRows(self, sourceParent: QModelIndex, sourceRow: int, count: int, destinationParent: QModelIndex, destinationChild: int) -> bool:
        try:
            if sourceRow > destinationChild:  
                self.beginMoveRows(sourceParent, sourceRow, sourceRow + count - 1, destinationParent, destinationChild)
                adjust = 0
            else:
                self.beginMoveRows(sourceParent, sourceRow, sourceRow + count - 1, destinationParent, destinationChild + 1)
                adjust  = 0
            self._data.insert(destinationChild + adjust, self._data.pop(sourceRow))
            self._header_data[Qt.Orientation.Vertical].insert(destinationChild + adjust, self._header_data[Qt.Orientation.Vertical].pop(sourceRow))
            self.endMoveRows()
            print("Moved row", sourceRow, "to", destinationChild, "successfully")
            print("Table now:\n", self)
            print("Headers:", self._header_data)
            return True
        except IndexError:
            return False
        
    def moveColumns(self, sourceParent: QModelIndex, sourceColumn: int, count: int, destinationParent: QModelIndex, destinationChild: int) -> bool:
        try:
            if sourceColumn > destinationChild: 
                self.beginMoveColumns(sourceParent, sourceColumn, sourceColumn + count - 1, destinationParent, destinationChild)
                adjust = 0
            else:
                self.beginMoveColumns(sourceParent, sourceColumn, sourceColumn + count - 1, destinationParent, destinationChild + 1)
                adjust = 0
            for row in self._data:
                row.insert(destinationChild + adjust, row.pop(sourceColumn))
            self._header_data[Qt.Orientation.Horizontal].insert(destinationChild + adjust, self._header_data[Qt.Orientation.Horizontal].pop(sourceColumn))
            self.endMoveRows()
            print("Moved column", sourceColumn, "to", destinationChild, "successfully")
            print("Table now:\n", self)
            print("Headers:", self._header_data)
            return True
        except IndexError:
            return False
    
    def mimeData(self, indexes):
        mimedata = QMimeData()
        encoded_data = QByteArray()
        stream = QDataStream(encoded_data, QIODevice.OpenModeFlag.WriteOnly)

        # Write source info
        index = indexes[0]
        stream.writeInt32(index.row())
        stream.writeInt32(index.column())
        stream.writeInt32(1)  # map_items
        stream.writeQString('Table')  # Source identifier

        mimedata.setData('application/x-qabstractitemmodeldatalist', encoded_data)
        return mimedata

    def canDropMimeData(self, data, action, row, column, parent):
        if action == Qt.DropAction.IgnoreAction:
            return False

        if not data.hasFormat('application/x-qabstractitemmodeldatalist'):
            return False
        
        if not parent.isValid():
            return False
        
        return True
        
    def dropMimeData(self, data, action, row, column, parent):
        if self.canDropMimeData(data, action, row, column, parent):
            print("Dropped at", row, column, "with parent", parent.row(), parent.column(), "and data format", data.formats())
            
            encoded_data = data.data('application/x-qabstractitemmodeldatalist')
            stream = QDataStream(encoded_data, QIODevice.OpenModeFlag.ReadOnly)

            source_table_row = stream.readInt32()
            source_table_column = stream.readInt32()
            source_item_row = stream.readInt32()
            map_items = stream.readInt32()
            source_type = stream.readQString()

            if source_type == 'CellEditor':
                # Move item between cells
                source_cell = self._data[source_table_row][source_table_column]
                target_cell = self._data[parent.row()][parent.column()]
                
                model = source_cell.pop_model(source_item_row)
                target_cell.add_model(model)
                return True
            else:
                # Handle table internal move
                self.swap_items(self.index(source_table_row, source_table_column), parent)
                return True

        return False   

    def swap_items(self, source_index: QModelIndex, destination_index: QModelIndex) -> None:
        source_row, source_column = source_index.row(), source_index.column()
        destination_row, destination_column = destination_index.row(), destination_index.column()

        self._data[source_row][source_column], self._data[destination_row][destination_column] = (
            self._data[destination_row][destination_column],
            self._data[source_row][source_column],
        )

        self.dataChanged.emit(source_index, source_index)
        self.dataChanged.emit(destination_index, destination_index)

    def expected_row_height(self, row: int) -> int:
        return max([cell.height for cell in self._data[row]])
    
    def flags(self, index):
        return Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsDropEnabled | Qt.ItemFlag.ItemIsDragEnabled   
    
    def __str__(self):
        l = ""
        for row in self._data:
            l += str(row) + "\n"
        return l