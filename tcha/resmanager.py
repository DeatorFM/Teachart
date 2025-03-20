from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QVariant
from collections import Counter
from typing import Any, Protocol
from dataclasses import dataclass
import enum
import tempfile
import random
import string
import os.path as osp

class LessonFileProtocol(Protocol):
    def read_resource(self, name: str) -> bytes: ...
    def close(self) -> None: ...

@dataclass(frozen=True)
class ResourceLocation:
    path: str
    serialised: bool

class ResourceType(enum.Enum):
    NONE = 0
    TEXT =  1
    IMAGE = 2
    AUDIO = 3
    DOC = 4
    OTHER = 5

class ResourceObject(QObject):
    resourceExpired = pyqtSignal(QVariant)

    def __init__(self, type: ResourceType = ResourceType.NONE, path: str = "", serialised=False, parent = None): 
        """Creates object that holds reference to a resource and manages its lifetime by counting its users"""
        super().__init__(parent)
        self._type = type
        self._location: ResourceLocation = ResourceLocation(path, serialised)
        self._member_count: int = 0
        self._id: int = 0
        self._old_name: str = ""
        self._serialised_name: str = ""
        self._data: bytes | None = None

    def delete_member(self) -> None:
        """Decreases member count in case a model stops using this resource"""
        self._member_count -= 1
        if self._member_count == 0:
            current_hash = self.__hash__()
            self.resourceExpired.emit(QVariant(current_hash))
            print("Object is expired")

    def add_member(self) -> None:
        """Increases member count when a model starts using this resource"""
        self._member_count += 1

    def get_data(self) -> bytes:
        """Returns the data as bytes from the file set by location of the ResourceObject"""
        print("Trying to open:", self._location.path)
        with open(self.path, "rb") as f:
            return f.read()

    @property
    def path(self) -> str:
        """Returns the original path of the resource"""
        return self._location.path
    
    def make_serialised_name(self, prefix: str, suffix: str) -> str:
        """Creates an identifiable name for the file when serialised"""
        self._old_name = self._serialised_name
        self._serialised_name = f"{prefix}{self._id}{suffix}"
        return self._serialised_name
    
    def set_serialised_name(self, name: str) -> None:
        self._serialised_name = name
    
    @property
    def serialised_name(self) -> str:
        """Returns serialised name if existing"""
        return self._serialised_name
    
    @property
    def old_name(self) -> str:
        return self._old_name

    @property
    def type(self) -> ResourceType:
        """Returns resource type"""
        return self._type
    
    @property
    def id(self) -> int:
        return self._id
    
    def set_id(self, id: int) -> None:
        self._id = id

    @property
    def data(self) -> bytes:
        """Returns the data that the ResourceObject is holding.
           Often used when unserialised data needs to be serialised"""
        return self._data
    
    def set_data(self, data: bytes) -> None:
        """Sets data as bytes that are expected to be written into a .lesson-file"""
        self._data = data

    def is_serialised(self) -> bool:
        return self._location.serialised

    def __hash__(self) -> int:
        return hash((self._type, self._location))
        
    def __eq__(self, value) -> bool:
        if isinstance(value, ResourceObject):
            return self._type == value.type and self.path == value.path
        return False
        
    def __repr__(self) -> str:
        return f"ResourceObject: {self._type} {self.path} {hash(self)} {self._member_count}"

class ResourceContainer(QObject):
    """A container with all references of files."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._objects: set[ResourceObject] = set()
        self._tempdir = tempfile.TemporaryDirectory(".tmp", "RESC")
        self._lessonfile: LessonFileProtocol | None = None

    def save(self, restype: ResourceType, path: str, serialised=False, parent=None)  -> ResourceObject:
        """Creates and saves ResourceObject in ResourceContainer and returns an identical object if existing"""
        res_object = ResourceObject(restype, path, serialised, parent)
        res_object.resourceExpired.connect(self.delete)
        h = hash(res_object)    
        self._objects.add(res_object)
        existing_object = self.call(restype, h)   
        return existing_object              
        
    def create(self, restype: ResourceType, parent=None) -> ResourceObject:
        """Creates a unique ResourceObject and returns it"""
        res_object = ResourceObject(restype, self._generate_32_char_string(), None, parent)
        res_object.resourceExpired.connect(self.delete)
        self._objects.add(res_object)
        return res_object
    
    def make_path(self, suffix: str) -> str:
        """Creates path to temporary folder and returns its random generated path as a string"""
        suffix = suffix.strip(".")
        return f"{self._tempdir.name}/{self._generate_32_char_string()}.{suffix}"
    
    def _generate_32_char_string(self) -> str:
        characters = string.ascii_letters + string.digits
        path = ''.join(random.choice(characters) for _ in range(32))
        return path

    def call(self, type: ResourceType, _hash: int) -> ResourceObject:
        """Returns resource object with matching hash otherwise returns an invalid ResourceObject"""
        for obj in self._objects:
            if type == obj.type and hash(obj) == _hash:
                return obj
        return ResourceObject() # Invalid ResourceObject

    @pyqtSlot(QVariant)
    def delete(self, _hash: QVariant) -> None:
        """Removes object from container"""
        for obj in self._objects:
            print("Analyse object with hash", hash(obj), "compared with hash", _hash)
            if hash(obj) == _hash:
                print("Item with hash found")
                self._objects.discard(obj)
                return

    def contents(self) -> set[ResourceObject]:
        """Returns list of all ResourceObjects in the temporary directory of container."""
        return self._objects

    def has_ressource(self, type: ResourceType, _hash: int) -> bool:
        """Returns True if there is a ressource in the container that has the same type and hash as a ResourceObject in the container."""
        for obj in self._objects:
            if type == obj.type and hash(obj) == _hash:
                return True
        return False
    
    def prepare_for_serialisation(self) -> None:
        """Gives each ResourceObject a unique number that's used in the file name for serialisation"""
        type_counter = Counter([obj.type for obj in self._objects])
        for obj in self._objects:
            obj.set_id(type_counter[obj.type])
            type_counter[obj.type] -= 1

    def set_lessonfile(self, lessonfile: LessonFileProtocol) -> None:
        "Sets LessonFile object to reference location in ResourceObjects"
        self._lessonfile = lessonfile

    def hashof(self, restype: ResourceType, path: str) -> int:
        return hash((restype, path))
    
    def count_type(self, restype: ResourceType) -> int:
        return len([obj.type for obj in self._objects if obj.type == restype])
    
    def __del__(self) -> None:
        self._tempdir = None
    
    def __len__(self) -> int:
        return len(self._objects)

    def __repr__(self) -> str:
        return str(self._objects)
    
    def __contains__(self, __x: ResourceObject) -> bool:
        if __x in self._objects:
            return True
        return False