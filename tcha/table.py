from math import sqrt

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
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPen,
    QPolygonF,
    QResizeEvent,
    QScreen,
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
    QInputDialog,
    QLabel,
    QLineEdit,
    QListView,
    QMenu,
    QMessageBox,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableView,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from nativeelements.baseelement import (
    BaseElementDelegate,
    BaseElementModel,
    BaseElementToolset,
)
from tcha.consts import CanvasTool, EditingLevel
from tcha.tablemodel import (
    CellItem,
    CellModel,
    IndexModel,
    IndexPoint,
    TableModel,
)


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
        self.setAutoFillBackground(True)

        self.setDragEnabled(True)
        self.setDragDropMode(QListView.DragDropMode.InternalMove)
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

    def currentChanged(self, current: QModelIndex, previous: QModelIndex):
        super().currentChanged(current, previous)
        self.currentIndexChanged.emit(current, previous)

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

    def copied_index(self) -> QModelIndex:
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

    def enable_presenter_mode(self, enabled: bool):
        self._pres_mode = enabled
        current = self.currentIndex()
        self.change_index(current)

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
        self.element_selection = False
        self.last_idx = IndexPoint(-1, -1, -1, QPoint())
        self._open_editor_index = QModelIndex()

    def paint(
        self, painter: QPainter | None, option: QStyleOptionViewItem, index: QModelIndex
    ) -> None:
        if not self.element_selection:
            painter.save()
            super().paint(painter, option, QModelIndex())
            painter.restore()

        # print(f"CellDelegate's rect: {option.rect.width()}")

        if index != self._open_editor_index:
            # Apply 2px padding to simulate CellEditor frame
            cell_rect = option.rect.adjusted(2, 2, -2, -2)
            y_offset = 2
            # print("Initial y offset", y_offset)
            # print("Painted rect:", option.rect.x(), option.rect.y(), option.rect.width())
            # print("State", index.row(), index.column(), option.state)
            if (
                cell_rect.width() < 140 and cell_rect.width() > 135
            ):  # Text display problems between 125 and 130 to fix
                cell_rect.setWidth(140)
            cell: CellItem[BaseElementModel] = index.data()
            sub_option = QStyleOptionViewItem(option)
            if cell:
                cmodel = CellModel(cell, index)
                for i, model in enumerate(cell):
                    trindex = IndexPoint(index.row(), index.column(), i, QPoint())
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
                        if self.element_selection and self.last_idx == trindex:
                            painter.save()
                            super().paint(painter, sub_option, QModelIndex())
                            painter.restore()
                        else:
                            pass
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
            model = CellModel(index.data(), index)
            editor.setModel(model)
            if self.element_selection:
                selected = model.index(self.last_idx.erow, 0)
                editor.edit(selected)

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
        self._painting = True
        self._editor: CellEditor | None = None
        self._top_idx = QModelIndex()

        self.setEditTriggers(QTableView.EditTrigger.CurrentChanged)
        self.setDragEnabled(True)
        self.setDragDropMode(QTableView.DragDropMode.DragDrop)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setCornerButtonEnabled(False)

        self.setVerticalScrollMode(QTableView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QTableView.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectItems)

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

        self.verticalScrollBar().valueChanged.connect(self.on_vscrolled)
        self.verticalScrollBar().rangeChanged.connect(self.on_vslider_range_changed)

        self.horizontalScrollBar().valueChanged.connect(self.on_hscrolled)
        self.horizontalScrollBar().rangeChanged.connect(self.on_hslider_range_changed)

        self.row_list = QComboBox()
        self.row_list.activated.connect(lambda row: self.scroll_to_index(row, -1))

        self.count_label = QLabel()

        self._drag_start_position: QPoint | None = None
        self._last_painted = IndexPoint(-1, -1, -1, QPoint())
        self._can_close_editor = True
        self._pres_mode = False

    @property
    def editor(self) -> CellEditor | None:
        return self._editor

    def enable_painting(self, painting: bool) -> None:
        self._painting = painting

    def enable_presenter_mode(self, enabled: bool) -> None:
        self._pres_mode = enabled
        if self._editor:
            self._editor.enable_presenter_mode(enabled)

    def editing_level(self) -> EditingLevel:
        if self._editor:
            if self._editor.state() == QListView.State.EditingState:
                return EditingLevel.CellEditing | EditingLevel.ElementEditing
            return EditingLevel.CellEditing
        return EditingLevel.NoEditing

    def model(self) -> TableModel:
        return super().model()

    def setModel(self, model: QAbstractItemModel | None) -> bool:
        if model:
            super().setModel(model)
            self.setCurrentIndex(QModelIndex())

            self.horizontalHeader().setModel(model)
            self.verticalHeader().setSectionResizeMode(
                QHeaderView.ResizeMode.ResizeToContents
            )
            self.verticalHeader().setModel(model)

            self.model().dataChanged.connect(self.set_extra_emit)
            self.model().dataChanged.connect(self.update_row_geometries)
            self.model().modelChanged.connect(self.on_model_changed)
            self.model().columnsMoved.connect(self.update_row_geometries)
            self.model().rowsMoved.connect(self.update_row_geometries)
            self.model().rowsInserted.connect(self.update_count_label)
            self.model().rowsRemoved.connect(self.update_count_label)
            self.model().columnsInserted.connect(self.update_count_label)
            self.model().columnsRemoved.connect(self.update_count_label)

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
            self.on_vscrolled()
            self.on_hscrolled()
            self.row_list.setCurrentIndex(0)
            self.row_list.setModel(IndexModel(model))
            self.update_count_label()

            return True

        return False

    def on_model_changed(self) -> None:
        self.changeMade.emit()

    def on_vslider_range_changed(self, min: int, max: int) -> None:
        if self.model():
            if not min == max and self.model():
                self.verticalScrollBar().blockSignals(True)
                last_row_height = self.sizeHintForRow(self.model().rowCount() - 1)
                added_height = self.height() - last_row_height
                if added_height > 0:
                    self.verticalScrollBar().setMaximum(max + added_height)
                else:
                    self.verticalScrollBar().setMaximum(max + 200)
                print(f"VSlider: Adjusted max from {max} to {max + added_height}")
                self.verticalScrollBar().blockSignals(False)
            else:
                self.verticalScrollBar().blockSignals(True)
                last_row_height = self.sizeHintForRow(self.model().rowCount() - 1)
                self.verticalScrollBar().setMaximum(last_row_height)
                self.verticalScrollBar().blockSignals(False)

    def on_vscrolled(self) -> None:
        self._top_idx = self.indexAt(QPoint(0, 0))
        if self._top_idx.isValid():
            try:
                self.row_list.blockSignals(True)
                self.row_list.setCurrentIndex(self._top_idx.row())
                self.row_list.blockSignals(False)
            except IndexError:
                pass

    def on_hscrolled(self) -> None:
        self._top_idx = self.indexAt(QPoint(0, 0))

    def on_hslider_range_changed(self, min: int, max: int) -> None:
        if self.model():
            if not min == max:
                self.horizontalScrollBar().blockSignals(True)
                last_col_width = self.sizeHintForColumn(self.model().columnCount() - 1)
                added_width = self.width() - last_col_width
                if added_width > 0:
                    self.horizontalScrollBar().setMaximum(max + added_width - 30)
                else:
                    self.horizontalScrollBar().setMaximum(max + 200)
                    print(f"HSlider: Adjusted max from {max} to {max + added_width}")
                self.horizontalScrollBar().blockSignals(False)
            else:
                self.horizontalScrollBar().blockSignals(True)
                pos = sum(
                    self.columnWidth(col)
                    for col in range(self.model().columnCount() - 1)
                )
                self.horizontalScrollBar().setMaximum(pos)
                self.horizontalScrollBar().blockSignals(False)

    def scroll_to_index(self, row: int, column: int) -> None:
        idx_row = row if row >= 0 else 0
        idx_col = column if column >= 0 else 0
        model_index = self.model().index(idx_row, idx_col)
        print(f"Go to index {idx_row} | {idx_col}")

        if column == -1 and row >= 0:
            hvalue = self.horizontalScrollBar().value()
            self.scrollTo(model_index, QTableView.ScrollHint.PositionAtTop)
            self.horizontalScrollBar().setValue(hvalue)
        elif row == -1 and column >= 0:
            vvalue = self.verticalScrollBar().value()
            position = sum(self.columnWidth(col) for col in range(idx_col))
            self.horizontalScrollBar().setValue(position)
            # self.horizontalScrollBar().setValue(self.columnViewportPosition(model_index.column()))
            self.verticalScrollBar().setValue(vvalue)
        else:
            self.scrollTo(model_index, QTableView.ScrollHint.PositionAtTop)

    def scroll_by(self, row_incr: int, column_incr=0) -> None:
        current_row = (
            self.row_list.currentIndex() if self.row_list.currentIndex() > -1 else 0
        )

        dest_row = current_row + row_incr
        dest_column = self._top_idx.column() + column_incr
        print("Scrolled", current_row, row_incr, dest_row)

        if dest_row >= 0 and dest_row < self.row_list.count() and column_incr == 0:
            self.scroll_to_index(dest_row, -1)
        elif (
            dest_column >= 0
            and dest_column < self.model().columnCount()
            and row_incr == 0
        ):
            self.scroll_to_index(-1, dest_column)
        elif row_incr != 0 and column_incr != 0:
            self.scroll_to_index(dest_row, dest_column)

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

    def update_count_label(self) -> None:
        translated1 = tr("R")
        translated2 = tr("C")
        self.count_label.setText(
            f"{translated1} {self.model().rowCount()} | {translated2} {self.model().columnCount()}"
        )

    @pyqtSlot(CellEditor)
    def on_editor_opened(self, editor: CellEditor) -> None:
        """Connects the cell editor with the signals to notify the editor tab"""
        print("Editor opened", editor)
        if editor:
            self._editor = editor
            self._editor.enable_presenter_mode(self._pres_mode)
            self.cellEditorOpened.emit(self._editor)
            if self._editor.model():
                self._editor.model().modelChanged.connect(self.changeMade.emit)
                self._editor.model().dataChanged.connect(self.changeMade.emit)

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

    def enable_element_selection(self, enable: bool) -> None:
        self.itemDelegate().element_selection = enable
        print(f"Mouse tracking {enable}")
        self.setMouseTracking(enable)
        self.update()

    def resizeEvent(self, ev: QResizeEvent):
        return super().resizeEvent(ev)

    def keyPressEvent(self, e: QKeyEvent):
        print("Table got key press")
        if e.key() == Qt.Key.Key_Control:
            self.enable_element_selection(True)

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
            elif e.key() == Qt.Key.Key_Down:
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

    def keyReleaseEvent(self, ev: QKeyEvent):
        if ev.key() == Qt.Key.Key_Control:
            self.enable_element_selection(False)
            self.itemDelegate().last_idx = IndexPoint(-1, -1, -1, QPoint())

        return super().keyReleaseEvent(ev)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.itemDelegate().element_selection:
            mouse_pos = event.pos()
            idx = self.indexAt(event.pos())
            if idx.isValid():
                cell_rect = self.visualRect(idx)
                relative_mouse_pos = QPoint(
                    mouse_pos.x() - cell_rect.x(), mouse_pos.y() - cell_rect.y()
                )
                erow = idx.data().row_for_pos(relative_mouse_pos.y())
                trindex = IndexPoint(
                    idx.row(),
                    idx.column(),
                    erow,
                    self.viewport().mapFromParent(event.pos()),
                )
                if trindex != self.itemDelegate().last_idx:
                    self.itemDelegate().last_idx = trindex
                    self.viewport().update()

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
            print("Trying to paint")
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
            self._painting = True if self.items() else False
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
                print("Added Arrow")
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
        self.setOptimizationFlag(
            QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing, True
        )
        self.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing, False)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        # self.setMouseTracking(True)

    def change_item(self, item: QGraphicsItem):
        self.scene().lines.clear()
        self.scene().clear()
        self.scene().addItem(item)

        self.rescale()

        print(f"Current items: {self.scene().items()}")

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
        self._view.setViewportUpdateMode(
            QGraphicsView.ViewportUpdateMode.SmartViewportUpdate
        )
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
        other_screens = [
            s for s in editor_screen.virtualSiblings() if s != editor_screen
        ]
        if other_screens:
            target_screen = other_screens[0]
            self.setGeometry(target_screen.geometry())
            super().showFullScreen()
            self.rescale()

    def wheelEvent(self, a0):
        return super().wheelEvent(a0)
