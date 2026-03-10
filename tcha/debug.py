from dataclasses import dataclass, field
from typing import Any, Self

from PyQt6 import uic
from PyQt6.QtCore import (
    QAbstractItemModel,
    QAbstractTableModel,
    QFile,
    QModelIndex,
    Qt,
    QVariant,
)
from PyQt6.QtWidgets import QDialog, QHeaderView
from PyQt6.QtXml import QDomDocument

from tcha.lesson import Lesson
from tcha.lfio import LessonFile
from tcha.resmanager import ResourceContainer
from tcha.tablemodel import CellModel, TableModel


class FileView(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Tool)
        self.ui = uic.loadUi("ui/debug_file_info.ui", self)

    def setup_view(
        self, lf: LessonFile, lesson: Lesson, schedule_id: int | None
    ) -> None:
        if lf.path:
            self.ui.lb_show_path.setText(lf.path)
        else:
            self.ui.lb_show_path.setText("No file")

        self.ui.lb_show_fileid.setText(lf.file_id.hex)
        self.ui.lb_show_version.setText(str(lf.version))

        if lesson.course_id != 0:
            self.ui.lb_show_course_name.setText(lesson.course_name)
        else:
            self.ui.lb_show_course_name.setText("No course")
        self.ui.lb_show_courseid.setText(str(lesson.course_id))

        if schedule_id != None:
            self.ui.lb_show_scheduleid.setText(str(schedule_id))
        else:
            self.ui.lb_show_scheduleid.setText("No schedule found")

        self.ui.lb_show_sourceid.setText(lesson.source_id)
        self.ui.lb_show_date.setText(
            f"Formatted: {lesson.datetime.date().toString('dd/MM/yyyy')}; Raw: {lesson.datetime.date().toJulianDay()}"
        )
        self.ui.lb_show_time.setText(
            f"Formatted: {lesson.datetime.time().toString('hh:mm')}; Raw: {lesson.datetime.time().msecsSinceStartOfDay()}"
        )
        self.ui.lb_show_duration.setText(f"{lesson.duration} min")


class XmlView(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Tool)
        self.ui = uic.loadUi("ui/debug_xml.ui", self)

    def setup_view(self, structure_xml: QFile, resource_xml: QFile) -> None:
        structure_def = QDomDocument()
        structure_def.setContent(structure_xml)
        resource_def = QDomDocument()
        resource_def.setContent(resource_xml)
        self.ui.tb_structure.setText(structure_def.toString(2))
        self.ui.tb_resources.setText(resource_def.toString(2))


class ResourceViewModel(QAbstractTableModel):
    def __init__(self, rescont: ResourceContainer, parent=None):
        super().__init__(parent)
        self._rescont = tuple(rescont.contents())

    def rowCount(self, parent=QModelIndex) -> int:
        if parent.isValid():
            return 0
        return len(self._rescont)

    def columnCount(self, parent=...) -> int:
        return 4

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> str | None:
        # print(f"Getting data for {index.row()}|{index.column()}")
        if role == Qt.ItemDataRole.DisplayRole:
            resobj = self._rescont[index.row()]
            match index.column():
                case 0:
                    return resobj.type.name
                case 1:
                    return str(resobj.type_num)
                case 2:
                    return resobj.path if resobj.path else "Not an external resource"
                case 3:
                    print(resobj.member_count)
                    return str(resobj.member_count)
        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role=Qt.ItemDataRole.DisplayRole,
    ) -> str:
        if orientation == Qt.Orientation.Horizontal:
            if role == Qt.ItemDataRole.DisplayRole:
                match section:
                    case 0:
                        return "Type"
                    case 1:
                        return "Type Index"
                    case 2:
                        return "Path"
                    case 3:
                        return "Member Count"
            elif role == Qt.ItemDataRole.SizeHintRole:
                if section == 2:
                    return 490
        return super().headerData(section, orientation, role)


class ResourceView(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Tool)
        self.ui = uic.loadUi("ui/debug_resources.ui", self)
        self.resize(830, 500)

    def setup_view(self, rescont: ResourceContainer) -> None:
        model = ResourceViewModel(rescont)
        self.ui.tv_robjects.setModel(model)
        self.tv_robjects.header().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )


@dataclass(frozen=True)
class TreeNode:
    level: int  # 2b 62-63
    row: int  # 18b 44-61
    column: int = field(default=0)  # 18b 26-44
    model_idx: int = field(default=0)  # 18b 8-25
    attr_key: int = field(default=0)  # 8b 0-7

    def to_int(self) -> int:
        """Converts TreeNode structure into a 64-bit integer."""
        mask = self.level << 62
        val = 0 | mask

        mask = self.row << 44
        val = val | mask

        mask = self.column << 26
        val = val | mask

        mask = self.model_idx << 8
        val = val | mask

        val = val | self.attr_key

        return val

    @classmethod
    def from_int(cls, val: int) -> Self:
        """Reads the TreeNode values from a single 62 to 64-bit integer."""
        level = val >> 62
        row = val >> 44 & 262143
        column = val >> 26 & 262143
        model_idx = val >> 8 & 262143
        attr_key = val & 255
        return cls(level, row, column, model_idx, attr_key)


class TreeTableModel(QAbstractItemModel):
    """Converts a TableModel to a Model with a tree structure."""

    def __init__(self, tablemodel: TableModel, parent=...):
        super().__init__(parent)
        self._model: TableModel = tablemodel

    def transpose_index(self, index: QModelIndex) -> int:
        """Converts twodimensional table index to list index."""
        return index.row() + self._model.columnCount() + index.column()

    def columnCount(self, parent: QModelIndex = QModelIndex()):
        return 2

    def rowCount(self, parent: QModelIndex = QModelIndex()):
        if not parent.isValid():
            return self._model.rowCount()

        node: TreeNode = TreeNode.from_int(parent.internalId())

        if isinstance(node, TreeNode):
            if node.level == 0:
                return self._model.columnCount()
            elif node.level == 1:
                cell = self._model.data(self._model.index(node.row, node.column))
                return len(cell)
            elif node.level == 2:
                cell = CellModel(
                    self._model.data(self._model.index(node.row, node.column)),
                    self._model.index(node.row, node.column),
                )
                model = cell.data(cell.index(node.model_idx))
                return len(model.attrs())

        return 0

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            return self.createIndex(row, column, TreeNode(0, row).to_int())

        node: TreeNode = TreeNode.from_int(parent.internalId())

        if isinstance(node, TreeNode):
            if node.level == 0:
                return self.createIndex(
                    row, column, TreeNode(1, node.row, row).to_int()
                )

            elif node.level == 1:
                return self.createIndex(
                    row, column, TreeNode(2, node.row, node.column, row).to_int()
                )

            elif node.level == 2:
                return self.createIndex(
                    row,
                    column,
                    TreeNode(3, node.row, node.column, node.model_idx, row).to_int(),
                )

        return QModelIndex()

    def parent(self, index: QModelIndex = QModelIndex()):
        if not index.isValid():
            return QModelIndex()

        node: TreeNode = TreeNode.from_int(index.internalId())

        if isinstance(node, TreeNode):
            if node.level == 0:
                return QModelIndex()
            elif node.level == 1:
                return self.createIndex(node.row, 0, TreeNode(0, node.row).to_int())

            elif node.level == 2:
                return self.createIndex(
                    node.column, 0, TreeNode(1, node.row, node.column).to_int()
                )

            elif node.level == 3:
                return self.createIndex(
                    node.model_idx,
                    0,
                    TreeNode(2, node.row, node.column, node.model_idx).to_int(),
                )

        return QModelIndex()

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None

        node: TreeNode = TreeNode.from_int(index.internalId())

        if not isinstance(node, TreeNode):
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == 0:
                if node.level == 0:
                    return f"Row {node.row}"
                elif node.level == 1:
                    return f"Cell {node.row}|{node.column}"
                elif node.level == 2:
                    cell = CellModel(
                        self._model.data(self._model.index(node.row, node.column)),
                        self._model.index(node.row, node.column),
                    )
                    model = cell.data(cell.index(node.model_idx))
                    return f"{type(model).__name__}"
                elif node.level == 3:
                    cell = CellModel(
                        self._model.data(self._model.index(node.row, node.column)),
                        self._model.index(node.row, node.column),
                    )
                    model = cell.data(cell.index(node.model_idx))
                    return model.attrs()[node.attr_key]

            elif index.column() == 1:
                if node.level == 3:
                    cell = CellModel(
                        self._model.data(self._model.index(node.row, node.column)),
                        self._model.index(node.row, node.column),
                    )
                    model = cell.data(cell.index(node.model_idx))
                    attr = model.attrs()[node.attr_key]
                    value = getattr(model, f"_{attr}")
                    return str(value)

        elif role == Qt.ItemDataRole.EditRole:
            if index.column() == 1:
                if node.level == 3:
                    cell = CellModel(
                        self._model.data(self._model.index(node.row, node.column)),
                        self._model.index(node.row, node.column),
                    )
                    model = cell.data(cell.index(node.model_idx))
                    attr = model.attrs()[node.attr_key]
                    value = getattr(model, f"_{attr}")
                    return value

        return None

    def setData(self, index: QModelIndex, value: Any, role=Qt.ItemDataRole.EditRole):
        if not index.isValid():
            return False

        node: TreeNode = TreeNode.from_int(index.internalId())

        if not isinstance(node, TreeNode):
            return False

        if index.column() == 1:
            if node.level == 3:
                cell = CellModel(
                    self._model.data(self._model.index(node.row, node.column)),
                    self._model.index(node.row, node.column),
                )
                model = cell.data(cell.index(node.model_idx))
                attr = model.attrs()[node.attr_key]
                type_ = type(getattr(model, f"_{attr}"))
                setattr(model, f"_{attr}", type_(value))
                self.dataChanged.emit(index, index, [role])
                source_idx = self._model.index(node.row, node.column)
                self._model.dataChanged.emit(source_idx, source_idx, [role])
                return True

        return False

    def headerData(
        self, section: int, orientation, role=Qt.ItemDataRole.DisplayRole
    ) -> str | None:
        if role == Qt.ItemDataRole.DisplayRole:
            if section == 0:
                return "Attribute"
            elif section == 1:
                return "Value"
        return super().headerData(section, orientation, role)

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        node: TreeNode = TreeNode.from_int(index.internalId())

        if not isinstance(node, TreeNode):
            return Qt.ItemFlag.NoItemFlags

        if index.column() == 1:
            if node.level == 3 and node.attr_key != 0:
                return (
                    Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsSelectable
                    | Qt.ItemFlag.ItemIsEditable
                )

        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable


class TableTreeView(QDialog):
    # TODO: Editable "Value" Column (problem not editable and interactable)

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Tool)
        self.ui = uic.loadUi("ui/debug_table.ui", self)
        self.ui.tv_table.doubleClicked.connect(self.index_double_clicked)

    def index_double_clicked(self, index: QModelIndex) -> None:
        print("Clicked: ", index.row(), index.column())

    def setup_view(self, tablemodel: TableModel) -> None:
        tree_model = TreeTableModel(tablemodel, None)
        self.ui.tv_table.setModel(tree_model)
        self.tv_table.header().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
