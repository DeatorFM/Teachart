from PyQt6.QtCore import pyqtSignal, QXmlStreamWriter, QObject
from PyQt6.QtWidgets import QWidget, QTextEdit, QFrame, QStyledItemDelegate
from PyQt6.QtXml import QDomElement
from tcha.resmanager import ResourceType
from abc import abstractmethod

class BaseModel(QObject):

    @abstractmethod
    def xml(self, stream: QXmlStreamWriter, path: str) -> QXmlStreamWriter:
        return QXmlStreamWriter
       
    @classmethod
    @abstractmethod
    def read(cls, domelement: QDomElement):
        return BaseModel

    @staticmethod
    @abstractmethod
    def restype() -> ResourceType:
        return ResourceType

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
    

class BaseElement(QFrame):
    focussed = pyqtSignal(QWidget)
    unfocussed = pyqtSignal()
    requestToolset = pyqtSignal()
    _isfocussed = False

    @property
    def isFocussed(self) -> bool:
        return self._isfocussed

    def setFocussed(self, widget):
        if widget == self:
            self._isfocussed = True
        else:
            self._isfocussed = False
        self.on_focussed(self._isfocussed)

    @property
    @abstractmethod
    def toolset(self) -> str:
        return "BaseElement"

    @abstractmethod   
    def model(self) -> BaseModel:
        return BaseModel
    
    @abstractmethod
    def on_focussed(self, focussed: bool) -> None:
        return
    
class BaseEditor(QTextEdit):
    focussed = pyqtSignal(QWidget)
    unfocussed = pyqtSignal()
    requestToolset = pyqtSignal()
    _isfocussed = False

    @property
    def isFocussed(self) -> bool:
        return self._isfocussed

    def setFocussed(self, widget):
        if widget == self:
            self._isfocussed = True
        else:
            self._isfocussed = False
        self.on_focussed(self._isfocussed)

    @property
    @abstractmethod
    def toolset(self) -> str:
        return "BaseElement"
    
    @abstractmethod
    def on_focussed(self, focussed: bool) -> None:
        return