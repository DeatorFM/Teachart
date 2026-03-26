from enum import Enum


class AppAction(Enum):
    NoAction = 0
    NewFile = 1
    OpenFile = 2
    CourseExplorer = 3
    Settings = 4
    StartDialog = 5
    OpenDialog = 6
    PresenterView = 7


class ResourceFlag(Enum):
    NoResource = 0
    Optional = 1
    HasResource = 2


class ResourceType(Enum):
    """Defines ResourceType. Class can be inherited to create custom types or use 'OTHER'."""

    NONE = 0
    TEXT = 1
    IMAGE = 2
    AUDIO = 3
    DOC = 4
    OTHER = 5
