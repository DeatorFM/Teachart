from PyQt6.QtCore import QT_TR_NOOP as tr
from PyQt6.QtCore import (
    QAbstractItemModel,
    QByteArray,
    QDataStream,
    QEvent,
    QIODevice,
    QMimeData,
    QModelIndex,
    QObject,
    QPoint,
    QRect,
    QSize,
    Qt,
    pyqtSignal,
    pyqtSlot,
)
from PyQt6.QtGui import (
    QAction,
    QDrag,
    QDropEvent,
    QIcon,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPaintEvent,
)
from PyQt6.QtWidgets import (
    QApplication,
    QHeaderView,
    QInputDialog,
    QLineEdit,
    QListView,
    QMenu,
    QMessageBox,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableView,
    QWidget,
)

from nativeelements.baseelement import (
    BaseElementDelegate,
    BaseElementModel,
    BaseElementToolset,
)
from tcha.status import StatusButton, StatusLabel
from tcha.tablemodel import CellItem, CellModel, TableModel


class CellEditor(QListView):
    geometriesChanged = pyqtSignal()
    elementActivated = pyqtSignal(bool)

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
        self.setAutoFillBackground(True)

        self.setDragEnabled(True)
        self.setDragDropMode(QListView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)

        self._editor_just_destroyed = False
        self._drag_start_position: QPoint | None = None

        self.activated.connect(lambda: self.elementActivated.emit(True))

        # Create context menu
        self.context_menu = QMenu(self)
        self.add_text_action = QAction("Add Text", self)
        self.add_picture_action = QAction("Add Picture", self)
        self.context_menu.addAction(self.add_text_action)
        self.context_menu.addAction(self.add_picture_action)

    # Toolset methods

    def connect_toolsets(self, toolsets: dict[str, BaseElementToolset]) -> None:
        self._toolsets = toolsets

    def on_closed(self) -> None:
        self.setCurrentIndex(QModelIndex())

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

    def closeEditor(self, editor, hint=QStyledItemDelegate.EndEditHint.NoHint) -> None:
        print("An element editor has been closed:", editor)
        if editor:
            super().closeEditor(editor, hint)
            self._editor_just_destroyed = True
            self.elementActivated.emit(False)
            self.setCurrentIndex(QModelIndex())
            self.setFocus()
            print("Close complete")

    def paintEvent(self, e: QPaintEvent | None) -> None:
        # print("painting list")
        self.scrollToTop()
        super().paintEvent(e)
        if self._editor_just_destroyed:
            self._editor_just_destroyed = False
            self.geometriesChanged.emit()

    def copy_index(self, index: QModelIndex) -> None:
        if index.isValid():
            clipboard = QApplication.clipboard()
            mime_data = self.model().mimeData([index])
            clipboard.setMimeData(mime_data)

    def copied_index(self) -> QModelIndex | None:
        clipboard = QApplication.clipboard()
        if clipboard:
            if "application/x-teachart" in clipboard.mimeData().formats():
                encoded_data = clipboard.mimeData().data("application/x-teachart")
                stream = QDataStream(encoded_data, QIODevice.OpenModeFlag.ReadOnly)

                model_ptr = stream.readInt64()  # Model pointer
                source_model = self.model().cell_index.model()
                if id(source_model) == model_ptr:
                    source_lvl = stream.readInt8()  # Level
                    _ = stream.readInt32()  # Cell item number
                    model_num = stream.readInt32()  # Model item number
                    if source_lvl == 1:
                        model: CellModel = self.model()
                        idx = model.index_for_num(model_num)
                        return idx
        return QModelIndex()

    def keyPressEvent(self, e: QKeyEvent):
        print("Cell Editor got key press")
        if (
            Qt.KeyboardModifier.ControlModifier
            in e.keyCombination().keyboardModifiers()
        ):
            if e.key() == Qt.Key.Key_C:
                if self.currentIndex().isValid():
                    self.copy_index(self.currentIndex())
                    e.accept()

        return super().keyPressEvent(e)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        print("My mouse has clicked yeah")
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_position = event.pos()
            index = self.indexAt(event.pos())
            print("You clicked on", self.childAt(event.pos()))
            if (
                self.state() == QListView.State.EditingState
                and index != self.currentIndex()
            ):
                self.setCurrentIndex(QModelIndex())
                if index.isValid():
                    self.setCurrentIndex(index)
                event.accept()
                return
        super().mousePressEvent(event)

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
        mime_data = self.model().mimeData([self.currentIndex()])
        drag.setMimeData(mime_data)
        drag.exec(Qt.DropAction.MoveAction)
        clipboard = QApplication.clipboard()
        clipboard.mimeData().removeFormat("application/x-teachart")
        clipboard.dataChanged.emit()

    def dropEvent(self, event: QDropEvent):
        print("Drop event")
        if event.source() == self:
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()

            global_pos = self.mapToGlobal(event.position().toPoint())
            cell_pos = self.mapFromGlobal(global_pos)

            drop_index = self.indexAt(cell_pos)
            print("Dropped index at", drop_index.row())
            drop_row = (
                drop_index.row() if drop_index.isValid() else self.model().rowCount()
            )

            self.model().dropMimeData(
                event.mimeData(), event.dropAction(), drop_row, 0, QModelIndex()
            )

    def itemDelegateForIndex(self, index: QModelIndex) -> QStyledItemDelegate | None:
        model = index.data()
        if isinstance(model, BaseElementModel) and self._toolsets:
            # print(
            #     f"Delegate requested: model={model.name}, id={id(model)}, type={type(model)}"
            # )
            toolset = self._toolsets[model.name]
            delegate = model.delegate(toolset, self)
            delegate.commitData.connect(self.commitData)
            delegate.closeEditor.connect(self.closeEditor)
            delegate.sizeHintChanged.connect(self.update_list_geometry)

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

    def paint(
        self, painter: QPainter | None, option: QStyleOptionViewItem, index: QModelIndex
    ) -> None:
        painter.save()
        super().paint(painter, option, QModelIndex())
        painter.restore()

        # print(f"CellDelegate's rect: {option.rect.width()}")

        option.features

        if index != self._open_editor_index:
            # Apply 2px padding to simulate CellEditor frame
            cell_rect = option.rect.adjusted(2, 2, -2, -2)
            y_offset = 2
            # print("Initial y offset", y_offset)
            # print("Painted rect:", option.rect.x(), option.rect.y(), option.rect.width())
            # print("State", index.row(), index.column(), option.state)
            if cell_rect.width() < 140 and cell_rect.width() > 135:
                # Text display problems between 125 and 130 to fix
                cell_rect.setWidth(140)
            cell: CellItem[BaseElementModel] = index.data()
            sub_option = QStyleOptionViewItem(option)
            if cell:
                cmodel = CellModel(cell, index)
                for i, model in enumerate(cell):
                    if model:
                        # print("Cell width", cell_rect.width())
                        delegate: BaseElementDelegate = model.delegate(
                            None, self.parent()
                        )
                        delegate_size = delegate.sizeHint(
                            sub_option, cmodel.index(i, 0)
                        )
                        sub_option.rect = QRect(
                            QPoint(cell_rect.x(), cell_rect.y() + y_offset),
                            delegate_size,
                        )
                        delegate.paint(painter, sub_option, cmodel.index(i, 0), False)
                        y_offset += delegate_size.height()
                        # print("This model", model, "painted from", sub_option.rect.x(), sub_option.rect.y(), "To", sub_option.rect.x(), sub_option.rect.y() + sub_option.rect.height())
            # print("Cell offset height", y_offset, "vs. expected height", cell.expected_cell_height(option.rect.width()), "vs cell height ", cell.height)

            if self.extra_emit:
                self.sizeHintChanged.emit(index)
                self.extra_emit = False

    def createEditor(
        self, parent: QWidget | None, option: QStyleOptionViewItem, index: QModelIndex
    ) -> QWidget | None:
        editor = CellEditor(parent)
        editor.geometriesChanged.connect(
            lambda: self.update_cell_geometry(option.rect, index)
        )
        editor.setFocus()
        self.editorOpened.emit(editor)
        self._open_editor_index = index
        return editor

    def updateEditorGeometry(
        self, editor: QWidget | None, option: QStyleOptionViewItem, index: QModelIndex
    ) -> None:
        editor_rect = option.rect.adjusted(2, 2, -2, -2)
        # print(f"List's dimensions: {editor_rect.width()} | {editor_rect.height()}")
        if editor.geometry() != editor_rect:
            editor.setGeometry(editor_rect)
            editor.viewport().update()

    def setEditorData(self, editor: QListView | None, index: QModelIndex) -> None:
        if editor:
            editor.setModel(CellModel(index.data(), index))

    def update_cell_geometry(self, rect: QRect, index: QModelIndex) -> None:
        model: CellItem = index.data()
        model.recalculate_items()
        self.sizeHintChanged.emit(index)

    def eventFilter(self, object: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.FocusOut:
            return True
        # print(f"Event: Type {event.type().name}")

        if isinstance(event, QKeyEvent) and isinstance(object, CellEditor):
            if object.state() == QListView.State.EditingState:
                object.keyPressEvent(event)
                return True
            print(
                f"CellEditor QKeyEvent in Non-Editing-State: {Qt.Key(event.key()).name}"
            )

        # print(f"Passed event: {event.type().name} of object '{object}'")
        return super().eventFilter(object, event)

    def destroyEditor(self, editor: CellEditor, index: QModelIndex):
        self._open_editor_index = QModelIndex()
        super().destroyEditor(editor, index)

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        size = index.data().current_size
        return size


class HeaderView(QHeaderView):
    editingStarted = pyqtSignal()

    def __init__(
        self, orientation: Qt.Orientation, parent: QWidget | None = ...
    ) -> None:
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
        self.sectionMoved.connect(self.on_section_moved)
        self.sectionResized.connect(self.on_section_resized)

        if orientation == Qt.Orientation.Horizontal:
            self.setFixedHeight(30)
            self.setMinimumSectionSize(100)
        else:
            self.setFixedWidth(30)
            self.setMinimumSectionSize(30)

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
        if self.orientation() == Qt.Orientation.Horizontal:
            vindex = self.visualIndex(logicalIndex)
            cells: list[CellItem] = self.model().get_column(vindex)
            for cell in cells:
                cell.recalculate_items()
            self.model().setHeaderData(
                vindex,
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

    def on_section_moved(self, section: int, source: int, destination: int):
        print("Move", source, "to", destination)
        self.restoreState(self._state)
        if self.orientation() == Qt.Orientation.Horizontal:
            self.model().moveColumn(QModelIndex(), source, QModelIndex(), destination)
        else:
            self.model().moveRow(QModelIndex(), source, QModelIndex(), destination)

        if self.orientation() == Qt.Orientation.Horizontal:
            for i in range(self.model().columnCount()):
                qsize = self.model().headerData(
                    i, self.orientation(), Qt.ItemDataRole.SizeHintRole
                )
                self.resizeSection(self.logicalIndex(i), qsize.width())

    def remember(self) -> None:
        print("State stored")
        self._state = self.saveState()


class Table(QTableView):
    changeMade = pyqtSignal()
    cellEditorOpened = pyqtSignal(CellEditor)
    cellEditorClosed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._model_just_set = False
        self._painting = True
        self._editor: CellEditor | None = None

        self._size_status = StatusLabel("")
        self._current_status = StatusLabel("")
        self._goto_status = StatusButton(tr("Go to Row"), True)
        self._goto_status.setIcon(QIcon("resources/icons/ic_goto.svg"))

        self.setEditTriggers(QTableView.EditTrigger.CurrentChanged)
        self.setDragEnabled(True)
        self.setDragDropMode(QTableView.DragDropMode.DragDrop)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)

        self.setVerticalScrollMode(QTableView.ScrollMode.ScrollPerPixel)
        self.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectItems)
        self.setMouseTracking(True)

        self.setAttribute(Qt.WidgetAttribute.WA_NoMousePropagation, True)

        self.setItemDelegate(CellDelegate(self))
        self.itemDelegate().sizeHintChanged.connect(self.update_row_geometries)
        self.itemDelegate().editorOpened.connect(self.on_editor_opened)

        self.setHorizontalHeader(HeaderView(Qt.Orientation.Horizontal, self))
        self.setVerticalHeader(HeaderView(Qt.Orientation.Vertical, self))

        self.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.verticalHeader().sectionMoved.connect(self.update_row_geometries)
        self.verticalHeader().sectionMoved.connect(
            lambda: self.setCurrentIndex(QModelIndex())
        )
        self.horizontalHeader().sectionResized.connect(self.close_current_editor)
        self.horizontalHeader().editingStarted.connect(self.close_current_editor)

        self._goto_status.clicked.connect(self.focus_row)

        self._drag_start_position: QPoint | None = None
        self._last_hover_pos = None
        self._can_close_editor = True

    @property
    def editor(self) -> CellEditor | None:
        return self._editor

    def status(self) -> tuple[QWidget]:
        return self._size_status, self._current_status, self._goto_status

    def enable_painting(self, painting: bool) -> None:
        self._painting = painting

    def setModel(self, model: QAbstractItemModel | None) -> bool:
        if model:
            super().setModel(model)
            self.setCurrentIndex(QModelIndex())
            self.horizontalHeader().setModel(model)
            self.verticalHeader().setSectionResizeMode(
                QHeaderView.ResizeMode.ResizeToContents
            )
            self.verticalHeader().setModel(model)
            self._model_just_set = True
            self.model().dataChanged.connect(self.set_extra_emit)
            self.model().dataChanged.connect(self.update_row_geometries)
            self.model().modelChanged.connect(self.on_model_changed)
            self.model().columnsMoved.connect(self.update_row_geometries)
            self.model().rowsMoved.connect(self.update_row_geometries)
            self.selectionModel().selectionChanged.connect(self.update_status)
            for column in range(self.model().columnCount()):
                size = (
                    self.model()
                    .headerData(
                        column, Qt.Orientation.Horizontal, Qt.ItemDataRole.SizeHintRole
                    )
                    .width()
                )
                self.horizontalHeader().resizeSection(column, size)
            self.update_row_geometries()
            self.update_status()
            return True
        return False

    def on_model_changed(self) -> None:
        self.changeMade.emit()
        self.update_status()

    def update_status(self) -> None:
        self._size_status.setText(self.size_status())
        self._current_status.setText(self.selection_status())

    def size_status(self) -> str:
        rows, columns = self.model().rowCount(), self.model().columnCount()
        tr_rows = tr("Rows:")
        tr_columns = tr("Columns")
        return f"{tr_rows} {rows} | {tr_columns} {columns}"

    def selection_status(self) -> str:
        if self.selectionModel().currentIndex().isValid():
            index = self.selectionModel().currentIndex()
            row = index.row() + 1
            column: str = self.model().headerData(
                index.column(), Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole
            )
            print("Selected index status updated", row, column)
            tr_row = tr("Row")
            tr_column = tr("Column")
            return f"{tr_row} {row} in {tr_column} {column}"
        else:
            tr_noselect = tr("No selection")
            return tr_noselect

    def focus_row(self) -> None:
        row, ok = QInputDialog.getInt(
            self,
            tr("Focus on row"),
            tr("Enter row number"),
            1,
            1,
            self.model().rowCount(),
        )
        if ok:
            self.scrollTo(self.model().index(row - 1, 0))

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
        print("Update row geometries")
        self.verticalHeader().resizeSections()
        self.update()
        self.viewport().update()
        print("Viewport updated")

    def close_current_editor(self) -> None:
        print("Trying to close current editor")
        self.selectionModel().clearCurrentIndex()
        if self._editor:
            self._editor.disconnect()
            self.closeEditor(self._editor, QStyledItemDelegate.EndEditHint.NoHint)

    @pyqtSlot(CellEditor)
    def on_editor_opened(self, editor: CellEditor) -> None:
        """Connects the cell editor with the signals to notify the editor tab"""
        print("Editor opened", editor)
        if editor:
            self._editor = editor
            self.cellEditorOpened.emit(self._editor)
            if self._editor.model():
                self._editor.model().modelChanged.connect(self.changeMade.emit)
                self._editor.model().dataChanged.connect(self.changeMade.emit)

    # def on_selection_changed(self, selected, deselected) -> None:
    #     print("Changed selection")

    def add_row(self, row: int = -1) -> None:
        if row == -1:
            self.model().insertRow(self.currentIndex().row())
        else:
            self.model().insertRow(row)

    def add_column(self, column: int = -1) -> None:
        if column == -1:
            self.model().insertColumn(self.currentIndex().column())
        else:
            self.model().insertColumn(column)

    def remove_row(self, row: int = -1) -> None:
        """Removes specified row or if not current row"""
        rmv_row = row if row > -1 else self.currentIndex().row()
        print(f"About to remove row {rmv_row}")
        model: TableModel = self.model()
        if self._editor and self.model().rowCount() > 1:
            if any(model.get_row(rmv_row)):
                result = QMessageBox.question(
                    self,
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

            if not self.copied_index().isValid():
                clipboard = QApplication.clipboard()
                clipboard.mimeData().removeFormat("application/x-teachart")
                clipboard.dataChanged.emit()

    def remove_column(self, column: int = -1) -> None:
        """Removes column from model and clears clipboard if index with same column was copied"""
        rmv_col = column if column > -1 else self.currentIndex().column()
        print(f"About to remove column {rmv_col}")
        model: TableModel = self.model()
        if self._editor and self.model().columnCount() > 1:
            if any(model.get_column(rmv_col)):
                result = QMessageBox.question(
                    self,
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
        print("Table got key press")
        if (
            Qt.KeyboardModifier.ControlModifier
            in e.keyCombination().keyboardModifiers()
        ):
            if e.key() == Qt.Key.Key_C:
                self.copy_index(self.currentIndex())
                e.accept()
                return
            elif e.key() == Qt.Key.Key_V:
                self.paste_index(QApplication.clipboard().mimeData())

        return super().keyPressEvent(e)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton:
            if self._drag_start_position:
                # self.setCurrentIndex(QModelIndex())
                distance = (event.pos() - self._drag_start_position).manhattanLength()
                if distance >= QApplication.startDragDistance():
                    drag = QDrag(self)
                    mime_data = self.model().mimeData([self.currentIndex()])
                    drag.setMimeData(mime_data)
                    drag.exec(Qt.DropAction.MoveAction)
                    # self.startDrag(Qt.DropAction.MoveAction)
                    clipboard = QApplication.clipboard()
                    clipboard.mimeData().removeFormat("application/x-teachart")
                    clipboard.dataChanged.emit()
        super().mouseMoveEvent(event)

    def mousePressEvent(self, e) -> None:
        index = self.indexAt(e.pos())
        if e.button() == Qt.MouseButton.LeftButton and self.underMouse():
            self._drag_start_position = e.pos()
            if self._editor:
                self.setCurrentIndex(QModelIndex())
                if index.isValid():
                    self.setCurrentIndex(index)
                e.accept()
                return
        super().mousePressEvent(e)

    def copy_index(self, index: QModelIndex) -> None:
        if index.isValid():
            clipboard = QApplication.clipboard()
            mime_data = self.model().mimeData([index])
            clipboard.setMimeData(mime_data)

    def paste_index(self, mime_data: QMimeData) -> None:
        if mime_data and not set(mime_data.formats()).isdisjoint(
            set(self.model().mimeTypes())
        ):
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

    def copied_index(self) -> QModelIndex:
        """Return the index that was copied. The index is unvalid if the cell item could not be found or is not in the clipboard."""
        clipboard = QApplication.clipboard()
        if clipboard:
            if "application/x-teachart" in clipboard.mimeData().formats():
                encoded_data = clipboard.mimeData().data("application/x-teachart")
                stream = QDataStream(encoded_data, QIODevice.OpenModeFlag.ReadOnly)

                model_ptr = stream.readInt64()  # Skip
                if id(self.model()) == model_ptr:
                    source_lvl = stream.readInt8()  # Level
                    item_num = stream.readInt32()  # Cell item number
                    if source_lvl == 0:
                        model: TableModel = self.model()
                        idx = model.index_for_num(item_num)
                        return idx
        return QModelIndex()

    def dropEvent(self, event: QDropEvent):
        if self._editor:
            editor_rect = self._editor.mapToGlobal(self._editor.rect().topLeft())
            editor_rect = QRect(editor_rect, self._editor.size())

            # Get the drop position in global coordinates
            drop_position = self.mapToGlobal(event.position().toPoint())

            # Check if the editor's rectangle contains the drop position
            if editor_rect.contains(drop_position):
                print("Disallowed drop in table")
                drop_position = self._editor.mapFromGlobal(
                    self.mapToGlobal(event.position())
                )
                editor_event = QDropEvent(
                    drop_position,
                    event.dropAction(),
                    event.mimeData(),
                    event.buttons(),
                    event.modifiers(),
                )
                self._editor.dropEvent(editor_event)
                event.ignore()
                self.setCurrentIndex(QModelIndex())
                return
        super().dropEvent(event)
        self.setCurrentIndex(QModelIndex())

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
        add_column_left_action.triggered.connect(
            lambda: self.add_column(index.column())
        )
        menu.addAction(add_column_left_action)

        add_column_right_action = QAction("Add Column Right", self)
        add_column_right_action.triggered.connect(
            lambda: self.add_column(index.column() + 1)
        )
        menu.addAction(add_column_right_action)

        remove_row_action = QAction("Remove Row", self)
        remove_row_action.triggered.connect(lambda: self.remove_row(index.row()))
        menu.addAction(remove_row_action)

        remove_column_action = QAction("Remove Column", self)
        remove_column_action.triggered.connect(
            lambda: self.remove_column(index.column())
        )
        menu.addAction(remove_column_action)

        menu.exec(self.viewport().mapToGlobal(position))

    def closeEditor(
        self, editor: QWidget | None, hint: QStyledItemDelegate.EndEditHint
    ) -> None:
        if self._editor and self._editor.state() != QListView.State.EditingState:
            print("Close CellEditor's editors")
            self._editor.setCurrentIndex(QModelIndex())
        super().closeEditor(editor, hint)
        print("An cell editor has been closed", self._can_close_editor, editor, hint)
        self.verticalHeader().resizeSections()
        self._editor = None
        self.setCurrentIndex(QModelIndex())
        self.cellEditorClosed.emit()
