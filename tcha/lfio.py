from PyQt6.QtCore import QXmlStreamWriter, QXmlStreamReader, QByteArray, QBuffer, QDateTime, Qt
from tcha.tablemodel import TableModel, CellModel, HeaderDataItem, TableData
from tcha.resmanager import ResourceContainer, ResourceObject
from tcha.lesson import Lesson
from zipfile import ZipFile, ZIP_DEFLATED
import importlib
import tempfile
import shutil
import os.path as osp

class LessonFile:
    """Provides file stream for serialised Lesson-Documents"""
    def __init__(self, mode: str, path: str):
        self._f = ZipFile(path, mode, ZIP_DEFLATED)
        self._path = path
        self._tempdir: str | None = None
        self._last_saved = QDateTime()
        self._file_id: str = self.generate_file_id()

        has_resources = any(name.startswith("resources/") for name in self._f.namelist())

        if mode == "r" and has_resources:
            self._last_saved = QDateTime.currentDateTime()
            self._tempdir = str(osp.normpath(tempfile.mkdtemp(".tmp", "TCHA")))
            print("Temporary", self._tempdir)
            self._f.extractall(self._tempdir)

        
    def save(self, lesson: Lesson, rescont: ResourceContainer, tablemodel: TableModel) -> None:
        """Saves a new file or overwrites the entire file's contents if existing"""
        self.change_open_mode("w")
        rescont.prepare_for_serialisation()
        xml_data = XmlWriter.write_xml(self.file_id(), tablemodel, lesson)
        with self._f.open("structure.xml", "w") as xml_f:
            xml_f.write(xml_data.data())
        
        for obj in rescont.contents():
            if not obj.data:
                self._copy(obj)
            else:
                self._write_new(obj)

        self._last_saved = QDateTime.currentDateTime()
        self.change_open_mode("r")
     
    def _copy(self, resobj: ResourceObject) -> None:
        self._f.write(resobj.path, f"resources/{resobj.serialised_name}")

    def _write_new(self, resobj: ResourceObject) -> None:
        with self._f.open(f"resources/{resobj.serialised_name}", "w") as f:
            f.write(resobj.data)

    def change_open_mode(self, mode: str) -> None:
        if mode == "r" or mode == "w":
            self._f.close()
            self._f = ZipFile(self._path, mode, ZIP_DEFLATED)

    def read_resource(self, name: str) -> bytes:
        """Return the data of the file 'name' in the 'resources/' directory as bytes"""
        self.change_open_mode("r")
        with self._f.open(name, "r") as f:
           return f.read()
        
    def xml(self) -> bytes:
        """Returns the DOM of the lesson-file found in structure.xml as bytes"""
        self.change_open_mode("r")
        with self._f.open("structure.xml", "r") as f:
            return f.read()
        
    def generate_file_id(self) -> str:
        return str(hash(self._path + self._last_saved.toString(Qt.DateFormat.ISODate)))
    
    def file_id(self) -> str:
        return self._file_id
    
    def set_file_id(self, file_id: str) -> None:
        self._file_id = file_id

    @property    
    def path(self) -> str:
        return self._path
    
    @property
    def temppath(self) -> str | None:
        return self._tempdir

    def __hash__(self) -> int:
        return hash(self._path)

    def __del__(self) -> None:
        if self._tempdir:
            print("Delete tempdir")
            shutil.rmtree(self._tempdir, ignore_errors=False)
           
class XmlWriter:

    @staticmethod
    def write_xml(file_id: str, table: TableModel, lesson: Lesson) -> QByteArray:
        writer = QXmlStreamWriter()
        xml_data = QByteArray()
        buffer = QBuffer(xml_data)
        buffer.open(QBuffer.OpenModeFlag.WriteOnly)
        writer.setDevice(buffer)

        writer.writeStartDocument()
        writer.writeStartElement("teachart")

        writer.writeEmptyElement("metadata")
        writer.writeAttribute("version", "1")
        writer.writeAttribute("file_id", file_id)

        writer = lesson.xml(writer)
        writer = table.xml(writer)

        writer.writeEndElement()
        writer.writeEndDocument()

        return xml_data

class XmlReader:

    @staticmethod
    def read_xml(xml_data: bytes, rescont: ResourceContainer, lessonfile: LessonFile) -> tuple[Lesson, TableModel]:
        reader = QXmlStreamReader(xml_data)
        lesson = None
        model = None

        while not reader.atEnd():
            token = reader.readNext()

            if token == QXmlStreamReader.TokenType.StartElement:
                if reader.name() == "metadata":
                    attrs = reader.attributes()
                    lessonfile.set_file_id(attrs.value("file_id"))
                if reader.name() == "lesson":
                    lesson = Lesson.read(reader)
                elif reader.name() == "table":
                    break
        model = XmlReader._read_table(reader, rescont, lessonfile)

        return lesson, model
    
    @staticmethod
    def _read_table(reader: QXmlStreamReader, rescont: ResourceContainer, lessonfile: LessonFile) -> TableModel:
        attrs = reader.attributes()
        rows = int(attrs.value("rows"))
        headers = {Qt.Orientation.Horizontal : [], Qt.Orientation.Vertical : [HeaderDataItem.vertical() for _ in range(rows)]}
        cell = None
        row = None
        data = []

        while not reader.atEnd():
            token = reader.readNext()
           
            if token == QXmlStreamReader.TokenType.StartElement:
                if reader.name() == "header":
                    attrs = reader.attributes()
                    headers[Qt.Orientation.Horizontal].append(HeaderDataItem(Qt.Orientation.Horizontal, int(attrs.value("size")), True, attrs.value("text")))
                elif reader.name() == "row":
                    row = []
                elif reader.name() == "cell":
                    cell = CellModel()
                elif reader.name() == "element":
                    attrs = reader.attributes()
                    model = XmlReader._element_model(attrs.value("type"))
                    print("Temporary", lessonfile.temppath)
                    resobj = rescont.save(model.restype(), osp.join(lessonfile.temppath, "resources", attrs.value("file")), True)
                    resobj.set_serialised_name(attrs.value("file"))
                    resobj.add_member()
                    model = model.read(attrs, resobj)
                    cell.add_model(model)
            elif token == QXmlStreamReader.TokenType.EndElement:
                if reader.name() == "row":
                    data.append(row)
                elif reader.name() == "cell":
                    row.append(cell)
                elif reader.name() == "table":
                    break

        return TableModel(TableData(data, headers))
   
    @staticmethod
    def _element_model(name: str) -> "BaseModel":
        model = getattr(importlib.import_module(f"tcha.elements.{name.lower()}"), "return_model")
        return model()