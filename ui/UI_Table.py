from PyQt6.QtWidgets import QStyledItemDelegate, QListView, QStyleOptionViewItem, QWidget
from PyQt6.QtCore import QModelIndex, pyqtSignal, QRect, QObject, QSize, QPoint
from PyQt6.QtGui import QPainter
from functools import cache

class CellDelegate(QStyledItemDelegate):
    editorOpened = pyqtSignal(QListView)

    def __init__(self, parent: QObject | None = ...) -> None:
        super().__init__(parent)
        self.extra_emit = False
        self.installEventFilter(self)

    def paint(self, painter: QPainter | None, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        # print("Paint complete cell")
        y_offset = 0
        # print("Initial y offset", y_offset)
        # print("Painted rect:", option.rect.x(), option.rect.y(), option.rect.width())
        # print("State", index.row(), index.column(), option.state)
        if option.rect.width() < 140 and option.rect.width() > 135:
            # Text display problems between 125 and 130 to fix
            option.rect.setWidth(140)
        cell = index.data()
        sub_option = QStyleOptionViewItem(option)
        if cell:
            for i, model in enumerate(cell):
                if model:
                    # print("Cell width", option.rect.width())
                    delegate = model.delegate(self.parent())
                    sub_option.rect = QRect(QPoint(option.rect.x(), option.rect.y() + y_offset), delegate.sizeHint(sub_option, cell.index(i)))
                    delegate.paint(painter, sub_option, cell.index(i))
                    y_offset += delegate.sizeHint(sub_option, cell.index(i)).height()
                    # print("This model", model, "painted from", sub_option.rect.x(), sub_option.rect.y(), "To", sub_option.rect.x(), sub_option.rect.y() + sub_option.rect.height())
                
        cell.height = y_offset + 20
        print("Cell offset height", y_offset, "vs. expected height", cell.expected_cell_height(option.rect.width()), "vs cell height ", cell.height)

        if self.extra_emit:
            self.sizeHintChanged.emit(index)
            self.extra_emit = False        

    def createEditor(self, parent: QWidget | None, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget | None:
        print("Editor for cell items created")
        from tcha.table import CellEditor
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

    def eventFilter(self, object, event) -> bool:
        if event.type() == 9:
            return True
        return super().eventFilter(object, event)
    
    def setEditorData(self, editor: QListView | None, index: QModelIndex) -> None:
        if editor:
            editor.setModel(index.data())
            editor.model().cell_index = (index.row(), index.column())  
            self.editorOpened.emit(editor)

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return QSize(option.rect.width(), index.data().expected_cell_height(option.rect.width()))