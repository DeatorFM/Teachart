import os.path as osp
import tempfile
import uuid
from base64 import b64decode, b64encode
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Literal
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile

from PyQt6.QtCore import (
    QBuffer,
    QByteArray,
    QDateTime,
    QFile,
    QObject,
    QSize,
    Qt,
    QXmlStreamReader,
    QXmlStreamWriter,
    pyqtSignal,
    qChecksum,
)

from tcha.elements import get_definitions
from tcha.error import ErrorLogger, LFExceptions, QtError
from tcha.lesson import Lesson
from tcha.resmanager import (
    ResourceContainer,
    ResourceObject,
    ResourceTransferObject,
    ResourceType,
)
from tcha.tablemodel import TableModel  # CellModel, HeaderDataItem, TableData,

CURRENT_VERSION: int = 1


class WriteState(Enum):
    Unserialised = auto()
    SerialisedBuffer = auto()
    SerialisedFile = auto()


class ProgressLogger(QObject):
    progressChanged = pyqtSignal(int)

    def __init__(self):
        super().__init__(None)
        self._progress = 0.0

    def raise_progress(self, by: float) -> None:
        self._progress += by
        self.progressChanged.emit(int(self._progress))

    @property
    def progress(self) -> float:
        return self._progress


@dataclass(frozen=True)
class SaveBuffer:
    struct_buffer: QByteArray
    res_buffer: QByteArray
    resobjects: list[ResourceTransferObject]


class LessonFile:
    """Provides file stream for serialised Lesson-Documents"""

    def __init__(self):
        self._save_buffer: SaveBuffer | None = None

        self._f: ZipFile | None = None
        self._tempdir: tempfile.TemporaryDirectory | None = None
        self._last_saved = None
        self._metadata = {"version": None, "file_id": None}
        self._progress = ProgressLogger()
        self._state = WriteState.Unserialised

    @property
    def progress(self) -> ProgressLogger:
        return self._progress

    def open(self, mode: Literal["r", "w"], path: str | None = None) -> bool:
        if mode == "r" and path:
            try:
                self._last_saved = QDateTime.currentDateTime()
                self._error_handler = ErrorLogger(path, True)
                self._error_handler.log_msg(
                    f"Start reading file {osp.basename(path)} at {self._last_saved.toString(Qt.DateFormat.ISODateWithMs)}"
                )
                self._tempdir = tempfile.TemporaryDirectory(
                    ".tmp", "TCHA", delete=False
                )
                print("Temporary", self._tempdir)
                self._f = ZipFile(path, mode)
                self._f.extractall(self.temppath)

                self.set_metadata(self._metadata)
                self._state = WriteState.SerialisedFile
                return True

            except BadZipFile as e:
                e.critical = True
                self._error_handler.log(
                    e,
                    "The file is corrupted and cannot not be opened. This can happen when a file has not been closed properly during a writing process.",
                )
                return False

        elif mode == "w":
            self._metadata["version"] = CURRENT_VERSION
            self._metadata["file_id"] = self.generate_file_id()
            return True

        else:
            raise ValueError("Open mode value invalid. It's either 'r' or 'w'.")

    def save(
        self,
        path: str | None = None,
    ) -> bool:
        """Saves a new file or overwrites the entire file's contents if existing"""
        if self._state == WriteState.SerialisedBuffer:
            self._last_saved = QDateTime.currentDateTime()

            if not self._f or path:
                self._f = ZipFile(path, "w", ZIP_DEFLATED)
                self._error_handler = ErrorLogger(path, True)
            else:
                self.change_open_mode("w")

            self._error_handler.log_msg(
                f"Start writing to file {self._f.filename} at {self._last_saved.toString(Qt.DateFormat.ISODateWithMs)}"
            )

            # Generate and write xml for document structure
            with self._f.open("structure.xml", "w") as xml_f:
                xml_f.write(self._save_buffer.struct_buffer.data())

            self._error_handler.log_msg("Table structure writing process complete")

            # Create checksum for document xml and write
            chksums = QByteArray()
            xml_chksum = f"\\xml:{qChecksum(self._save_buffer.struct_buffer, Qt.ChecksumType.ChecksumIso3309)}\n".encode()
            chksums.append(xml_chksum)

            # Copy the resources into file or create new file if necessary
            for obj in self._save_buffer.resobjects:
                if not obj.has_data():
                    self._error_handler.log_msg(
                        f"Writing '{obj.src_path}' to file as '{obj.filename}'"
                    )
                    self._copy(obj)
                else:
                    self._error_handler.log_msg(
                        f"Writing new resource with name '{obj.filename}' to file"
                    )
                    self._write_new(obj)

            self._error_handler.log_msg("Writing resource data to file complete")

            # Write resources definitions into seperate xml file
            with self._f.open("resources.xml", "w") as res_f:
                res_f.write(self._save_buffer.res_buffer.data())

            self._error_handler.log_msg(
                "Writing process for resource definitions complete "
            )

            # Generate checksum for resource definitions and append it to other definition
            res_chksum = f"\\res:{qChecksum(self._save_buffer.res_buffer, Qt.ChecksumType.ChecksumIso3309)}\n".encode()
            chksums.append(res_chksum)
            encoded = b64encode(chksums.data())

            # Writes checksums to seperate file
            with self._f.open("chksum.dat", "w") as chksum_f:
                chksum_f.write(encoded)

            self._error_handler.log_msg("Checksums written")

            self.change_open_mode("r")
            self._error_handler.log_msg("Finished writing successfully.")

            self._f.extract("structure.xml", self.temppath)
            self._f.extract("resources.xml", self.temppath)

            self._save_buffer = None
            self._state = WriteState.SerialisedFile

            return True
        return False

    def write_buffer(self, lesson: Lesson, tablemodel: TableModel) -> None:
        """Writes the current structure of table model and resource container to a buffer for later serialisation."""
        self._metadata["file_id"] = self.generate_file_id()

        struct_buffer = XmlWriter.write_xml(self.file_id, lesson, tablemodel)
        res_buffer = XmlWriter.write_res_xml(tablemodel.rescont)
        self._save_buffer = SaveBuffer(
            struct_buffer, res_buffer, tablemodel.rescont.to_transfer_objects()
        )
        self._state = WriteState.SerialisedBuffer

    def _copy(self, resobj: ResourceTransferObject) -> None:
        self._f.write(resobj.src_path, f"resources/{resobj.filename}")

    def _write_new(self, resobj: ResourceTransferObject) -> None:
        with self._f.open(f"resources/{resobj.filename}", "w") as f:
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

    def xml(self, name: str = "structure") -> QFile:
        """Returns IO to extracted strcuture.xml as QFile. Raises an Exception of file not found or QFile throws an error."""
        if self.extracted(f"{name}.xml"):
            qfile = QFile(osp.join(self.temppath, f"{name}.xml"))
            qfile.open(QFile.OpenModeFlag.ReadOnly)
            print("Path", qfile.fileName())

            if not qfile.error().value:
                return qfile
            raise QtError(qfile.error(), qfile.errorString(), True)
        raise FileNotFoundError

    def get_table(self) -> TableModel | None:
        """Returns TableModel if file is loaded."""
        try:
            struct_file = self.xml()
            res_file = self.xml("resources")
            table = XmlReader.read_table(
                struct_file,
                res_file,
                osp.join(self.temppath),
                self._error_handler,
                self._progress,
            )
            remaining = 100 - self._progress.progress
            self._progress.raise_progress(remaining)
            struct_file.close()
            res_file.close()

            return table

        except FileNotFoundError as e:
            e.critical = True
            self._error_handler.log(
                e, "The file that contains table definitions could not be found."
            )
            return None
        except QtError as e:
            self._error_handler.log(
                e,
                f"There was an error while trying to read the xml file. Details: {e.error_string}",
            )
            return None

    def get_lesson(self, default: Lesson | None = None) -> Lesson | None:
        """Returns Lesson model if file is loaded and could be read otherwise returns the default value."""
        try:
            self._progress.raise_progress(5.0)  # Total: 30%
            qfile = self.xml()
            model = XmlReader.read_lesson(qfile, self._error_handler, self._progress)
            qfile.close()
            return model

        except FileNotFoundError as e:
            e.critical = True
            self._error_handler.log(
                e, "The file containing table definitions could not be found."
            )
            return default

        except QtError as e:
            self._error_handler.log(
                e,
                f"There was an error while trying to read the xml file. Details: {e.error_string}",
            )
            return default

    def set_metadata(self, metadata: dict[str, Any]) -> None:
        metadata_read = False
        try:
            qfile = self.xml()
            reader = QXmlStreamReader(qfile)
            while not reader.atEnd():
                token = reader.readNext()

                if token == QXmlStreamReader.TokenType.StartElement:
                    if reader.name() == "metadata":
                        attrs = reader.attributes()
                        version = int(attrs.value("version"))
                        if version > CURRENT_VERSION or version < 0:
                            raise LFExceptions.UnsupportedVersion(version)
                        metadata["version"] = version
                        metadata["file_id"] = uuid.UUID(hex=attrs.value("file_id"))
                        metadata_read = True
                        break
            qfile.close()
            if reader.hasError():
                self._error_handler.log(
                    QtError(reader.error(), reader.errorString(), False),
                    "The file that contains table definitions could not be found.",
                )

        except FileNotFoundError as e:
            e.critical = True
            self._error_handler.log(e, "XML file could not be found.")

        except QtError as e:
            self._error_handler.log(
                e, f"An error occured while opening the XML file: {e.error_string}"
            )

        except ValueError as e:
            if self._metadata["version"]:
                e.critical = False
                self._error_handler.log(
                    e,
                    "File ID could not be read due to invalid xml attribute or value that is not a uuid. A new ID will be generated.",
                )
                self._metadata["file_id"] = self.generate_file_id()
                metadata_read = True
            else:
                e.critical = True
                self._error_handler.log(
                    e,
                    "Version number could not be read due to invalid xml attribute. File version could not be identified.",
                )

        except LFExceptions.UnsupportedVersion as e:
            self._error_handler.log(
                e,
                f"This file version is not supported. File's version: {e.version}. Max. supported version: {CURRENT_VERSION}",
            )

        finally:
            if not metadata_read:
                self._error_handler.log(
                    LFExceptions.MetadataReadError(True),
                    "Metadata could not be read because either the DOM-Element could not be found or the version number is invalid",
                )

    def checksums(self) -> dict[str, int]:
        with self._f.open("chksum.dat", "r") as f:
            data = f.read()
            decoded = b64decode(data).decode()
            decoded = decoded.rstrip("\n")
            print(decoded)
            pairs = decoded.split("\n")
            return {pair.split(":")[0]: int(pair.split(":")[1]) for pair in pairs}

    def generate_file_id(self) -> uuid.UUID:
        return uuid.uuid1()

    @property
    def file_id(self) -> uuid.UUID:
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
            self._f.close()
            self._tempdir.cleanup()
            self._tempdir = None


class XmlWriter:
    @staticmethod
    def write_xml(file_id: uuid.UUID, lesson: Lesson, table: TableModel) -> QByteArray:
        writer = QXmlStreamWriter()
        xml_data = QByteArray()
        buffer = QBuffer(xml_data)
        buffer.open(QBuffer.OpenModeFlag.WriteOnly)
        writer.setDevice(buffer)

        writer.writeStartDocument()
        writer.writeStartElement("teachart")

        writer.writeEmptyElement("metadata")
        writer.writeAttribute("version", "1")
        writer.writeAttribute("file_id", file_id.hex)

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
        writer.writeAttribute("count", str(len(rescont)))

        for resobj in rescont.contents():
            writer.writeEmptyElement("res")
            writer.writeAttribute("type", resobj.type.name)
            writer.writeAttribute("file", resobj.filename())
        writer.writeEndElement()

        return xml_data


class XmlReader:
    @staticmethod
    def read_lesson(
        xml_file: QFile,
        error_handler: ErrorLogger,
        progress_logger: ProgressLogger = ProgressLogger(),
    ) -> Lesson | None:
        reader = QXmlStreamReader(xml_file)

        while not reader.atEnd():
            token = reader.readNext()

            if token == QXmlStreamReader.TokenType.StartElement:
                if reader.name() == "lesson":
                    try:
                        model = Lesson.read(reader)
                        progress_logger.raise_progress(5.0)
                        return model

                    except LFExceptions.ModelReadError as e:
                        error_handler.log(
                            e,
                            "Reading of general lesson data failed. One or more of the values is invalid.",
                        )
                        return None
        return None

    @staticmethod
    def read_resources(
        xml_file: QFile,
        rescont: ResourceContainer,
        temppath: str,
        error_handler: ErrorLogger,
        progress_logger: ProgressLogger = ProgressLogger(),
    ) -> None:
        """Reads resources of an xml file and writes it to the container"""
        try:
            reader = QXmlStreamReader(xml_file)
            count = 25
            factor = 1.0

            while not reader.atEnd():
                token = reader.readNext()

                if token == QXmlStreamReader.TokenType.StartElement:
                    if reader.name() == "resources":
                        attrs = reader.attributes()
                        count = int(attrs.value("count"))
                        factor = count / 25

                    if reader.name() == "res":
                        attrs = reader.attributes()
                        path: str = osp.join(
                            temppath, "resources", str(attrs.value("file"))
                        )
                        rescont.save(ResourceType[str(attrs.value("type"))], path)
                        progress_logger.raise_progress(factor)

            if reader.error().value:
                error_handler.log(
                    QtError(reader.error(), reader.errorString(), True),
                    f"There was an error while parsing the xml. Details: {reader.errorString()}",
                )
                xml_file.close()
                # Total: 25%

        except (ValueError, KeyError) as e:
            e.critical = True
            error_handler.log(
                e,
                "Resource definition has invalid value. This is possibly due to an unknown or invalid resource type that is specified in the definitions.",
            )
            return None

        except FileNotFoundError as e:
            e.critical = True
            error_handler.log(
                e, f"The defined file at '{e.filename}' could not be found."
            )
            return None

    @staticmethod
    def read_table(
        struct_file: QFile,
        res_file: QFile,
        temppath: str,
        error_handler: ErrorLogger,
        progress_logger: ProgressLogger = ProgressLogger(),
    ) -> TableModel:
        """Reads table and returns a table model. If errors occur the tabel structure is amended if possible otherwise and invalid table will be returned."""
        reader = QXmlStreamReader(struct_file)

        row = 0
        column = 0
        def_row_count = 0
        def_column_count = 0
        header = 0

        total_progress = 70
        factor = 70 / total_progress  # Total: 70 %

        in_table = False
        writing_row = False
        writing_cell = False
        tmodel = None
        cell = None

        while not reader.atEnd():
            token = reader.readNext()

            # Initialise table

            if token == QXmlStreamReader.TokenType.StartElement:
                if reader.name() == "table":
                    attrs = reader.attributes()
                    try:
                        def_row_count = int(attrs.value("rows"))
                        # rows += def_row_count

                        def_column_count = int(attrs.value("columns"))
                        # columns += def_column_count

                        if def_row_count == 0 or def_column_count == 0:
                            raise ValueError

                        tmodel: TableModel = TableModel.new(
                            def_row_count, def_column_count
                        )

                        XmlReader.read_resources(
                            res_file,
                            tmodel.rescont,
                            temppath,
                            error_handler,
                            progress_logger,
                        )

                        total_progress = def_row_count + def_column_count * 2
                        factor = 70 / total_progress

                        progress_logger.raise_progress(factor * column)
                        in_table = True

                    except ValueError as e:
                        e.critical = True
                        error_handler.log(
                            e,
                            "Invalid value for row or column number. Value is not a number or values are 0.",
                        )
                        return TableModel.new(0, 0)
                    continue

                # Write Resource Container

                # Write Table

                if in_table:
                    match reader.name():
                        case "header":
                            attrs = reader.attributes()

                            try:
                                if header < def_column_count:
                                    tmodel.setHeaderData(
                                        header,
                                        Qt.Orientation.Horizontal,
                                        str(attrs.value("text")),
                                        Qt.ItemDataRole.DisplayRole,
                                    )
                                    tmodel.setHeaderData(
                                        header,
                                        Qt.Orientation.Horizontal,
                                        QSize(int(attrs.value("size")), 0),
                                        Qt.ItemDataRole.SizeHintRole,
                                    )
                                    header += 1
                                    continue
                                error_handler.log(
                                    LFExceptions.BrokenTable(False),
                                    "Skipped horizontal header definition because it would exceed defined column count.",
                                )
                            except (ValueError, TypeError) as e:
                                e.critical = False
                                error_handler.log(
                                    e,
                                    "Invalid value for header size and text. Check if values for header size or text are correct.",
                                )

                        case "row":
                            if row < def_row_count:
                                column = 0
                                writing_row = True
                                continue
                            error_handler.log(
                                LFExceptions.BrokenTable(False),
                                f"The table row was skipped because too many were parsed than specified in the definitions or the column count of the row doesn't match the definition: Specified rows: {def_row_count}; Specified columns: {def_column_count}",
                            )
                            writing_row = False

                        case "cell":
                            if column < def_column_count:
                                cell = tmodel.data(tmodel.index(row, column))
                                writing_cell = True
                                continue
                            error_handler.log(
                                LFExceptions.BrokenTable(False),
                                f"The table column was skipped because too many were parsed than specified in the definitions: Specified: {def_column_count}; Actual: {def_column_count + 1}",
                            )
                            writing_cell = False

                        case "element":
                            if writing_cell and writing_row:
                                attrs = reader.attributes()

                                try:
                                    definition = get_definitions(
                                        str(attrs.value("type"))
                                    )
                                    if definition:
                                        resobj = tmodel.rescont.get(
                                            osp.join(
                                                temppath,
                                                "resources",
                                                str(attrs.value("file")),
                                            )
                                        )
                                        model = definition.model_from_xml(attrs, resobj)
                                        cell.append(model)

                                except KeyError as e:
                                    e.critical = False
                                    error_handler.log(
                                        e,
                                        f"The resource for the element {str(attrs.value('type'))} does not exist. Model will be skipped.",
                                    )
                                    continue
                                except (AttributeError, TypeError) as e:
                                    e.critical = False
                                    error_handler.log(
                                        e,
                                        "Reading the model failed. Either the model type could not be identified or a required attribute is missing. Model will be skipped.",
                                    )
                                    continue
                                except ValueError as e:
                                    e.critical = False
                                    error_handler.log(
                                        e,
                                        f"The resource value for model of type '{attrs.value('type')}' could not be parsed. Model will be skipped.",
                                    )
                                    continue
                                except FileNotFoundError as e:
                                    e.critical = False
                                    error_handler.log(
                                        e,
                                        f"The resource file for model of type '{attrs.value('type')} could not be found. Model will be skipped.",
                                    )
                                    continue
                                except LFExceptions.ModelReadError as e:
                                    error_handler.log(
                                        e,
                                        f"Reading the model of type '{attrs.value('type')}' has failed. This could be due to invalid value. Model will be skipped.",
                                    )
                                    continue

                            else:
                                continue

            elif token == QXmlStreamReader.TokenType.EndElement and in_table:
                match reader.name():
                    case "headers":
                        continue

                    case "row" if writing_row:
                        row += 1
                        writing_row = False
                        column = 0
                        progress_logger.raise_progress(factor)
                        continue

                    case "cell" if writing_cell:
                        column += 1
                        writing_cell = False
                        progress_logger.raise_progress(factor)
                        continue

                    case "table":
                        if row == def_row_count:
                            in_table = False
                            break
                        error_handler.log(
                            LFExceptions.BrokenTable(False),
                            "The number of parsed rows does not match the actual number. Some rows' content might be missing.",
                        )
                        in_table = False

                        break

        return tmodel

    @staticmethod
    def _element_model(name: str) -> "BaseElementModel":
        print("Getting model of type:", name)
        definition = get_definitions(name)
        return definition.model()
