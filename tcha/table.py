from unittest.mock import Base
from PyQt6.QtWidgets import QTableView, QListView, QHeaderView, QWidget, QApplication, QMenu, QSizePolicy, QStyledItemDelegate, QLineEdit
from PyQt6.QtCore import Qt, QPoint, QAbstractItemModel, QModelIndex, pyqtSignal, pyqtSlot, QSize, QByteArray, QItemSelectionModel, QRect
from PyQt6.QtGui import QAction, QMouseEvent, QWheelEvent, QPaintEvent, QDrag, QDragEnterEvent, QDropEvent
from tcha.elements.baseelement import BaseElement
from ui.ui_table import CellDelegate

TableViewStyleSheet = """
QTableView {selection-background-color: none; background-color: white; border: 1px solid #ababab}
QTableView::item:selected {border: 2px solid #2980b9; background-color: white}
"""

ListViewStyleSheet = """
QListView {selection-background-color: none; border: 2px solid #1967d2; background-color: white;}
QListView::item:selected {selection-background-color: none; border: 2px solid #3498db; background-color: white;}
"""

HeaderViewStyleSheet = """
QLineEdit {background-color: white;}
QHeaderView::section {color: black;}
"""

class CellEditor(QListView):
    geometriesChanged = pyqtSignal()
    editorOpened = pyqtSignal(QWidget)
    editorClosed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(ListViewStyleSheet)
        self.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QListView.Shape.NoFrame)
        self.setSizeAdjustPolicy(QListView.SizeAdjustPolicy.AdjustToContents)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setSelectionMode(QListView.SelectionMode.SingleSelection)

        self.setDragEnabled(True)
        self.setDragDropMode(QListView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)

        self._editor_just_destroyed = False
        self._drag_start_position: QPoint | None = None
        self._editor = None

        # Create context menu
        self.context_menu = QMenu(self)
        self.add_text_action = QAction("Add Text", self)
        self.add_picture_action = QAction("Add Picture", self)
        self.context_menu.addAction(self.add_text_action)
        self.context_menu.addAction(self.add_picture_action)

    @property
    def editor(self) -> QWidget | None:
        return self._editor
    
    @pyqtSlot(QWidget)
    def set_editor(self, editor: QWidget) -> None:
        self._editor = editor
        self.editorOpened.emit(self._editor)
    
    @pyqtSlot(QWidget)
    def on_editor_opened(self, editor: QWidget) -> None:
        print("Editor opened", editor)
        if editor:
            self.editorOpened.emit(editor)
            self._editor = editor

    def update_list_geometry(self) -> None:
        self.geometriesChanged.emit()
        self.viewport().update()

    def wheelEvent(self, e):
        e.ignore()
        return super().wheelEvent(e)

    def setModel(self, model: QAbstractItemModel):
        model.rowsRemoved.connect(self.close_current_editor)
        super().setModel(model)
    
    def remove_current_row(self, index: int) -> None:
        self.close_current_editor()

    # def editorDestroyed(self, editor: QWidget | None) -> None:
    #     super().editorDestroyed(editor)
    #     self.geometriesChanged.emit()
    #     self._editor_just_destroyed = True

    def closeEditor(self, editor, hint=QStyledItemDelegate.EndEditHint.NoHint) -> None:
        print("An element editor has been closed:", editor)
        if editor:
            super().closeEditor(editor, hint)
            self.editorClosed.emit()
            self.clearSelection()
            self._editor_just_destroyed = True
            self._editor = None
            print("Close complete")
    
    def close_current_editor(self) -> None:
        if self._editor:
            self.closeEditor(self._editor)

    def paintEvent(self, e: QPaintEvent | None) -> None:
        # print("painting list")
        self.scrollToTop()
        super().paintEvent(e)
        if self._editor_just_destroyed:            
            self._editor_just_destroyed = False
            self.geometriesChanged.emit()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        print("My mouse has clicked yeah")
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_position = event.pos()
                # self.selectionModel().setCurrentIndex(index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
                # if index.isValid() and not self._editor:
                #     self.edit(index)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
            
        if not self._drag_start_position:
            return
            
        if (event.pos() - self._drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return

        drag = QDrag(self)
        mime_data = self.model().mimeData([self.currentIndex()])
        drag.setMimeData(mime_data)
        
        drag.exec(Qt.DropAction.MoveAction)

    def mouseReleaseEvent(self, e) -> None:
        print("Clicked on CellEditor")
        pos = e.pos()
        index = self.indexAt(pos)
        if e.button() == Qt.MouseButton.LeftButton:
            if index.isValid():
                self.close_current_editor()
                self.selectionModel().setCurrentIndex(index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
                self.edit(index)
                print("Clicked on valid element")
            else:
                print("Unvalid index")
                self.close_current_editor()
                self.clearSelection()
        print(f"Index of clicked list item is {index.row()} | {index.column()} with rect height {self.rectForIndex(index).height()} compared to expected height {self.model().expected_cell_height(self.width())}")
        super().mouseReleaseEvent(e)

    def dropEvent(self, event: QDropEvent):
        print("Drop event")
        if event.source() == self:
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()

            global_pos = self.mapToGlobal(event.position().toPoint())
            cell_pos = self.mapFromGlobal(global_pos)

            drop_index = self.indexAt(cell_pos)
            print("Dropped index at", drop_index.row())
            drop_row = drop_index.row() if drop_index.isValid() else self.model().rowCount()

            self.model().dropMimeData(event.mimeData(), event.dropAction(), drop_row, 0, QModelIndex())

    def itemDelegateForIndex(self, index: QModelIndex) -> QStyledItemDelegate | None:
            model = self.model().data(index)
            if model:
                delegate = model.delegate(self)
                delegate.sizeHintChanged.connect(self.update_list_geometry)
                delegate.editorOpened.connect(self.set_editor)
                return delegate
            else: 
                return None

    def sizeHint(self) -> QSize:
        return QSize(self.width(), self.model().expected_cell_height(self.width()) + 10)
    
class HeaderView(QHeaderView):

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
        self.sectionMoved.connect(self.on_section_moved)
        self.sectionResized.connect(self.on_section_resized)

        self.setStyleSheet(HeaderViewStyleSheet)

        if orientation == Qt.Orientation.Horizontal:
            self.setFixedHeight(30)
            self.setMinimumSectionSize(100)
        else:
            self.setFixedWidth(30)
            self.setMinimumSectionSize(30)

    def activate_editor(self, section: int) -> None:
        if self.orientation() == Qt.Orientation.Horizontal:
            text = self.model().headerData(self.visualIndex(section), self.orientation(), Qt.ItemDataRole.DisplayRole)
            self.line_edit.setText(text)
            self.line_edit.show()
            self._last_section = self.visualIndex(section)
            rect = self.rect()
            pos = self.sectionPosition(section)
            self.line_edit.setGeometry(rect.x() + pos, rect.y(), self.sectionSize(section), rect.height())

    def on_section_resized(self, logicalIndex: int, oldSize: int, newSize: int) -> None:
        if self.orientation() == Qt.Orientation.Horizontal:
            self.model().setHeaderData(self.visualIndex(logicalIndex), self.orientation(), QSize(newSize, 30), Qt.ItemDataRole.SizeHintRole)
    
    def on_editing_finished(self) -> None:
        text = self.line_edit.text()
        self.model().setHeaderData(self._last_section, self.orientation(), text, Qt.ItemDataRole.DisplayRole)
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
                qsize = self.model().headerData(i, self.orientation(), Qt.ItemDataRole.SizeHintRole)
                self.resizeSection(self.logicalIndex(i), qsize.width())

    def remember(self) -> None:
        print("State stored")
        self._state = self.saveState()

class Table(QTableView):
    cellEditorOpened = pyqtSignal(CellEditor)
    cellEditorClosed = pyqtSignal()
    elementEditorClosed = pyqtSignal()
    elementEditorOpened = pyqtSignal(BaseElement)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._model_just_set = False
        self._editor: CellEditor | None = None

        self.setEditTriggers(QTableView.EditTrigger.CurrentChanged)
        self.setDragEnabled(True)
        self.setDragDropMode(QTableView.DragDropMode.DragDrop)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)

        self.setVerticalScrollMode(QTableView.ScrollMode.ScrollPerPixel)
        self.setSelectionMode(QTableView.SelectionMode.SingleSelection) 
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectItems)
        self.setMouseTracking(True)
        self.setAutoFillBackground(True)

        self.setItemDelegate(CellDelegate(self))

        self.setHorizontalHeader(HeaderView(Qt.Orientation.Horizontal, self))
        self.setVerticalHeader(HeaderView(Qt.Orientation.Vertical, self))  

        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.verticalHeader().sectionMoved.connect(self.update_row_geometries)
        self.horizontalHeader().sectionResized.connect(self.close_current_editor)     

        self.setStyleSheet(TableViewStyleSheet)

        # self.pressed.connect(self.on_cell_pressed)

        self.itemDelegate().sizeHintChanged.connect(self.update_row_geometries)
        self.itemDelegate().editorOpened.connect(self.on_editor_opened)

        self._drag_start_position: QPoint | None = None
        self._last_hover_pos = None
        self._can_close_editor = True

    @property
    def editor(self) -> CellEditor:
        return self._editor 

    def sizeHintForRow(self, row: int) -> int:
        if self.model():
            return self.model().expected_row_height(row)
        else:
            return 30

    def setModel(self, model: QAbstractItemModel | None) -> None:
        super().setModel(model)
        self.horizontalHeader().setModel(model)
        self.verticalHeader().setModel(model)
        self._model_just_set = True
        self.model().dataChanged.connect(self.set_extra_emit)
        self.model().columnsMoved.connect(self.update_row_geometries)
        self.model().rowsMoved.connect(self.update_row_geometries)
        self.update_row_geometries()

    def add_element(self, element) -> None:
        if self.currentIndex().isValid():
            cell = self.currentIndex().data()
            cell.add_model(element)

    def set_extra_emit(self):
        self.itemDelegate().extra_emit = True

    def paintEvent(self, e):
        self.verticalHeader().resizeSections()
        super().paintEvent(e)
            
    def update_row_geometries(self) -> None:
        self.update()
        self.viewport().update()
        print("Viewport updated")

    def close_current_editor(self) -> None:
        print("Trying to close current editor")
        if self._editor:
            self.closeEditor(self._editor, QStyledItemDelegate.EndEditHint.NoHint)
    
    def on_editor_opened(self, editor: CellEditor) -> None:
        """Connects the cell editor with the signals to notify the editor tab"""
        print("Editor opened", editor)
        if editor:
            self._editor = editor
            self.cellEditorOpened.emit(self._editor)
            self._editor.editorOpened.connect(self.elementEditorOpened.emit)
            self._editor.editorClosed.connect(self.elementEditorClosed.emit)

    def on_selection_changed(self, selected, deselected) -> None:
        print("Changed selection")

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
        if row == -1:
            self.model().removeRow(self.currentIndex().row())
        else:
            self.model().removeRow(row)

    def remove_column(self, column: int = -1) -> None:
        if column == -1:
            self.model().removeColumn(self.currentIndex().column())
        else:
            self.model().removeColumn(column)

    def currentChanged(self, current, previous):
        print("Current index changed from", previous.row(), previous.column(), "to", current.row(), current.column())
        super().currentChanged(current, previous)

    def selectionChanged(self, selected, deselected):
        print("Current selection changed")
        super().selectionChanged(selected, deselected)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton:
            if self._drag_start_position is not None:
                distance = (event.pos() - self._drag_start_position).manhattanLength()
                if distance >= QApplication.startDragDistance():
                    self.startDrag(Qt.DropAction.MoveAction)
        super().mouseMoveEvent(event)

        cell = self.indexAt(event.pos()).data()
        if cell and cell.change_on_mouse_hover():
            # Force redraw of viewport
            self.viewport().update()

    def mousePressEvent(self, e) -> None:
        index = self.indexAt(e.pos())
        if e.button() == Qt.MouseButton.LeftButton:
            if self.underMouse():
                print("Mouse on cell on index", index.row(), index.column())
                self._drag_start_position = e.pos()
                self.selectionModel().setCurrentIndex(index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
                if index.isValid() and not self._editor:
                    self.edit(index)
        super().mousePressEvent(e)

    def keyPressEvent(self, e) -> None:
        if e.key() == Qt.Key.Key_Escape:
            self.closePersistentEditor(self.currentIndex())
            self.setCurrentIndex(QModelIndex())
            self.clearSelection()
        elif e.key() == Qt.Key.Key_Enter:
            return
        super().keyPressEvent(e)

    def dropEvent(self, event: QDropEvent):
        if self._editor:
            editor_rect = self._editor.mapToGlobal(self._editor.rect().topLeft())
            editor_rect = QRect(editor_rect, self._editor.size())

            # Get the drop position in global coordinates
            drop_position = self.mapToGlobal(event.position().toPoint())

            # Check if the editor's rectangle contains the drop position
            if editor_rect.contains(drop_position):
                print("Disallowed drop in table")
                drop_position = self._editor.mapFromGlobal(self.mapToGlobal(event.position()))
                editor_event = QDropEvent(drop_position, event.dropAction(), event.mimeData(), event.buttons(), event.modifiers())
                self._editor.dropEvent(editor_event)
                event.ignore()
                return
        super().dropEvent(event)

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

    def closeEditor(self, editor: QWidget | None, hint: QStyledItemDelegate.EndEditHint) -> None:
        if self._editor:
            self._editor.close_current_editor()
            self._editor.clearSelection()
        super().closeEditor(editor, QStyledItemDelegate.EndEditHint.NoHint)
        print("An cell editor has been closed", self._can_close_editor, editor, hint)
        self.verticalHeader().resizeSections()
        self.clearSelection()
        self._editor = None
        self.cellEditorClosed.emit()
        self.elementEditorClosed.emit()