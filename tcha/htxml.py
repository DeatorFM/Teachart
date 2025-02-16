from PyQt6.QtCore import QXmlStreamWriter
from tcha.tablemodel import TableModel
from tcha.resmanager import ResourceContainer
from tcha.lesson import Lesson
import zipfile

class HtxWriter:
    def __init__(self, path: str, table: TableModel, lesson: Lesson, rescont: ResourceContainer) -> None:
        self.table = table
        self.lesson = lesson
        self.resources = rescont

        self.path = self.join_path(path)
        self.zipf = self.create_zip()
        self.xmlwriter = QXmlStreamWriter()

    def join_path(self, path: str) -> str:
        if not path.endswith(".htx"):
            return "".join((path, ".htx"))
        else:
            return path
        
    def create_zip(self) -> zipfile.ZipFile:
        htxzip = zipfile.ZipFile(self.path, "w")
        return htxzip

    def write_xml(self) -> None:
        self.xmlwriter.writeStartDocument()
        self.xmlwriter.writeNamespace("h", "h")
        self.xmlwriter.writeStartElement("h", "htx") 

        self.xmlwriter = self.lesson.xml(self.xmlwriter)
        self.xmlwriter = self.table.xml(self.xmlwriter)

    def write_cells(self) -> None:
        for row in self.table.structure():
            for cell in row:
                self.xmlwriter.writeStartElement("h", "cell")

class HtxReader:
    pass