from PyQt6.QtWidgets import QWidget, QStyledItemDelegate, QStyleOptionViewItem, QStyle
from PyQt6.QtCore import QSize, Qt, pyqtSignal, QXmlStreamWriter, QModelIndex, QRect, QXmlStreamAttributes
from PyQt6.QtGui import QPixmap,  QMouseEvent, QTransform, QPainter, QPen
from tcha.resmanager import ResourceType, ResourceObject
from ui.UI_PictureElement import PictureView
from tcha.elements.baseelement import BaseElement, BaseModel
from dataclasses import dataclass, field
from typing import Self
import os, sys

@dataclass(frozen=True)
class PictureModel(BaseModel):
    rotationChanged = pyqtSignal()
    sizeChanged = pyqtSignal(int, int)

    resource: ResourceObject
    width: int
    height: int
    rotation: int = field(default=0)
    adjusted: bool = field(default=False)
    pixmap: QPixmap = field(default=QPixmap())

    def __post_init__(self, parent=None) -> None:
        super().__init__(parent)
        pixmap = QPixmap()
        pixmap.loadFromData(self.resource.get_data())
        object.__setattr__(self, "pixmap", pixmap)
    
    def xml(self, writer: QXmlStreamWriter) -> QXmlStreamWriter:
        writer.writeEmptyElement("element")
        writer.writeAttribute("type", "PictureElement")
        root, suffix = os.path.splitext(self.resource.path)
        writer.writeAttribute("file", self.resource.make_serialised_name("image", suffix))
        writer.writeAttribute("width", str(self.width))
        writer.writeAttribute("height", str(self.height))
        writer.writeAttribute("rotation", str(self.rotation))
        writer.writeAttribute("adjusted", str(int(self.adjusted)))
        return writer

    @classmethod
    def read(cls: Self, xml: QXmlStreamAttributes, resobj: ResourceObject) -> "PictureModel":
        model = cls(resobj, 
                    int(xml.value("width")), 
                    int(xml.value("height")), 
                    int(xml.value("rotation")), 
                    bool(xml.value("adjusted")))
        return model

    @staticmethod
    def restype() -> ResourceType:
        return ResourceType.IMAGE
    
    def delegate(self, parent: QWidget) -> 'PictureDelegate':
        return PictureDelegate(parent)
    
    def editor(self) -> QWidget | None:
        return None
    
    @property
    def path(self) -> str:
        return self.resource.path
    
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

    def set_by_width(self, width: int, paint_mode=False) -> None:
        if not self.adjusted:
            height = self.pixmap.scaledToWidth(width).height()
            object.__setattr__(self, "width", width)
            object.__setattr__(self, "height", height)
            if not paint_mode:
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
        
    def __del__(self) -> None:
        self.resource.delete_member()  

def return_model() -> PictureModel:
    return PictureModel  

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

    def rotate_right(self) -> None:
        self._model.rotate_by(90)

    def rotate_left(self) -> None:
        self._model.rotate_by(-90)

    def set_size(self, width: int, height: int) -> None:
        self._model.set_size(width, height)
        
    def current_size(self) -> tuple[int, int]:
        return self._model.width, self._model.height
    
    def current_width(self) -> int:
        return self._model.width
    
    def current_height(self) -> int:
        return self._model.height


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
            model.set_by_width(sub_rect.width(), True)
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

    def setModelData(self, editor: PictureElement, model, index):
        editor.model().sizeChanged.disconnect()
        editor.model().rotationChanged.disconnect()

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