from PyQt6.QtCore import pyqtSignal, QXmlStreamWriter, QObject
from PyQt6.QtWidgets import QWidget, QTextEdit, QFrame, QStyledItemDelegate
from PyQt6.QtXml import QDomElement
from tcha.resmanager import ResourceType
from abc import abstractmethod

class BaseModel(QObject):

    @abstractmethod
    def xml(self, writer: QXmlStreamWriter) -> QXmlStreamWriter:
        """Writes the DOM-element holding the attributes of the model"""
        return QXmlStreamWriter
       
    @classmethod
    @abstractmethod
    def read(cls, domelement: QDomElement, resobject):
        """Creates a model from the Dom-element and the ResourceObject"""
        return BaseModel

    @staticmethod
    @abstractmethod
    def restype() -> ResourceType:
        """Returns the ResourceType used for the ResourceObject"""
        return ResourceType

    @abstractmethod
    def delegate(self) -> QStyledItemDelegate:
        """Required delegate for visualisation in the table"""
        return QStyledItemDelegate()
    
    @abstractmethod
    def editor(self) -> QWidget | None:
        return None
    
    @abstractmethod
    def expected_height(self, width: int) -> int:
        """Height of the element as seen in the table calculated with the cell's width"""
        return 30
    
    @abstractmethod
    def editable(self) -> bool:
        return False    
    

class BaseElement(QFrame):
    requestToolset = pyqtSignal()

    @property
    @abstractmethod
    def toolset(self) -> str:
        return "BaseElement"

    @abstractmethod   
    def model(self) -> BaseModel:
        return BaseModel
    
    
class BaseEditor(QTextEdit):
    requestToolset = pyqtSignal()

    @property
    @abstractmethod
    def toolset(self) -> str:
        return "BaseElement"