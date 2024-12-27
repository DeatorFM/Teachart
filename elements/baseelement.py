from PyQt6.QtCore import pyqtSignal, QObject, QXmlStreamWriter
from PyQt6.QtWidgets import QWidget, QTextEdit, QFrame
from PyQt6.QtXml import QDomElement
from educ.resmanager import ResourceType
import abc

class BaseModel(QObject):

    @abc.abstractmethod
    def xml(self, stream: QXmlStreamWriter, path: str) -> QXmlStreamWriter:
        return QXmlStreamWriter
       
    @classmethod
    @abc.abstractmethod
    def read(cls, domelement: QDomElement):
        return BaseModel

    @staticmethod
    @abc.abstractmethod
    def restype() -> ResourceType:
        return ResourceType    
    

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
    @abc.abstractmethod
    def toolset(self) -> str:
        return "BaseElement"

    @abc.abstractmethod   
    def model(self) -> BaseModel:
        return BaseModel
    
    @abc.abstractmethod
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
    @abc.abstractmethod
    def toolset(self) -> str:
        return "BaseElement"
    
    @abc.abstractmethod
    def on_focussed(self, focussed: bool) -> None:
        return