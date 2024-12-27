from cgitb import text
from pydoc import doc
import sys

from typing import Any
from abc import abstractmethod
from educ.headers import HeaderView
from PyQt6.QtWidgets import QApplication, QGraphicsWidget, QGraphicsItem, QGraphicsView, QGraphicsScene, QGraphicsLinearLayout, QGraphicsLayoutItem, QGraphicsGridLayout, QFrame, QSizePolicy, QGraphicsTextItem, QGraphicsPixmapItem, QTextEdit
from PyQt6.QtCore import QRectF, QPointF, Qt, pyqtSlot, QSize, QModelIndex, pyqtSignal, QSizeF, QObject, QAbstractTableModel, QAbstractListModel, QModelIndex
from PyQt6.QtGui import QPainter, QPen, QColor, QResizeEvent, QPixmap, QTextDocument, QTextOption


HTML = """<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-size:14pt; font-weight:600;">Meine liebe Ute,</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-size:14pt; color:#ff5500;">wie geht es dir?</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-size:14pt;">Hast </span><span style=" font-size:14pt; font-style:italic;">du</span><span style=" font-size:14pt;"> dich </span><span style=" font-size:14pt; text-decoration: underline;">gut</span><span style=" font-size:14pt;"> erholt?</span></p></body></html>"""
IMAGE1 = "D:/Bilder/312WEQ3JPPL.jpg"


class BaseModel:        
    @abstractmethod
    def expected_height(self, width: int) -> int:
        return 30
    
    @abstractmethod
    def editable(self) -> bool:
        return False
    
    @abstractmethod
    def view(self) -> QGraphicsItem:
        return QGraphicsItem()
    
class ImageModel(BaseModel):
    def __init__(self, path: str) -> None:
        super().__init__()
        self.path = path

    def editable(self) -> bool:
        return False
    
    def view(self) -> QGraphicsItem:
        return ImageElement(self)
    
class ImageElement(QGraphicsPixmapItem, QGraphicsLayoutItem):
    def __init__(self, model: ImageModel) -> None:
        super().__init__(QPixmap(model.path))

    
class TextModel(QTextDocument, BaseModel):   
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        text_option = QTextOption()
        text_option.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        self.setDefaultTextOption(text_option)

    def expected_size(self, width: int) -> QSize:
        self.setTextWidth(float(width))
        size = self.size().toSize()
        print("Model's text height", size.height(), "with width", size.width())
        return size
    
    def editable(self) -> bool:
        return True
    
    def view(self, width: float, parent) -> QGraphicsItem:
        return TextElement(self, width, parent)
    
class TextElement(QGraphicsWidget, QGraphicsTextItem):
    def __init__(self, model: TextModel, width: float, parent=None) -> None:
        QGraphicsLayoutItem.__init__(self)
        QGraphicsTextItem.__init__(self, parent)
        self.current_width = width

        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditable)
        self.setDocument(model)
        self.setTextWidth(width)
        # self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        
        # self.document().contentsChanged.connect(self.on_contents_changed)

    def boundingRect(self):
        return QRectF(0, 0, self.textWidth(), self.document().size().height())

    def sizeHint(self, which: Qt.SizeHint = Qt.SizeHint.PreferredSize, constraint: QSizeF = ...) -> QSizeF:
        print("Text constraint is", constraint.width())
        document_size = self.document().size()
        width = constraint.width() if constraint.width() > 0 else self.textWidth()
        return QSizeF(width, document_size.height())

    def setGeometry(self, rect: QRectF) -> None:
        print("Text rect", rect.getRect())
        self.prepareGeometryChange()
        QGraphicsLayoutItem.setGeometry(rect)
        self.setTextWidth(rect.width())
        self.setPos(rect.topLeft())
        print("This rect now", rect.height())

class CellModel(QAbstractListModel):
    elementActivated = pyqtSignal(QGraphicsItem)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._data: list[BaseModel] = []
        self.height: int = 30

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self._data)
        
    def add_model(self, model: BaseModel) -> None:
        self._data.append(model)
        self.rowsInserted.emit(self.index(self.rowCount() - 1), self.rowCount() - 1, self.rowCount() - 1)

    def remove_model(self, i: int) -> None:
        self._data.pop(i)

    def index(self, row: int, column: int = 0, parent: QModelIndex = ...) -> QModelIndex:
        return self.createIndex(row, column)

    def data(self, index: QModelIndex, role: int = 1) -> Any:
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
        
    def has_data(self) -> bool:
        if self._data:
            return True
        else:
            return False
        
    def view(self) -> QGraphicsItem:
        return Cell(self)
    
class Cell(QGraphicsWidget):
    def __init__(self, model: CellModel, parent=None) -> None:
        super().__init__(parent)
        self._model = model
        self._selected = False
        self.default_width = 100

        layout = QGraphicsLinearLayout(Qt.Orientation.Vertical, self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5.0)
        self.setLayout(layout)

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        # self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(100.0, 30.0)

        self.on_model_changed()

        self._model.rowsInserted.connect(self.on_model_changed)
        self._model.rowsMoved.connect(self.on_model_changed)
        self._model.rowsRemoved.connect(self.on_model_changed)

    def on_model_changed(self) -> None:
        print("Initialisation order", TextElement.mro())
        self.clear()
        for element in self._model:
            item = element.view(self.rect().width(), self)
            print("About to add item")
            self.layout().addItem(item)
            print("Successfully added!")
            self.layout().setAlignment(item, Qt.AlignmentFlag.AlignTop)

    def clear(self) -> None:
        for row in reversed(range(self._model.rowCount())):
            self.layout().removeAt(row)

    def sizeHint(self, which: Qt.SizeHint, constraint: QSizeF = ...) -> QSizeF:
        print("Cell's constraint", constraint.width())
        return super().sizeHint(which, constraint)
        
    def setGeometry(self, rect: QRectF) -> None:
        if self._model.has_data(): 
            print("Cell rect is", rect.getRect())
            print("Layout wants to", self.layout().sizeHint(Qt.SizeHint.MinimumSize).width(), self.layout().sizeHint(Qt.SizeHint.PreferredSize).height())
        width = max(rect.width(), 100.0)
        rect.setWidth(self.minimumWidth())
        rect.setHeight(self._model.expected_cell_height(self.minimumWidth()))
        super().setGeometry(rect)        

class TableModel(QAbstractTableModel):
    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._data: list[list[CellModel]]
        self._header_items: list

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

class ExHeaderView(HeaderView):
    def __init__(self, orientation: Qt.Orientation, parent=None) -> None:
        super().__init__(orientation, parent)
        if orientation is Qt.Orientation.Vertical:
            self.setFixedWidth(30)
            self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
            self.move(0, 30)
        else:
            self.setFixedHeight(30)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.move(30, 0)

class HeaderItem:
    def __init__(self) -> None:
        self._width: int = 100

    def widthF(self) -> float:
        return float(self.width)

    def set_width(self, width: int) -> None:
        self._width = max(width, 100)

class Table(QGraphicsView):
    def __init__(self, parent=None):
        self._model: TableModel | None = None
        self._model_set: bool = False
        super().__init__(QGraphicsScene(), parent)

        self._verticalHeader = ExHeaderView(Qt.Orientation.Vertical, self)
        self._horizontalHeader = ExHeaderView(Qt.Orientation.Horizontal, self)
        self._horizontalHeader.sectionResized.connect(self.set_column_size)

        self.widget = QGraphicsWidget()
        # self.widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._grid = QGraphicsGridLayout(self.widget)
        self.widget.setLayout(self._grid)
        self.scene().addItem(self.widget)

        self.setViewportMargins(30, 30, 0, 0)
        self.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.setFrameShape(QFrame.Shape.NoFrame)

        self.verticalScrollBar().valueChanged.connect(self.scroll_verticalHeader)
        self.horizontalScrollBar().valueChanged.connect(self.scroll_horizontalHeader)
    
    def drawItems(self) -> None:
        for row in range(self._model.rowCount()):
            for column in range(self._model.columnCount()):
                cell = self._model.data(self._model.index(row, column))
                self._grid.setColumnFixedWidth(column, 100)
                self._grid.addItem(cell.view(), row, column)

        self.set_vertical_header_size()
        self.drawBackground(QPainter(), self.sceneRect())

    def set_vertical_header_size(self) -> None:
        for row in range(self._model.rowCount()):
            self.verticalHeader().resizeSection(self.verticalHeader().logicalIndex(row), int(self._grid.rowMinimumHeight(row)))

    def set_column_size(self, column: int, old_size: int, new_size: int) -> None:
        print("Change column size")
        visual_index = self.horizontalHeader().visualIndex(column)
        for row in range(self.model().rowCount()):
            item = self._grid.itemAt(row, visual_index)
            item.setMaximumWidth(new_size)
        # self._grid.setColumnMinimumWidth(visual_index, float(new_size))
        # self._grid.setColumnPreferredWidth(visual_index, float(new_size))
        # self.widget.updateGeometry()
    
    def index_at(self, pos: QPointF) -> QModelIndex:
        row = self.horizontalHeader.visualIndexAt(pos.toPoint().x())
        column = self.verticalHeader.visualIndexAt(pos.toPoint().y())
        return self._model.index(row, column)

    @pyqtSlot(int)
    def scroll_verticalHeader(self, by: int):
        print("Value", by)
        self.verticalHeader().setOffset(by)

    @pyqtSlot(int)
    def scroll_horizontalHeader(self, by: int):
        print("Value", by)
        self.horizontalHeader().setOffset(by)

    def set_model(self, model: TableModel):
        self._model = model
        self._verticalHeader.setModel(model)
        self._horizontalHeader.setModel(model)
        self._model_set = True

        # self._model.rowsInserted.connect(self._on_rows_changed)
        # self._model.rowsRemoved.connect(self._on_rows_changed)
        # self._model.rowsMoved.connect(self._on_rows_moved)
        # self._model.columnsInserted.connect(self._on_columns_changed)
        # self._model.columnsRemoved.connect(self._on_columns_changed)
        # self._model.columnsChanged.connect(self._on_columns_moved)

        self.drawItems()
        # self.drawBackground(QPainter(), self.sceneRect())

    def resizeEvent(self, event: QResizeEvent | None) -> None:
        self.verticalHeader().setMinimumHeight(self.height())
        self.horizontalHeader().setMinimumWidth(self.width())
        super().resizeEvent(event)

    def drawBackground(self, painter: QPainter | None, rect: QRectF) -> None:
        painter.setBackground(Qt.GlobalColor.transparent)
        super().drawBackground(painter, rect)
        pen = QPen()
        pen.setWidthF(1.0)
        pen.setColor(QColor.fromRgb(224, 224, 224)) # Linienfarbe
        painter.setPen(pen)

        if self._model:
            for xsection in [self.horizontalHeader().sectionPosition(i) + self.horizontalHeader().sectionSize(i) - 1 for i in range(self._model.columnCount())]:
                # print("SectionSize", xsection, 0, xsection, max(self.verticalHeader().sectionPositions()), self.verticalHeader().sectionSize(self._model.rowCount()))
                painter.drawLine(xsection, 0, xsection, max(self.verticalHeader().sectionPositions()) + self.verticalHeader().sectionSize(self._model.rowCount()-1) -1)

            for ysection in [self.verticalHeader().sectionPosition(i) + self.verticalHeader().sectionSize(i) - 1 for i in range(self._model.rowCount())]:
                painter.drawLine(0, ysection, max(self.horizontalHeader().sectionPositions()) + self.horizontalHeader().sectionSize(self._model.columnCount()-1) -1, ysection)

    def verticalHeader(self) -> ExHeaderView:
        return self._verticalHeader
    
    def horizontalHeader(self) -> ExHeaderView:
        return self._horizontalHeader
    
    def model(self) -> TableModel:
        return self._model
    
def configure_model(model: TableModel) -> None:
    element1 = TextModel()   
    element1.setHtml(HTML)
    cell = model.data(model.index(0, 0))
    cell.add_model(element1)

    element2 = TextModel()
    element2.setHtml(HTML)
    cell.add_model(element2)

    # element3 = ImageModel(IMAGE1)
    # cell = model.data(model.index(1, 1))
    # cell.add_model(element3)
        

def main() -> None:
    rowcolumn = input()
    rowcolumn = rowcolumn.split()
    rows, columns = rowcolumn[:2]
    rows = int(rows)
    columns = int(columns)

    app = QApplication(sys.argv)
    test = Table()
    model = TableModel()
    model.initiate_table(rows, columns)

    configure_model(model)

    test.set_model(model)
    test.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()