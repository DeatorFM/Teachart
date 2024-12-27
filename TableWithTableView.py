import sys

from typing import Any
from PyQt6.QtWidgets import QAbstractItemDelegate, QStyledItemDelegate, QStyleOptionViewItem, QTableView, QApplication, QWidget, QTextEdit, QHeaderView, QListView, QFrame, QSizePolicy, QAbstractItemView
from PyQt6.QtCore import QAbstractItemModel, QEvent, QPoint, Qt, QModelIndex, QObject, QAbstractListModel, QRect, QRectF, QSize, QAbstractTableModel, QMargins, pyqtSignal
from PyQt6.QtGui import QMouseEvent, QPaintEngine, QPaintEvent, QPainter, QTextDocument, QPixmap, QWheelEvent
from abc import abstractmethod

"""
Probleme: 
- Wenn das erste Element einer Zelle ein Bild und danach ein Text foltist, verschwindet der Text beim Aufrufen des Zelleneditors: Zeilenhöhe = Originalhöhe des Bildes
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
QListView {selection-background-color: none;}
QListView::item:selected {border: 2px solid #1967d2; background-color: white}
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
        option.features = QStyleOptionViewItem.ViewItemFeature.None_
        option.backgroundBrush.setColor(0)
        model = index.data()
        print("Model:", model)
        model.delegate().paint(painter, option, index)

    def createEditor(self, parent: QWidget | None, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget | None:
        print("Editor for list item created!")
        return index.data().delegate().createEditor(parent, option, index)
    
    def updateEditorGeometry(self, editor: QWidget | None, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        print("Editor geometry updated!")
        index.data().delegate().updateEditorGeometry(editor, option, index)

    def setEditorData(self, editor: QWidget | None, index: QModelIndex) -> None:
        print("Editor data set!")
        index.data().delegate().setEditorData(editor, index)

    def setModelData(self, editor: QWidget | None, model: QAbstractItemModel | None, index: QModelIndex) -> None:
        index.data().delegate().setModelData(editor, model, index)
        print("Model data updated!", model)

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return index.data().delegate().sizeHint(option, index)

    def destroyEditor(self, editor: QWidget | None, index: QModelIndex) -> None:
        print("Editor destroyed!")
        self.closeEditor.emit(editor)
        self.sizeHintChanged.emit(index)
        super().destroyEditor(editor, index)

class CellEditor(QListView):
    geometriesChanged = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setItemDelegate(SwitchDelegate(self))
        self.setStyleSheet(ListViewStyleSheet)
        self.setEditTriggers(QListView.EditTrigger.SelectedClicked)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setSizeAdjustPolicy(QListView.SizeAdjustPolicy.AdjustToContents)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setSelectionRectVisible(True)
        self.setItemAlignment(Qt.AlignmentFlag.AlignTop)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        # self.itemDelegate().sizeHintChanged.connect(self.update_list_geometry)

        self._editor_just_destroyed = False

    def update_list_geometry(self) -> None:
        print("QListView: geometry updated")
        self.geometriesChanged.emit()
        self.viewport().update()

    def wheelEvent(self, a0: QWheelEvent | None) -> None:
        pass

    # def closeEditor(self, editor: QWidget | None, hint: QAbstractItemDelegate.EndEditHint) -> None:
    #     # print("Closing editor!")
    #     super().closeEditor(editor, hint)
    #     self.geometriesChanged.emit()
    #     self._editor_just_destroyed = True

    def editorDestroyed(self, editor: QObject | None) -> None:
        self.geometriesChanged.emit()
        super().editorDestroyed(editor)
        self._editor_just_destroyed = True
        self.scrollToTop()

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
        i = self.indexAt(pos)
        print(f"Index of clicked list item is {i.row()} | {i.column()} with rect height {self.rectForIndex(i).height()} compared to expected height {self.model().expected_cell_height(self.width())}")
        super().mousePressEvent(e)#

    def sizeHint(self) -> QSize:
        return QSize(self.width(), self.model().expected_cell_height(self.width()))


class TextDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter | None, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        data = index.data()
        painter.save()
        data.setTextWidth(float(option.rect.width()))
        painter.translate(option.rect.topLeft())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        data.drawContents(painter)
        painter.restore()
        super().paint(painter, option, index)

    def createEditor(self, parent: QWidget | None, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget | None:
        print("Text Editor Created")
        editor = QTextEdit(parent)
        editor.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        editor.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        editor.textChanged.connect(lambda: self.fit_to_text(editor, option, index))
        editor.setContentsMargins(3, 3, 3, 3)
        return editor
    
    def setEditorData(self, editor: QTextEdit | None, index: QModelIndex) -> None:
        editor.setDocument(index.data(Qt.ItemDataRole.EditRole))

    def setModelData(self, editor: QTextEdit | None, model: QAbstractItemModel | None, index: QModelIndex) -> None:
        model.setData(index, editor.document())

    def updateEditorGeometry(self, editor: QTextEdit | None, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        editor.setGeometry(option.rect)

    def fit_to_text(self, editor: QTextEdit, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        document = editor.document()
        docHeight = document.size().height()
        if 0 <= docHeight:
            editor.setFixedHeight(int(docHeight) + 10)
        self.sizeHintChanged.emit(index)
        index.model().dataChanged.emit(index, index)

    def destroyEditor(self, editor: QWidget | None, index: QModelIndex) -> None:
        print("Editor destroyed!")
        self.closeEditor.emit(editor)
        super().destroyEditor(editor, index)

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return index.data().expected_size(option.rect.width())
    
class TextModel(QTextDocument, BaseModel):
    def editor(self) -> QWidget:
        return QTextEdit()
    
    def expected_size(self, width: int) -> QSize:
        self.setTextWidth(float(width))
        size = self.size().toSize()
        print("Model's text height", size.height(), "with width", size.width())
        return size
    
    def editable(self) -> bool:
        return True
    
    def delegate(self) -> TextDelegate:
        return TextDelegate()
    
class ImageModel(BaseModel):
    def __init__(self, path: str) -> None:
        self.pixmap = QPixmap(path)

    def delegate(self) -> QStyledItemDelegate:
        return ImageDelegate()
    
    def editor(self) -> QWidget | None:
        return None
    
    def expected_size(self, width: int) -> QSize:
        size = self.pixmap.scaledToWidth(width).size()
        print("Model's image height", size.height(), "with width", width)
        return size
    
    def editable(self) -> bool:
        return False

class ImageDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter | None, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        # print("Paint Image")
        painter.save()
        image = index.data().pixmap
        image = image.scaledToWidth(option.rect.width(), Qt.TransformationMode.FastTransformation)
        option.rect = QRect(option.rect.x(), option.rect.y(), image.width(), image.height())
        print("Image rect in row", index.row(), "is", option.rect.width(), option.rect.height())
        painter.drawPixmap(option.rect, image)
        painter.restore()
        super().paint(painter, option, index)

    def createEditor(self, parent, option, index):
        return None

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        image = index.data().pixmap
        image = image.scaledToWidth(option.rect.width())
        return image.rect().size()
        
class CellDelegate(QStyledItemDelegate):
    def __init__(self, parent: QObject | None = ...) -> None:
        super().__init__(parent)
        self.extra_emit = False
        self.editor_opened = False

    def paint(self, painter: QPainter | None, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        # print("Paint complete cell")
        option.rect = option.rect.marginsAdded(QMargins(-5, -5, -5, -5))
        y_offset = 0
        # print("Initial y offset", y_offset)
        # print("Painted rect:", option.rect.x(), option.rect.y(), option.rect.width())
        # print("State", index.row(), index.column(), option.state)
        cell_models = index.data()
        # print(cell_models)
        if cell_models:
            # print("Let's paint!")
            for i, model in enumerate(cell_models):
                # print(model)
                sub_option = QStyleOptionViewItem(option)
                sub_option.rect = QRect(QPoint(option.rect.x(), option.rect.y() + y_offset), model.expected_size(option.rect.width()))
                model.delegate().paint(painter, sub_option, cell_models.index(i))
                y_offset += model.expected_size(option.rect.width()).height()
                # print("This model", model, "painted from", sub_option.rect.x(), sub_option.rect.y(), "To", sub_option.rect.x(), sub_option.rect.y() + sub_option.rect.height())
        cell_models.height = y_offset + 5
        if self.extra_emit:
            self.sizeHintChanged.emit(index)
            self.extra_emit = False
        print(f"Final Cell {index.row()} | {index.column()} height", y_offset)

    def createEditor(self, parent: QWidget | None, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget | None:
        print("Editor for cell items created")
        editor = CellEditor(parent)
        editor.geometriesChanged.connect(lambda: self.sizeHintChanged.emit(index))
        self.editor_opened = True
        return editor
    
    def updateEditorGeometry(self, editor: QWidget | None, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        option.rect = option.rect.marginsAdded(QMargins(-5, -5, -5, -5))
        print(f"List's dimensions: {option.rect.width()} | {option.rect.height()}")
        editor.setGeometry(option.rect)
    
    def setEditorData(self, editor: QListView | None, index: QModelIndex) -> None:
        if editor:
            editor.setModel(index.data())

    def destroyEditor(self, editor: QWidget | None, index: QModelIndex) -> None:
        self.editor_opened = False
        self.closeEditor.emit(editor)
        super().destroyEditor(editor, index)    

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return QSize(option.rect.width(), index.data().expected_cell_height(option.rect.width()))

class Table(QTableView):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._model_just_set = False

        self.setEditTriggers(QTableView.EditTrigger.CurrentChanged)
        self.setItemDelegate(CellDelegate(self))
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.verticalHeader().sectionResized.connect(self.update)
        self.horizontalHeader().setMinimumSectionSize(100)
        self.horizontalHeader().sectionResized.connect(self.verticalHeader().resizeSections)
        self.setVerticalScrollMode(QTableView.ScrollMode.ScrollPerPixel)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)      

        self.setStyleSheet(TableViewStyleSheet)

        self.itemDelegate().sizeHintChanged.connect(self.update_row_geometries)
        self.setMinimumSize(800, 600)

    def sizeHintForRow(self, row: int) -> int:
        if self.model():
            return self.model().expected_row_height(self.verticalHeader().visualIndex(row)) + 5
        else:
            return 30

    def setModel(self, model: QAbstractItemModel | None) -> None:
        super().setModel(model)
        self._model_just_set = True
        self.model().dataChanged.connect(self.set_extra_emit)

    def set_extra_emit(self):
        self.itemDelegate().extra_emit = True

    def paintEvent(self, e: QPaintEvent | None) -> None:
        super().paintEvent(e)
        self.update_row_geometries()
        # if self._model_just_set:
        #     self._model_just_set = False
        #     self.update_row_geometries()
        #     self.setVerticalScrollMode(QTableView.ScrollMode.ScrollPerPixel)
            
    
    def update_row_geometries(self) -> None:
        print("Row geometries adjusted!")
        print("Row sizes are", [self.verticalHeader().sectionSize(self.verticalHeader().logicalIndex(i)) for i in range(self.model().rowCount())])
        self.verticalHeader().resizeSections()
        
    
    # def wheelEvent(self, a0: QWheelEvent | None) -> None:
    #     self.update()
    #     super().wheelEvent(a0)

    def closeEditor(self, editor: QWidget | None, hint: QAbstractItemDelegate.EndEditHint) -> None:
        super().closeEditor(editor, hint)
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