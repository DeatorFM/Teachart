from enum import Enum, Flag, auto
from pathlib import Path

PROJECT_PATH = Path().parent
RESOURCE_PATH = PROJECT_PATH / "resources"


class AppAction(Enum):
    NoAction = 0
    NewFile = 1
    OpenFile = 2
    CourseExplorer = 3
    Settings = 4
    StartDialog = 5
    OpenDialog = 6
    PresenterView = 7
    AboutTeachart = 8


class DialogType(Enum):
    Editor = 0
    Start = 1
    Settings = 2
    DbManager = 3
    About = 4
    Other = 100


class CellAction(Enum):
    Discard = auto()
    Accept = auto()
    AddElement = auto()
    AddFromClipboard = auto()
    RemoveElement = auto()
    MoveUp = auto()
    MoveDown = auto()
    Clear = auto()


class ClipboardContent(Flag):
    NotParsable = auto()
    ElementData = auto()
    CopiedIndex = auto()


class ResourceFlag(Enum):
    NoResource = 0
    Optional = 1
    HasResource = 2


class CloseState(Enum):
    StayOpen = 0
    Closed = 1
    ScheduleClosure = 2


class ResourceType(Enum):
    """Defines ResourceType. Class can be inherited to create custom types or use 'OTHER'."""

    NONE = 0
    TEXT = 1
    IMAGE = 2
    AUDIO = 3
    DOC = 4
    OTHER = 5


class DisplayMode(Enum):
    Single = 0
    Extended = 1
    Duplicated = 2


class CanvasTool(Enum):
    Pen = 1
    Rubber = 2
    Arrow = 3
    Pointer = 4


class EditingLevel(Flag):
    NoEditing = auto()
    CellEditing = auto()
    ElementEditing = auto()


class TableViewMode(Enum):
    Table = 0
    SingleRow = 1


class SaveState(Enum):
    Unsaved = 0
    Saving = 1
    Saved = 2
    SaveAndQuit = 3


class FilterMode(Enum):
    NoFilter = 0
    ShowOnlyFiltered = 1
    HideFiltered = 2


class FilteredArea(Enum):
    Index = 0
    Row = 1
    Column = 2
