import sys

from typing import Any
from PyQt6.QtWidgets import QAbstractItemDelegate, QStyledItemDelegate, QStyleOptionViewItem, QTableView, QApplication, QWidget, QTextEdit, QHeaderView, QListView, QFrame, QSizePolicy, QAbstractItemView, QStyle, QMenu
from PyQt6.QtCore import QAbstractItemModel, QPoint, Qt, QModelIndex, QObject, QAbstractListModel, QRect, QEvent, QSize, QAbstractTableModel, QMargins, pyqtSignal
from PyQt6.QtGui import QMouseEvent, QAction, QPaintEvent, QPainter, QTextDocument, QPixmap, QWheelEvent, QPen
from abc import abstractmethod

"""
Probleme: 
"""

"""
Aufgaben:
    - Mauseingaben mit Signal pressed() verarbeiten statt Event
    - Mauseingaben an Editor weiterleiten
"""

HTML = """
</style></head><body style=" font-family:'MS Shell Dlg 2'; font-size:8pt; font-weight:400; font-style:normal;">
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-size:18pt; font-style:italic; text-decoration: underline;">Hilfe</span><span style=" font-size:18pt;"> meine </span><span style=" font-size:18pt; font-style:italic;">Schwiegertochter</span><span style=" font-size:18pt;"> dreht durch. </span><span style=" font-size:18pt; font-weight:600;">So rette sie doch einer.</span></p></body></html>
"""


TableViewStyleSheet = """
QTableView {selection-background-color: none;}
QTableView::item:selected {border: 2px solid #1967d2; background-color: white}
"""

ListViewStyleSheet = """
QListView {selection-background-color: none; border: 2px solid #1967d2; background-color: white;}
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
        self.rects: list[QRect] = []
        self.height: int = 30

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self._data)
        
    def add_model(self, model: BaseModel) -> None:
        self._data.append(model)

    def remove_model(self, i: int) -> None:
        self._data.pop(i)

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
        self.setItemAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        self._editor_just_destroyed = False

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
    
    def sizeHintForRow(self, row):
        item = self.model().data(self.model().index(row, 0))
        return item.expected_height(self.width())

    def mousePressEvent(self, e):
        pos = e.pos()
        index = self.indexAt(pos)
        if index.isValid():
            self.closePersistentEditor(self.currentIndex())
            self.openPersistentEditor(index)
            self.setCurrentIndex(index)
            print("Clicked on valid index")
        else:
            print("Unvalid index")
            self.closePersistentEditor(self.currentIndex())
            self.clearSelection()
        print(f"Index of clicked list item is {index.row()} | {index.column()} with rect height {self.rectForIndex(index).height()} compared to expected height {self.model().expected_cell_height(self.width())}")
        super().mousePressEvent(e)
    
    def itemDelegateForIndex(self, index):
        if index.isValid():
            model = self.model().data(index)
            delegate = model.delegate(self)
            delegate.sizeHintChanged.connect(self.update_list_geometry)
            return delegate

    def sizeHint(self) -> QSize:
        return QSize(self.width(), self.model().expected_cell_height(self.width()))


class TextDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter | None, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        data: QTextDocument = index.data()

        painter.save()
        style = option.widget.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, option, painter, option.widget)

        print("Text width", option.rect.width() - 10)
        option.rect.setTopLeft(option.rect.topLeft() + QPoint(5, 5))
        painter.translate(option.rect.topLeft())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        data.drawContents(painter)
        painter.restore()

        if index.row() < index.model().rowCount() - 1:
            painter.save()
            pen = QPen(Qt.GlobalColor.lightGray, 1)
            painter.setPen(pen)
            painter.drawLine(option.rect.bottomLeft().x() + 5, option.rect.bottomLeft().y() + 5, option.rect.bottomRight().x() - 5, option.rect.bottomRight().y() + 5)
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
        editor.setGeometry(option.rect)

    def fit_to_text(self, editor: QTextEdit, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        document = editor.document()
        docHeight = document.size().height()
        if 0 <= docHeight:
            editor.setFixedHeight(int(docHeight) + editor.currentFont().pixelSize() + 5)
        self.sizeHintChanged.emit(index)
        index.model().dataChanged.emit(index, index)

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        size = index.data().expected_size(option.rect.width() - 10)
        size.setHeight(size.height() + 15)
        return size
    
class TextModel(QTextDocument, BaseModel):
    def __init__(self) -> None:
        super().__init__()
        self.setDocumentMargin(3.0)

    def editor(self) -> QWidget:
        return QTextEdit()
    
    def expected_size(self, width: int) -> QSize:
        self.setTextWidth(float(width))
        size = self.size().toSize()
        return size
    
    def editable(self) -> bool:
        return True
    
    def delegate(self, parent: QWidget) -> TextDelegate:
        return TextDelegate(parent)
    
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

class ImageDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter | None, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        painter.save()

        style = option.widget.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, option, painter, option.widget)

        image = index.data().pixmap
        image = image.scaledToWidth(option.rect.width() - 10, Qt.TransformationMode.FastTransformation)
        option.rect = QRect(option.rect.x() + 5, option.rect.y() + 5, image.width(), image.height())
        painter.drawPixmap(option.rect, image)
        painter.restore()

        if index.row() < index.model().rowCount() - 1:
            painter.save()
            pen = QPen(Qt.GlobalColor.lightGray, 1)
            painter.setPen(pen)
            painter.drawLine(option.rect.bottomLeft().x() + 5, option.rect.bottomLeft().y() + 5, option.rect.bottomRight().x() + 5, option.rect.bottomRight().y() + 5)
            painter.restore()

    def createEditor(self, parent, option, index):
        return None

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        image: QPixmap = index.data().pixmap
        image = image.scaledToWidth(option.rect.width() )
        size = image.rect().size()
        size.setHeight(size.height() + 10)
        return size
        
class CellDelegate(QStyledItemDelegate):
    editorOpened = pyqtSignal(QListView)

    def __init__(self, parent: QObject | None = ...) -> None:
        super().__init__(parent)
        self.extra_emit = False

    def paint(self, painter: QPainter | None, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        # print("Paint complete cell")
        y_offset = 5
        # option.rect = option.rect.marginsAdded(QMargins(-5, -5, -5, -5))
        # print("Initial y offset", y_offset)
        # print("Painted rect:", option.rect.x(), option.rect.y(), option.rect.width())
        # print("State", index.row(), index.column(), option.state)
        if option.rect.width() < 140 and option.rect.width() > 135:
            # Text display problems between 125 and 130 to fix
            option.rect.setWidth(130)
        cell = index.data()
        sub_option = QStyleOptionViewItem(option)
        if cell:
            for i, model in enumerate(cell):
                print("Cell width", option.rect.width())
                sub_option.rect = QRect(QPoint(option.rect.x() + 5, option.rect.y() + y_offset), QSize(option.rect.width() - 10, model.expected_size(option.rect.width() - 10).height()))
                model.delegate(self.parent()).paint(painter, sub_option, cell.index(i))
                y_offset += model.expected_size(option.rect.width() - 10).height() + 10
                # print("This model", model, "painted from", sub_option.rect.x(), sub_option.rect.y(), "To", sub_option.rect.x(), sub_option.rect.y() + sub_option.rect.height())
                if i < cell.rowCount() - 1:
                    painter.save()
                    pen = QPen(Qt.GlobalColor.lightGray, 1)
                    painter.setPen(pen)
                    painter.drawLine(sub_option.rect.bottomLeft().x() + 5, sub_option.rect.bottomLeft().y() + 5, sub_option.rect.bottomRight().x() - 5, sub_option.rect.bottomRight().y() + 5)
                    painter.restore()
                
        cell.height = y_offset

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
    
    def updateEditorGeometry(self, editor: QWidget | None, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        print(f"List's dimensions: {option.rect.width()} | {option.rect.height()}")
        if editor.geometry() != option.rect:
            editor.setGeometry(option.rect)
            editor.viewport().update()
    
    def setEditorData(self, editor: QListView | None, index: QModelIndex) -> None:
        if editor:
            editor.setModel(index.data())  

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return QSize(option.rect.width(), index.data().expected_cell_height(option.rect.width()))

class Table(QTableView):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._model_just_set = False
        self._editor: QListView | None = None

        self.setEditTriggers(QTableView.EditTrigger.CurrentChanged)
        self.setItemDelegate(CellDelegate(self))
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setMinimumSectionSize(100)
        self.horizontalHeader().sectionResized.connect(self.close_all)
        self.setVerticalScrollMode(QTableView.ScrollMode.ScrollPerPixel)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)      

        self.setStyleSheet(TableViewStyleSheet)

        self.pressed.connect(self.on_cell_pressed)

        self.itemDelegate().sizeHintChanged.connect(self.update_row_geometries)
        self.itemDelegate().editorOpened.connect(self.on_editor_opened)
        self.setMinimumSize(800, 600)

    @property
    def editor(self) -> QListView:
        return self._editor

    def sizeHintForRow(self, row: int) -> int:
        if self.model():
            return self.model().expected_row_height(self.verticalHeader().visualIndex(row))
        else:
            return 30

    def sizeHintForColumn(self, column: int) -> int:
        if self.model():
            return self.horizontalHeader().sectionSize(column)
        else:
            return 100

    def setModel(self, model: QAbstractItemModel | None) -> None:
        super().setModel(model)
        self._model_just_set = True
        self.model().dataChanged.connect(self.set_extra_emit)
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

    def mousePressEvent(self, e):
        index = self.indexAt(e.pos())
        if e.button() == Qt.MouseButton.LeftButton:
            if index.isValid():
                self.edit(index)
                self.setCurrentIndex(index)
                print("Clicked cell:", index.row(), index.column())
                if self.editor:
                    event = QMouseEvent(QMouseEvent.Type.MouseButtonPress, self.editor.viewport().mapFromGlobal(e.globalPosition()), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
                    self.editor.mousePressEvent(event)
            else:
                print("Click outside of cell with current Index", )
                self.closePersistentEditor(self.currentIndex())
                self.clearSelection()
                return
        elif e.button() == Qt.MouseButton.RightButton:
            self.show_context_menu(e.pos())
            return
        super().mousePressEvent(e)

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

class TableModel(QAbstractTableModel):
    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._data: list[list[CellModel]]

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self._data)
        
    def columnCount(self, parent: QModelIndex = ...) -> int:
        return len(max(self._data, key=len))
    
    def initiate_table(self, rows: int, columns: int):
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
    
    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        # print("Index called!")
        return self.createIndex(row, column)
        
    def data(self, index: QModelIndex, role: int = ...) -> Any:
        return self._data[index.row()][index.column()] 
        
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> Any:
        if role is Qt.ItemDataRole.DisplayRole:
            return str(section + 1)        
        
    def insertRows(self, row: int, count: int, parent: QModelIndex = ...) -> bool:
        try:
            self.beginInsertRows(QModelIndex(), row, row)
            self._data.insert(row, [CellModel(self) for _ in range(self.columnCount())])
            self.endInsertRows()
            return True
        except IndexError:
            return False

    def insertColumns(self, column: int, count: int, parent: QModelIndex = ...) -> bool:
        try:
            self.beginInsertColumns(QModelIndex(), column, column)
            for row in self._data:
                row.insert(column, CellModel(self))
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
        self.endRemoveRows()
        return True

    def removeColumns(self, column: int, count: int, parent: QModelIndex = QModelIndex()) -> bool:
        if column < 0 or column >= self.columnCount() and self.columnCount() > 1:
            return False
        self.beginRemoveColumns(parent, column, column + count - 1)
        for row in self._data:
            for _ in range(count):
                del row[column]
        self.endRemoveColumns()
        return True

    def expected_row_height(self, row: int) -> int:
        return max([cell.height for cell in self._data[row]])
    
    def flags(self, index):
        return Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

def create_table(row: int, column: int) -> list[list[CellModel]]:
    return [[CellModel() for _ in range(column)] for _ in range(row)]

def test_routine(table: Table) -> None:
    # print(raw_model)
    model = TableModel()
    model.initiate_table(3, 5)
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