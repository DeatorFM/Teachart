from __future__ import annotations

import enum
import os.path as osp
import random
import string
import tempfile
from abc import ABCMeta, abstractmethod
from collections.abc import KeysView, ValuesView
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from PyQt6.QtCore import QFile, QObject, pyqtSignal, pyqtSlot


class ResourceType(enum.Enum):
    """Defines ResourceType. Class can be inherited to create custom types or use 'OTHER'."""

    NONE = 0
    TEXT = 1
    IMAGE = 2
    AUDIO = 3
    DOC = 4
    OTHER = 5


class ResourceObject(QObject):
    __metaclass__ = ABCMeta
    resourceExpired = pyqtSignal(str, ResourceType, int)  #  self.name, self.type, self._type_num

    def __init__(
        self,
        num: int,
        rtype: ResourceType = ResourceType.NONE,
        parent: ResourceContainer | None = None,
    ):
        """Baseclass for ResourceObjects."""
        super().__init__(parent)
        self._type_num: int = num  # Ordinal number of object with type 'type'
        self._type = rtype
        self._member_count: int = 0

    def add_member(self) -> None:
        """Increases member count when a model starts using this resource"""
        print("Added member to resource")
        self._member_count += 1

    def delete_member(self) -> None:
        """Decreases member count in case a model stops using this resource"""
        self._member_count -= 1
        if self._member_count == 0:
            self.resourceExpired.emit(self.name, self._type, self._type_num)
            if self._f:
                self._f.close()
            print("Object is expired")

    def adjust_type_num(self, num: int) -> bool:
        """Adjusts the type number and returns True if adjusted."""
        print(f"Comparing {num} with own {self._type_num} of original filename {self.filename()}")
        if num < self._type_num:
            self._type_num -= 1
            print(f"Filename is now {self.filename()}")
            return True
        print("Filename unchanged")
        return False

    @property
    def type(self) -> ResourceType:
        """Returns resource type"""
        return self._type

    @property
    def member_count(self) -> int:
        return self._member_count

    @property
    def type_num(self) -> int:
        return self._type_num

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the identifiable name of the object. This is usually the path for serialised files otherwise the id."""
        return ""

    @property
    @abstractmethod
    def path(self) -> Path | None:
        """Return the path to a resource if existing else None"""
        return None

    @property
    @abstractmethod
    def data(self) -> bytes | None:
        """Returns the data associated with the ResourceObject"""
        return None

    @abstractmethod
    def filename(self) -> str:
        """Returns the filename used to serialise a tch-file."""
        return ""

    @abstractmethod
    def close(self) -> None:
        """Close handle for data streams."""
        pass

    def __eq__(self, value: Any) -> bool:
        if isinstance(value, ResourceObject):
            return self._type == value.type and self.name == value.name
        return False


class UniqueResourceObject(ResourceObject):
    """ResourceObject without external resource that is always unique."""

    def __init__(self, num: int, rtype=ResourceType.NONE, parent=None):
        super().__init__(num, rtype, parent)

        self._datalink: Callable | None = None
        self._extension: str | None = None

    @property
    def name(self):
        return str(id(self))

    @property
    def data(self) -> bytes | None:
        """Returns the data by using the function set as a datalink else returns an empty bytes object."""
        return self._datalink() if self._datalink else None

    def set_datalink(self, link: Callable) -> None:
        """Sets a function that returns data from an element"""
        self._datalink = link

    def set_extension(self, suffix: str) -> None:
        self._extension = suffix.strip(".")

    def filename(self) -> str | None:
        """Returns a filename that is used for serialisation as long as the file extension is provided."""
        return f"{self._type.name.lower()}{self._type_num}.{self._extension.strip('.')}"

    def __str__(self):
        return self.name


class FileResourceObject(UniqueResourceObject):
    """ResourceObject with external resource that can be shared between models."""

    def __init__(self, num: int, path: Path, rtype=ResourceType.NONE, parent=None):
        super().__init__(num, rtype, parent)

        self._f = QFile(str(path))
        self._f.open(QFile.OpenModeFlag.ReadOnly)

    def is_valid(self) -> bool:
        return self._f.isOpen()

    @property
    def name(self) -> str:
        """Returns the object name. On FileResourceObject this is always a POSIX compliant path (/)."""
        return self.path.as_posix()

    @property
    def path(self) -> Path:
        """Returns the original path of the resource if existing."""
        return Path(self._f.fileName())

    def qfile(self) -> QFile | None:
        """Returns the filepath as a QFile object."""
        if self.path:
            self._f.reset()
            return self._f

    def filename(self) -> str | None:
        """Returns a filename that is used for serialisation as long as the file extension is provided."""
        return f"{self._type.name.lower()}{self._type_num}.{self.path.suffix.strip('.')}"

    def close(self) -> None:
        """Safely close file handle"""
        if self._f:
            self._f.close()

    def __str__(self):
        return self.path


class CompressedResourceObject(FileResourceObject):
    def __init__(self, num: int, path: str, rtype=ResourceType.NONE, parent=None):
        """File object with different name and path definition"""
        super().__init__(num, path, rtype, parent)

        self._name = path
        self._original_file = path
        self._compressed = False if ".compressed" not in path else True

    @property
    def name(self) -> str:
        return self._name

    @property
    def original_resource(self) -> str:
        return self._original_file

    def set_compressed_file(self, path: str) -> None:
        qfile = QFile(path)
        if qfile.exists():
            qfile.open(QFile.OpenModeFlag.ReadOnly)
            self._f = qfile
            self._compressed = True


@dataclass(frozen=True, slots=True)
class ResourceTransferObject:
    """Representation of a resource without file i/o. Use to write resources to a tch-file."""

    rtype: ResourceType
    filename: str
    src_path: str | None = None
    data: bytes | None = None

    def has_data(self) -> bool:
        return bool(self.data)


class ResourceContainer(QObject):
    """A container with objects linking element model and resource."""

    tempdir: tempfile.TemporaryDirectory = tempfile.TemporaryDirectory(".tmp", "RESC", delete=False)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._objects: dict[str, ResourceObject] = {}
        self._internal_counter = 0

    @property
    def temppath(self) -> Path:
        return Path(self.tempdir.name)

    def save(self, restype: ResourceType, path: Path) -> ResourceObject:
        """Creates and saves ResourceObject with a file in ResourceContainer and returns an identical object if existing"""
        if not path.exists() and path.is_file():
            raise FileNotFoundError
        self._internal_counter += 1

        try:
            return self._objects[path.as_posix()]
        except KeyError:
            res_object = FileResourceObject(self.count_type(restype) + 1, path, restype, self)
            res_object.resourceExpired.connect(self.delete)
            self._objects[res_object.name] = res_object
            return self._objects[res_object.name]

    def create(self, restype: ResourceType) -> ResourceObject:
        """Creates a unique ResourceObject and returns it"""
        self._internal_counter += 1
        res_object = UniqueResourceObject(self.count_type(restype) + 1, restype, self)
        res_object.resourceExpired.connect(self.delete)
        self._objects[res_object.name] = res_object
        return res_object

    def get(self, name: str) -> ResourceObject:
        """Returns ResourceObject with the corresponding name. Raises 'KeyError' if object doesn't exist"""
        return self._objects[name]

    def make_path(self, extension: str) -> str:
        """Creates path to temporary folder and returns its random generated path as a string"""
        extension = extension.strip(".")
        return f"{self._tempdir.name}/{self._generate_32_char_string()}.{extension}"

    def _generate_32_char_string(self) -> str:
        characters = string.ascii_letters + string.digits
        name = "".join(random.choice(characters) for _ in range(32))
        return name

    def _adjust_type_nums(self, restype: ResourceType, num: int) -> str:
        """The ordinal number of every object of one type is adjusted."""
        for obj in self.contents_by_type(restype):
            obj.adjust_type_num(num)

    @pyqtSlot(str, ResourceType, int)
    def delete(self, name: str, restype: ResourceType, num: int) -> bool:
        """Removes object with given name ResourceTyoe and number from container"""
        try:
            print("Deleting ResourceObject")
            del self._objects[name]
            self._adjust_type_nums(restype, num)
            return True
        except KeyError:
            return False

    def names(self) -> KeysView[str]:
        """Returns all objects' names."""
        return self._objects.keys()

    def contents(self) -> ValuesView[ResourceObject]:
        """Returns list of all Resource:Objects in the temporary directory of container."""
        return self._objects.values()

    def contents_by_type(self, restype: ResourceType) -> tuple[ResourceObject]:
        return tuple(filter(lambda x: x.type == restype, self._objects.values()))

    def count_type(self, restype: ResourceType) -> int:
        return len(self.contents_by_type(restype))

    def to_transfer_objects(self) -> list[ResourceTransferObject]:
        tobjects = []
        for obj in self.contents():
            tobjects.append(ResourceTransferObject(obj.type, obj.filename(), obj.path, obj.data))
        return tobjects

    def close_file_streams(self) -> None:
        for obj in self.contents():
            obj.close()

    def __len__(self) -> int:
        return len(self._objects)

    def __str__(self) -> str:
        return f"ResourceContainer: key:value {self._objects}"

    def __bool__(self) -> bool:
        if self._objects:
            return True
        return False

    def __contains__(self, __x: ResourceObject | str) -> bool:
        if isinstance(__x, ResourceObject):
            if __x in self._objects.values():
                return True
        elif isinstance(__x, str):
            if __x in self._objects.keys():
                return True
        else:
            raise TypeError("Only types  'ResourceObject' and 'str' are accepted.")
        return False
