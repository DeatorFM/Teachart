import bisect
from collections.abc import Iterator
from itertools import accumulate
from math import sqrt

from nativeelements.baseelement import (
    BaseElementDefinitions,
    BaseElementDelegate,
    BaseElementEditor,
    BaseElementModel,
    BaseElementToolset,
    BaseTextElementEditor,
)
from PyQt6.QtCore import QT_TR_NOOP as tr
from PyQt6.QtCore import (
    QAbstractItemModel,
    QByteArray,
    QEvent,
    QMimeData,
    QModelIndex,
    QObject,
    QPoint,
    QPointF,
    QRect,
    QRectF,
    QSize,
    Qt,
    pyqtSignal,
    pyqtSlot,
)
from PyQt6.QtGui import (
    QAction,
    QBrush,
    QDrag,
    QDropEvent,
    QKeyEvent,
    QKeySequence,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPen,
    QPolygonF,
    QScreen,
    QWheelEvent,
)
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QGraphicsItem,
    QGraphicsScene,
    QGraphicsSceneMouseEvent,
    QGraphicsView,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListView,
    QMenu,
    QMessageBox,
    QSizePolicy,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableView,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from tcha.consts import (
    CanvasTool,
    CellAction,
    ClipboardContent,
    EditingLevel,
    TableViewMode,
)
from tcha.elements import (
    compatible_mime_types,
    definition_for_mime_data,
)
from tcha.error import StandardLogger
from tcha.settings import Settings
from tcha.tablemodel import (
    CellItem,
    CellModel,
    IndexModel,
    TableModel,
    Trindex,
)


class CellGeometry:
    """Object that defines the geometry of a cell"""

    def __init__(self, index: QModelIndex):
        self._index = index

        if index.isValid():
            item: CellItem = index.data()
            self._height_range = item.height + 1
            self._positions: tuple[int] = tuple(
                accumulate(model.item_size.height() for model in item)
            )
        else:
            self._height_range = range(-1)
            self._positions = ()

    @property
    def index(self) -> QModelIndex:
        return self._index

    def get_cell_index(self, gcell_top_left: QPoint, gmouse_pos: QPoint) -> int:
        ypos = gmouse_pos.y() - gcell_top_left.y()
        if ypos < self._height_range:
            return bisect.bisect_left(self._positions, ypos)

        return -1

    def __str__(self):
        return f"CellGeometry.positions = {self._positions}"


class CellEditor(QListView):
    geometriesChanged = pyqtSignal()
    elementActivated = pyqtSignal(bool)
    currentIndexChanged = pyqtSignal(QModelIndex, QModelIndex)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._toolsets: dict[str, BaseElementToolset] | None = None

        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QListView.Shape.NoFrame)
        self.setLineWidth(0)
        self.setSizeAdjustPolicy(QListView.SizeAdjustPolicy.AdjustToContents)
        self.setSelectionMode(QListView.SelectionMode.SingleSelection)
        self.setEditTriggers(QListView.EditTrigger.CurrentChanged)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setStyleSheet("background-color: white;")
        self.setAutoFillBackground(True)

        self.setDragEnabled(True)
        self.setDragDropMode(QListView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)

        self._editor_just_destroyed = False
        self._drag_start_position: QPoint | None = None
        self._pres_mode = False

        self.activated.connect(lambda: self.elementActivated.emit(True))

        # Create context menu
        self.context_menu = QMenu(self)
        self.add_text_action = QAction("Add Text", self)
        self.add_picture_action = QAction("Add Picture", self)
        self.context_menu.addAction(self.add_text_action)
        self.context_menu.addAction(self.add_picture_action)

    # Toolset methods

    def set_toolset_reference(self, toolsets: dict[str, BaseElementToolset]) -> None:
        self._toolsets = toolsets

    def on_closed(self) -> None:
        self.setCurrentIndex(QModelIndex())

    def model(self) -> CellModel:
        return super().model()

    @property
    def editor(self) -> BaseElementEditor | BaseTextElementEditor | None:
        return self.indexWidget(self.currentIndex())

    def setModel(self, model):
        super().setModel(model)
        self.setCurrentIndex(QModelIndex())
        model.rowsInserted.connect(self.update_list_geometry)
        model.rowsRemoved.connect(self.update_list_geometry)

    def update_list_geometry(self) -> None:
        self.geometriesChanged.emit()
        self.scheduleDelayedItemsLayout()

    def wheelEvent(self, e):
        e.ignore()
        return super().wheelEvent(e)

    def close_active_editor(self, submit=True) -> None:
        if self.editor:
            if submit:
                self.commitData(self.editor)
            else:
                self.model().revert_work_data(self.currentIndex())
            self.closeEditor(self.editor)

    def closeEditor(
        self,
        editor: BaseElementEditor | BaseTextElementEditor,
        hint=QStyledItemDelegate.EndEditHint.NoHint,
    ) -> None:

        if editor:
            if hint == QStyledItemDelegate.EndEditHint.RevertModelCache:
                self.model().revert_work_data(self.currentIndex())
            super().closeEditor(editor, hint)
            self._editor_just_destroyed = True
            self.elementActivated.emit(False)
            self.setCurrentIndex(QModelIndex())
            self.setFocus()
            StandardLogger.debug(
                f"An element editor has been closed: {editor}, {hint.name}",
                extra={"sender": "CELLEDITOR"},
            )

    def remove_current_element(self) -> None:
        result = QMessageBox.question(
            None,
            tr("Confirm removal"),
            tr("Are you sure you want to permanently remove the selected element?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if result == QMessageBox.StandardButton.Yes:
            model = self.model()
            index = self.currentIndex()
            self.setCurrentIndex(QModelIndex())
            model.removeRow(index.row())

    def move_element_up(self) -> None:
        model = self.model()
        index = self.currentIndex()
        if index.row() > 0:
            model.moveRow(QModelIndex(), index.row(), QModelIndex(), index.row() - 1)

    def move_element_down(self) -> None:
        model = self.model()
        index = self.currentIndex()
        if index.row() != model.rowCount() - 1:
            model.moveRow(QModelIndex(), index.row(), QModelIndex(), index.row() + 1)

    def clear_item(self) -> None:
        result = QMessageBox.question(
            None,
            "Confirm deletion",
            "Are you sure to permanently delete the entire cell's content?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if result == QMessageBox.StandardButton.Yes:
            self.model().clear()

    def can_make_element_from_mime_data(self) -> bool:
        current = frozenset(QApplication.clipboard().mimeData().formats())
        compatible = compatible_mime_types()
        return current <= compatible

    def currentChanged(self, current: QModelIndex, previous: QModelIndex):
        super().currentChanged(current, previous)
        self.currentIndexChanged.emit(current, previous)

    def paintEvent(self, e: QPaintEvent | None) -> None:
        self.scrollToTop()
        super().paintEvent(e)
        if self._editor_just_destroyed:
            self._editor_just_destroyed = False
            self.geometriesChanged.emit()

    def copy_index(self, index: QModelIndex) -> None:
        # TODO: Implement function for element editors
        if index.isValid():
            clipboard = QApplication.clipboard()
            mime_data = self.model().mimeData([index], Qt.DropAction.CopyAction)
            clipboard.setMimeData(mime_data)

    def copy_current_index(self) -> None:
        if (
            self.editor and self.editor.can_copy()
        ):  # Copy permission check to avoid overwriting copied data of active editor
            self.copy_index(self.currentIndex())

    def copied_index(self) -> QModelIndex:
        return QModelIndex

    def enable_presenter_mode(self, enabled: bool):
        self._pres_mode = enabled
        current = self.currentIndex()
        self.change_index(current)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_position = event.pos()
            index = self.indexAt(event.pos())
            if self.state() == QListView.State.EditingState and index != self.currentIndex():
                self.setCurrentIndex(QModelIndex())
                if index.isValid():
                    self.setCurrentIndex(index)
                event.accept()
                return
        super().mousePressEvent(event)

    def change_index(self, new_idx: QModelIndex) -> None:
        self.setCurrentIndex(QModelIndex())
        if new_idx.isValid():
            self.setCurrentIndex(new_idx)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return

        if not self._drag_start_position:
            return

        if (
            event.pos() - self._drag_start_position
        ).manhattanLength() < QApplication.startDragDistance():
            return

        drag = QDrag(self)
        mime_data = self.model().mimeData([self.currentIndex()], Qt.DropAction.MoveAction)
        drag.setMimeData(mime_data)
        drag.exec(Qt.DropAction.MoveAction)

    def dropEvent(self, event: QDropEvent):
        if event.source() == self:
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()

            drop_index = self.indexAt(event.position().toPoint())
            drop_row = drop_index.row() if drop_index.isValid() else self.model().rowCount()

            self.model().dropMimeData(
                event.mimeData(), event.dropAction(), drop_row, 0, QModelIndex()
            )
        else:
            event.ignore()

    def itemDelegateForIndex(self, index: QModelIndex) -> QStyledItemDelegate | None:
        model = index.data()
        if isinstance(model, BaseElementModel) and self._toolsets:
            toolset = self._toolsets[model.name]
            delegate = model.delegate(toolset, self)
            delegate.commitData.connect(self.commitData)
            delegate.closeEditor.connect(self.closeEditor)
            delegate.sizeHintChanged.connect(self.update_list_geometry)
            delegate.pres_mode = self._pres_mode

            return delegate
        else:
            return None

    def sizeHint(self) -> QSize:
        return self.model().sizeHint(self.width())


class CellDelegate(QStyledItemDelegate):
    editorOpened = pyqtSignal(QListView)

    def __init__(self, parent: QObject | None = ...) -> None:
        super().__init__(parent)
        self.extra_emit = False
        self._open_editor_index = QModelIndex()
        self.hovered_index = Trindex(QModelIndex(), -1)

        self.element_selection = False
        self.mouse_pos = QPoint()

    def paint(
        self, painter: QPainter | None, option: QStyleOptionViewItem, index: QModelIndex
    ) -> None:
        if not self.hovered_index:
            painter.save()
            super().paint(painter, option, QModelIndex())
            painter.restore()

        if index != self._open_editor_index:
            # Apply 2px padding to simulate CellEditor frame
            cell_rect = option.rect.adjusted(2, 2, -2, -2)
            y_offset = 2
            if (
                cell_rect.width() < 140 and cell_rect.width() > 135
            ):  # Text display problems between 125 and 130 to fix
                cell_rect.setWidth(140)
            cell: CellItem[BaseElementModel] = index.data()
            sub_option = QStyleOptionViewItem(option)
            if cell:
                cmodel = CellModel(cell, index)
                for i, model in enumerate(cell):
                    if model:
                        delegate: BaseElementDelegate = model.delegate(None, self.parent())
                        delegate_size = delegate.sizeHint(sub_option, cmodel.index(i, 0))
                        sub_option.rect = QRect(
                            QPoint(cell_rect.x(), cell_rect.y() + y_offset),
                            delegate_size,
                        )
                        if Trindex(index, i) == self.hovered_index:
                            painter.save()
                            super().paint(painter, sub_option, QModelIndex())
                            painter.restore()
                        else:
                            pass
                        delegate.paint(painter, sub_option, cmodel.index(i, 0), False)
                        y_offset += delegate_size.height()

            if self.extra_emit:
                self.sizeHintChanged.emit(index)
                self.extra_emit = False

    def createEditor(
        self, parent: QWidget | None, option: QStyleOptionViewItem, index: QModelIndex
    ) -> QWidget | None:
        self._editor = CellEditor(parent)
        self._editor.geometriesChanged.connect(
            lambda: self.update_cell_geometry(option.rect, index)
        )
        self._editor.setFocus()
        self._open_editor_index = index
        return self._editor

    def updateEditorGeometry(
        self, editor: QWidget | None, option: QStyleOptionViewItem, index: QModelIndex
    ) -> None:
        editor_rect = option.rect.adjusted(2, 2, -2, -2)
        if editor.geometry() != editor_rect:
            editor.setGeometry(editor_rect)
            editor.viewport().update()

    def setEditorData(self, editor: CellEditor | None, index: QModelIndex) -> None:
        if editor:
            model: CellItem = index.data(Qt.ItemDataRole.EditRole)
            editor.setModel(model)
            self.editorOpened.emit(editor)

            if self.hovered_index.table_index == index:
                selected = model.index(self.hovered_index.cell_index, 0)
                editor.edit(selected)
                return

    def setModelData(self, editor: CellEditor, model: TableModel, index: QModelIndex):
        model.setData(index, editor.model().item)

    def update_cell_geometry(self, rect: QRect, index: QModelIndex) -> None:
        item: CellItem = index.data()
        item.recalculate_items()
        self.sizeHintChanged.emit(index)

    def eventFilter(self, object: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.FocusOut:
            return True

        if isinstance(event, QKeyEvent) and isinstance(object, CellEditor):
            if object.state() == QListView.State.EditingState:
                object.keyPressEvent(event)
                return True

        return super().eventFilter(object, event)

    def destroyEditor(self, editor: CellEditor, index: QModelIndex):
        self._open_editor_index = QModelIndex()
        super().destroyEditor(editor, index)

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        if index.isValid():
            return index.data(Qt.ItemDataRole.SizeHintRole)
        return QSize(0, 0)


class HeaderView(QHeaderView):
    editingStarted = pyqtSignal()

    def __init__(self, orientation: Qt.Orientation, parent: QWidget | None = ...) -> None:
        super().__init__(orientation, parent)
        self.line_edit = QLineEdit(self)
        self._last_section = 0
        self._state = QByteArray()

        self.setSectionsClickable(True)
        self.setHighlightSections(True)
        self.setStretchLastSection(False)
        self.setSectionsMovable(True)
        self.line_edit.hide()

        self.line_edit.editingFinished.connect(self.on_editing_finished)
        self.sectionDoubleClicked.connect(self.activate_editor)
        self.sectionPressed.connect(self.remember)
        self.sectionResized.connect(self.on_section_resized)

        if orientation == Qt.Orientation.Horizontal:
            self.setFixedHeight(30)
            self.setMinimumSectionSize(100)
        else:
            self.setFixedWidth(30)
            self.setMinimumSectionSize(30)

    def model(self) -> TableModel:
        return super().model()

    def activate_editor(self, section: int) -> None:
        if self.orientation() == Qt.Orientation.Horizontal:
            self.editingStarted.emit()
            text = self.model().headerData(
                self.visualIndex(section),
                self.orientation(),
                Qt.ItemDataRole.DisplayRole,
            )
            self.line_edit.setText(text)
            self.line_edit.show()
            self._last_section = self.visualIndex(section)
            rect = self.rect()
            pos = self.sectionPosition(section)
            self.line_edit.setGeometry(
                rect.x() + pos, rect.y(), self.sectionSize(section), rect.height()
            )

    def on_section_resized(self, logicalIndex: int, oldSize: int, newSize: int) -> None:
        # CHANGED TO LOGICAL INDEX

        if self.orientation() == Qt.Orientation.Horizontal:
            cells: list[CellItem] = self.model().get_column(logicalIndex)
            for cell in cells:
                cell.recalculate_items()
            self.model().setHeaderData(
                logicalIndex,
                self.orientation(),
                QSize(newSize, 30),
                Qt.ItemDataRole.SizeHintRole,
            )

    def on_editing_finished(self) -> None:
        text = self.line_edit.text()
        self.model().setHeaderData(
            self._last_section, self.orientation(), text, Qt.ItemDataRole.DisplayRole
        )
        self.line_edit.hide()

    def remember(self) -> None:
        self._state = self.saveState()


class BaseTable(QTableView):
    changeMade = pyqtSignal()
    editingLevelChanged = pyqtSignal(EditingLevel)
    currentEditorIndexChanged = pyqtSignal(QModelIndex)
    clipboardChanged = pyqtSignal(ClipboardContent)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._painting = True
        self._editor: CellEditor | None = None
        self._drag_start_position: QPoint | None = None
        self._visible_row = -1
        self._definition_for_mime_data = None
        self._toolset_reference: dict[str, BaseElementDefinitions] | None = None
        self._element_selection = Settings.value("User/editor.single_selection")
        self._entered_cell = CellGeometry(QModelIndex())

        self.setEditTriggers(QTableView.EditTrigger.CurrentChanged)
        self.setDragEnabled(True)
        self.setDragDropMode(QTableView.DragDropMode.DragDrop)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setCornerButtonEnabled(False)
        self.setMouseTracking(True)

        self.entered.connect(self._on_entered)

        self.setVerticalScrollMode(QTableView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QTableView.ScrollMode.ScrollPerPixel)
        self.verticalScrollBar().setSingleStep(10)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectItems)

        self.setItemDelegate(CellDelegate(self))
        self.itemDelegate().sizeHintChanged.connect(self.update_row_geometries)
        self.itemDelegate().editorOpened.connect(self.on_editor_opened)

        self.setHorizontalHeader(HeaderView(Qt.Orientation.Horizontal, self))
        self.setVerticalHeader(HeaderView(Qt.Orientation.Vertical, self))

        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.verticalHeader().sectionMoved.connect(self.update_row_geometries)
        self.verticalHeader().sectionMoved.connect(self.close_active_editor)
        self.verticalHeader().sectionMoved.connect(self._on_vsection_moved)
        self.horizontalHeader().sectionResized.connect(self.close_active_editor)
        self.horizontalHeader().editingStarted.connect(self.close_active_editor)
        self.horizontalHeader().sectionMoved.connect(self._on_hsection_moved)

        self.count_label = QLabel()

        QApplication.clipboard().changed.connect(self._on_clipboard_changed)

    @property
    def editor(self) -> CellEditor | None:
        return self._editor

    def enable_painting(self, painting: bool) -> None:
        self._painting = painting

    def current_model(self) -> BaseElementModel | None:
        """Return model of editor's current index"""
        if self.editor:
            return self.editor.currentIndex().data()
        return None

    # States

    def check_clipboard(self) -> None:
        self._on_clipboard_changed()

    def editing_level(self) -> EditingLevel:
        if self.editor:
            if self.editor.state() == QListView.State.EditingState:
                return EditingLevel.CellEditing | EditingLevel.ElementEditing
            return EditingLevel.CellEditing
        return EditingLevel.NoEditing

    def can_create_from_clipboard(self) -> bool:
        return bool(self._definition_for_mime_data)

    # Model connection and signal handling

    def model(self) -> TableModel:
        return super().model()

    def itemDelegate(self) -> CellDelegate:
        return super().itemDelegate()

    def setModel(self, model: QAbstractItemModel | None) -> bool:
        if model:
            super().setModel(model)
            self.setCurrentIndex(QModelIndex())

            self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

            self.model().dataChanged.connect(self.set_extra_emit)
            self.model().dataChanged.connect(self.update_row_geometries)
            self.model().modelChanged.connect(self.on_model_changed)
            self.model().columnsMoved.connect(self.update_row_geometries)
            self.model().rowsMoved.connect(self.update_row_geometries)
            self.model().rowsInserted.connect(self.update_count_label)
            self.model().rowsRemoved.connect(self.update_count_label)
            self.model().rowsRemoved.connect(self._on_row_removed)
            self.model().columnsInserted.connect(self.update_count_label)
            self.model().columnsRemoved.connect(self.update_count_label)
            self.model().columnsRemoved.connect(self._on_column_removed)

            for column in range(self.model().columnCount()):
                size = (
                    self.model()
                    .headerData(column, Qt.Orientation.Horizontal, Qt.ItemDataRole.SizeHintRole)
                    .width()
                )
                self.horizontalHeader().resizeSection(column, size)

            self.update_row_geometries()
            self.update_count_label()

            return True

        return False

    # Signal Handler

    def on_model_changed(self) -> None:
        self.changeMade.emit()

    def _on_entered(self, index: QModelIndex) -> None:
        self._entered_cell = CellGeometry(index)

    def _on_row_removed(self, parent: QModelIndex, first: int, last: int) -> None:
        for row in range(first, self.model().rowCount()):
            self.model().setHeaderData(
                row,
                Qt.Orientation.Vertical,
                self.verticalHeader().visualIndex(row),
                Qt.ItemDataRole.EditRole,
            )

    def _on_column_removed(self, parent: QModelIndex, first: int, last: int) -> None:
        for col in range(first, self.model().columnCount()):
            self.model().setHeaderData(
                col,
                Qt.Orientation.Horizontal,
                self.verticalHeader().visualIndex(col),
                Qt.ItemDataRole.EditRole,
            )

    def _on_hsection_moved(self, logicalIndex: int, oldVisualIndex: int, newVisualIndex: int):
        StandardLogger.debug(
            f"H-Section moved from {oldVisualIndex} to {newVisualIndex}",
            extra={"sender": "BASETABLE"},
        )
        starting_index = min(oldVisualIndex, newVisualIndex)
        for visual_index in range(starting_index, self.model().columnCount()):
            self.model().setHeaderData(
                self.horizontalHeader().logicalIndex(visual_index),
                Qt.Orientation.Horizontal,
                visual_index,
                Qt.ItemDataRole.EditRole,
            )

    def _on_vsection_moved(self, logicalIndex: int, oldVisualIndex: int, newVisualIndex: int):
        StandardLogger.debug(
            f"V-Section moved from {oldVisualIndex} to {newVisualIndex}",
            extra={"sender": "BASETABLE"},
        )
        starting_index = min(oldVisualIndex, newVisualIndex)
        for visual_index in range(starting_index, self.model().rowCount()):
            self.model().setHeaderData(
                self.verticalHeader().logicalIndex(visual_index),
                Qt.Orientation.Vertical,
                visual_index,
                Qt.ItemDataRole.EditRole,
            )

    def _on_clipboard_changed(self) -> None:
        flags = ClipboardContent(0)
        mime_data = QApplication.clipboard().mimeData()
        if mime_data:
            self._definition_for_mime_data = definition_for_mime_data(mime_data)
            if self._definition_for_mime_data:
                flags |= ClipboardContent.ElementData

            if "application/x-teachart" in mime_data.formats():
                flags |= ClipboardContent.CopiedIndex

        if not flags:
            flags = ClipboardContent.NotParsable

        StandardLogger.debug(
            f"Clipboard data changed with flags '{flags}' and parsable definition '{self._definition_for_mime_data}'.",
            extra={"sender": "TABLE"},
        )
        self.clipboardChanged.emit(flags)

    # Editor interaction

    @pyqtSlot(QAction)
    def handle_cell_action(self, action: QAction) -> None:
        if self.editor:
            match action.data():
                case CellAction.Discard:
                    self.editor.close_active_editor(False)
                    return
                case CellAction.Accept:
                    self.editor.close_active_editor()
                    return
                case CellAction.RemoveElement:
                    self.editor.remove_current_element()
                    return
                case CellAction.MoveUp:
                    self.editor.move_element_up()
                    return
                case CellAction.MoveDown:
                    self.editor.move_element_down()
                    return
                case CellAction.Clear:
                    self.editor.clear_item()
                    return

    @pyqtSlot(QAction)
    def handle_element_action(self, action: QAction) -> None:
        if self.editor and action.property("is_element_action"):
            model = self.editor.model()
            model.create_model(action.data())

    def add_clipboard_data(self) -> None:
        if self.editor and self.can_create_from_clipboard():
            self.editor.model().create_from_clipboard(self._definition_for_mime_data)

    def add_column_after_current(self) -> None:
        current = self.currentIndex()
        if current.isValid():
            logical_current = current.column()
            visual_current = self.horizontalHeader().visualIndex(logical_current)

            new_logical = self.model().columnCount()
            self.model().insertColumn(new_logical)

            self.horizontalHeader().moveSection(new_logical, visual_current + 1)
            self.setCurrentIndex(current)

    def add_column_at_end(self) -> None:
        new_logical = self.model().columnCount()
        self.model().insertColumn(new_logical)

    def add_row_after_current(self) -> None:
        current = self.currentIndex()
        if current.isValid():
            logical_current = current.row()
            visual_current = self.verticalHeader().visualIndex(logical_current)

            new_logical = self.model().rowCount()
            self.model().insertRow(new_logical)

            self.verticalHeader().moveSection(new_logical, visual_current + 1)
            self.setCurrentIndex(current)

    def add_row_at_end(self) -> None:
        new_logical = self.model().rowCount()
        self.model().insertRow(new_logical)

    # DELETE
    def add_element(self, element: BaseElementModel) -> None:
        if self.currentIndex().isValid():
            cell = self.currentIndex().data()
            cell.append(element)
            self.model().dataChanged.emit(self.currentIndex(), self.currentIndex())

    def set_extra_emit(self):
        self.itemDelegate().extra_emit = True

    def paintEvent(self, e):
        if self._painting:
            self.verticalHeader().resizeSections()
            super().paintEvent(e)

    def update_row_geometries(self) -> None:
        self.verticalHeader().resizeSections()
        self.update()
        self.viewport().update()

    def update_count_label(self) -> None:
        translated1 = tr("R")
        translated2 = tr("C")
        self.count_label.setText(
            f"{translated1} {self.model().rowCount()} | {translated2} {self.model().columnCount()}"
        )

    def cache_editor(self, editor: CellEditor) -> None:
        self._editor = editor

    @pyqtSlot(CellEditor)
    def on_editor_opened(self, editor: CellEditor) -> None:
        """Connects the cell editor with the signals to notify the editor tab"""
        StandardLogger.debug(
            f"Editor opened '{editor}' at {self.currentIndex().row()}|{self.currentIndex().column()}",
            extra={"sender": "TABLE"},
        )
        if editor:
            self.cache_editor(editor)
            self._editor.set_toolset_reference(self._toolset_reference)
            self._editor.selectionModel().currentChanged.connect(
                self.currentEditorIndexChanged.emit
            )
            self.editingLevelChanged.emit(self.editing_level())
            if self._editor.model():
                self._editor.model().modelChanged.connect(self.changeMade.emit)
                self._editor.model().dataChanged.connect(self.changeMade.emit)

    def set_toolset_reference(self, toolsets: dict[str, BaseElementToolset]) -> None:
        if not self._toolset_reference:
            self._toolset_reference = toolsets

    def close_active_editor(self, hint=QStyledItemDelegate.EndEditHint.NoHint) -> None:
        if self.selectionModel():
            self.selectionModel().clearCurrentIndex()
        if self.editor:
            self.editor.disconnect()
            self.closeEditor(self.editor, hint)

    def closeEditor(self, editor: CellEditor | None, hint: QStyledItemDelegate.EndEditHint) -> None:
        if editor and editor.state() != QListView.State.EditingState:
            editor.close_active_editor()
        super().closeEditor(editor, hint)
        StandardLogger.debug(
            f"An cell editor has been closed: {editor}, {hint}", extra={"sender": "TABLE"}
        )
        self.verticalHeader().resizeSections()
        self._editor = None
        self.model().clear_cache()
        self.setCurrentIndex(QModelIndex())
        self.editingLevelChanged.emit(EditingLevel.NoEditing)

    # Event handler

    def keyReleaseEvent(self, ev: QKeyEvent):
        if ev.keyCombination().keyboardModifiers() & Qt.KeyboardModifier.ControlModifier:
            updated_index = self.itemDelegate().hovered_index.table_index
            self.itemDelegate().hovered_index = Trindex(QModelIndex(), -1)
            self.update(updated_index)

        super().keyReleaseEvent(ev)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton:
            if self._drag_start_position:
                distance = (event.pos() - self._drag_start_position).manhattanLength()
                if distance >= QApplication.startDragDistance():
                    drag = QDrag(self)
                    mime_data = self.model().mimeData(
                        [self.currentIndex()], Qt.DropAction.MoveAction
                    )
                    drag.setMimeData(mime_data)
                    drag.exec(Qt.DropAction.MoveAction)

        if event.modifiers() & Qt.KeyboardModifier.ControlModifier or (
            self._element_selection and not event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            index = self.indexAt(event.pos())
            cell_rect = self.visualRect(index)
            cell_idx = self._entered_cell.get_cell_index(cell_rect.topLeft(), event.pos())
            trindex = Trindex(index, cell_idx)
            if trindex != self.itemDelegate().hovered_index:
                self.itemDelegate().hovered_index = trindex
                self.update(index)

        else:
            self.itemDelegate().hovered_index = Trindex(QModelIndex(), -1)

        super().mouseMoveEvent(event)

    def mousePressEvent(self, e) -> None:
        index = self.indexAt(e.pos())
        if e.button() == Qt.MouseButton.LeftButton and self.underMouse():
            self._drag_start_position = e.pos()
            if self.editor:
                self.close_active_editor()
                if index.isValid():
                    self.setCurrentIndex(index)
                e.accept()
                return
        super().mousePressEvent(e)

    def dropEvent(self, event: QDropEvent):
        drop_index = self.indexAt(event.position().toPoint())

        # Check if the item is dropped on the active editor
        if self._editor:
            editor_index = self.currentIndex()
            editor_rect = self._editor.mapToGlobal(self._editor.rect().topLeft())
            editor_rect = QRect(editor_rect, self._editor.size())
            drop_position = self.mapToGlobal(event.position().toPoint())

            if editor_rect.contains(drop_position) and drop_index == editor_index:
                drop_pos_local = self._editor.mapFromGlobal(drop_position)
                editor_event = QDropEvent(
                    drop_pos_local.toPointF(),
                    event.dropAction(),
                    event.mimeData(),
                    event.buttons(),
                    event.modifiers(),
                )
                self._editor.dropEvent(editor_event)
                event.accept()
                return

            if drop_index.isValid():
                self.close_active_editor()

        # Item is dropped on a different index
        if drop_index.isValid():
            success = self.model().dropMimeData(
                event.mimeData(),
                event.dropAction(),
                drop_index.row(),
                drop_index.column(),
                drop_index,
            )
            if success:
                event.accept()
                self.changeMade.emit()
            else:
                event.ignore()
        else:
            event.ignore()

    # Copy and paste functions

    def can_copy(self) -> bool:
        return self.currentIndex().isValid()

    def can_paste(self) -> bool:
        mime_data = QApplication.clipboard().mimeData()
        if mime_data:
            return "application/x-teachart" in mime_data.formats()
        return False

    def copy_index(self, index: QModelIndex) -> None:
        if index.isValid():
            if self.editor and self.editor.state() == QListView.State.EditingState:
                element_index = self.editor.currentIndex()
                if element_index.isValid():
                    # Copy the individual element
                    self.editor.copy_index(element_index)
                    return

        clipboard = QApplication.clipboard()
        mime_data = self.model().mimeData([index], Qt.DropAction.CopyAction)
        clipboard.setMimeData(mime_data)
        StandardLogger.debug(
            f"Copied entire cell at {index.row()}|{index.column()}", extra={"sender": "TABLE"}
        )

    def copy_current_index(self) -> None:
        if self.editing_level() & EditingLevel.ElementEditing:
            self.editor.copy_current_index()
        elif self.editing_level() & EditingLevel.CellEditing:
            self.copy_index(self.currentIndex)

    def paste_index(self, mime_data: QMimeData) -> None:
        if mime_data and not set(mime_data.formats()).isdisjoint(set(self.model().mimeTypes())):
            current = self.currentIndex()
            self.setCurrentIndex(QModelIndex())
            if current.isValid():
                self.model().dropMimeData(
                    mime_data,
                    Qt.DropAction.CopyAction,
                    current.row(),
                    current.column(),
                    current,
                )


class Table(BaseTable):
    sizesSplitted = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._top_idx = QModelIndex()
        self._view_mode = TableViewMode.Table
        self._pres_mode = False
        self._can_close_editor = True
        self._exclusive_row = -1

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        self.verticalScrollBar().valueChanged.connect(self.on_vscrolled)
        self.verticalScrollBar().rangeChanged.connect(self.on_vslider_range_changed)

        self.horizontalScrollBar().valueChanged.connect(self.on_hscrolled)
        self.horizontalScrollBar().rangeChanged.connect(self.on_hslider_range_changed)

        # Linked Widgets

        self.row_list = QComboBox()
        self.row_list.activated.connect(
            lambda row: self.scroll_to_index(self.verticalHeader().logicalIndex(row), -1)
        )

        self.frozen_table = FrozenRowTable(self)

        self.frozen_table.changeMade.connect(self.changeMade.emit)
        self.frozen_table.horizontalHeader().sectionResized.connect(self.close_active_editor)
        self.frozen_table.unfrozen.connect(self.unfreeze_row)
        self.frozen_table.editingLevelChanged.connect(self.editingLevelChanged.emit)

        self.horizontalScrollBar().valueChanged.connect(
            self.frozen_table.horizontalScrollBar().setValue
        )
        self.verticalHeader().sectionMoved.connect(
            lambda x, y, z: self.frozen_table.verticalHeader().moveSection(y, z)
        )

    # Model setter / getter

    def model(self) -> TableModel:
        return super().model()

    def setModel(self, model: QAbstractItemModel | None) -> bool:
        result = super().setModel(model)
        if result:
            model.rowsAboutToBeRemoved.connect(self._on_rows_about_to_be_removed)
            model.rowsInserted.connect(self._on_rows_inserted)
            self.on_vscrolled()
            self.on_hscrolled()
            self.row_list.setModel(IndexModel(self.verticalHeader()))
            self.row_list.setCurrentIndex(0)
        return result

    def has_frozen_row(self) -> bool:
        return self.frozen_table.isVisible() and self.frozen_table.model()

    def enable_presenter_mode(self, enabled: bool) -> None:
        self._pres_mode = enabled
        if self.editor:
            self.editor.enable_presenter_mode(enabled)

    def currentIndex(self):
        table_idx = super().currentIndex()
        frozen_idx = self.frozen_table.currentIndex()
        return frozen_idx if frozen_idx.isValid() else table_idx

    def add_column_after_current(self):
        if self.has_frozen_row():
            self.frozen_table.add_column_after_current()
        else:
            super().add_column_after_current()

    def add_row_after_current(self):
        if self.has_frozen_row():
            self.frozen_table.add_row_after_current()
        else:
            super().add_row_after_current()

    def _on_rows_about_to_be_removed(self, parent: QModelIndex, first: int, last: int) -> None:
        if self._view_mode == TableViewMode.SingleRow:
            if self._exclusive_row >= first and self._exclusive_row <= last:
                incr = 1 if self._exclusive_row < self.model().rowCount() - 1 else -1
                self.scroll_by(incr)

    def _on_rows_inserted(self, parent: QModelIndex, first: int, last: int) -> None:
        if self._view_mode == TableViewMode.SingleRow:
            for row in range(first, last + 1):
                self.hideRow(row)

    # Editor functions

    @property
    def editor(self):
        return super().editor if super().editor else self.frozen_table.editor

    @pyqtSlot(CellEditor)
    def on_editor_opened(self, editor: CellEditor) -> None:
        """Connects the cell editor with the signals to notify the editor"""
        StandardLogger.debug(
            f"Editor opened '{editor}' at {self.currentIndex().row()}|{self.currentIndex().column()}",
            extra={"sender": "TABLE"},
        )
        if editor:
            self.cache_editor(editor)
            if self.has_frozen_row():
                self.frozen_table.close_active_editor()
            self._editor.set_toolset_reference(self._toolset_reference)
            self._editor.selectionModel().currentChanged.connect(
                self.currentEditorIndexChanged.emit
            )
            self.editingLevelChanged.emit(self.editing_level())
            if self._editor.model():
                self._editor.model().modelChanged.connect(self.changeMade.emit)
                self._editor.model().dataChanged.connect(self.changeMade.emit)

    def close_active_editor(self, hint=QStyledItemDelegate.EndEditHint.NoHint):
        if self.has_frozen_row() and self.frozen_table.state() == QTableView.State.EditingState:
            self.frozen_table.close_active_editor()
        else:
            super().close_active_editor(hint)

    def set_toolset_reference(self, toolsets):
        super().set_toolset_reference(toolsets)
        self.frozen_table.set_toolset_reference(toolsets)

    # Scrolling behaviour

    def _on_vsection_moved(self, logicalIndex, oldVisualIndex, newVisualIndex):
        super()._on_vsection_moved(logicalIndex, oldVisualIndex, newVisualIndex)
        self._top_idx = self.indexAt(QPoint(0, 0))
        self.on_vslider_range_changed(0, self.verticalScrollBar().maximum())

    def on_vslider_range_changed(self, min: int, max: int) -> None:
        if self.model() and self._view_mode == TableViewMode.Table:
            if min != max and self.model():
                self.verticalScrollBar().blockSignals(True)
                last_row_height = self.sizeHintForRow(
                    self.verticalHeader().logicalIndex(self.model().rowCount() - 1)
                )
                added_height = self.height() - last_row_height
                if added_height > 0:
                    self.verticalScrollBar().setMaximum(max + added_height)
                else:
                    self.verticalScrollBar().setMaximum(max + 200)
                self.verticalScrollBar().blockSignals(False)
            else:
                self.verticalScrollBar().blockSignals(True)
                last_row_height = self.sizeHintForRow(
                    self.verticalHeader().logicalIndex(self.model().rowCount() - 1)
                )
                self.verticalScrollBar().setMaximum(last_row_height)
                self.verticalScrollBar().blockSignals(False)

        self.on_vscrolled()

    def on_vscrolled(self) -> None:
        self._top_idx = self.indexAt(QPoint(0, 0))
        if self._top_idx.isValid():
            try:
                self.row_list.blockSignals(True)
                self.row_list.setCurrentIndex(
                    self.verticalHeader().visualIndex(self._top_idx.row())
                )
                self.row_list.blockSignals(False)
            except IndexError:
                pass

    def _on_hsection_moved(self, logicalIndex, oldVisualIndex, newVisualIndex):
        super()._on_hsection_moved(logicalIndex, oldVisualIndex, newVisualIndex)
        self._top_idx = self.indexAt(QPoint(0, 0))
        self.on_hslider_range_changed(0, self.horizontalScrollBar().maximum())

    def on_hscrolled(self) -> None:
        self._top_idx = self.indexAt(QPoint(0, 0))

    def on_hslider_range_changed(self, min: int, max: int) -> None:
        if self.model():
            self.horizontalScrollBar().blockSignals(True)
            if min != max:
                # self.frozen_table.horizontalScrollBar().blockSignals(True)
                last_col_width = self.columnWidth(
                    self.horizontalHeader().logicalIndex(self.model().columnCount() - 1)
                )
                added_width = self.width() - last_col_width
                if added_width > 0:
                    self.horizontalScrollBar().setMaximum(max + added_width - 30)
                    self.frozen_table.horizontalScrollBar().setMaximum(max + added_width - 30)
                else:
                    self.horizontalScrollBar().setMaximum(max + 200)
                    self.frozen_table.horizontalScrollBar().setMaximum(max + 200)
                # self.frozen_table.horizontalScrollBar().blockSignals(False)
            else:
                # self.frozen_table.horizontalScrollBar().blockSignals(True)
                pos = sum(self.columnWidth(col) for col in range(self.model().columnCount() - 1))
                self.horizontalScrollBar().setMaximum(pos)
                self.frozen_table.horizontalScrollBar().setMaximum(pos)
            self.horizontalScrollBar().blockSignals(False)
            # self.frozen_table.horizontalScrollBar().blockSignals(False)

    def iterate_column_indices(self, logical_stop: int) -> Iterator[int]:
        """Iterates visual indices from 0 to stop and returns their logical indices."""
        visual_stop = self.horizontalHeader().visualIndex(logical_stop)
        for visual_column in range(visual_stop):
            logical_column = self.horizontalHeader().logicalIndex(visual_column)
            yield logical_column

    def scroll_to_index(self, row: int, column: int) -> None:
        """Scrolls the view to the given logical 'row' and 'column'."""
        idx_row = max(row, 0)
        idx_col = max(column, 0)
        StandardLogger.debug(
            f"Go to logical index {idx_row} | {idx_col}",
            extra={"sender": "TABLE"},
        )

        if self._view_mode == TableViewMode.Table:
            model_index = self.model().index(idx_row, idx_col)
            # mapped = self.model().mapFromSource(model_index)
            if column == -1 and row >= 0:
                hvalue = self.horizontalScrollBar().value()
                self.scrollTo(model_index, QTableView.ScrollHint.PositionAtTop)
                self.horizontalScrollBar().setValue(hvalue)
            elif row == -1 and column >= 0:
                vvalue = self.verticalScrollBar().value()
                position = sum(
                    self.columnWidth(col) for col in self.iterate_column_indices(idx_col)
                )
                self.horizontalScrollBar().setValue(position)
                self.verticalScrollBar().setValue(vvalue)
            else:
                self.scrollTo(model_index, QTableView.ScrollHint.PositionAtTop)

        elif self._view_mode == TableViewMode.SingleRow:
            model_index = self.model().index(idx_row, idx_col)
            if row == -1 and column >= 0:
                vvalue = self.verticalScrollBar().value()
                position = sum(
                    self.columnWidth(col) for col in self.iterate_column_indices(idx_col)
                )
                self.horizontalScrollBar().setValue(position)
                self.verticalScrollBar().setValue(vvalue)
                return

            self.change_exclusive_row(self._exclusive_row, model_index.row())
            self.row_list.setCurrentIndex(self.verticalHeader().visualIndex(idx_row))

            if self.currentIndex().isValid() and self.currentIndex().row() != self._exclusive_row:
                self.setCurrentIndex(QModelIndex())

    def scroll_by(self, row_incr: int, column_incr=0) -> None:
        """Scroll the table by increasing/decreasing the visual index by the given row and column increment parameters. The frozen row index is skipped."""
        current_row = self.verticalHeader().visualIndex(self._top_idx.row())
        current_col = self.horizontalHeader().visualIndex(self._top_idx.column())

        dest_row = current_row + row_incr
        if dest_row == self.verticalHeader().visualIndex(self.frozen_table.frozen_row):
            dest_row += row_incr
        dest_column = current_col + column_incr

        if dest_row >= 0 and dest_row < self.row_list.count() and column_incr == 0:
            logical_dest_row = self.verticalHeader().logicalIndex(dest_row)
            self.scroll_to_index(logical_dest_row, -1)
        elif dest_column >= 0 and dest_column < self.model().columnCount() and row_incr == 0:
            logical_dest_column = self.horizontalHeader().logicalIndex(dest_column)
            self.scroll_to_index(-1, logical_dest_column)
        elif row_incr != 0 and column_incr != 0:
            logical_dest_row = self.verticalHeader().logicalIndex(dest_row)
            logical_dest_column = self.horizontalHeader().logicalIndex(dest_column)
            self.scroll_to_index(logical_dest_row, logical_dest_column)

    def scroll_to_current(self) -> None:
        if self.currentIndex().isValid():
            self.scroll_to_index(self.currentIndex().row(), self.currentIndex().column())

    # View mode handling

    def set_view_mode(self, mode: TableViewMode) -> None:
        """Changed the view mode of the table. If 'Table' the entire table is shown. If 'SingleRow' only one row is shown at a time."""
        StandardLogger.debug(
            f"Change view mode to {mode}",
            extra={"sender": "TABLE"},
        )
        if mode == TableViewMode.Table:
            self._view_mode = mode
            self._exclusive_row = -1
            self.show_all_rows()
            self.on_vscrolled()

        elif mode == TableViewMode.SingleRow:
            if self._top_idx.isValid():
                self._exclusive_row = self._top_idx.row()
            else:
                self._exclusive_row = 0
            self._view_mode = mode

            self.show_only_row(self._exclusive_row)

            if self.currentIndex().isValid() and self.currentIndex().row() != self._exclusive_row:
                self.setCurrentIndex(QModelIndex())

    def change_exclusive_row(self, old: int, new: int) -> None:
        self.setRowHidden(old, True)
        self.setRowHidden(new, False)
        self._exclusive_row = new
        self._top_idx = self.indexAt(QPoint(0, 0))

    def show_only_row(self, visible_row: int) -> None:
        """Hides all rows except row with the given logical index."""
        for row in range(self.model().rowCount()):
            self.setRowHidden(row, row != visible_row)
        self._top_idx = self.indexAt(QPoint(0, 0))

    def show_all_rows(self) -> None:
        for row in range(self.model().rowCount()):
            self.setRowHidden(row, row == self.frozen_table.frozen_row)

    def freeze_current_row(self) -> None:
        if self.currentIndex().isValid():
            if self.currentIndex().row() == self.frozen_table.frozen_row:
                self.unfreeze_row()
            else:
                self.freeze_row(self.currentIndex())

    def freeze_row(self, idx: QModelIndex) -> None:
        """Make a row fixed on top of the table to be always visible."""
        self.close_active_editor()
        if self.has_frozen_row():
            self.row_list.model().clear_inactive_indices()

        if self._view_mode is TableViewMode.SingleRow:
            if self.currentIndex().row() == idx.row():
                incr = 1 if self.currentIndex().row() + 1 < self.model().rowCount() else -1
                self.scroll_by(incr)

        else:
            # Hide the row in the main table instead of using filter
            if self.has_frozen_row():
                self.verticalHeader().setSectionHidden(self.frozen_table.frozen_row, False)
            self.verticalHeader().setSectionHidden(idx.row(), True)

        self.row_list.model().add_inactive_index(idx)

        self.frozen_table.freeze_row(self.model(), idx.row())

        self.frozen_table.horizontalHeader().sectionResized.connect(
            lambda x, y, z: self.horizontalHeader().resizeSection(x, z)
        )
        self.horizontalHeader().setVisible(False)

    def unfreeze_row(self) -> None:
        """Unfreezes the current frozen row"""
        self.close_active_editor()
        self.row_list.model().clear_inactive_indices()
        if self._view_mode is TableViewMode.SingleRow:
            pass
        else:
            # Show the previously hidden row
            if self.frozen_table.frozen_row >= 0:
                self.verticalHeader().setSectionHidden(self.frozen_table.frozen_row, False)

        self.frozen_table.unfreeze()
        self.horizontalHeader().setVisible(True)

    # Special model editing behaviour

    def remove_row(self, row: int = -1) -> None:
        """Removes specified row or if not current row"""
        rmv_row = row if row > -1 else self.currentIndex().row()
        model: TableModel = self.model()
        if self.editor and model.rowCount() > 1:
            if any(model.get_row(rmv_row)):
                result = QMessageBox.question(
                    None,
                    tr("Confirm removal"),
                    tr(
                        "This row has content. Are you sure you want to permanently remove this row?"
                    ),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if result == QMessageBox.StandardButton.Yes:
                    self.setCurrentIndex(QModelIndex())
                    model.removeRow(rmv_row)

            else:
                self.setCurrentIndex(QModelIndex())
                model.removeRow(rmv_row)

    def remove_column(self, column: int = -1) -> None:
        """Removes column from model and clears clipboard if index with same column was copied"""
        rmv_col = column if column > -1 else self.currentIndex().column()
        model: TableModel = self.model()
        if self.editor and self.model().columnCount() > 1:
            if any(model.get_column(rmv_col)):
                result = QMessageBox.question(
                    None,
                    tr("Confirm removal"),
                    tr(
                        "This column has content. Are you sure you want to permanently remove this column?"
                    ),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if result == QMessageBox.StandardButton.Yes:
                    self.setCurrentIndex(QModelIndex())
                    model.removeColumn(rmv_col)
                    if self.copied_index() and self.copied_index().column() == rmv_col:
                        QApplication.clipboard().clear()
            else:
                self.setCurrentIndex(QModelIndex())
                model.removeColumn(rmv_col)
                if not self.copied_index().isValid():
                    clipboard = QApplication.clipboard()
                    clipboard.mimeData().removeFormat("application/x-teachart")
                    clipboard.dataChanged.emit()

    def keyPressEvent(self, e: QKeyEvent):
        if Qt.KeyboardModifier.ControlModifier in e.keyCombination().keyboardModifiers():
            if e.key() == Qt.Key.Key_Down:
                self.scroll_by(1)
                e.accept()
                return
            elif e.key() == Qt.Key.Key_Up:
                self.scroll_by(-1)
                e.accept()
                return
            elif e.key() == Qt.Key.Key_Right:
                self.scroll_by(0, 1)
                e.accept()
                return
            elif e.key() == Qt.Key.Key_Left:
                self.scroll_by(0, -1)
                e.accept()
                return

        super().keyPressEvent(e)

    def wheelEvent(self, ev: QWheelEvent):
        if self._view_mode == TableViewMode.SingleRow:
            if ev.angleDelta().y() >= 15:
                self.scroll_by(-1)
            elif ev.angleDelta().y() <= -15:
                self.scroll_by(1)
        super().wheelEvent(ev)

    def show_context_menu(self, position):
        index = self.indexAt(position)
        if not index.isValid():
            return

        menu = QMenu(self)

        add_row_above_action = QAction("Add Row Above", self)
        add_row_above_action.triggered.connect(lambda: self.add_row(index.row()))
        menu.addAction(add_row_above_action)

        add_row_below_action = QAction("Add Row Below", self)
        add_row_below_action.triggered.connect(lambda: self.add_row(index.row() + 1))
        menu.addAction(add_row_below_action)

        add_column_left_action = QAction("Add Column Left", self)
        add_column_left_action.triggered.connect(lambda: self.add_column(index.column()))
        menu.addAction(add_column_left_action)

        add_column_right_action = QAction("Add Column Right", self)
        add_column_right_action.triggered.connect(lambda: self.add_column(index.column() + 1))
        menu.addAction(add_column_right_action)

        remove_row_action = QAction("Remove Row", self)
        remove_row_action.triggered.connect(lambda: self.remove_row(index.row()))
        menu.addAction(remove_row_action)

        remove_column_action = QAction("Remove Column", self)
        remove_column_action.triggered.connect(lambda: self.remove_column(index.column()))
        menu.addAction(remove_column_action)

        menu.exec(self.viewport().mapToGlobal(position))


class FrozenRowTable(BaseTable):
    unfrozen = pyqtSignal()

    def __init__(self, parent_table: Table, parent=None):
        super().__init__(parent)
        self._table = parent_table
        self._frozen = False
        self._frozen_row = -1

        self.setVisible(False)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.setSizeAdjustPolicy(QTableView.SizeAdjustPolicy.AdjustToContentsOnFirstShow)
        self.horizontalScrollBar().rangeChanged.connect(self.sync_scroll_bar_max)
        self.horizontalHeader().sectionMoved.connect(
            lambda x, y, z: self._table.horizontalHeader().moveSection(y, z)
        )
        self.verticalHeader().sectionMoved.disconnect()

    def model(self) -> TableModel | None:
        return super().model()

    @property
    def frozen_row(self) -> int:
        return self._frozen_row

    def setModel(self, model):
        if model:
            result = super().setModel(model)
            if result:
                model.rowsInserted.connect(lambda: self.verticalHeader().viewport().update())
                model.rowsInserted.connect(self._on_rows_inserted)
                model.rowsRemoved.connect(self._on_rows_removed)
                model.dataChanged.connect(self._update_size)
            return result
        return super().setModel(model)

    def freeze_row(self, model: TableModel, visible_source_idx: int) -> None:
        self._frozen_row = visible_source_idx

        self.hide()
        if self.model():
            self.setModel(None)
        self.setModel(model)

        if not self._frozen:
            self.horizontalHeader().restoreState(self._table.horizontalHeader().saveState())
            self.verticalHeader().restoreState(self._table.verticalHeader().saveState())
            self._frozen = True

        if visible_source_idx >= 0:
            # Show only the frozen row - hide all others
            for row in range(self.model().rowCount()):
                if row != visible_source_idx:
                    self.verticalHeader().setSectionHidden(row, True)
                else:
                    self.verticalHeader().setSectionHidden(row, False)

        self.show()

    def unfreeze(self) -> None:
        self.setModel(None)
        self._frozen_row = -1
        self._frozen = False
        self.hide()

    def on_editor_opened(self, editor: CellEditor | None):
        if not editor:
            return
        self._table.close_active_editor()
        super().on_editor_opened(editor)
        self._editor.selectionModel().currentChanged.connect(
            self._table.currentEditorIndexChanged.emit
        )
        self._table.editingLevelChanged.emit(self.editing_level())

    def paste_index(self, mime_data):
        super().paste_index(mime_data)
        self.hideRow(self._frozen_row)
        self.showRow(self._frozen_row)

    def add_column_after_current(self) -> None:
        if self._table.currentIndex().isValid():
            logical_current = self._table.currentIndex().column()
            visual_current = self.horizontalHeader().visualIndex(logical_current)

            new_logical = self.model().columnCount()
            self.model().insertColumn(new_logical)

            self.horizontalHeader().moveSection(new_logical, visual_current + 1)

    def add_row_after_current(self) -> None:
        if self._table.currentIndex().isValid():
            logical_current = self._table.currentIndex().row()
            visual_current = self._table.verticalHeader().visualIndex(logical_current)

            new_logical = self.model().rowCount()
            self.model().insertRow(new_logical)

            self._table.verticalHeader().moveSection(new_logical, visual_current + 1)

    def _update_size(self) -> None:
        pass
        # self.freeze_row(self.model(), self.frozen_row)

    def _on_rows_inserted(self, parent: QModelIndex, first: int, last: int) -> None:
        for row in range(first, last + 1):
            self.verticalHeader().setSectionHidden(row, True)

    def _on_rows_removed(self, parent: QModelIndex, first: int, last: int) -> None:
        if self.frozen_row <= last and self.frozen_row >= first:
            self.unfrozen.emit()

    def sync_scroll_bar_max(self) -> None:
        parent_max = self._table.horizontalScrollBar().maximum()
        if parent_max != self.horizontalScrollBar().maximum():
            self.horizontalScrollBar().blockSignals(True)
            self.horizontalScrollBar().setMaximum(parent_max)
            self.horizontalScrollBar().blockSignals(False)

    def dropEvent(self, event):
        super().dropEvent(event)
        if event.isAccepted():
            self.hide()
            self.show()
            self.setState(QTableView.State.NoState)
            self.viewport().update()

    def sizeHint(self) -> QSize:
        if self.model():
            height = self.rowHeight(self._frozen_row) + 35
            if height > self.parent().height():
                return QSize(self.width(), self.parent().height() // 2)
            return QSize(self.width(), height)
        else:
            return super().sizeHint()

    def update_row_geometries(self):
        super().update_row_geometries()
        self.adjustSize()

    def wheelEvent(self, ev: QWheelEvent):
        if ev.angleDelta().x() != 0:
            self._table.wheelEvent(ev)
        return super().wheelEvent(ev)


class ArrowPath(QPainterPath):
    def __init__(self, p1: QPointF, p2: QPointF, pen: QPen = QPen()):
        super().__init__()
        self.pen = pen
        self.pen.setWidthF(1.0)
        self.brush = QBrush(Qt.BrushStyle.SolidPattern)
        self.brush.setColor(self.pen.color())
        self.mode = QPainter.CompositionMode.CompositionMode_SourceOver

        # Sorry I'm bad at maths so I made an AI write the vector calculations for me

        # Draw line from p1 to p2
        self.moveTo(p1)
        self.lineTo(p2)

        # Calculate direction vector from p1 to p2
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        length = sqrt(dx**2 + dy**2)

        # If points are the same, just return (no arrow to draw)
        if length == 0:
            return

        # Normalize direction vector
        dx_norm = dx / length
        dy_norm = dy / length

        # Arrow head height (0.25 of the line length)
        arrow_height = length * 0.25

        # For equilateral triangle: side = 2 * height / sqrt(3)
        side_length = 2 * arrow_height / sqrt(3)

        # Calculate base center point (0.25 length back from p2)
        base_x = p2.x() - arrow_height * dx_norm
        base_y = p2.y() - arrow_height * dy_norm

        # Perpendicular vector (rotated 90 degrees counter-clockwise)
        perp_x = -dy_norm
        perp_y = dx_norm

        # Two base points of the triangle (half side length on each side)
        half_side = side_length / 2
        a1 = QPointF(base_x + half_side * perp_x, base_y + half_side * perp_y)
        a2 = QPointF(base_x - half_side * perp_x, base_y - half_side * perp_y)

        # Create equilateral triangle with p2 as the apex
        head = QPolygonF()
        head.append(p2)
        head.append(a1)
        head.append(a2)
        head.append(p2)

        self.addPolygon(head)


class FormattedLine(QPolygonF):
    def __init__(self):
        super().__init__()
        self.pen = QPen()
        self.mode = QPainter.CompositionMode.CompositionMode_SourceOver

    def contains(self, value: QPointF):
        return self.containsPoint(value, Qt.FillRule.OddEvenFill)


class PointerPen(QPen):
    def __init__(self):
        super().__init__()
        self.setWidthF(2.0)
        self.setColor(Qt.GlobalColor.red)


class CanvasScene(QGraphicsScene):
    def __init__(self):
        super().__init__()
        self._lines: list[FormattedLine | ArrowPath] = []

        self.pen = QPen()
        self.pen.setWidthF(3.0)
        self.pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.tool = CanvasTool.Pointer

        self._start = QPointF(0.0, 0.0)
        self._end = QPointF(0.0, 0.0)
        self._current_pos = QPointF(0.0, 0.0)

        self._painting = False

    @property
    def lines(self) -> list[QPolygonF]:
        return self._lines

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        # self._current_pos == event.scenePos()

        if event.buttons() == Qt.MouseButton.LeftButton:
            if self._painting:
                pointf = event.scenePos()

                if self.tool == CanvasTool.Pen and self._lines:
                    self._lines[-1].append(pointf)
                    self.update()
                elif self.tool == CanvasTool.Rubber:
                    for i, line in enumerate(self._lines):
                        if line.contains(pointf):
                            del self._lines[i]
                            break

                    self.update()

        event.accept()

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self._painting = bool(self.items())
            if self.tool == CanvasTool.Pen:
                new_line = FormattedLine()
                new_line.pen = QPen(self.pen)
                self._lines.append(new_line)
                pointf = event.scenePos()
                new_line.append(pointf)
            elif self.tool == CanvasTool.Arrow:
                self._start = event.scenePos()

        event.accept()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        self._painting = False
        self._eraser_path = None
        if self._start != event.scenePos():
            self._end = event.scenePos()
            if self.tool == CanvasTool.Arrow:
                path = ArrowPath(self._start, self._end, QPen(self.pen))
                self._lines.append(path)
                self.update()
        event.accept()

    def drawForeground(self, painter: QPainter, rect: QRectF):
        for line in self._lines:
            painter.setPen(line.pen)
            painter.setCompositionMode(line.mode)
            if isinstance(line, QPolygonF):
                painter.drawPolyline(line)
                continue
            painter.setBrush(line.brush)
            painter.drawPath(line)

        if self.tool == CanvasTool.Pointer:
            painter.setPen(PointerPen())
            painter.drawEllipse(self._current_pos, 2.0, 2.0)


class PresenterCanvas(QGraphicsView):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        scene = CanvasScene()
        self.setScene(scene)

        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing, True)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing, False)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)

    def change_item(self, item: QGraphicsItem):

        self.scene().lines.clear()
        self.scene().clear()
        self.scene().addItem(item)
        StandardLogger.debug(f"Changed current item to {item}", extra={"sender": "PRESENTERCANVAS"})

        self.rescale()

    def clear(self) -> None:
        self.scene().clear()

    def rescale(self) -> None:
        for item in self.scene().items():
            self.fitInView(item, Qt.AspectRatioMode.KeepAspectRatio)

    def set_color(self, button: QToolButton) -> None:
        color: Qt.GlobalColor = button.property("color")
        self.scene().pen.setColor(color)

    def set_tool(self, button: QToolButton) -> None:
        tool: CanvasTool = button.property("tool")
        self.scene().tool = tool

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.rescale()


class PresenterView(QDialog):
    def __init__(self, scene: QGraphicsScene, editor: "Editor", parent=None):
        super().__init__(parent, Qt.WindowType.Dialog)
        lo = QVBoxLayout(self)
        self._view = QGraphicsView(scene)
        self._my_editor = editor
        self.setWindowTitle(tr("Presentation View - Teachart"))
        lo.addWidget(self._view)
        self.setLayout(lo)
        self.rescale()

        self._view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self._view.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self._view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self._view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)
        self._view.setInteractive(False)

        self._view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scene.changed.connect(self.rescale)

    @property
    def scene(self) -> QGraphicsScene:
        return self.view.scene()

    @property
    def editor(self) -> "Editor":
        return self._my_editor

    @property
    def view(self) -> QGraphicsView:
        return self._view

    def rescale(self) -> None:
        for item in self.scene.items():
            self.view.fitInView(item, Qt.AspectRatioMode.KeepAspectRatio)

    def set_current_editor(self, editor: "Editor") -> None:
        self.my_editor = editor

    def showFullScreen(self):
        editor_screen: QScreen = self._my_editor.windowHandle().screen()
        other_screens = [s for s in editor_screen.virtualSiblings() if s != editor_screen]
        if other_screens:
            target_screen = other_screens[0]
            self.setGeometry(target_screen.geometry())
            super().showFullScreen()
            self.rescale()
