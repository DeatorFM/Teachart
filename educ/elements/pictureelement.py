from PyQt6.QtWidgets import QWidget, QStyledItemDelegate, QStyleOptionViewItem, QStyle
from PyQt6.QtCore import QSize, Qt, pyqtSignal, QXmlStreamWriter, QModelIndex, QRect
from PyQt6.QtGui import QPixmap, QFocusEvent, QMouseEvent, QTransform, QPainter, QPen
from PyQt6.QtXml import QDomElement
from educ.resmanager import ResourceType
from ui.UI_PictureElement import PictureView
from educ.elements.baseelement import BaseElement, BaseModel
from dataclasses import dataclass, field
import os, sys

@dataclass(frozen=True)
class PictureModel(BaseModel):
    rotationChanged = pyqtSignal()
    sizeChanged = pyqtSignal(int, int)

    resource: str
    width: int
    height: int
    rotation: int = field(default=0)
    adjusted: bool = field(default=False)
    pixmap: QPixmap = field(default=QPixmap())

    def __post_init__(self, parent=None) -> None:
        super().__init__(parent)
        object.__setattr__(self, "pixmap", QPixmap(self.resource))
    
    def xml(self, stream: QXmlStreamWriter, path: str) -> QXmlStreamWriter:
        stream.writeEmptyElement("h", "element")
        stream.writeAttribute("h", "type", "PictureElement")
        stream.writeAttribute("h", "resource", path)
        stream.writeAttribute("h", "width", str(self.width))
        stream.writeAttribute("h", "height", str(self.height))
        stream.writeAttribute("h", "rotation", str(self.rotation))
        stream.writeEndElement()
        return stream

    @classmethod
    def read(cls, domelement: QDomElement) -> "PictureModel":
        if domelement.attribute("type") == "PictureElement":
            resource = domelement.attribute("resource")
            width = int(domelement.attribute("width"))
            height = int(domelement.attribute("height"))
            rotation = int(domelement.attribute("rotation"))
            return cls(resource, width, height, rotation)
        else:
            raise TypeError("DOM-Element has not attribute: type=PictureElement.")

    @staticmethod
    def restype() -> ResourceType:
        return ResourceType.IMAGE
    
    def delegate(self, parent: QWidget) -> 'PictureDelegate':
        return PictureDelegate(parent)
    
    def editor(self) -> QWidget | None:
        return None
    
    def expected_size(self, width: int) -> QSize:
        size = self.pixmap.scaledToWidth(width).size()
        return size
    
    def size(self) -> QSize:
        return QSize(self.width, self.height)
    
    def editable(self) -> bool:
        return False

    def change_on_mouse_hover(self) -> bool:
        return False
    
    def set_resource(self, path: str) -> None:
        object.__setattr__(self, "resource", path)

    def set_by_width(self, width: int) -> None:
        if not self.adjusted:
            height = self.pixmap.scaledToWidth(width).height()
            object.__setattr__(self, "width", width)
            object.__setattr__(self, "height", height)
            self.sizeChanged.emit(self.width, self.height)

    def set_adjusted(self, user_adjusted: bool) -> None:
        object.__setattr__(self, "adjusted", user_adjusted)
    
    def set_width(self, width: int) -> None:
        object.__setattr__(self, "width", width)
        object.__setattr__(self, "adjusted", True)
        self.sizeChanged.emit(self.width, self.height)

    def set_height(self, height: int) -> None:
        object.__setattr__(self, "height", height)
        object.__setattr__(self, "adjusted", True)
        self.sizeChanged.emit(self.width, self.height)

    def set_size(self, width: int, height: int) -> None:
        self.set_width(width)
        self.set_height(height)
        self.sizeChanged.emit(self.width, self.height)
    
    def set_rotation(self, rotation: int) -> None:
        if rotation % 90 == 0:
            object.__setattr__(self, "rotation", rotation)
            if rotation / 90 % 2 != 0:
                self.set_size(self.height, self.width)
            self.rotationChanged.emit()
        else: 
            raise ValueError("Number must be a multiple of 90.")

    def rotate_by(self, incr: int) -> None:
        if incr % 90 == 0:
            object.__setattr__(self, "rotation", self.rotation + incr)
            if incr / 90 % 2 != 0:
                print("Lying")
                self.set_size(self.height, self.width)
            self.rotationChanged.emit()
        else:
            raise ValueError("Number must be a multiple of 90.")
    

class PictureElement(BaseElement, PictureView):
    imageChanged = pyqtSignal(int, int)

    def __init__(self, model: PictureModel, max_width: int, parent=None) -> None:
        super().__init__(parent)
        self.setUi(self)

        self._model = model
        self._base_width = self._model.width
        self._base_height = self._model.height
        self._max_width = max_width

        self._model.rotationChanged.connect(self.refresh)
        self._model.sizeChanged.connect(self.refresh)

        self.setAttribute(Qt.WidgetAttribute.WA_NoMousePropagation, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("{background: none;}")
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

    @property
    def toolset(self) -> str:
        return "PictureToolset"
    
    def model(self) -> BaseModel:
        return self._model
    
    def set_size(self, width: int, height: int) -> None:
        self._model.set_size(width, height)

    def refresh(self) -> None:
        self.imageChanged.emit(self._model.width, self._model.height)

    def open_in_subprocess(self) -> None:
        if sys.platform == "win32":
            adjusted_path = self._model.resource.replace("/", "\\")
            os.startfile(f'"{adjusted_path}"')

    def rotate_right(self) -> None:
        self._model.rotate_by(90)

    def rotate_left(self) -> None:
        self._model.rotate_by(-90)
        
    def current_size(self) -> tuple[int, int]:
        return self._model.width, self._model.height
    
    def current_width(self) -> int:
        return self._model.width
    
    def current_height(self) -> int:
        return self._model.height

    # def focusInEvent(self, e: QFocusEvent) -> None:
    #     print(self.current_size())
    #     self.imageChanged.emit(self.current_width(), self.current_height())

    def mouseDoubleClickEvent(self, e: QMouseEvent) -> None:
        self.open_in_subprocess()
        super().mouseDoubleClickEvent(e)


class PictureDelegate(QStyledItemDelegate):
    editorOpened = pyqtSignal(QWidget)

    def paint(self, painter: QPainter | None, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        painter.save()

        sub_rect = option.rect.adjusted(5, 5, -5, -5)

        style = option.widget.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, option, painter, option.widget)

        model: PictureModel = index.data()
        image = model.pixmap
        if model.rotation % 360 > 0:
            image = image.transformed(QTransform().rotate(model.rotation))
        if not model.adjusted or sub_rect.width() < model.width:
            model.set_by_width(sub_rect.width())
            model.set_adjusted(False)
            painter.drawPixmap(sub_rect, image)
        else:
            new_rect = QRect(sub_rect.topLeft(), model.size())
            painter.drawPixmap(new_rect, image)
        painter.restore()

        if index.row() < index.model().rowCount() - 1:
            painter.save()
            pen = QPen(Qt.GlobalColor.lightGray, 1)
            painter.setPen(pen)
            painter.drawLine(option.rect.bottomLeft().x() + 5, option.rect.bottomLeft().y(), option.rect.bottomRight().x() - 5, option.rect.bottomRight().y())
            painter.restore()

    def createEditor(self, parent, option, index):
        editor = PictureElement(index.data(), option.rect.adjusted(5, 5, -5, -5).width(), parent)
        editor.imageChanged.connect(lambda: index.model().dataChanged.emit(index, index))
        editor.setFocus()
        self.editorOpened.emit(editor)
        return editor

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect.adjusted(5, 5, -5, -5))

    def passthru(self) -> None:
        return False

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        if index.data():
            image: QPixmap = index.data().pixmap
            image = image.scaledToWidth(option.rect.width() - 10)
            size = image.rect().size()
            if size.height() < index.data().height:
                size.setHeight(index.data().height + 10)
            else:
                size.setHeight(size.height() + 10)
            return QSize(option.rect.width(), size.height())
        else:
            return QSize(option.rect.width(), 0)