from multiprocessing import Value
from zipfile import ZipFile, ZIP_DEFLATED
from base64 import b64decode, b64encode
from typing import Literal, Any
import importlib
import tempfile
import os.path as osp

from PyQt6.QtCore import QXmlStreamWriter, QXmlStreamReader, QByteArray, QBuffer, QDateTime, Qt, qChecksum, QFile

from tcha.tablemodel import TableModel, CellModel, HeaderDataItem, TableData
from tcha.resmanager import ResourceContainer, ResourceObject, ResourceType
from tcha.lesson import Lesson
from tcha.error import LFExceptions, ErrorLogger, QtError
from tcha.elements import get_definitions


class LessonFile:
    """Provides file stream for serialised Lesson-Documents"""
    def __init__(self, mode: str, path: str | None = None):
        self._f = ZipFile(path, mode, ZIP_DEFLATED) if path and mode == "r" else None
        self._tempdir: tempfile.TemporaryDirectory | None = None
        self._last_saved = None
        self._cached_xml = None
        self._metadata = {
            "version" : 1,
            "file_id" : 0
            }
        
        if mode == "r" and path:
            self._last_saved = QDateTime.currentDateTime()
            self._tempdir = tempfile.TemporaryDirectory(".tmp", "TCHA", ignore_cleanup_errors=True)
            print("Temporary", self._tempdir)
            self._f.extractall(self.temppath)
            self._error_handler = ErrorLogger(f"{osp.basename(path)}")
            self._error_handler.log_msg(f"Start reading file {osp.basename(path)} at {self._last_saved.toString(Qt.DateFormat.ISODateWithMs)}")
            self.set_metadata(self._metadata)
        elif mode == "w":
            pass
        else:
            raise ValueError
        
    def save(self, lesson: Lesson, rescont: ResourceContainer, tablemodel: TableModel, path: str | None = None) -> bool:
        """Saves a new file or overwrites the entire file's contents if existing"""
        # How can we imporve that??

        self._last_saved = QDateTime.currentDateTime()

        if not self._f or path:
            self._f = ZipFile(path, "w", ZIP_DEFLATED)
            self._metadata["file_id"] = self.generate_file_id()
            self._error_handler = ErrorLogger(f"{self.file_id}.log")
        else:
            self.change_open_mode("w")

        # Generate and write xml for document structure
        xml_data = XmlWriter.write_xml(self.file_id, tablemodel, lesson)
        with self._f.open("structure.xml", "w") as xml_f:
            xml_f.write(xml_data.data())

        # Create checksum for document xml and write
        chksums = QByteArray()
        xml_chksum = f"\\xml:{qChecksum(xml_data, Qt.ChecksumType.ChecksumIso3309)}\n".encode()
        chksums.append(xml_chksum)

        # Copy the resources into file or create new file if necessary
        for obj in rescont.contents():
            if not obj.data:
                self._copy(obj)
            else:
                self._write_new(obj)

        # Write resources definitions into seperate xml file
        res_xml = XmlWriter.write_res_xml(rescont)
        with self._f.open("resources.xml", "w") as res_f:
            res_f.write(res_xml.data())

        # Generate checksum for resource definitions and append it to other definition
        res_chksum = f"\\res:{qChecksum(res_xml, Qt.ChecksumType.ChecksumIso3309)}\n".encode()
        chksums.append(res_chksum)
        encoded = b64encode(chksums.data())

        # Writes checksums to seperate file
        with self._f.open("chksum.dat", "w") as chksum_f:
            chksum_f.write(encoded)

        self.change_open_mode("r")
        return True


    def _copy(self, resobj: ResourceObject) -> None:
        self._f.write(resobj.path, f"resources/{resobj.filename()}")

    def _write_new(self, resobj: ResourceObject) -> None:
        with self._f.open(f"resources/{resobj.filename()}", "w") as f:
            f.write(resobj.data)

    def change_open_mode(self, mode: str) -> None:
        if mode == "r" or mode == "w":
            self._f.close()
            self._f = ZipFile(self.path, mode, ZIP_DEFLATED)

    def read_resource(self, name: str) -> bytes:
        """Return the data of the file 'name' in the 'resources/' directory as bytes"""
        self.change_open_mode("r")
        with self._f.open(name, "r") as f:
           return f.read()
        
    def extracted(self, name: str) -> bool:
        return osp.exists(osp.join(self.temppath, name))
        
    def xml(self) -> QFile:
        """Returns IO to extracted strcuture.xml as QFile. Raises an Exception of file not found or QFile throws an error."""
        if self.extracted("structure.xml"):
            qfile = QFile(osp.join(self.temppath, "structure.xml"))
            qfile.open(QFile.OpenModeFlag.ReadOnly)
            
            if not qfile.error().value:
                return qfile
            raise QtError(qfile.error(), qfile.errorString(), True)
        raise FileNotFoundError
                # if self.checksums()["\\xml"] == qChecksum(xml):
                #     print(xml)
                #     return xml
                # raise LFExceptions.InvalidXml(True)

    def get_resource_container(self, parent=None) -> ResourceContainer | None:
        """Returns ResourceContainer of the loaded file if file loaded."""
        try:
            qfile = QFile(osp.join(self.temppath, "resources.xml"))
            qfile.open(QFile.OpenModeFlag.ReadOnly)

            container = ResourceContainer(parent)
            reader = QXmlStreamReader(qfile)

            while not reader.atEnd():
                token = reader.readNext()

                if token == QXmlStreamReader.TokenType.StartElement:
                    if reader.name() == "res":
                        attrs = reader.attributes()
                        path: str = osp.join(self.temppath, "resources", str(attrs.value("file")))
                        container.save(ResourceType[str(attrs.value("type"))], path)
           
            if reader.error().value: self._error_handler.log(QtError(reader.error(), reader.errorString(), True), f"There was an error while reading the xml. Details: {reader.errorString()}")
            qfile.close()
            return container

        except (ValueError, KeyError) as e:
            e.critical = True
            self._error_handler.log(e, "Resource definition has invalid value. This is possibly due to an unknown or invalid resource type that is specified in the definitions.")
            return None
        
        except FileNotFoundError as e:
            e.critical = True
            self._error_handler.log(e, f"The defined file at '{e.filename}' could not be found.")
            return None

        except LFExceptions.MissingResource as e:
            e.critical = True
            self._error_handler.log(e, f"The defined file at '{e.path}' could not be found.")
            return None

    
    def get_table(self, rescont: ResourceContainer) -> TableModel | None:
        """Returns TableModel if file is loaded."""
        try:
            qfile = self.xml()
            table = XmlReader.read_table(qfile, rescont, osp.join(self.temppath, "resources"), self._error_handler)
            qfile.close()
            return table
        
        except FileNotFoundError as e:
            e.critical = True
            self._error_handler.log(e, "The file that contains table definitions could not be found.")
            return None
        except QtError as e:
            self._error_handler.log(e, f"There was an error while trying to read the xml file. Details: {e.error_string}")
            return None
        
    
    def get_lesson(self, default: Lesson | None = None) -> Lesson | None:
        """Returns Lesson model if file is loaded and could be read otherwise returns the default value."""
        try:
            qfile = self.xml()
            model =  XmlReader.read_lesson(qfile, self._error_handler)
            qfile.close()
            return model
        
        except FileNotFoundError as e:
            e.critical = True
            self._error_handler.log(e, "The file containing table definitions could not be found.")
            return default
        
        except QtError as e:
            self._error_handler.log(e, f"There was an error while trying to read the xml file. Details: {e.error_string}")
            return default
    
    def set_metadata(self, metadata: dict[str, Any]) -> None:
        try:
            qfile = self.xml()      
            reader = QXmlStreamReader(qfile)
            while not reader.atEnd():
                token = reader.readNext()

                if token == QXmlStreamReader.TokenType.StartElement:
                    if reader.name() == "metadata":
                        attrs = reader.attributes()
                        metadata["file_id"] = int(attrs.value("file_id"))
                        metadata["version"] = int(attrs.value("version"))
                        break
            qfile.close()

        except FileNotFoundError as e:
            e.critical = True
            self._error_handler.log(e, "The file that contains table definitions could not be found.")
            return 
        except QtError as e:
            self._error_handler.log(e, f"There was an error while trying to read the xml file. Details: {e.error_string}")
            return        
        except (ValueError, TypeError) as e:
            e.critical = False
            self._error_handler.log(e, "File ID and/or version could not be read due to invalid xml attributes.")
            return  
            
        
    def checksums(self) -> dict[str, int]:
        with self._f.open("chksum.dat", "r") as f:
            data = f.read()
            decoded = b64decode(data).decode()
            decoded = decoded.rstrip("\n")
            print(decoded)
            pairs = decoded.split("\n")
            return {pair.split(":")[0] : int(pair.split(":")[1]) for pair in pairs}
            
            
    def generate_file_id(self) -> str:
        if not self.file_id:
            return hash(self.path + self._last_saved.toString(Qt.DateFormat.ISODate))
        return self.file_id
    
    @property
    def file_id(self) -> int:
        return self._metadata["file_id"]
    
    @property
    def version(self) -> int:
        return self._metadata["version"]

    @property    
    def path(self) -> str | None:
        if self._f:
            return self._f.filename
        return None
    
    @property
    def mode(self) -> Literal["w", "r"]:
        return self._f.mode if self._f else "w"
    
    @property
    def temppath(self) -> str | None:
        return self._tempdir.name if self._tempdir else None
    
    @property
    def error_handler(self) -> ErrorLogger:
        return self._error_handler
    
    def close(self) -> None:
        if self._f:
            self._f.close()
    
    def __del__(self) -> None:
        print("LessonFile object deleted")
        if self._f:
            if self._f.mode == "r": 
                self._error_handler.log_msg(f"Finished reading file {self._f.filename} at {QDateTime.currentDateTime().toString(Qt.DateFormat.ISODateWithMs)}\n")
            self._f.close()
            self._tempdir.cleanup()
            self._tempdir = None
            
           
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
        writer.writeAttribute("file_id", str(file_id))

        writer = lesson.xml(writer)
        writer = table.xml(writer)

        writer.writeEndElement()
        writer.writeEndDocument()

        return xml_data
    
    @staticmethod
    def write_res_xml(rescont: ResourceContainer) -> QByteArray:
        writer = QXmlStreamWriter()
        xml_data = QByteArray()
        buffer = QBuffer(xml_data)
        buffer.open(QBuffer.OpenModeFlag.WriteOnly)
        writer.setDevice(buffer)

        writer.writeStartDocument()
        writer.writeStartElement("resources")

        for resobj in rescont.contents():
            writer.writeEmptyElement("res")
            writer.writeAttribute("type", resobj.type.name)
            writer.writeAttribute("file", resobj.filename())
        writer.writeEndElement()

        return xml_data


class XmlReader:
    
    @staticmethod
    def read_lesson(xml_file: QFile, error_handler: ErrorLogger) -> Lesson | None:
        reader = QXmlStreamReader(xml_file) 

        while not reader.atEnd():
            token = reader.readNext()
            
            if token == QXmlStreamReader.TokenType.StartElement:
                if reader.name() == "lesson":
                    try:
                        model = Lesson.read(reader)
                        return model

                    except LFExceptions.ModelReadError as e:
                        error_handler.log(e, "Reading of general lesson data failed. One or more of the values is invalid.")
                        return None
        return None
    
    @staticmethod
    def read_table(xml_file: QFile, rescont: ResourceContainer, res_path: str, error_handler: ErrorLogger) -> TableModel:
        """Reads table and returns a table model. If errors occur the tabel structure is amended if possible otherwise and invalid table will be returned."""
        reader = QXmlStreamReader(xml_file)        
        
        rows = 0
        columns = 0
        def_row_count = 0
        def_column_count = 0
        
        in_table = False
        writing_row = False
        writing_cell = False
        cell = None
        row = None
        data = []

        while not reader.atEnd():
            token = reader.readNext()

            if token == QXmlStreamReader.TokenType.StartElement: 
                if reader.name() == "table":
                    attrs = reader.attributes()
                    try:
                        def_row_count = int(attrs.value("rows"))
                        rows += def_row_count

                        def_column_count = int(attrs.value("columns"))
                        columns += def_column_count 
                        
                        if rows == 0 or columns == 0: raise ValueError

                        headers = {Qt.Orientation.Horizontal : [], Qt.Orientation.Vertical : [HeaderDataItem.vertical() for _ in range(rows)]}
                        in_table = True

                    except ValueError as e:
                        if error_handler:
                            e.critical = True
                            error_handler.log(e, "Invalid value for row or column number. Value is not a number or values are 0.")
                        return TableModel.new(0, 0)
                    continue
            
                if in_table:
                    match reader.name():
                        case "header":
                            attrs = reader.attributes()

                            try:
                                if len(headers[Qt.Orientation.Horizontal]) < def_column_count:
                                    headers[Qt.Orientation.Horizontal].append(HeaderDataItem(Qt.Orientation.Horizontal, int(attrs.value("size")), True, str(attrs.value("text"))))
                                    continue
                                error_handler.log(LFExceptions.BrokenTable(False), "Skipped horizontal header definition because it would exceed defined column count.")
                            except (ValueError, TypeError) as e:
                                e.critical = False
                                error_handler.log(e, "Invalid value for header size and text. Check if values for header size or text are correct.")
                                headers[Qt.Orientation.Horizontal].append(HeaderDataItem.horizontal())

                        case "row":
                            row = []
                            columns = def_column_count
                            writing_row = True

                        case "cell":
                            cell = CellModel()
                            writing_cell = True

                        case "element":
                            if writing_cell and writing_row:
                                attrs = reader.attributes()

                                try:
                                    model = XmlReader._element_model(str(attrs.value("type")))
                                    resobj = rescont.get(osp.join(res_path, str(attrs.value("file"))))
                                    model = model.read(attrs, resobj)
                                    cell.add_model(model)
                                
                                except KeyError as e:
                                    e.critical = False
                                    error_handler.log(e, f"The resource for the element {str(attrs.value("type"))} does not exist. Model will be skipped.")
                                    continue
                                except AttributeError as e:
                                    e.critical = False
                                    error_handler.log(e, f"Reading the model failed. Either the model type could not be identified or a required attribute is missing. Model will be skipped.")
                                    continue
                                except ValueError as e:
                                    e.critical = False
                                    error_handler.log(e, f"The resource value for model of type '{attrs.value("type")}' could not be parsed. Model will be skipped.")
                                    continue
                                except FileNotFoundError as e:
                                    e.critical = False
                                    error_handler.log(e, f"The resource file for model of type '{attrs.value("type")} could not be found. Model will be skipped.")
                                    continue
                                except LFExceptions.ModelReadError as e:
                                    error_handler.log(e, f"Reading the model of type '{attrs.value("type")}' has failed. This could be due to invalid value. Model will be skipped.")
                                    continue

                            else:
                                continue

            elif token == QXmlStreamReader.TokenType.EndElement and in_table:
                
                match reader.name():

                    case "headers":
                        header_len = len(headers[Qt.Orientation.Horizontal])
                        if header_len < def_column_count:
                            error_handler.log(LFExceptions.BrokenTable(False, "Too less horizontal header definitions were parsed than the defined column count. Missing headers will be added."))
                            for _ in range(def_column_count - header_len):
                                headers[Qt.Orientation.Horizontal].append(HeaderDataItem.horizontal())

                    case "row" if writing_row:
                        if rows > 0 and len(row) == def_column_count:
                            data.append(row)
                            rows -= 1
                            writing_row = False
                            continue
                        error_handler.log(LFExceptions.BrokenTable(False), f"The table row was skipped because too many were parsed than specified in the definitions or the column count of the row doesn't match the definition: Specified rows: {def_row_count}; Specified columns: {def_column_count}")
                        writing_row = False

                    case "cell" if writing_cell:
                        if columns > 0:
                            row.append(cell)
                            columns -= 1
                            writing_cell = False
                            continue
                        error_handler.log(LFExceptions.BrokenTable(False), f"The table column was skipped because too many were parsed than specified in the definitions: Specified: {def_column_count}; Actual: {def_column_count + 1}")
                        writing_row = False

                    case "table":
                        if rows ==  0:
                            in_table = False
                            break
                        error_handler.log(LFExceptions.BrokenTable(False), f"Too less rows were parsed than the number specified in the definitions. Empty rows will be added as necessary.")
                        for _ in range(rows):
                            data.append([CellModel()] * def_column_count)
                        in_table = False
                        break

        return TableModel(TableData(data, headers))
            
    @staticmethod
    def _element_model(name: str) -> 'BaseElementModel':
        print("Getting model of type:", name)
        definition = get_definitions(name)
        return definition.model()