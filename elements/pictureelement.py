from PyQt6.QtCore import QSize, Qt, pyqtSignal, QXmlStreamWriter
from PyQt6.QtGui import QPixmap, QFocusEvent, QMouseEvent, QTransform
from PyQt6.QtXml import QDomElement
from educ.resmanager import ResourceType
from ui.UI_PictureElement import PictureView
from elements.baseelement import BaseElement, BaseModel
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

    def __post_init__(self, parent=None) -> None:
        super().__init__(parent)
    
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
    
    def set_resource(self, path: str) -> None:
        object.__setattr__(self, "resource", path)
    
    def set_width(self, width: int) -> None:
        object.__setattr__(self, "width", width)
        self.sizeChanged.emit(self.width, self.height)

    def set_height(self, height: int) -> None:
        object.__setattr__(self, "height", height)
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
    imageResized = pyqtSignal(int, int)

    def __init__(self, model: PictureModel, parent=None) -> None:
        super().__init__(parent)
        self.setUi(self)
        self.setProperty("focussed", False)

        self._model = model
        self._base_width = self._model.width
        self._base_height = self._model.height
        self.set_picture(model.resource)

        self.connect_signals()
        self._model.rotationChanged.connect(self.refresh)
        self._model.sizeChanged.connect(self.refresh)

        self.setAttribute(Qt.WidgetAttribute.WA_NoMousePropagation, True)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

    def connect_signals(self) -> None:
        self.piclabel.resized.connect(self._model.set_size)

    @property
    def toolset(self) -> str:
        return "PictureToolset"
    
    def model(self) -> BaseModel:
        return self._model
    
    def baseSize(self) -> QSize:
        return QSize(self._base_width, self._base_height)

    def on_focussed(self, focussed: bool) -> None:
        self.setProperty("focussed", focussed)
        self.style().polish(self)
    
    def set_picture(self, path: str) -> None:
        """Sets the picture of the label from local file 'path'."""
        pxm  = QPixmap(path)
        pxm = pxm.scaledToWidth(self._base_width)
        self.piclabel.setPixmap(pxm)
        self._model.set_width(self.piclabel.width())
        self._model.set_height(self.piclabel.height())

    def repaint_picture(self, width: int, height: int):
        """Repaints picture with sizes given by the arguments."""
        pxm  = QPixmap(self._model.resource)
        pxm = pxm.scaled(width, height, aspectRatioMode=Qt.AspectRatioMode.IgnoreAspectRatio, transformMode=Qt.TransformationMode.SmoothTransformation)
        pxm = pxm.transformed(QTransform().rotate(self._model.rotation))
        self.piclabel.setPixmap(pxm)
        print(f"Repainted to size {width} * {height}")

    def refresh(self):
        """Refreshes image with sizes and rotation from model."""
        if self.isFocussed:
            print(self._model)
            self.piclabel.setFixedSize(self._model.width, self._model.height)
            self.fitToPicture()
            self.repaint_picture(self._model.width, self._model.height)
            self.imageResized.emit(self.current_width(), self.current_height())

    def open_in_subprocess(self) -> None:
        if sys.platform == "win32":
            adjusted_path = self._model.resource.replace("/", "\\")
            os.startfile(f'"{adjusted_path}"')

    def rotate_right(self) -> None:
        if self.isFocussed:
            self._model.rotate_by(90)

    def rotate_left(self) -> None:
        if self.isFocussed:
            self._model.rotate_by(-90)
        
    def current_size(self) -> tuple[int, int]:
        return self._model.width, self._model.height
    
    def current_width(self) -> int:
        return self._model.width
    
    def current_height(self) -> int:
        return self._model.height

    def focusInEvent(self, e: QFocusEvent) -> None:
        self.focussed.emit(self)
        print(self.current_size())
        self.imageResized.emit(self.current_width(), self.current_height())

    def mouseDoubleClickEvent(self, e: QMouseEvent) -> None:
        self.open_in_subprocess()
        super().mouseDoubleClickEvent(e)