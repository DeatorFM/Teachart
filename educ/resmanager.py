from collections.abc import Container
import enum
import tempfile

class ResourceType(enum.Enum):
    NONE = 0
    TEXT =  1
    IMAGE = 2
    AUDIO = 3
    DOC = 4
    OTHER = 5

class ResourceContainer(Container):
    """A container with all references of files."""

    def __init__(self) -> None:
        self._paths = {restype: [] for restype in ResourceType}
        self.tempdir = tempfile.TemporaryDirectory()

    def save(self, file: str, restype: ResourceType) -> str|None:
        """Saves file path and return it. If the file already exist it will not append the path"""
        if not self.hasRessource(file):
            self._paths[restype].append(file)
            return file
        else:
            return self.callSame(file, restype)
        
    def create(self, ext: str, restype: ResourceType) -> str:
        """Creates new reference in the container with the given file extension 'ext' and ResourceType 'restype' """
        name = "{}{}{}".format(restype.name.lower(), len(self._paths[restype])+1, ext)
        print("Created", name)
        self._paths[restype].append(name)
        return name

    def call(self, file: str, restype: ResourceType) -> str|bool:
        """Returns path of ressource with basename 'file' if existing"""
        if file in self.contents():
            return self._paths[restype][self._paths[restype].index(file)]
        else:
            return False
        
    def callSame(self, file: str, restype: ResourceType) -> str|None:
        """Compares 'file' with every file in the container. Returns the one that is the same."""
        if file in self._paths[restype]:
            return file

    def delete(self, file: str) -> None:
        """Removes file from ressource container. 'file' must be the basename."""
        for key in self._paths.keys():
            if file in self._paths[key]:
                self._paths[key].remove(file)

    def contents(self) -> list[str]:
        """Returns list of all files in the temporary directory of container."""
        contents = []
        for l in self._paths.values():
            contents += l
        return contents

    def hasRessource(self, file: str) -> bool:
        """Returns True if there is a ressource in the container that is the same as 'file' with the given ressource type 'restype'."""
        if file in self.contents():
            return True
        else:
            return False

    def paths(self, restype: ResourceType) -> list:
        return self._paths[restype]

    def __repr__(self) -> str:
        return str(self.contents())
    
    def __contains__(self, __x: object) -> bool:
        if __x in self.contents():
            return True
        else: 
            return False