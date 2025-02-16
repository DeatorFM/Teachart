import sys
import random

from typing import Any
from PyQt6.QtWidgets import QAbstractItemDelegate, QStyledItemDelegate, QStyleOptionViewItem, QTableView, QApplication, QWidget, QTextEdit, QHeaderView, QListView, QFrame, QSizePolicy, QAbstractItemView, QStyle, QMenu, QLineEdit, QStyleOptionHeader
from PyQt6.QtCore import QAbstractItemModel, QPoint, Qt, QModelIndex, QObject, QAbstractListModel, QRect, QEvent, QSize, QAbstractTableModel, QDataStream, pyqtSignal, QIODevice, QByteArray, QMimeData
from PyQt6.QtGui import QMouseEvent, QAction, QPaintEvent, QPainter, QTextDocument, QPixmap, QWheelEvent, QPen, QFont, QDrag, QCursor
from abc import abstractmethod
from dataclasses import dataclass, field
from tcha.elements.audioelement import AudioModel

"""
Probleme: 
"""

"""
Aufgaben:
    - DragundDrop im CellEditor
    - AudioElement -> Delegate programmieren
"""

HTML = """
</style></head><body style=" font-family:'MS Shell Dlg 2'; font-size:8pt; font-weight:400; font-style:normal;">
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-size:18pt; font-style:italic; text-decoration: underline;">Hilfe</span><span style=" font-size:18pt;"> meine </span><span style=" font-size:18pt; font-style:italic;">Schwiegertochter</span><span style=" font-size:18pt;"> dreht durch. </span><span style=" font-size:18pt; font-weight:600;">So rette sie doch einer.</span></p></body></html>
"""


TableViewStyleSheet = """
QTableView {selection-background-color: none;}
QTableView::item:selected {border: 2px solid #2980b9; background-color: white}
"""

ListViewStyleSheet = """
QListView {selection-background-color: none; border: 2px solid #1967d2; background-color: white;}
QListView::item:selected {selection-background-color: none; border: 2px solid #3498db; background-color: white;}
"""

class BaseModel:
    @abstractmethod
    def delegate(self) -> QStyledItemDelegate:
        return QStyledItemDelegate()
    
    @abstractmethod
    def editor(self) -> QWidget | None:
        return None
    
    @abstractmethod
    def expected_height(self, width: int) -> int:
        return 30
    
    @abstractmethod
    def editable(self) -> bool:
        return False

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

    def remove_model(self, i: int) -> None:
        self._data.pop(i)
        self.dataChanged.emit(self.index(0), self.index(len(self._data) - 1))

    def pop_model(self, row: int) -> BaseModel:
        model = self._data.pop(row)
        self.layoutChanged.emit()
        return model

    def index(self, row: int, column: int = 0, parent: QModelIndex = ...) -> QModelIndex:
        return self.createIndex(row, column)

    def data(self, index: QModelIndex, role: int = 1) -> QStyledItemDelegate | BaseModel:
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
            if sourceRow > destinationChild:
                self.beginMoveRows(sourceParent, sourceRow, sourceRow + count - 1, destinationParent, destinationChild)
            else:
                self.beginMoveRows(sourceParent, sourceRow, sourceRow + count - 1, destinationParent, destinationChild + 1)
            
            self._data.insert(destinationChild, self._data.pop(sourceRow))
            self.endMoveRows()
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

class SwitchDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter | None, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        # option.rect = option.rect.marginsAdded(QMargins(-5, -5, -5, -5))
        model = index.data()
        model.delegate(self.parent()).paint(painter, option, index)

    def createEditor(self, parent: QWidget | None, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget | None:
        print("Editor for list item created!")
        return index.data().delegate(self.parent()).createEditor(parent, option, index)
    
    def updateEditorGeometry(self, editor: QWidget | None, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        print("Editor geometry updated!")
        index.data().delegate(self.parent()).updateEditorGeometry(editor, option, index)
        self.sizeHintChanged

    def setEditorData(self, editor: QWidget | None, index: QModelIndex) -> None:
        print("Editor data set!")
        index.data().delegate(self.parent()).setEditorData(editor, index)

    def setModelData(self, editor: QWidget | None, model: QAbstractItemModel | None, index: QModelIndex) -> None:
        index.data().delegate(self.parent()).setModelData(editor, model, index)
        print("Model data updated!", model)

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return index.data().delegate(self.parent()).sizeHint(option, index)

    def destroyEditor(self, editor: QWidget | None, index: QModelIndex) -> None:
        print("Editor destroyed!")
        self.closeEditor.emit(editor)
        self.sizeHintChanged.emit(index)
        super().destroyEditor(editor, index)

class CellEditor(QListView):
    geometriesChanged = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(ListViewStyleSheet)
        self.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setSizeAdjustPolicy(QListView.SizeAdjustPolicy.AdjustToContents)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        self.setDragEnabled(True)
        self.setDragDropMode(QListView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)

        self._editor_just_destroyed = False
        self._drag_start_position: QPoint | None = None

        # Create context menu
        self.context_menu = QMenu(self)
        self.add_text_action = QAction("Add Text", self)
        self.add_picture_action = QAction("Add Picture", self)
        self.context_menu.addAction(self.add_text_action)
        self.context_menu.addAction(self.add_picture_action)

        # Connect actions
        self.add_text_action.triggered.connect(self.add_text)
        self.add_picture_action.triggered.connect(self.add_picture)

    def update_list_geometry(self) -> None:
        self.geometriesChanged.emit()
        self.viewport().update()

    def wheelEvent(self, a0: QWheelEvent | None) -> None:
        pass

    def editorDestroyed(self, editor: QObject | None) -> None:
        self.geometriesChanged.emit()
        super().editorDestroyed(editor)
        self._editor_just_destroyed = True
        # self.scrollToTop()

    def paintEvent(self, e: QPaintEvent | None) -> None:
        # print("painting list")
        self.scrollToTop()
        super().paintEvent(e)
        if self._editor_just_destroyed:            
            self._editor_just_destroyed = False
            self.geometriesChanged.emit()

    def add_text(self) -> None:
        text_model = TextModel()
        self.model().add_model(text_model)

    def add_picture(self) -> None:
        image_model = ImageModel(random.choice(["D:/Bilder/312WEQ3JPPL.jpg", "D:/Bilder/Herzstich.png", "D:/Bilder/Perfume_JPN.jpg", "D:/Bilder/pngwing.com.png"]))
        self.model().add_model(image_model)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_position = event.pos()
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
        pos = e.pos()
        index = self.indexAt(pos)
        if e.button() == Qt.MouseButton.LeftButton:
            if index.isValid():
                self.closePersistentEditor(self.currentIndex())
                self.openPersistentEditor(index)
                self.setCurrentIndex(index)
                print("Clicked on valid index")
            else:
                print("Unvalid index")
                self.closePersistentEditor(self.currentIndex())
                self.clearSelection()
        elif e.button() == Qt.MouseButton.RightButton:
            self.context_menu.exec(self.mapToGlobal(pos))
        print(f"Index of clicked list item is {index.row()} | {index.column()} with rect height {self.rectForIndex(index).height()} compared to expected height {self.model().expected_cell_height(self.width())}")
        super().mouseReleaseEvent(e)
    
    def itemDelegateForIndex(self, index) -> QStyledItemDelegate:
        if index.isValid():
            model = self.model().data(index)
            delegate = model.delegate(self)
            delegate.sizeHintChanged.connect(self.update_list_geometry)
            return delegate

    def sizeHint(self) -> QSize:
        return QSize(self.width(), self.model().expected_cell_height(self.width()) + 10)


class TextDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter | None, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        data: QTextDocument = index.data()
        data.setDocumentMargin(3.0)

        sub_rect = QRect(option.rect.x() + 5, option.rect.y() + 5, option.rect.width() - 10, option.rect.height() + 10)
        data.setTextWidth(sub_rect.width())
        sub_rect.setHeight(int(data.size().height() + 10))

        painter.save()
        style = option.widget.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, option, painter, option.widget)

        # print("Text width", sub_rect.width())
        painter.translate(sub_rect.topLeft())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        data.drawContents(painter)
        painter.restore()

        if index.row() < index.model().rowCount() - 1:
            painter.save()
            pen = QPen(Qt.GlobalColor.lightGray, 1)
            painter.setPen(pen)
            painter.drawLine(option.rect.bottomLeft().x() + 5, option.rect.bottomLeft().y(), option.rect.bottomRight().x() - 5, option.rect.bottomRight().y())
            painter.restore()
        

    def createEditor(self, parent: QWidget | None, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget | None:
        editor = QTextEdit(parent)
        editor.setStyleSheet("background: none; border: 1px solid LightGray")
        editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        editor.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        editor.textChanged.connect(lambda: self.fit_to_text(editor, option, index))
        editor.setContentsMargins(3, 3, 3, 3)
        editor.setFocus()
        return editor
    
    def setEditorData(self, editor: QTextEdit | None, index: QModelIndex) -> None:
        editor.setDocument(index.data(Qt.ItemDataRole.EditRole))

    def setModelData(self, editor: QTextEdit | None, model: QAbstractItemModel | None, index: QModelIndex) -> None:
        model.setData(index, editor.document())

    def updateEditorGeometry(self, editor: QTextEdit | None, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        print("Rect width", option.rect.width())
        editor.setGeometry(option.rect.adjusted(5, 5, -5, -5))

    def fit_to_text(self, editor: QTextEdit, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        document = editor.document()
        docHeight = document.size().height()
        if 0 <= docHeight:
            editor.setFixedHeight(int(docHeight) + editor.currentFont().pixelSize() + 5)
        self.sizeHintChanged.emit(index)
        index.model().dataChanged.emit(index, index)

    def passthru(self) -> bool:
        return False

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        size = index.data().expected_size(option.rect.width() - 10)
        return QSize(option.rect.width(), size.height() + 10)
    
class TextModel(QTextDocument, BaseModel):
    def __init__(self) -> None:
        super().__init__()
        self.setDocumentMargin(3.0)

    def editor(self) -> QWidget:
        return QTextEdit()
    
    def expected_size(self, width: int) -> QSize:
        self.setTextWidth(float(width))
        self.setDocumentMargin(3.0)
        size = self.size().toSize()
        return size
    
    def editable(self) -> bool:
        return True
    
    def delegate(self, parent: QWidget) -> TextDelegate:
        return TextDelegate(parent)

    def change_on_mouse_hover(self) -> bool:
        return False
    
class ImageModel(BaseModel):
    def __init__(self, path: str) -> None:
        self.pixmap = QPixmap(path)
        self.rotation: int = 0

    def delegate(self, parent: QWidget) -> QStyledItemDelegate:
        return ImageDelegate(parent)
    
    def editor(self) -> QWidget | None:
        return None
    
    def expected_size(self, width: int) -> QSize:
        size = self.pixmap.scaledToWidth(width).size()
        # print("Model's image height", size.height(), "with width", width)
        return size
    
    def editable(self) -> bool:
        return False

    def change_on_mouse_hover(self) -> bool:
        return False

class ImageDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter | None, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        painter.save()

        sub_rect = option.rect.adjusted(5, 5, -5, -5)

        style = option.widget.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, option, painter, option.widget)

    
        image = index.data().pixmap
        # image = image.scaledToWidth(sub_rect.width(), Qt.TransformationMode.FastTransformation)
        # print("Image width", image.width(), "with rect width")
        # sub_rect = QRect(sub_rect.x(), sub_rect.y(), image.width(), image.height())
        painter.drawPixmap(sub_rect, image)
        painter.restore()

        if index.row() < index.model().rowCount() - 1:
            painter.save()
            pen = QPen(Qt.GlobalColor.lightGray, 1)
            painter.setPen(pen)
            painter.drawLine(option.rect.bottomLeft().x() + 5, option.rect.bottomLeft().y(), option.rect.bottomRight().x() - 5, option.rect.bottomRight().y())
            painter.restore()

    def createEditor(self, parent, option, index):
        return None

    def passthru(self) -> None:
        return False

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        image: QPixmap = index.data().pixmap
        image = image.scaledToWidth(option.rect.width() - 10)
        size = image.rect().size()
        size.setHeight(size.height() + 10)
        return QSize(option.rect.width(), size.height())
    
    def can_pass_through(self) -> bool:
        return False
        
class CellDelegate(QStyledItemDelegate):
    editorOpened = pyqtSignal(QListView)

    def __init__(self, parent: QObject | None = ...) -> None:
        super().__init__(parent)
        self.extra_emit = False

    def paint(self, painter: QPainter | None, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        # print("Paint complete cell")
        y_offset = 0
        # print("Initial y offset", y_offset)
        # print("Painted rect:", option.rect.x(), option.rect.y(), option.rect.width())
        # print("State", index.row(), index.column(), option.state)
        if option.rect.width() < 140 and option.rect.width() > 135:
            # Text display problems between 125 and 130 to fix
            option.rect.setWidth(140)
        cell: CellModel = index.data()
        sub_option = QStyleOptionViewItem(option)
        if cell:
            for i, model in enumerate(cell):
                # print("Cell width", option.rect.width())
                delegate = model.delegate(self.parent())
                sub_option.rect = QRect(QPoint(option.rect.x(), option.rect.y() + y_offset), delegate.sizeHint(sub_option, cell.index(i)))
                delegate.paint(painter, sub_option, cell.index(i))
                y_offset += delegate.sizeHint(sub_option, cell.index(i)).height()
                # print("This model", model, "painted from", sub_option.rect.x(), sub_option.rect.y(), "To", sub_option.rect.x(), sub_option.rect.y() + sub_option.rect.height())
                
        cell.height = y_offset + 20
        # print("Cell offset height", y_offset, "vs. expected height", cell.expected_cell_height(option.rect.width()))

        if self.extra_emit:
            self.sizeHintChanged.emit(index)
            self.extra_emit = False        

    def createEditor(self, parent: QWidget | None, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget | None:
        print("Editor for cell items created")
        editor = CellEditor(parent)
        editor.geometriesChanged.connect(lambda: self.sizeHintChanged.emit(index))
        editor.setFocus()
        self.editorOpened.emit(editor)
        return editor
    
    def editorEvent(self, event, model, option, index):
        if event.type() == event.Type.MouseButtonPress:
            print("I've been clicked at", event.pos())
        return super().editorEvent(event, model, option, index)
    
    def updateEditorGeometry(self, editor: QWidget | None, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        print(f"List's dimensions: {option.rect.width()} | {option.rect.height()}")
        if editor.geometry() != option.rect:
            editor.setGeometry(option.rect)
            editor.viewport().update()
    
    def setEditorData(self, editor: QListView | None, index: QModelIndex) -> None:
        if editor:
            editor.setModel(index.data())
            editor.model().cell_index = (index.row(), index.column())  

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return QSize(option.rect.width(), index.data().expected_cell_height(option.rect.width()))
    
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

        self.setStyleSheet("QHeaderView::section {color: black;}")

        if orientation == Qt.Orientation.Horizontal:
            self.setFixedHeight(30)
            self.setMinimumSectionSize(100)
        else:
            self.setFixedWidth(30)
            self.setMinimumSectionSize(30)

        # self.setMaximumHeight(30)

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
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._model_just_set = False
        self._editor: QListView | None = None

        self.setEditTriggers(QTableView.EditTrigger.CurrentChanged)
        self.setDragEnabled(True)
        self.setDragDropMode(QTableView.DragDropMode.DragDrop)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setVerticalScrollMode(QTableView.ScrollMode.ScrollPerPixel)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection) 
        self.setMouseTracking(True)

        self.setItemDelegate(CellDelegate(self))

        self.setHorizontalHeader(HeaderView(Qt.Orientation.Horizontal, self))
        self.setVerticalHeader(HeaderView(Qt.Orientation.Vertical, self))  

        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.verticalHeader().sectionMoved.connect(self.update_row_geometries)
        self.horizontalHeader().sectionResized.connect(self.close_all)     

        self.setStyleSheet(TableViewStyleSheet)

        self.pressed.connect(self.on_cell_pressed)

        self.itemDelegate().sizeHintChanged.connect(self.update_row_geometries)
        self.itemDelegate().editorOpened.connect(self.on_editor_opened)
        self.setMinimumSize(800, 600)

        self._drag_start_position: QPoint | None = None
        self._last_hover_pos = None

    @property
    def editor(self) -> QListView:
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

    def set_extra_emit(self):
        self.itemDelegate().extra_emit = True

    def paintEvent(self, e):
        self.verticalHeader().resizeSections()
        super().paintEvent(e)
            
    def update_row_geometries(self) -> None:
        self.update()
        self.viewport().update()
        print("Viewport updated")

    def close_all(self) -> None:
        self.closePersistentEditor(self.currentIndex())
        self.clearSelection()
    
    def on_editor_opened(self, editor: QListView) -> None:
        print("Editor opened", editor)
        self._editor = editor

    def on_cell_pressed(self, index: QModelIndex) -> None:
        ...

    def add_row(self, row: int) -> None:
        self.model().insertRows(row, 1)

    def add_column(self, column: int) -> None:
        self.model().insertColumns(column, 1)

    def remove_row(self, row: int) -> None:
        self.model().removeRows(row, 1)

    def remove_column(self, column: int) -> None:
        self.model().removeColumns(column, 1)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_position = event.pos()
        super().mousePressEvent(event)

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

    def mouseReleaseEvent(self, e):
        index = self.indexAt(e.pos())
        if e.button() == Qt.MouseButton.LeftButton:
            if index.isValid():
                self.edit(index)
                self.setCurrentIndex(index)
                print("Clicked cell:", index.row(), index.column())
                # if self.editor:
                #     event = QMouseEvent(QMouseEvent.Type.MouseButtonPress, self.editor.viewport().mapFromGlobal(e.globalPosition()), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
                #     self.editor.mouseReleaseEvent(event)
            else:
                print("Click outside of cell with current Index", )
                self.closePersistentEditor(self.currentIndex())
                self.clearSelection()
                return
        elif e.button() == Qt.MouseButton.RightButton:
            self.show_context_menu(e.pos())
            return
        super().mouseReleaseEvent(e)

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

    def closeEditor(self, editor: QWidget | None, hint: QAbstractItemDelegate.EndEditHint) -> None:
        print("An editor has been closed", editor)
        super().closeEditor(editor, QAbstractItemDelegate.EndEditHint.NoHint)
        self.verticalHeader().resizeSections()

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
            self.beginInsertRows(QModelIndex(), row, row)
            self._data.insert(row, [CellModel(self) for _ in range(self.columnCount())])
            self._header_data[Qt.Orientation.Vertical].insert(row, HeaderDataItem.vertical())
            self.endInsertRows()
            return True
        except IndexError:
            return False

    def insertColumns(self, column: int, count: int, parent: QModelIndex = QModelIndex()) -> bool:
        try:
            self.beginInsertColumns(parent, column, column)
            for row in self._data:
                row.insert(column, CellModel(self))
            self._header_data[Qt.Orientation.Horizontal].insert(column, HeaderDataItem.horizontal())
            self.endInsertColumns()
            return True
        except IndexError:
            return False
        
    def removeRows(self, row: int, count: int, parent: QModelIndex = QModelIndex()) -> bool:
        if row < 0 or row >= len(self._data) and self.rowCount() > 1:
            return False
        self.beginRemoveRows(parent, row, row + count - 1)
        for _ in range(count):
            del self._data[row]
        del self._header_data[Qt.Orientation.Vertical][row]
        self.endRemoveRows()
        return True

    def removeColumns(self, column: int, count: int, parent: QModelIndex = QModelIndex()) -> bool:
        if column < 0 or column >= self.columnCount() and self.columnCount() > 1:
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


def test_routine(table: Table) -> None:
    # print(raw_model)
    model = TableModel()
    model.new(3, 5)

    cell = model.data(model.index(0, 0))
    audio_model = AudioModel("D:/Dokumente/Deutschunterricht/Audio/Schritte_plus_Neu_4_Arbeitsbuchteil_Audio/601083_AB_L08_01.mp3", "601083_AB_L08_01.mp3")
    cell.add_model(audio_model)

    cell = model.data(model.index(0, 2))
    text_model = TextModel()
    text_model.setHtml(HTML)
    cell.add_model(text_model)
    image_model = ImageModel("D:/Bilder/312WEQ3JPPL.jpg")
    cell.add_model(image_model)

    cell = model.data(model.index(2, 4))
    text_model2 = TextModel()
    text_model2.setHtml(HTML)
    cell.add_model(text_model2)
    image_model2 = ImageModel("D:/Bilder/Herzstich.png")
    cell.add_model(image_model2)

    cell = model.data(model.index(0, 3))
    image_model3 = ImageModel("D:/Bilder/Perfume_JPN.jpg")
    cell.add_model(image_model3)
    image_model4 = ImageModel("D:/Bilder/pngwing.com.png")
    cell.add_model(image_model4)
    text_model3 = TextModel()
    text_model3.setHtml(HTML)
    cell.add_model(text_model3)

    old = table.selectionModel()
    table.setModel(model)
    del old
        
def main():
    app = QApplication(sys.argv)
    window = Table()
    test_routine(window)
    window.show()
    window.update()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()