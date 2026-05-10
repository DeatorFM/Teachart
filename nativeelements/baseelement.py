from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Self, Type

from PyQt6.QtCore import (
    QByteArray,
    QEvent,
    QMimeData,
    QObject,
    QSize,
    Qt,
    QXmlStreamReader,
    QXmlStreamWriter,
    pyqtSignal,
)
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsItem,
    QMainWindow,
    QMenu,
    QStyledItemDelegate,
    QTextEdit,
    QToolBar,
)

from tcha.consts import ResourceFlag
from tcha.resmanager import ResourceContainer, ResourceObject, ResourceType


class BaseElementToolset(QToolBar):
    """Enables interface between user and element editor."""

    __metaclass__ = ABCMeta
    called = pyqtSignal(str)
    closed = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAllowedAreas(Qt.ToolBarArea.TopToolBarArea)
        self.setFloatable(False)
        self.setMovable(False)
        self.setIconSize(QSize(22, 22))

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the name of the toolset as an identifier."""
        return ""

    @abstractmethod
    def connect_editor(self, editor: "BaseElementEditor") -> None:
        """Connect signals between editor and toolset to have editing interface.
        Editor must be made visible and emit called in this method."""
        return

    @abstractmethod
    def enable_presenter_mode(self, enabled: bool) -> None: ...

    def close_(self) -> None:
        self.setVisible(False)


class BaseElementDelegate(QStyledItemDelegate):
    def __init__(self, toolset: BaseElementToolset | None, parent=None):
        super().__init__(parent)
        self._toolset = toolset
        self.pres_mode = False

    def eventFilter(self, object: QObject, event: QEvent):
        if event.type() == QEvent.Type.FocusOut:
            return True
        return super().eventFilter(object, event)


class BaseElementModel(QObject):
    __metaclass__ = ABCMeta

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._item_size = QSize(100, 30)
        self._num = 0

    @property
    def item_size(self) -> QSize:
        return self._item_size

    def set_item_size(self, size: QSize) -> None:
        self._item_size = size

    @property
    def number(self) -> int:
        """Returns the item number."""
        return self._num

    def set_number(self, num: int) -> None:
        self._num = num  #

    @abstractmethod
    def recalculate_size(self, width: int) -> None:
        return

    @abstractmethod
    def xml(self, writer: QXmlStreamWriter) -> QXmlStreamWriter:
        """Writes the DOM-element holding the attributes of the model"""
        return QXmlStreamWriter

    @classmethod
    @abstractmethod
    def read(cls, reader: QXmlStreamReader, resobject):
        """Creates a model from the Dom-element and the ResourceObject"""
        return BaseElementModel

    @classmethod
    @abstractmethod
    def from_mime_data(cls, resobj: ResourceObject, mime_data: QMimeData) -> Self:
        return BaseElementModel

    @classmethod
    @abstractmethod
    def from_bytes(cls, resobj: ResourceObject, bytearr: QByteArray) -> Self:
        """Returns a model made from the byte data obtained from mime data. See mime-data()."""
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
    def delegate(
        self, toolset: BaseElementToolset, parent: QObject | None = None
    ) -> BaseElementDelegate:
        """Returns an uninitialised delegate for visualising the model."""
        return BaseElementDelegate(toolset, parent)

    @abstractmethod
    def sizeHint(self, width: int) -> QSize:
        """Height of the element as seen in the table calculated with the cell's width"""
        return QSize(100, 30)

    @abstractmethod
    def presentable_item(self) -> QGraphicsItem:
        return QGraphicsItem()

    @property
    @abstractmethod
    def toolset(self) -> str:
        return ""

    @abstractmethod
    def copy(self, rescont: ResourceContainer) -> BaseElementModel:
        """Creates a unique copy of the model storing the resource into the ResourceContainer 'rescont'."""
        return BaseElementModel()

    @abstractmethod
    def attrs(self) -> tuple[str]:
        return tuple()

    @staticmethod
    @abstractmethod
    def definitions() -> BaseElementDefinitions:
        return BaseElementDefinitions

    @abstractmethod
    def to_byte_array() -> QByteArray:
        """Returns the model data as bytes that can be written to mime data"""
        return QByteArray


class BaseElementEditor(QFrame):
    __metaclass__ = ABCMeta

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    @abstractmethod
    def model(self) -> BaseElementModel:
        return BaseElementModel

    @abstractmethod
    def enable_presenter_mode(self, enabled: bool) -> None: ...

    def focusOutEvent(self, a0):
        return


class BaseTextElementEditor(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    @abstractmethod
    def model(self) -> BaseElementModel:
        return BaseElementModel

    def enable_presenter_mode(self, enabled: bool) -> None:
        self.setReadOnly(enabled)

    def focusOutEvent(self, e):
        return


class BaseElementDefinitions:
    __metaclass__ = ABCMeta

    @staticmethod
    @abstractmethod
    def name() -> str:
        """Name to identify the element definition. Must by shared by every other object of the same element."""
        return "BaseElement"

    @staticmethod
    @abstractmethod
    def id() -> int:
        """ID to identify the element in a QByteArray. Numbers 0-100 are reserved."""
        return 0

    @staticmethod
    @abstractmethod
    def create_model(resource: ResourceObject) -> BaseElementModel:
        """Creates an initialised model object using the passsed RespurceObject."""
        return BaseElementModel()

    @staticmethod
    @abstractmethod
    def resource_flag() -> ResourceFlag:
        return ResourceFlag.NoResource

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
    def toolset(parent: QMainWindow) -> BaseElementToolset:
        return BaseElementToolset(parent)

    @staticmethod
    @abstractmethod
    def editor(model: BaseElementModel) -> BaseElementEditor:
        return BaseElementEditor(model)

    @staticmethod
    @abstractmethod
    def mime_types() -> list[str]:
        return [""]

    @staticmethod
    @abstractmethod
    def supports_mime_data(mime_data: QMimeData) -> bool:
        return False

    @staticmethod
    @abstractmethod
    def model_from_mime_data(
        rescont: ResourceContainer, mime_data: QMimeData
    ) -> BaseElementModel | None:
        """Creates a model from mime data if format is supported"""
        return None

    @staticmethod
    @abstractmethod
    def model_from_bytes(
        resobj: ResourceObject, bytearr: QByteArray
    ) -> BaseElementModel:
        """Creates the model from a QByteArray extracted from mime data.
        The byte array must start with the first value that's required by the model excluding the ResourceObject"""
        return BaseElementModel | None

    def make_copy(
        rescont: ResourceContainer, original: BaseElementModel
    ) -> BaseElementModel:
        """Make a copy of an element model copying its Resourceobject with the given ResourceContainer."""
        return BaseElementModel
