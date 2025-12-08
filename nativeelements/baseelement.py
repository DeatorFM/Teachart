from abc import abstractmethod, ABCMeta
from typing import Type

from PyQt6.QtCore import pyqtSignal, QXmlStreamWriter, QObject, QSize, Qt, QXmlStreamReader
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QTextEdit, QFrame, QStyledItemDelegate, QToolBar, QSizePolicy, QMenu

from tcha.resmanager import ResourceObject, ResourceType
from ui.element_toolsets import ElementOptions


ToolBarStyleSheet = """
QToolButton::menu-indicator {image: none;}
"""

class BaseElementToolset(QToolBar):
    """Enables interface between user and element editor."""
    __metaclass__ = ABCMeta
    called = pyqtSignal(str)
    closed = pyqtSignal()
    elementActionTriggered = pyqtSignal(QAction)

    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(50)
        self.setFloatable(False)
        self.setMovable(False)
        self.setIconSize(QSize(23, 23))
        self.setSizePolicy(
        QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.setAllowedAreas(Qt.ToolBarArea.TopToolBarArea)
        self.setStyleSheet(ToolBarStyleSheet)

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the name of the toolset as an identifier."""
        return "" 
    
    @abstractmethod
    def connect_editor(self, editor: 'BaseElementEditor') -> None:
        """Connect signals between editor and toolset to have editing interface.
           Editor must be made visible and emit called in this method."""
        return
    
    @property
    @abstractmethod
    def element_menu(self) -> ElementOptions:
        return ElementOptions()    
    
    def close_(self) -> None:
        self.setVisible(False)
    
class BaseElementDelegate(QStyledItemDelegate):
    def __init__(self, toolset: BaseElementToolset | None, parent = None):
        super().__init__(parent)
        self._toolset = toolset


class BaseElementModel(QObject):
    __metaclass__ = ABCMeta

    @abstractmethod
    def xml(self, writer: QXmlStreamWriter) -> QXmlStreamWriter:
        """Writes the DOM-element holding the attributes of the model"""
        return QXmlStreamWriter
       
    @classmethod
    @abstractmethod
    def read(cls, reader: QXmlStreamReader, resobject):
        """Creates a model from the Dom-element and the ResourceObject"""
        return BaseElementModel
    
    @property
    @abstractmethod
    def name(self) -> str:
        return "BaseElement"

    @staticmethod
    @abstractmethod
    def restype() -> ResourceType:
        """Returns the ResourceType used for the ResourceObject"""
        return ResourceType

    @abstractmethod
    def delegate(self, toolset: BaseElementToolset, parent: QObject | None = None) -> BaseElementDelegate:
        """Returns an uninitialised delegate for visualising the model."""
        return BaseElementDelegate(toolset, parent)
    
    @abstractmethod
    def expected_height(self, width: int) -> int:
        """Height of the element as seen in the table calculated with the cell's width"""
        return 30
    
    @property
    @abstractmethod
    def toolset(self) -> str:
        return ""

class BaseElementEditor(QFrame):
    __metaclass__ = ABCMeta

    @abstractmethod   
    def model(self) -> BaseElementModel:
        return BaseElementModel
    
    
class BaseTextElementEditor(QTextEdit):
    @abstractmethod   
    def model(self) -> BaseElementModel:
        return BaseElementModel
    
class BaseElementDefinitions:
    __metaclass__ = ABCMeta

    @staticmethod
    @abstractmethod
    def name() -> str:
        """Name to identify the element definition. Must by shared by every other object of the same element."""
        return "BaseElement"

    @staticmethod
    @abstractmethod
    def create_model(resource: ResourceObject) -> BaseElementModel:
        """Creates an initialised model object using the passsed RespurceObject."""
        return BaseElementModel()
    
    @staticmethod
    @abstractmethod
    def get_file(parent=None) -> str | None:
        """Gets an external resource if required else None."""
        return None
    
    @staticmethod 
    def model() -> Type[BaseElementModel]:
        """Returns the model class object."""
        return BaseElementModel
    
    @staticmethod
    @abstractmethod
    def type() -> ResourceType:
        return ResourceType.NONE

    @staticmethod
    @abstractmethod
    def action(parent: QMenu) -> QAction:
        """QAction found in 'Add to Cell' menu."""
        return QAction()
    
    @staticmethod
    @abstractmethod
    def toolset() -> BaseElementToolset:
        return BaseElementToolset()
    
    @staticmethod
    @abstractmethod
    def editor(model: BaseElementModel) -> BaseElementEditor:
        return BaseElementEditor(model)