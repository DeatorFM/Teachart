from __future__ import annotations

import enum
import os.path as osp
import random
import string
import tempfile
from collections.abc import KeysView, ValuesView
from dataclasses import dataclass
from genericpath import exists
from pathlib import Path
from typing import Any, Callable

from PyQt6.QtCore import QFile, QObject, pyqtSignal, pyqtSlot

from tcha.error import CopyError


class ResourceType(enum.Enum):
    """Defines ResourceType. Class can be inherited to create custom types or use 'OTHER'."""

    NONE = 0
    TEXT = 1
    IMAGE = 2
    AUDIO = 3
    DOC = 4
    OTHER = 5


class ResourceObject(QObject):
    resourceExpired = pyqtSignal(
        str, ResourceType, int
    )  #  self.name, self.type, self._type_num

    def __init__(
        self,
        num: int,
        rtype: ResourceType = ResourceType.NONE,
        name: str | None = None,
        parent: ResourceContainer | None = None,
    ):
        """Creates object that holds reference to a resource and manages its lifetime by counting its users"""
        super().__init__(parent)
        self._type_num: int = num  # Ordinal number of object with type 'type'
        self._type = rtype
        self._name: str = name if name else str(id(self))
        self._f: QFile | None = QFile(self.path) if self.path else None
        if self._f:
            self._f.open(QFile.OpenModeFlag.ReadOnly)
        self._extension: str | None = Path(self.path).suffix if self.path else None
        self._member_count: int = 0
        self._datalink: Callable | None = None

    def delete_member(self) -> None:
        """Decreases member count in case a model stops using this resource"""
        self._member_count -= 1
        if self._member_count == 0:
            self.resourceExpired.emit(self._name, self._type, self._type_num)
            if self._f:
                self._f.close()
            print("Object is expired")

    def add_member(self) -> None:
        """Increases member count when a model starts using this resource"""
        print("Added member to resource")
        self._member_count += 1

    def get_data(self) -> bytes:
        """Returns the data as bytes from the file set by location of the ResourceObject or the raw data if unserialised."""
        if self.path:
            data = self._f.readAll()
            self._f.reset()
            return data.data()
        return self._datalink() if self._datalink else bytes()

    def adjust_type_num(self, num: int) -> bool:
        """Adjusts the type number and returns True if adjusted."""
        print(
            f"Comparing {num} with own {self._type_num} of original filename {self.filename()}"
        )
        if num < self._type_num:
            self._type_num -= 1
            print(f"Filename is now {self.filename()}")
            return True
        print("Filename unchanged")
        return False

    @property
    def name(self) -> str:
        """Returns the identifiable name of the object. This is usually the path for serialised files otherwise the id."""
        return self._name

    @property
    def path(self) -> str | None:
        """Returns the original path of the resource if existing."""
        return self._name if self.name and exists(self.name) else None

    def qfile(self) -> QFile | None:
        """Returns the filepath as a QFile object."""
        if self.path:
            self._f.reset()
            return self._f

    @property
    def type(self) -> ResourceType:
        """Returns resource type"""
        return self._type

    @property
    def filetype(self) -> str:
        "Return filetype for serialising the object."
        return self._extension

    @property
    def member_count(self) -> int:
        return self._member_count

    @property
    def type_num(self) -> int:
        return self._type_num

    def set_extension(self, suffix: str) -> None:
        self._extension = suffix.strip(".")

    def filename(self) -> str | None:
        """Returns a filename that is used for serialisation as long as the file extension is provided."""
        return f"{self._type.name.lower()}{self._type_num}.{self._extension}"

    @property
    def data(self) -> bytes | None:
        """Returns the data by using the function set as a datalink else returns an empty bytes object."""
        return self._datalink() if self._datalink else None

    def set_datalink(self, link: Callable) -> None:
        """Sets a function that returns data from an element"""
        self._datalink = link

    def copy(self) -> ResourceObject:
        if self.path:
            raise CopyError(
                "ResourceObject with cannot be copied because en external resource cannot exist more than once."
            )
        else:
            cont: ResourceContainer = self.parent()
            obj = cont.create(self.type)
        return obj

    def is_serialised(self) -> bool:
        return exists(self.path) if self.path else False

    def has_references(self) -> bool:
        return bool(self._member_count)

    def close(self) -> None:
        """Safely close file handle"""
        if self._f:
            self._f.close()

    def __eq__(self, value: Any) -> bool:
        if isinstance(value, ResourceObject):
            return self._type == value.type and self.name == value.name
        return False

    def __repr__(self) -> str:
        return f"ResourceObject: {self.type} {self.name} {self._member_count}"

    def __deepcopy__(self, memo: dict | None = None) -> ResourceObject:
        return ResourceObject(self._type_num, self._type, self._name)


@dataclass
class ResourceTransferObject:
    """Simple Resource API to deepcopy models"""

    type_num: int
    rtype: ResourceType
    filename: str
    path: Path | None = None
    datalink: Callable | None = None


class ResourceContainer(QObject):
    """A container with objects linking element model and resource."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._objects: dict[str, ResourceObject] = {}
        self._internal_counter = 0
        self._tempdir = tempfile.TemporaryDirectory(".tmp", "RESC")
        self._blocked = False
        self._deletion_queue: list[ResourceObject] = []

    def save(self, restype: ResourceType, path: str) -> ResourceObject:
        """Creates and saves ResourceObject with a file in ResourceContainer and returns an identical object if existing"""
        if not osp.exists(path) and osp.isfile(path):
            raise FileNotFoundError
        self._internal_counter += 1
        try:
            return self._objects[path]
        except KeyError:
            res_object = (
                ResourceObject(self.count_type(restype) + 1, restype, path, self)
                if not self._objects.get(path)
                else self._objects[""]
            )
            res_object.resourceExpired.connect(self.delete)
            self._objects[res_object.name] = res_object
            return self._objects[res_object.name]

    def create(self, restype: ResourceType) -> ResourceObject:
        """Creates a unique ResourceObject and returns it"""
        self._internal_counter += 1
        res_object = ResourceObject(self.count_type(restype) + 1, restype, None, self)
        res_object.resourceExpired.connect(self.delete)
        self._objects[res_object.name] = res_object
        return res_object

    def get(self, name: str) -> ResourceObject | None:
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

    @pyqtSlot(ResourceObject)
    def _on_object_copied(self, obj: ResourceObject) -> None:
        obj.resourceExpired.connect(self.delete)
        obj.copied.connect(self._on_object_copied)
        self._objects[obj.name] = obj

    @pyqtSlot(str, ResourceType, int)
    def delete(self, name: str, restype: ResourceType, num: int) -> bool:
        """Removes object from container if deletion not blocked else queue for deletion"""
        if not self._blocked:
            try:
                print("Deleting ResourceObject")
                del self._objects[name]
                self._adjust_type_nums(restype, num)
                return True
            except KeyError:
                return False
        else:
            self._deletion_queue.append(self._objects[name])

    def set_blocked(self, blocked: bool) -> None:
        """Blocks the ResourceContainer to delete resource objects immediately."""
        self._blocked = blocked
        if not blocked:
            self._deletion_queue.clear()

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

    def __del__(self) -> None:
        # print("ResourceContainer deleted")
        self._objects.clear()
        self._tempdir.cleanup()
        self._tempdir = None
