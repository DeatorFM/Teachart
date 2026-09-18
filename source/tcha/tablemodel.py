from __future__ import annotations

from collections.abc import Iterator, Sequence
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from random import getrandbits
from typing import Any, Self

from nativeelements.baseelement import BaseElementDefinitions, BaseElementModel
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
    QRect,
    QSize,
    Qt,
    QXmlStreamAttributes,
    QXmlStreamWriter,
    pyqtSignal,
)
from PyQt6.QtGui import QFont, QGuiApplication
from PyQt6.QtWidgets import QHeaderView
from tcha.consts import ResourceFlag
from tcha.elements import get_definitions
from tcha.error import StandardLogger
from tcha.resmanager import ResourceContainer
from tcha.utils import debug_enabled
from ui.commons import PasteConfirmation

TCHA_IDENTIFIER = 0x54434841


def decode_mime_data(mime_data: QMimeData) -> MimeData | None:
    """Decodes mime data of type 'application/x-teachart' and return the decoded data in a structured data type"""
    if "application/x-teachart" in mime_data.formats():
        encoded_data = mime_data.data("application/x-teachart")
        stream = QDataStream(encoded_data, QIODevice.OpenModeFlag.ReadOnly)

        identifier = stream.readUInt32()
        if identifier == TCHA_IDENTIFIER:
            model_id = stream.readInt16()  # Source model must have the same pointer
            source_lvl = stream.readInt8()  # Source Level

            # Sources
            table_row = stream.readInt32()  # Table row
            table_col = stream.readInt32()  # Table column
            cell_row = stream.readInt32()  # Cell row

            element_data = None
            if not stream.atEnd():
                device = stream.device()
                if device:
                    element_data = device.readAll()

            if stream.status() == QDataStream.Status.Ok:
                return MimeData(model_id, source_lvl, table_row, table_col, cell_row, element_data)
    StandardLogger.error("Failed to decode mime data", extra={"sender": "TABLEMODEL"})
    return None


@dataclass(frozen=True)
class MimeData:
    model_id: int
    level: int
    table_row: int
    table_column: int
    cell_row: int
    element_data: QByteArray | None = field(default=None)


@dataclass(frozen=True)
class Trindex:
    """Combined table and cell index as structure"""

    table_index: QModelIndex
    cell_index: int

    def __bool__(self) -> bool:
        return self.table_index.isValid() and self.cell_index > -1


class CellItem(list):
    """Describes the raw data of a cell."""

    def __init__(self, hheader_item: HeaderDataItem, num: int):
        super().__init__()
        if hheader_item.orientation != Qt.Orientation.Horizontal:
            raise ValueError("HeaderDataItem must have a horizontal orientation.")
        self._internal_counter = len(self)
        self._header = hheader_item
        self._rects = [QRect()] * len(self)
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
        raise TypeError(f"Argument must be of type of BaseElementModel but type is {type(object)}")

    def insert(self, index: int, object: BaseElementModel):
        if isinstance(object, BaseElementModel):
            object.recalculate_size(self.width)
            if object.number == 0:
                self._internal_counter += 1
                object.set_number(self._internal_counter)
            super().insert(index, object)
            return
        raise TypeError(f"Argument must be of type of BaseElementModel but type is {type(object)}")

    def rects(self, top_left: QPoint = QPoint(0, 0)) -> list[QRect]:
        y_offset = 0
        rects = []
        for model in self:
            rects.append(QRect(top_left.x(), top_left.y() + y_offset, model.item_size))
            y_offset += model.item_size.height()
        return rects

    @property
    def current_size(self) -> QSize:
        return QSize(self.width, self.height)

    @property
    def height(self) -> int:
        if len(self) > 0:
            return sum(map(lambda x: x.item_size.height() + 3, self))  # noqa: C417
        return 30

    @property
    def width(self) -> int:
        return self._header.section_size - 9

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
            # IMPLEMENT PARALLELISATION OF RECALCULATION
            item.recalculate_size(self.width)

    def set_header_item(self, hheader: HeaderDataItem) -> None:
        self._header = hheader
        self.recalculate_items()

    def copy(self) -> CellItem:
        """Shallow copy of CellItem"""
        new_item = CellItem(self.header, self.num)
        new_item[:] = self[:]
        return new_item

    def row_for_pos(self, y_pos: int) -> int:
        y_offset = 0
        for row, model in enumerate(self):
            model: BaseElementModel
            if y_pos >= y_offset and y_pos <= y_offset + model.item_size.height() + 8:
                return row
            y_offset += model.item_size.height() + 8
        return -1

    def xml(self, writer: QXmlStreamWriter) -> QXmlStreamWriter:
        writer.writeStartElement("cell")
        if len(self) > 0:
            for model in self:
                writer = model.xml(writer)
        else:
            writer.writeComment("Empty")
        writer.writeEndElement()
        return writer

    def __str__(self):
        lines = []
        position = 0
        for index, model in enumerate(self):
            lines.append(f"{index} {model.name} {position}")
            position += model.item_size.height()
        return f"CellItem (rows={len(self)} height={self.height}):\n" + "\n".join(lines)


@dataclass
class CachedModel:
    index: QPersistentModelIndex
    model: CellModel

    def __eq__(self, value: QModelIndex | QPersistentModelIndex | CellModel):
        return value == self.index or value == self.model


class CellModel(QAbstractListModel):
    """Model to edit a cell's data inside a CellEditor and to connect CellItem with views."""

    modelChanged = pyqtSignal()

    def __init__(
        self,
        data: CellItem,
        index: QModelIndex = QModelIndex(),  # noqa: B008
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._data: CellItem[BaseElementModel] = data  # Holds the currently saved data
        self._work_data = data.copy()  #  Holds the data to be changed
        self.cell_index: QModelIndex = index

    @property
    def tablemodel(self) -> TableModel:
        return self.cell_index.model()

    @property
    def item(self) -> CellItem:
        "Returns the item with the original data"
        return self._data

    @property
    def work_item(self) -> CellItem:
        "Returns the item used to edit data."
        return self._work_data

    @property
    def current_size(self) -> QSize:
        return self._work_data.current_size

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self._work_data)

    def add_model(self, model: BaseElementModel) -> None:
        self.beginInsertRows(QModelIndex(), len(self._data), len(self._data))
        self._data.append(model)
        self._work_data.append(model)
        self.endInsertRows()
        StandardLogger.debug(
            f"Added model of name '{model.name}'. Current cell structure:\n{self._work_data}"
        )

    def create_model(self, definition: BaseElementDefinitions) -> None:
        """Creates a model from a BaseElementDefinition and adds it to the work_data"""
        if definition:
            StandardLogger.debug(
                f"Adding model of definition '{definition.name()}' to cell at position {self.cell_index.row()}|{self.cell_index.column()}",
                extra={"sender": "CELLMODEL"},
            )
            rescont = self.tablemodel.rescont

            match definition.resource_flag():
                case ResourceFlag.NoResource:
                    resobj = rescont.create(definition.type())

                case ResourceFlag.HasResource:
                    resource = definition.get_file()
                    if resource:
                        resobj = rescont.save(definition.type(), Path(resource))
                    else:
                        return

                case ResourceFlag.Optional:
                    resource = definition.get_file()
                    if resource:
                        resobj = rescont.save(definition.type(), Path(resource))
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
        self.beginResetModel()
        self._data.clear()
        self._work_data.clear()
        self.endResetModel()

    def removeRows(self, row: int, count: int, parent=QModelIndex()) -> bool:  # noqa: B008
        try:
            if row >= 0:
                self.beginRemoveRows(parent, row, row + count - 1)
                for _ in range(count):
                    self._data[row].close()
                    del self._data[row]
                    del self._work_data[row]
                self.endRemoveRows()
                self.modelChanged.emit()
                return True
            return False
        except IndexError:
            return False

    def pop_model(self, row: int) -> BaseElementModel:
        model = self._data.pop(row)
        self._work_data.pop(row)
        self.layoutChanged.emit()
        self.modelChanged.emit()
        return model

    def index_for_num(self, num: int) -> QModelIndex:
        """Returns the model with the given number. If not found returns an invalid QModelIndex."""
        for row, model in enumerate(self._data):
            if model.number == num:
                return self.index(row, 0)

        return QModelIndex()

    # Data methods

    def data(
        self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole
    ) -> BaseElementModel | None:
        if index.isValid():
            model: BaseElementModel = self._data[index.row()]
            if role == Qt.ItemDataRole.DisplayRole:
                return model
            elif role == Qt.ItemDataRole.EditRole:
                mcopy = model.shcopy()
                self._work_data[index.row()] = mcopy
                return mcopy
            elif role == Qt.ItemDataRole.SizeHintRole:
                return self._work_data[index.row()].item_size

        return

    def revert_work_data(self, index: QModelIndex) -> None:
        """Reverts the working CellItem at index to the same model as the original data"""
        self._work_data[index.row()] = self._data[index.row()]
        self._work_data.recalculate_items()
        self.dataChanged.emit(index, index)

    def setData(
        self,
        index: QModelIndex,
        value: BaseElementModel,
        role: int = Qt.ItemDataRole.EditRole,
    ) -> bool:
        if index.isValid():
            if role == Qt.ItemDataRole.EditRole:
                self._data[index.row()] = value
                self._data.recalculate_items()
                self.dataChanged.emit(index, index, [role])
                StandardLogger.debug(
                    "Data of name '{value.name}' saved to the model", extra={"sender": "CELLMODEL"}
                )
                return True
            return False
        else:
            StandardLogger.error(
                "The data of name '{value.name}' could not be saved into model.",
                extra={"sender": "CELLMODEL"},
            )
            return False

    def mimeData(
        self,
        indexes: list[QModelIndex],
        action: Qt.DropAction = Qt.DropAction.MoveAction,
    ) -> QMimeData:
        mimedata = QMimeData()
        encoded_data = QByteArray()
        stream = QDataStream(encoded_data, QIODevice.OpenModeFlag.WriteOnly)

        try:
            index = indexes[0]
        except IndexError:
            return mimedata

        if index.isValid():
            stream.writeUInt32(TCHA_IDENTIFIER)
            stream.writeInt16(self.cell_index.model().model_id)  # Model id
            stream.writeInt8(1)  # Level: Cell level

            # Indexes for immediate operations (DropAction.Move)
            stream.writeInt32(self.cell_index.row())  # Table row
            stream.writeInt32(self.cell_index.column())  # Table column
            stream.writeInt32(index.row())  # Cell row

            if action is Qt.DropAction.CopyAction:
                model: BaseElementModel = index.data()
                model_data = model.to_byte_array()
                encoded_data.append(model_data)

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
        if action == Qt.DropAction.IgnoreAction or action != Qt.DropAction.MoveAction:
            return False

        if not data.hasFormat("application/x-teachart"):
            return False

        # For internal list reordering: invalid parent with valid row is OK
        if not parent.isValid() and row < 0:
            return False

        # Don't allow dropping on the same position
        if parent.isValid() and parent.row() == row:
            return False

        # Mime data checking
        mime_data = decode_mime_data(data)

        if mime_data:
            if mime_data.level != 1:
                return False

            if mime_data.model_id != self.cell_index.model().model_id:
                return False

            return (
                mime_data.table_row == self.cell_index.row()
                and mime_data.table_column == self.cell_index.column()
            )

        return False

    def dropMimeData(
        self,
        data: QMimeData,
        action: Qt.DropAction,
        row: int,
        column: int,
        parent: QModelIndex,
    ):
        if self.canDropMimeData(data, action, row, column, parent):
            mime_data = decode_mime_data(data)

            source_idx = self.index(mime_data.cell_row)

            if not parent.isValid():
                if source_idx.row() != row:
                    self.moveRow(QModelIndex(), source_idx.row(), QModelIndex(), row)
                    return True

            # For dropping onto an item (valid parent)
            elif source_idx != parent:
                self.moveRow(QModelIndex(), source_idx.row(), QModelIndex(), parent.row())
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

            self.beginMoveRows(sourceParent, sourceRow, sourceRow, destinationParent, target)
            self._data.insert(destinationChild, self._data.pop(sourceRow))
            self._work_data.insert(destinationChild, self._work_data.pop(sourceRow))
            self.endMoveRows()
            self.modelChanged.emit()
            StandardLogger.debug(
                "Moved successfully {count} row(s) from {sourceRow} to {destinationChild}",
                extra={"sender": "CELLMODEL"},
            )
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
        return Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

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
    def horizontal(cls, idx: int) -> HeaderDataItem:
        return cls(idx, Qt.Orientation.Horizontal, 100)

    @classmethod
    def vertical(cls, idx: int) -> HeaderDataItem:
        return cls(idx, Qt.Orientation.Vertical, 30, False)

    def __deepcopy__(self, memo: dict | None = None) -> HeaderDataItem:
        return HeaderDataItem(self.orientation, self.section_size, self.editable, self.text)


class TableModel(QAbstractTableModel):
    modelChanged = pyqtSignal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._internal_counter = 0
        self._model_id = getrandbits(15)

        self._cached_model: CachedModel | None = None
        self._data: list[list[CellItem]] = []
        self._header_data: dict[Qt.Orientation, list[HeaderDataItem]] = {
            Qt.Orientation.Horizontal: [],
            Qt.Orientation.Vertical: [],
        }

        StandardLogger.info(f"Model has id: {self._model_id}", extra={"sender": "TABLEMODEL"})
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

    @classmethod
    def new_from_xml(cls: TableModel, xml: QXmlStreamAttributes) -> TableModel:
        """Parses the attributes of <table> tag and creates an empty model with the row and column number in the xml."""
        return cls.new(int(xml.value("rows")), int(xml.value("columns")))

    # Indexing utilities

    def get_row(self, row: int) -> tuple[CellItem]:
        return tuple(self._data[row])

    def get_column(self, column: int) -> tuple[CellItem]:
        return tuple([row[column] for row in self._data])

    def visual_row_order(self) -> dict[int, int]:
        """Return a dict converting the visual row index to logicals based on the header section order."""
        return {
            item.visual_index: lindex
            for lindex, item in enumerate(self._header_data[Qt.Orientation.Vertical])
        }

    def visual_column_order(self) -> dict[int, int]:
        """Return a dict converting the visual column index to logicals based on the header section order."""
        return {
            item.visual_index: lindex
            for lindex, item in enumerate(self._header_data[Qt.Orientation.Horizontal])
        }

    def iter_visual_rows(self) -> Iterator[list[CellItem]]:
        converter = self.visual_row_order()
        for i in range(self.rowCount()):
            yield self._data[converter[i]]

    def iter_visual_columns(self, column: list[CellItem]) -> Iterator[CellItem]:
        converter = self.visual_column_order()
        for i in range(self.columnCount()):
            yield column[converter[i]]

    def increase_counter(self) -> int:
        """Return the number of items created."""
        self._internal_counter += 1
        return self._internal_counter

    # Data access and manipulation

    def clear_cache(self) -> None:
        self._cached_model = None

    def data(
        self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole
    ) -> CellItem | CellModel | QSize | None:
        if index.isValid():
            item = (
                self._data[index.row()][index.column()]
                if index != self._cached_model
                else self._cached_model.model.work_item
            )
            if role == Qt.ItemDataRole.EditRole:
                pindex = QPersistentModelIndex(index)
                model = CellModel(item, pindex)
                self._cached_model = CachedModel(pindex, model)
                return model
            elif role == Qt.ItemDataRole.SizeHintRole:
                return item.current_size
            elif role == Qt.ItemDataRole.ToolTipRole:
                return None
            return item
        return None

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

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> Any:
        try:
            if role == Qt.ItemDataRole.DisplayRole:
                if self._header_data[orientation][section].text:
                    return self._header_data[orientation][section].text
                else:
                    if debug_enabled() and orientation == Qt.Orientation.Horizontal:
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
                    return QSize(self._header_data[orientation][section].section_size, 30)
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

    def insertRows(self, row: int, count: int, parent: QModelIndex = QModelIndex()) -> bool:
        """Inserts new row after the given row"""
        row = row if row > -1 else self.rowCount()
        try:
            self.beginInsertRows(QModelIndex(), row, row + count - 1)
            for num in range(count):
                self._header_data[Qt.Orientation.Vertical].append(
                    HeaderDataItem.vertical(row + num)
                )
                self._data.append(
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

    def insertColumns(self, column: int, count: int, parent: QModelIndex = QModelIndex()) -> bool:
        column = column if column > -1 else self.columnCount()
        try:
            self.beginInsertColumns(parent, column, column + count - 1)
            for num in range(count):
                hitem = HeaderDataItem.horizontal(column + num)
                for row in self._data:
                    row.append(
                        CellItem(hitem, self.increase_counter()),
                    )
                self._header_data[Qt.Orientation.Horizontal].insert(column + num, hitem)
            self.endInsertColumns()
            self.modelChanged.emit()
            return True
        except IndexError:
            return False

    def removeRows(self, row: int, count: int, parent: QModelIndex = QModelIndex()) -> bool:
        if row < 0 or row >= len(self._data) or self.rowCount() == 1:
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

    def mimeData(
        self,
        indexes: list[QModelIndex],
        action: Qt.DropAction = Qt.DropAction.MoveAction,
    ) -> QMimeData:
        mimedata = QMimeData()
        encoded_data = QByteArray()
        stream = QDataStream(encoded_data, QIODevice.OpenModeFlag.WriteOnly)

        try:
            index = indexes[0]
        except IndexError:
            return mimedata

        if index.isValid():
            stream.writeUInt32(TCHA_IDENTIFIER)
            stream.writeInt16(self._model_id)  # Model id
            stream.writeInt8(0)  # Level

            # Indexes for immediate operations (DropAction.Move)
            stream.writeInt32(index.row())  # Table row
            stream.writeInt32(index.column())  # Table column
            stream.writeInt32(-1)  # No cell row -> -1

            if action is Qt.DropAction.CopyAction:
                cell: CellItem = index.data()
                for model in cell:
                    model: BaseElementModel
                    model_data = model.to_byte_array()
                    encoded_data.append(model_data)

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

        mime_data = decode_mime_data(data)
        if not mime_data:  # noqa: SIM103
            return False

        return True

    def _decode_element_data(self, bytearr: QByteArray) -> list[BaseElementModel]:
        stream = QDataStream(bytearr, QIODevice.OpenModeFlag.ReadOnly)
        models = []
        while not stream.atEnd():
            name = stream.readQString()
            definition = get_definitions(name)
            if definition:
                resource = stream.readQString()
                if resource:
                    resobj = self.rescont.save(definition.type(), resource)
                else:
                    resobj = self.rescont.create(definition.type())
                device = stream.device()
                if device:
                    model = definition.model_from_bytes(resobj, stream)
                    if model:
                        models.append(model)
            else:
                StandardLogger.error(
                    f"Decoding element data failed: No definition for {name}",
                    extra={"sender": "TABLEMODEL"},
                )
                break
        StandardLogger.debug(f"Decoded models: {models}", extra={"sender": "TABLEMODEL"})
        return models

    def dropMimeData(
        self,
        data: QMimeData,
        action: Qt.DropAction,
        row: int,
        column: int,
        parent: QModelIndex,
    ) -> bool:
        if self.canDropMimeData(data, action, row, column, parent):
            StandardLogger.debug(
                f"Dropped at {row} | {column} from parent {parent.row()}|{parent.column()}, action '{action}' and data format {data.formats()}",
                extra={"sender": "TABLEMODEL"},
            )
            mime_data = decode_mime_data(data)

            if action == Qt.DropAction.MoveAction:
                source_idx = self.index(mime_data.table_row, mime_data.table_column)
                if mime_data.level == 0:  # Cell has been moved
                    # Handle cell swapping
                    if mime_data.model_id == self.model_id:
                        self.swap_items(source_idx, parent)
                        return True
                    return False

                if mime_data.level == 1:  # Cell element has been moved
                    target_cell = self._data[parent.row()][parent.column()]
                    if source_idx == parent and mime_data.model_id == self.model_id:
                        # Internal cell move
                        cmodel = CellModel(target_cell, source_idx)
                        return cmodel.dropMimeData(data, action, row, column, parent)

                    else:
                        # Move between cells
                        source_cell: CellItem = source_idx.data()
                        if len(source_cell) > 0:
                            model = source_cell.pop(mime_data.cell_row)
                            target_cell.append(model)
                            self.dataChanged.emit(parent, parent)
                            return True

            elif action == Qt.DropAction.CopyAction and mime_data.element_data:
                loose_source_idx = self.index(mime_data.table_row, mime_data.table_column)

                if mime_data.level == 0:  # Cell is copied
                    if parent.data():
                        dialog = PasteConfirmation()
                        result = dialog.exec()

                        if result == PasteConfirmation.DialogCode.Accepted:
                            if dialog.selected_paste_method() == 1:  # Replace cell
                                if (
                                    parent != loose_source_idx
                                    or mime_data.model_id != self.model_id
                                ):
                                    new_item = CellItem(
                                        self.headerData(
                                            parent.column(),
                                            Qt.Orientation.Horizontal,
                                            Qt.ItemDataRole.EditRole,
                                        ),
                                        0,
                                    )
                                    models = self._decode_element_data(mime_data.element_data)
                                    if models:
                                        for model in models:
                                            new_item.append(model)
                                        return self.setData(parent, new_item)

                            elif dialog.selected_paste_method() == 2:  # Append to cell
                                models = self._decode_element_data(mime_data.element_data)
                                destination_item = parent.data()
                                if models:
                                    for model in models:
                                        destination_item.append(model)
                                    self.dataChanged.emit(parent, parent)
                                    return True
                    else:
                        destination_item = parent.data()
                        models = self._decode_element_data(mime_data.element_data)
                        for model in models:
                            destination_item.append(model)
                        self.dataChanged.emit(parent, parent)
                        return True

                    return False

                if mime_data.level == 1:  # Model is copied
                    destination_item: CellItem = parent.data()
                    model = self._decode_element_data(mime_data.element_data)
                    if model:
                        destination_item.append(model.pop())
                        return True

        return False

    def mimeTypes(self) -> list[str]:
        return ["application/x-teachart"]

    def swap_items(self, source_index: QModelIndex, destination_index: QModelIndex) -> None:
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
        visual_order = self.visual_column_order()
        writer.writeStartElement("headers")
        for i in range(self.columnCount()):
            header_item = self._header_data[Qt.Orientation.Horizontal][visual_order[i]]
            writer.writeEmptyElement("header")
            writer.writeAttribute("size", str(header_item.section_size))
            writer.writeAttribute("text", header_item.text)
        writer.writeEndElement()

        # Start writing cells
        for row in self.iter_visual_rows():
            writer.writeStartElement("row")
            for cell in self.iter_visual_columns(row):
                writer = cell.xml(writer)
            writer.writeEndElement()

        writer.writeEndElement()
        return writer

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
        if self._data:
            self.clear()

    def __str__(self):
        return f"Data: {self._data}\nHeader: {self._header_data}"


class IndexModel(QAbstractListModel):
    """Model to only display the row indices."""

    def __init__(self, vheader: QHeaderView, parent=None):
        super().__init__(parent)
        self._vheader = vheader
        self._inactive: list[QPersistentModelIndex] = []

        self._vheader.sectionMoved.connect(self._on_section_moved)
        self._vheader.sectionCountChanged.connect(self._on_section_count_changed)

    def _on_section_moved(self, logicalIndex: int, oldVisualIndex: int, newVisualIndex: int):
        start = min(oldVisualIndex, newVisualIndex)
        end = max(oldVisualIndex, newVisualIndex)
        self.dataChanged.emit(self.index(start, 0), self.index(end, 0))

    def _on_section_count_changed(self, oldCount: int, newCount: int):
        if newCount > oldCount:
            self.beginInsertRows(QModelIndex(), oldCount, newCount - 1)
            self.endInsertRows()
        elif newCount < oldCount:
            self.beginRemoveRows(QModelIndex(), newCount, oldCount - 1)
            self.endRemoveRows()

    def add_inactive_index(self, idx: QPersistentModelIndex) -> None:
        if idx.isValid():
            self._inactive.append(idx)
            visual_row = self._vheader.visualIndex(idx.row())
            visual_idx = self.index(visual_row, 0)
            self.dataChanged.emit(QModelIndex(visual_idx), QModelIndex(visual_idx))

    def clear_inactive_indices(self):
        if self._inactive:
            min_row = min(self._inactive, key=lambda x: self._vheader.visualIndex(x.row())).row()
            max_row = max(self._inactive, key=lambda x: self._vheader.visualIndex(x.row())).row()
            self._inactive.clear()
            min_idx = self.index(min_row, 0)
            max_idx = self.index(max_row, 0)
            self.dataChanged.emit(QModelIndex(min_idx), QModelIndex(max_idx))

    def columnCount(self, parent=QModelIndex()):
        return 1

    def rowCount(self, parent=...):
        return self._vheader.count()

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            return str(index.row() + 1)
        return None

    def flags(self, index: QModelIndex):
        if index.row() not in (self._vheader.visualIndex(x.row()) for x in self._inactive):
            return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        return Qt.ItemFlag.NoItemFlags
