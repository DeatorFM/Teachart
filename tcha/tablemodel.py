from PyQt6.QtCore import QAbstractTableModel, QAbstractListModel, QObject, QModelIndex, Qt, QSize, QMimeData, QDataStream, QIODevice, QByteArray, QXmlStreamWriter, QXmlStreamReader, pyqtSignal, QVariant
from PyQt6.QtGui import QFont

from typing import Any, Protocol, Self, Sequence
from dataclasses import dataclass, field

class BaseElementModel(Protocol):
    ...

class CellModel(QAbstractListModel):
    modelChanged = pyqtSignal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._data: list[BaseElementModel] = []
        self.height: int = 30
        self.cell_index = (-1, -1)

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self._data)
        
    def add_model(self, model: BaseElementModel) -> None:
        self.beginInsertRows(QModelIndex(), len(self._data), len(self._data))
        self._data.append(model)
        self.endInsertRows()
        print(f"Model of type {model} added.")

    def clear(self) -> None:
        while self._data:
            model = self._data.pop()
            del model

    def removeRows(self, row: int, count: int, parent = QModelIndex()) -> bool:
        try:
            print(f"Row is {row} * {count}")
            if row >= 0:
                self.beginRemoveRows(parent, row, row + count - 1)
                for _ in range(count):
                    self._data[row].close()
                    del self._data[row]
                self.endRemoveRows()
                self.modelChanged.emit()
                print("Successfully removed. Current data", self._data)
                return True
            return False
        except IndexError:
            return False

    def pop_model(self, row: int) -> BaseElementModel:
        model = self._data.pop(row)
        self.layoutChanged.emit()
        self.modelChanged.emit()
        return model

    def index(self, row: int, column: int = 0, parent: QModelIndex = ...) -> QModelIndex:
        return self.createIndex(row, column, "Cell")

    def data(self, index: QModelIndex, role: int = 1) -> BaseElementModel:
        try:
            return self._data[index.row()]
        except IndexError:
            return QVariant(None)
            
    def setData(self, index: QModelIndex, value: Any, role: int = 1) -> bool:
        if index.isValid():
            self._data[index.row()] = value
            self.dataChanged.emit(index, index, [role])
            return True
        else:
            print("The data could not be saved into model.")
            return False

    def mimeData(self, indexes) -> QMimeData:
        print("Cell's mime data")
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
        
        print(source_type)
        if source_type != 'CellEditor':
            return False
            
        # Handle internal moves
        if (source_table_row, source_table_column) == self.cell_index:
            print("Dropped from", source_item_row, "to", row)
            return self.moveRows(QModelIndex(), source_item_row, 1, 
                               QModelIndex(), row)
                           
        return False

    def moveRows(self, sourceParent: QModelIndex, sourceRow: int, count: int, destinationParent: QModelIndex, destinationChild: int) -> bool:
        print("Begin moving rows from", sourceRow, "to", destinationChild)
        try:
            if sourceRow == self.rowCount() - 1 and destinationChild > sourceRow or sourceRow == destinationChild:
                return False
            if destinationChild > sourceRow:
                target = destinationChild + 1
            elif destinationChild == -1:
                target = 0
            else:
                target = destinationChild

            self.beginMoveRows(sourceParent, sourceRow, sourceRow, destinationParent, target)
            self._data.insert(destinationChild, self._data.pop(sourceRow))
            self.endMoveRows()
            self.modelChanged.emit()
            return True
            
        except IndexError:
            return False

    def change_on_mouse_hover(self) -> bool:
        for row in self:
            if row.change_on_mouse_hover():
                return True
            else:
                return False
            
    def xml(self, writer: QXmlStreamWriter) -> QXmlStreamWriter:
        writer.writeStartElement("cell")
        if self._data:
            for model in self._data:
                writer = model.xml(writer)
        else:
            writer.writeComment("Empty")
        writer.writeEndElement()
        return writer
    
    @classmethod
    def create_with_models(cls: Self, models: Sequence[BaseElementModel]) -> Self:
        cell = cls()
        for model in models:
            cell.add_model(model)
        return cell
    
    def parent(self):
        return super().parent()

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
        
    def __del__(self) -> None:
        # print("CellModel deleted")
        self.clear()
        
    def flags(self, index: QModelIndex):
        return Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
    
    def __str__(self):
        return f"CellModel {self._data}"

    
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
    
@dataclass
class TableData:
    """Provides raw data for the table"""
    table: list[list[CellModel]]
    headers: dict[Qt.Orientation, list[HeaderDataItem]]
    

class TableModel(QAbstractTableModel):
    modelChanged = pyqtSignal()

    def __init__(self, data: TableData | None = None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        print(data)
        self._data: list[list[CellModel]]
        self._header_data: dict[Qt.Orientation, list[HeaderDataItem]] = {Qt.Orientation.Horizontal: [], Qt.Orientation.Vertical: []}
        self.header_index: tuple[int, int] = (0, 0)
    
        if data:
            self._data = data.table
            self._header_data = data.headers
        else:
            self._data = None

    def is_valid(self) -> bool:
        return self.rowCount() >= 1 and self.columnCount() >= 1 and len(self._header_data[Qt.Orientation.Horizontal]) == self.columnCount() and len(self._header_data[Qt.Orientation.Vertical]) == self.rowCount()

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self._data)
        
    def columnCount(self, parent: QModelIndex = ...) -> int:
        return len(max(self._data, key=len))
    
    def supportedDropActions(self):
        return Qt.DropAction.MoveAction
    
    @classmethod
    def new(cls, rows: int, columns: int) -> Self:
        """Creates empty TableModel with number of rows and column"""
        data = []
        header_data = {}
        for _ in range(rows):
            row = []
            for _ in range(columns):
                cell = CellModel()
                row.append(cell)
            data.append(row)
        header_data[Qt.Orientation.Horizontal] = [HeaderDataItem.horizontal() for _ in range(columns)]
        header_data[Qt.Orientation.Vertical] = [HeaderDataItem.vertical() for _ in range(rows)]
        return cls(TableData(data, header_data))

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        # print("Index called!")
        return self.createIndex(row, column, 0)
        
    def data(self, index: QModelIndex, role: int = ...) -> CellModel:
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
                self.modelChanged.emit()
                return True
            elif role == Qt.ItemDataRole.SizeHintRole and isinstance(value, QSize):
                self._header_data[orientation][section].section_size = value.width()
                self.headerDataChanged.emit(orientation, section, section)
                self.modelChanged.emit()
                return True
            else:
                return False
        except IndexError:
            return False
        
    def insertRows(self, row: int, count: int, parent: QModelIndex = QModelIndex()) -> bool:
        try:
            self.beginInsertRows(QModelIndex(), row, row)
            self._data.insert(row + 1, [CellModel(self) for _ in range(self.columnCount())])
            self._header_data[Qt.Orientation.Vertical].insert(row + 1, HeaderDataItem.vertical())
            self.endInsertRows()
            self.modelChanged.emit()
            return True
        except IndexError:
            return False

    def insertColumns(self, column: int, count: int, parent: QModelIndex = QModelIndex()) -> bool:
        try:
            self.beginInsertColumns(parent, column, column)
            for row in self._data:
                row.insert(column + 1, CellModel(self))
            self._header_data[Qt.Orientation.Horizontal].insert(column + 1, HeaderDataItem.horizontal())
            self.endInsertColumns()
            self.modelChanged.emit()
            return True
        except IndexError:
            return False
        
    def removeRows(self, row: int, count: int, parent: QModelIndex = QModelIndex()) -> bool:
        if row < 0 or row >= len(self._data) or self.rowCount() == 1:
            print("Invalid row number")
            return False
        self.beginRemoveRows(parent, row, row + count - 1)
        for _ in range(count):
            _row = self._data[row]
            for cell in _row:
                cell.clear()
            del self._data[row]
        del self._header_data[Qt.Orientation.Vertical][row]
        self.endRemoveRows()
        self.modelChanged.emit()
        return True

    def removeColumns(self, column: int, count: int, parent: QModelIndex = QModelIndex()) -> bool:
        if column < 0 or column >= self.columnCount() or self.columnCount() == 1:
            return False
        self.beginRemoveColumns(parent, column, column + count - 1)
        for row in self._data:
            for _ in range(count):
                cell = row[column]
                cell.clear()
                del row[column]
        del self._header_data[Qt.Orientation.Horizontal][column]
        self.endRemoveColumns()
        self.modelChanged.emit()
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
            self.modelChanged.emit()
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
            self.modelChanged.emit()
            print("Moved column", sourceColumn, "to", destinationChild, "successfully")
            print("Table now:\n", self)
            print("Headers:", self._header_data)
            return True
        except IndexError:
            return False
    
    def mimeData(self, indexes):
        print("Table's mime data")
        mimedata = QMimeData()
        encoded_data = QByteArray()
        stream = QDataStream(encoded_data, QIODevice.OpenModeFlag.WriteOnly)

        # Write source info
        index = indexes[0]
        stream.writeInt32(index.row())
        stream.writeInt32(index.column())
        stream.writeInt32(0)
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

            print(source_type)
            if source_type == 'Table':
                # Handle cell swapping
                source_index = self.index(source_table_row, source_table_column)
                self.swap_items(source_index, parent)
                return True

            if source_type == 'CellEditor':
                target_cell = self._data[parent.row()][parent.column()]
                if (source_table_row, source_table_column) == (parent.row(), parent.column()):
                    # Internal cell move
                    return target_cell.dropMimeData(data, action, row, column, parent)
                else:
                    # Move between cells
                    source_cell = self._data[source_table_row][source_table_column]
                    if source_cell.rowCount() > 0:
                        model = source_cell.pop_model(source_item_row)
                        target_cell.add_model(model)
                        return True
                    else:
                        return False

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
        self.modelChanged.emit()

    def xml(self, writer: QXmlStreamWriter) -> QXmlStreamWriter:
        writer.writeStartElement("table")
        writer.writeAttribute("rows", str(self.rowCount()))
        writer.writeAttribute("columns", str(self.columnCount()))

        # Writing Header info
        writer.writeStartElement("headers")
        for header_item in self._header_data[Qt.Orientation.Horizontal]:#
            writer.writeEmptyElement("header")
            writer.writeAttribute("size", str(header_item.section_size))
            writer.writeAttribute("text", header_item.text)
        writer.writeEndElement()

        # Start writing cells
        for row in self._data:
            writer.writeStartElement("row")
            for cell in row:
                writer = cell.xml(writer)
            writer.writeEndElement()

        writer.writeEndElement()
        return writer
    
    @classmethod
    def read(cls, reader: QXmlStreamReader) -> Self:
        attrs = reader.attributes()
        model = cls()
        model.new(int(attrs.value("rows")), int(attrs.value("columns")))

    def expected_row_height(self, row: int) -> int:
        return max([cell.height for cell in self._data[row]])
    
    def flags(self, index):
        return Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsDropEnabled | Qt.ItemFlag.ItemIsDragEnabled
    
    def clear(self) -> None:
        self._data.clear()
        self._header_data.clear()

    def __bool__(self) -> bool:
        return self.is_valid()
    
    def __del__(self) -> None:
        print("TableModel deleted")
        if self._data:
            self.clear()
    
    def __str__(self):
        return str(self._data)