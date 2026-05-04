from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from email.header import Header
from random import getrandbits
from typing import Any, Self, Sequence

from PyQt6.QtCore import (
    QAbstractListModel,
    QAbstractTableModel,
    QByteArray,
    QDataStream,
    QIODevice,
    QMimeData,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    QPoint,
    QSize,
    QSortFilterProxyModel,
    Qt,
    QVariant,
    QXmlStreamReader,
    QXmlStreamWriter,
    pyqtSignal,
)
from PyQt6.QtGui import QFont, QGuiApplication

from nativeelements.baseelement import BaseElementDefinitions, BaseElementModel
from tcha.consts import ResourceFlag
from tcha.resmanager import ResourceContainer, ResourceObject
from tcha.settings import Settings
from ui.commons import PasteConfirmation


@dataclass(frozen=True)
class IndexPoint:
    """Stores cell index at table and cell level as well as the selected mouse position inside a table."""

    row: int
    column: int
    erow: int
    point: QPoint

    def __eq__(self, value: IndexPoint):
        return (
            self.row == value.row
            and self.column == value.column
            and self.erow == value.erow
        )


class CellItem(list):
    """Describes the raw data of a cell."""

    def __init__(self, hheader_item: HeaderDataItem, num: int):
        super().__init__()
        if hheader_item.orientation != Qt.Orientation.Horizontal:
            raise ValueError("HeaderDataItem must have a horizontal orientation.")
        self._internal_counter = 0
        self._header = hheader_item
        self._num = num

    def append(self, object: BaseElementModel):
        """Append an element model to the cell."""
        if isinstance(object, BaseElementModel):
            object.recalculate_size(self.width)
            if object.number == 0:
                self._internal_counter += 1
                object.set_number(self._internal_counter)
            super().append(object)
            return
        raise TypeError(
            f"Argument must be of type of BaseElementModel but type is {type(object)}"
        )

    def insert(self, index: int, object: BaseElementModel):
        if isinstance(object, BaseElementModel):
            object.recalculate_size(self.width)
            if object.number == 0:
                self._internal_counter += 1
                object.set_number(self._internal_counter)
            super().insert(index, object)
            return
        raise TypeError(
            f"Argument must be of type of BaseElementModel but type is {type(object)}"
        )

    @property
    def current_size(self) -> QSize:
        return QSize(self.width, self.height)

    @property
    def height(self) -> int:
        if len(self) > 0:
            return sum(map(lambda x: x.item_size.height() + 8, self))
        return 30

    @property
    def width(self) -> int:
        return self._header.section_size - 4

    @property
    def header(self) -> HeaderDataItem:
        return self._header

    @property
    def num(self) -> int:
        return self._num

    def recalculate_items(self) -> None:
        """Recalculates the cell's size based on headers width"""
        for item in self:
            item: BaseElementModel
            item.recalculate_size(self.width)

    def set_header_item(self, hheader: HeaderDataItem) -> None:
        self._header = hheader
        self.recalculate_items()

    def copy_to(self, new_cell: CellItem) -> None:
        """Copies all elements of a model to another CellItem"""
        for model in self:
            copied_model = model.copy()
            new_cell.append(copied_model)

    def row_for_num(self, num: int) -> int:
        for row, model in enumerate(self):
            if model.number == num:
                return row
        return -1

    def row_for_pos(self, y_pos: int) -> int:
        y_offset = 0
        for row, model in enumerate(self):
            model: BaseElementModel
            if y_pos >= y_offset and y_pos <= y_offset + model.item_size.height() + 8:
                return row
            y_offset += model.item_size.height() + 8

    def xml(self, writer: QXmlStreamWriter) -> QXmlStreamWriter:
        writer.writeStartElement("cell")
        if len(self) > 0:
            for model in self:
                writer = model.xml(writer)
        else:
            writer.writeComment("Empty")
        writer.writeEndElement()
        return writer

    def __repr__(self):
        return f"CellItem: {super().__repr__()}"

    def __str__(self):
        return f"CellItem: {super().__str__()}"


class CellModel(QAbstractListModel):
    """Model to edit a cell's data inside a CellEditor and to connect CellItem with views."""

    modelChanged = pyqtSignal()

    def __init__(
        self,
        data: CellItem,
        index: QModelIndex = QModelIndex(),
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._data: CellItem[BaseElementModel] = data
        self.cell_index: QModelIndex = index

    @property
    def height(self) -> int:
        return self._cached_size.height()

    @property
    def tablemodel(self) -> TableModel:
        return self.cell_index.model()

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self._data)

    def add_model(self, model: BaseElementModel) -> None:
        self.beginInsertRows(QModelIndex(), len(self._data), len(self._data))
        self._data.append(model)
        self.endInsertRows()

    def create_model(
        self, definition: BaseElementDefinitions
    ) -> BaseElementDefinitions:
        if definition:
            rescont = self.tablemodel.rescont

            match definition.resource_flag():
                case ResourceFlag.NoResource:
                    resobj = rescont.create(definition.type())

                case ResourceFlag.HasResource:
                    resource = definition.get_file()
                    if resource:
                        resobj = rescont.save(definition.type(), resource)
                        assert isinstance(resobj, ResourceObject)
                    else:
                        return

                case ResourceFlag.Optional:
                    resource = definition.get_file()
                    if resource:
                        resobj = rescont.save(definition.type(), resource)
                        assert isinstance(resobj, ResourceObject)
                    else:
                        resobj = rescont.create(definition.type())

            model = definition.create_model(resobj)
            self.add_model(model)

    def create_from_clipboard(self, definition: BaseElementDefinitions | None) -> None:
        if definition:
            mime_data = QGuiApplication.clipboard().mimeData()
            model = definition.model_from_mime_data(self.tablemodel.rescont, mime_data)
            if model:
                self.add_model(model)

    def clear(self) -> None:
        while self._data:
            model = self._data.pop()
            del model

    def removeRows(self, row: int, count: int, parent=QModelIndex()) -> bool:
        try:
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

    def index(
        self, row: int, column: int = 0, parent: QModelIndex = ...
    ) -> QModelIndex:
        return self.createIndex(row, column, 1)

    def index_for_num(self, num: int) -> QModelIndex:
        """Returns the model with the given number. If not found returns an invalid QModelIndex."""
        for row, model in enumerate(self._data):
            if model.number == num:
                return self.index(row, 0)

        return QModelIndex()

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

    def mimeData(self, indexes: list[QModelIndex]) -> QMimeData:
        mimedata = QMimeData()
        encoded_data = QByteArray()
        stream = QDataStream(encoded_data, QIODevice.OpenModeFlag.WriteOnly)

        # Write source info
        from tcha.core import AppCore

        index = indexes[0]
        AppCore.set_shared_index(
            QPersistentModelIndex(self.cell_index)
        )  # Setting so it can be accessed by other models
        stream.writeInt16(self.cell_index.model().model_id)  # Source model
        stream.writeInt8(1)  # Source Level
        stream.writeInt32(index.data().number)  # Model number
        stream.writeBool(False)  # Delete source?
        print(
            f"Written mime data: Source level 1; Table row {self.cell_index.row()}; Table column {self.cell_index.column()}; Cell row {index.row()}"
        )

        mimedata.setData("application/x-teachart", encoded_data)
        return mimedata

    def canDropMimeData(
        self,
        data: QMimeData,
        action: Qt.DropAction,
        row: int,
        column: int,
        parent: QModelIndex,
    ):
        if action == Qt.DropAction.IgnoreAction or action == Qt.DropAction.CopyAction:
            return False

        if not data.hasFormat("application/x-teachart"):
            return False

        # For internal list reordering: invalid parent with valid row is OK
        if not parent.isValid() and row < 0:
            return False

        # Don't allow dropping on the same position
        if parent.isValid() and parent.row() == row:
            return False

        return True

    def dropMimeData(
        self,
        data: QMimeData,
        action: Qt.DropAction,
        row: int,
        column: int,
        parent: QModelIndex,
    ):
        if self.canDropMimeData(data, action, row, column, parent):
            encoded_data = data.data("application/x-teachart")
            stream = QDataStream(encoded_data, QIODevice.OpenModeFlag.ReadOnly)

            model_id = stream.readInt16()  # Source model must have the same pointer
            source_lvl = stream.readInt8()  # Level
            source_model_num = stream.readInt32()  # Model number

            if source_lvl != 1:
                return False

            source_idx = self.index_for_num(source_model_num)

            if not parent.isValid():
                if source_idx.row() != row:
                    self.moveRow(QModelIndex(), source_idx.row(), QModelIndex(), row)
                    return True

            # For dropping onto an item (valid parent)
            elif source_idx != parent:
                self.moveRow(
                    QModelIndex(), source_idx.row(), QModelIndex(), parent.row()
                )
                return True

        return False

    def mimeTypes(self) -> list[str]:
        return ["application/x-teachart"]

    def moveRows(
        self,
        sourceParent: QModelIndex,
        sourceRow: int,
        count: int,
        destinationParent: QModelIndex,
        destinationChild: int,
    ) -> bool:
        print("Begin moving rows from", sourceRow, "to", destinationChild)
        try:
            if (
                sourceRow == self.rowCount() - 1
                and destinationChild > sourceRow
                or sourceRow == destinationChild
            ):
                return False
            if destinationChild > sourceRow:
                target = destinationChild + 1
            elif destinationChild == -1:
                target = 0
            else:
                target = destinationChild

            self.beginMoveRows(
                sourceParent, sourceRow, sourceRow, destinationParent, target
            )
            self._data.insert(destinationChild, self._data.pop(sourceRow))
            self.endMoveRows()
            self.modelChanged.emit()
            return True

        except IndexError:
            return False

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

    def __bool__(self) -> bool:
        return bool(self._data)

    def flags(self, index: QModelIndex):
        return (
            Qt.ItemFlag.ItemIsEditable
            | Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
        )

    def __str__(self):
        return f"CellModel {self._data}"

    def __deepcopy__(self, memo: dict | None = None) -> CellModel:
        return CellModel(deepcopy(self._data))


@dataclass
class HeaderDataItem:
    visual_index: int
    orientation: Qt.Orientation
    section_size: int
    editable: bool = field(default=True)
    text: str = field(default="")

    @classmethod
    def horizontal(cls, idx: int) -> "HeaderDataItem":
        return cls(idx, Qt.Orientation.Horizontal, 100)

    @classmethod
    def vertical(cls, idx: int) -> "HeaderDataItem":
        return cls(idx, Qt.Orientation.Vertical, 30, False)

    def __deepcopy__(self, memo: dict | None = None) -> HeaderDataItem:
        return HeaderDataItem(
            self.orientation, self.section_size, self.editable, self.text
        )


class TableModel(QAbstractTableModel):
    modelChanged = pyqtSignal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._internal_counter = 0
        self._model_id = getrandbits(15)
        self._data: list[list[CellItem]] = []
        self._header_data: dict[Qt.Orientation, list[HeaderDataItem]] = {
            Qt.Orientation.Horizontal: [],
            Qt.Orientation.Vertical: [],
        }

        print(f"Model has id: {self._model_id}")
        self._rescont = ResourceContainer(self)

    @property
    def model_id(self) -> int:
        return self._model_id

    def is_valid(self) -> bool:
        return (
            self.rowCount() >= 1
            and self.columnCount() >= 1
            and len(self._header_data[Qt.Orientation.Horizontal]) == self.columnCount()
            and len(self._header_data[Qt.Orientation.Vertical]) == self.rowCount()
        )

    @property
    def rescont(self) -> ResourceContainer:
        return self._rescont

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self._data)

    def columnCount(self, parent: QModelIndex = ...) -> int:
        if not self._data:
            return 0
        return len(max(self._data, key=len))

    def counter(self) -> int:
        return self._internal_counter

    def supportedDropActions(self):
        return Qt.DropAction.MoveAction | Qt.DropAction.CopyAction

    @classmethod
    def new(cls: TableModel, rows: int, columns: int) -> Self:
        """Creates empty TableModel with number of rows and column"""
        if rows > 0 and columns > 0:
            model = cls()
            model.insertRows(-1, rows)
            model.insertColumns(-1, columns)
            return model
        raise ValueError("Row and column count must be at least 1.")

    def get_row(self, row: int) -> tuple[CellItem]:
        return tuple(self._data[row])

    def get_column(self, column: int) -> tuple[CellItem]:
        return tuple([row[column] for row in self._data])

    def index(
        self, row: int, column: int, parent: QModelIndex = QModelIndex()
    ) -> QModelIndex:
        return self.createIndex(row, column, 0)

    def index_for_num(self, num: int) -> QModelIndex:
        """Returns the index of the CellItem with the given number."""
        for row_idx, row in enumerate(self._data):
            for col_idx, cell in enumerate(row):
                if cell.num == num:
                    return self.index(row_idx, col_idx)
        return QModelIndex()

    def increase_counter(self) -> int:
        self._internal_counter += 1
        return self._internal_counter

    def data(self, index: QModelIndex, role: int = ...) -> CellItem:
        return self._data[index.row()][index.column()]

    def setData(
        self, index: QModelIndex, value: CellItem, role=Qt.ItemDataRole.DisplayRole
    ) -> bool:
        try:
            if isinstance(value, CellItem):
                self._data[index.row()][index.column()] = value
                self.dataChanged.emit(index, index)
                return True
            return False
        except IndexError:
            return False

    def header_count(self, orientation: Qt.Orientation) -> int:
        if orientation == Qt.Orientation.Horizontal:
            return self.columnCount()
        else:
            return self.rowCount()

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = ...
    ) -> Any:
        try:
            if role == Qt.ItemDataRole.DisplayRole:
                if self._header_data[orientation][section].text:
                    return self._header_data[orientation][section].text
                else:
                    if (
                        Settings.qsettings().value("Application/debug", False, bool)
                        and orientation == Qt.Orientation.Horizontal
                    ):
                        return str(self._header_data[orientation][section].section_size)
                    return self._header_data[orientation][section].visual_index + 1
            elif role == Qt.ItemDataRole.FontRole:
                font = QFont()
                font.setFamily("Segoe UI Semibold")
                return font
            elif role == Qt.ItemDataRole.TextAlignmentRole:
                return Qt.AlignmentFlag.AlignCenter
            elif role == Qt.ItemDataRole.SizeHintRole:
                if orientation == Qt.Orientation.Horizontal:
                    return QSize(
                        self._header_data[orientation][section].section_size, 30
                    )
            elif role == Qt.ItemDataRole.EditRole:
                return self._header_data[orientation][section]
        except IndexError:
            pass

    def setHeaderData(
        self, section: int, orientation: Qt.Orientation, value: Any, role=...
    ) -> bool:
        try:
            if role == Qt.ItemDataRole.DisplayRole and isinstance(value, str):
                self._header_data[orientation][section].text = value
                self.headerDataChanged.emit(orientation, section, section)
                self.modelChanged.emit()
                return True
            elif role == Qt.ItemDataRole.EditRole and isinstance(value, int):
                self._header_data[orientation][section].visual_index = value
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

    def insertRows(
        self, row: int, count: int, parent: QModelIndex = QModelIndex()
    ) -> bool:
        """Inserts new row after the given row"""
        row = row if row > -1 else self.rowCount()
        try:
            self.beginInsertRows(QModelIndex(), row, row + count - 1)
            for num in range(count):
                self._header_data[Qt.Orientation.Vertical].insert(
                    row + num, HeaderDataItem.vertical(row + num)
                )
                self._data.insert(
                    row + num,
                    [
                        CellItem(
                            self._header_data[Qt.Orientation.Horizontal][col],
                            self.increase_counter(),
                        )
                        for col in range(self.columnCount())
                    ],
                )
            self.endInsertRows()
            self.modelChanged.emit()
            return True
        except IndexError:
            return False

    def insertColumns(
        self, column: int, count: int, parent: QModelIndex = QModelIndex()
    ) -> bool:
        column = column if column > -1 else self.columnCount()
        try:
            self.beginInsertColumns(parent, column, column + count - 1)
            for num in range(count):
                hitem = HeaderDataItem.horizontal(column + num)
                for row in self._data:
                    row.insert(
                        column + num,
                        CellItem(hitem, self.increase_counter()),
                    )
                self._header_data[Qt.Orientation.Horizontal].insert(column + num, hitem)
            self.endInsertColumns()
            self.modelChanged.emit()
            return True
        except IndexError:
            return False

    def removeRows(
        self, row: int, count: int, parent: QModelIndex = QModelIndex()
    ) -> bool:
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

    def removeColumns(
        self, column: int, count: int, parent: QModelIndex = QModelIndex()
    ) -> bool:
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

    # def moveRows(
    #     self,
    #     sourceParent: QModelIndex,
    #     sourceRow: int,
    #     count: int,
    #     destinationParent: QModelIndex,
    #     destinationChild: int,
    # ) -> bool:
    #     try:
    #         if sourceRow > destinationChild:
    #             self.beginMoveRows(
    #                 sourceParent,
    #                 sourceRow,
    #                 sourceRow + count - 1,
    #                 destinationParent,
    #                 destinationChild,
    #             )
    #             adjust = 0
    #         else:
    #             self.beginMoveRows(
    #                 sourceParent,
    #                 sourceRow,
    #                 sourceRow + count - 1,
    #                 destinationParent,
    #                 destinationChild + 1,
    #             )
    #             adjust = -1
    #         self._data.insert(destinationChild + adjust, self._data.pop(sourceRow))
    #         self._header_data[Qt.Orientation.Vertical].insert(
    #             destinationChild + adjust,
    #             self._header_data[Qt.Orientation.Vertical].pop(sourceRow),
    #         )
    #         self.endMoveRows()
    #         self.modelChanged.emit()
    #         print("Moved row", sourceRow, "to", destinationChild, "successfully")
    #         print("Table now:\n", self)
    #         print("Headers:", self._header_data)
    #         return True
    #     except IndexError:
    #         return False

    # def moveColumns(
    #     self,
    #     sourceParent: QModelIndex,
    #     sourceColumn: int,
    #     count: int,
    #     destinationParent: QModelIndex,
    #     destinationChild: int,
    # ) -> bool:
    #     print("Starting move operation")
    #     try:
    #         if sourceColumn > destinationChild:
    #             self.beginMoveColumns(
    #                 sourceParent,
    #                 sourceColumn,
    #                 sourceColumn + count - 1,
    #                 destinationParent,
    #                 destinationChild,
    #             )
    #             adjust = 0
    #         else:
    #             self.beginMoveColumns(
    #                 sourceParent,
    #                 sourceColumn,
    #                 sourceColumn + count - 1,
    #                 destinationParent,
    #                 destinationChild + 1,
    #             )
    #             adjust = -1
    #         for row in self._data:
    #             row.insert(destinationChild + adjust, row.pop(sourceColumn))
    #         self._header_data[Qt.Orientation.Horizontal].insert(
    #             destinationChild + adjust,
    #             self._header_data[Qt.Orientation.Horizontal].pop(sourceColumn),
    #         )
    #         self.endMoveColumns()
    #         self.modelChanged.emit()
    #         print("Moved column", sourceColumn, "to", destinationChild, "successfully")
    #         print("Table now:\n", self)
    #         print("Headers:", self._header_data)
    #         return True
    #     except IndexError:
    #         return False

    def mimeData(self, indexes: list[QModelIndex]):
        mimedata = QMimeData()
        encoded_data = QByteArray()
        stream = QDataStream(encoded_data, QIODevice.OpenModeFlag.WriteOnly)

        # Write source info
        from tcha.core import AppCore

        index = indexes[0]
        AppCore.set_shared_index(QPersistentModelIndex(index))
        if index.isValid():
            stream.writeInt16(self._model_id)  # Model id
            stream.writeInt8(0)  # Level
            print(
                f"Written mime data: Source level 0; Table row {index.row()}; Table column {index.column()}; Cell row None"
            )

            mimedata.setData("application/x-teachart", encoded_data)
        return mimedata

    def canDropMimeData(
        self,
        data: QMimeData,
        action: Qt.DropAction,
        row: int,
        column: int,
        parent: QModelIndex,
    ):
        if action == Qt.DropAction.IgnoreAction:
            return False

        if not data.hasFormat("application/x-teachart"):
            return False

        if not parent.isValid():
            return False

        return True

    def dropMimeData(
        self,
        data: QMimeData,
        action: Qt.DropAction,
        row: int,
        column: int,
        parent: QModelIndex,
    ) -> bool:
        if self.canDropMimeData(data, action, row, column, parent):
            print(
                "Dropped at",
                row,
                column,
                "with parent",
                parent.row(),
                parent.column(),
                "and data format",
                data.formats(),
            )
            from tcha.core import AppCore

            encoded_data = data.data("application/x-teachart")
            stream = QDataStream(encoded_data, QIODevice.OpenModeFlag.ReadOnly)

            model_id = stream.readInt16()  # Source model must have the same pointer
            source_lvl = stream.readInt8()  # Level
            source_model_num = stream.readInt32()  # Model number

            shared_idx = AppCore.shared_index()
            if not shared_idx.isValid():
                return False
            print(
                f"Found shared index from model {model_id} with row {shared_idx.row()} and column {shared_idx.column()}"
            )

            if action == Qt.DropAction.MoveAction:
                if source_lvl == 0:  # Cell has been moved
                    # Handle cell swapping
                    if model_id == self.model_id:
                        self.swap_items(shared_idx, parent)
                        return True
                    return False

                if source_lvl == 1:  # Cell element has been moved
                    target_cell = self._data[parent.row()][parent.column()]
                    if (
                        parent.isValid()
                        and shared_idx == parent
                        and model_id == self.model_id
                    ):
                        # Internal cell move
                        cmodel = CellModel(target_cell, shared_idx)
                        return cmodel.dropMimeData(data, action, row, column, parent)

                    else:
                        # Move between cells
                        source_cell: CellItem = shared_idx.data()
                        if len(source_cell) > 0:
                            model = source_cell.pop(
                                source_cell.row_for_num(source_model_num)
                            )
                            target_cell.append(model)
                            return True

                        else:
                            return False

            elif action == Qt.DropAction.CopyAction:
                source_item: CellItem = shared_idx.data()
                if source_lvl == 0:  # Cell is copied
                    if parent.data():
                        dialog = PasteConfirmation()
                        result = dialog.exec()

                        if result == PasteConfirmation.DialogCode.Accepted:
                            if dialog.selected_paste_method() == 1:  # Replace cell
                                print("Replacing cell")
                                if parent != shared_idx or model_id != self.model_id:
                                    new_item = CellItem(
                                        self.headerData(
                                            parent.column(),
                                            Qt.Orientation.Horizontal,
                                            Qt.ItemDataRole.EditRole,
                                        ),
                                        0,
                                    )
                                    # source_item.copy_to(new_item)
                                    self.copy_to_cell(source_item, new_item)
                                    return self.setData(parent, new_item)
                                return False

                            elif dialog.selected_paste_method() == 2:  # Append to cell
                                destination_item = parent.data()
                                self.copy_to_cell(source_item, destination_item)
                                # source_item.copy_to(destination_item)
                                self.dataChanged.emit(parent, parent)

                        return False

                    else:
                        destination_item = parent.data()
                        self.copy_to_cell(source_item, destination_item)
                        # source_item.copy_to(destination_cell)
                        return True

                if source_lvl == 1:  # Model is copied
                    destination_item: CellItem = parent.data()
                    model: BaseElementModel = source_item[
                        source_item.row_for_num(source_model_num)
                    ]
                    if model:
                        destination_item.append(model.copy(self.rescont))
                        return True
                    return False

        return False

    def copy_to_cell(self, source_cell: CellItem, dest_cell: CellItem) -> None:
        for model in source_cell:
            copy = model.copy(self.rescont)
            dest_cell.append(copy)

    def mimeTypes(self) -> list[str]:
        return ["application/x-teachart"]

    def swap_items(
        self, source_index: QModelIndex, destination_index: QModelIndex
    ) -> None:
        source_row, source_column = source_index.row(), source_index.column()
        destination_row, destination_column = (
            destination_index.row(),
            destination_index.column(),
        )

        (
            self._data[source_row][source_column],
            self._data[destination_row][destination_column],
        ) = (
            self._data[destination_row][destination_column],
            self._data[source_row][source_column],
        )

        # Update header items after swap
        self._data[source_row][source_column].set_header_item(
            self._header_data[Qt.Orientation.Horizontal][source_column]
        )
        self._data[destination_row][destination_column].set_header_item(
            self._header_data[Qt.Orientation.Horizontal][destination_column]
        )

        if isinstance(source_index, QPersistentModelIndex):
            normalised = self.index(source_index.row(), source_index.column())
            self.dataChanged.emit(normalised, normalised)
        else:
            self.dataChanged.emit(source_index, source_index)
        self.dataChanged.emit(destination_index, destination_index)
        self.modelChanged.emit()

    def xml(self, writer: QXmlStreamWriter) -> QXmlStreamWriter:
        writer.writeStartElement("table")
        writer.writeAttribute("rows", str(self.rowCount()))
        writer.writeAttribute("columns", str(self.columnCount()))

        # Writing Header info
        writer.writeStartElement("headers")
        for header_item in self._header_data[Qt.Orientation.Horizontal]:  #
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
        return (
            Qt.ItemFlag.ItemIsEditable
            | Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsDropEnabled
            | Qt.ItemFlag.ItemIsDragEnabled
        )

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
        return f"Data: {self._data}\nHeader: {self._header_data}"


# class FilteredTableModel(QSortFilterProxyModel):
#     modelChanged = pyqtSignal()

#     def __init__(self, source_model: TableModel, parent=None):
#         super().__init__(parent)
#         self.setSourceModel(source_model)
#         source_model.modelChanged.connect(self.modelChanged.emit)

#         self._persistent_filtered_index = QPersistentModelIndex()
#         self._filter_mode = FilterMode.NoFilter
#         self._filtered_area = FilteredArea.Row

#     @property
#     def filtered_index(self) -> QPersistentModelIndex:
#         """Returns the index that is handled by the filter."""
#         return self._persistent_filtered_index

#     @property
#     def filter_mode(self) -> FilterMode:
#         return self._filter_mode

#     @property
#     def filtered_area(self) -> FilteredArea:
#         return self._filtered_area

#     def set_filter(
#         self, idx: QPersistentModelIndex, mode: FilterMode, area: FilteredArea
#     ) -> None:
#         self.beginFilterChange()
#         self._persistent_filtered_index = idx
#         self._filter_mode = mode
#         self._filtered_area = area
#         self.endFilterChange()

#     def set_filtered_index(self, idx: QPersistentModelIndex) -> None:
#         self.beginFilterChange()
#         self._persistent_filtered_index = idx
#         self.endFilterChange()

#     def set_filter_mode(self, mode: FilterMode) -> None:
#         self.beginFilterChange()
#         self._filter_mode = mode
#         self.endFilterChange()

#     def set_filtered_area(self, area: FilteredArea) -> None:
#         self.beginFilterChange()
#         self._filtered_area = area
#         self.endFilterChange()

#     def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
#         if self.filter_mode and self.filtered_area in (
#             FilteredArea.Row,
#             FilteredArea.Index,
#         ):
#             if self.filter_mode == FilterMode.ShowOnlyFiltered:
#                 return source_row == self.filtered_index.row()
#             else:
#                 return source_row != self.filtered_index.row()

#         return True

#     def filterAcceptsColumn(self, source_column: int, source_parent: QModelIndex):
#         if self.filter_mode and self.filtered_area in (
#             FilteredArea.Column,
#             FilteredArea.Index,
#         ):
#             if source_column == self.filtered_index.column():
#                 return (
#                     True if self.filter_mode == FilterMode.ShowOnlyFiltered else False
#                 )

#         return True

#     # TableModel methods

#     # No conversion

#     @property
#     def rescont(self) -> ResourceContainer:
#         return self.sourceModel().rescont

#     @property
#     def model_id(self) -> int:
#         return self.sourceModel().model_id

#     def counter(self) -> int:
#         return self.sourceModel().counter()

#     def increase_counter(self) -> int:
#         return self.sourceModel().increase_counter()

#     def is_valid(self) -> bool:
#         return self.sourceModel().is_valid()

#     # Index conversion needed

#     def get_row(self, proxy_row: int) -> tuple[CellItem]:
#         """Get row from source model using proxy row index."""
#         source_row = self.mapToSource(self.index(proxy_row, 0)).row()
#         return self.sourceModel().get_row(source_row)

#     def get_column(self, proxy_column: int) -> tuple[CellItem]:
#         """Get column from source model using proxy column index."""
#         source_column = self.mapToSource(self.index(0, proxy_column)).column()
#         return self.sourceModel().get_column(source_column)

#     def map_row_to_source(self, row: int) -> int:
#         idx = self.index(row, 0)
#         mapped = self.mapToSource(idx)
#         return mapped.row()

#     def index_for_num(self, num: int) -> QModelIndex:
#         """Returns the proxy index of the CellItem with the given number."""
#         source_index = self.sourceModel().index_for_num(num)
#         return self.mapFromSource(source_index)

#     def expected_row_height(self, proxy_row: int) -> int:
#         """Get expected row height using proxy row index."""
#         source_row = self.mapToSource(self.index(proxy_row, 0)).row()
#         return self.sourceModel().expected_row_height(source_row)

#     def swap_items(
#         self, proxy_source_index: QModelIndex, proxy_destination_index: QModelIndex
#     ) -> None:
#         """Swap items using proxy indices."""
#         source_index = self.mapToSource(proxy_source_index)
#         destination_index = self.mapToSource(proxy_destination_index)
#         self.sourceModel().swap_items(source_index, destination_index)

#     def copy_to_cell(self, source_cell: CellItem, dest_cell: CellItem) -> None:
#         """Copy cell contents (works directly with CellItem objects)."""
#         self.sourceModel().copy_to_cell(source_cell, dest_cell)

#     def insertRow(self, row: int, parent: QModelIndex = QModelIndex()) -> bool:
#         """Override to handle frozen row index updates."""
#         result = self.sourceModel().insertRow(row, parent)
#         if result:
#             self.invalidateRowsFilter()
#         return result

#     # Override base methods to ensure proper signal forwarding

#     def sourceModel(self) -> TableModel:
#         """Type hint override to return TableModel specifically."""
#         return super().sourceModel()

#     # XML serialization (delegates to source)

#     def xml(self, writer: QXmlStreamWriter) -> QXmlStreamWriter:
#         """Delegate XML writing to source model."""
#         return self.sourceModel().xml(writer)


class IndexModel(QSortFilterProxyModel):
    """Model to only display the row indices."""

    def __init__(self, tmodel: TableModel, parent=None):
        super().__init__(parent)
        self.setSourceModel(tmodel)
        self._inactive = []

    def add_inactive_index(self, idx: QPersistentModelIndex) -> None:
        if idx.isValid():
            print(f"Setting idx {idx.row()}")
            self._inactive.append(idx)
            self.dataChanged.emit(QModelIndex(idx), QModelIndex(idx))

    def clear_inactive_indices(self):
        if self._inactive:
            min_idx = min(self._inactive, key=lambda x: x.row())
            max_idx = max(self._inactive, key=lambda x: x.row())
            self._inactive.clear()
            # min_idx = self.index(min_row, 1)
            # max_idx = self.index(max_row, 1)
            self.dataChanged.emit(QModelIndex(min_idx), QModelIndex(max_idx))

    def columnCount(self, parent=QModelIndex()):
        return 1

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            return str(index.row() + 1)
        return None

    def flags(self, index: QModelIndex):
        if index.row() not in map(lambda x: x.row(), self._inactive):
            return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        return Qt.ItemFlag.NoItemFlags
