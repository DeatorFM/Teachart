import logging
import os.path as osp
import tempfile
import uuid
from dataclasses import dataclass
from enum import Enum, auto
from functools import cache
from pathlib import Path
from typing import Literal, TypedDict
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile

from PyQt6.QtCore import (
    QBuffer,
    QByteArray,
    QDateTime,
    QFile,
    QObject,
    QSize,
    Qt,
    QVersionNumber,
    QXmlStreamAttributes,
    QXmlStreamReader,
    QXmlStreamWriter,
    pyqtSignal,
)
from tcha.elements import get_definitions
from tcha.error import IOLogger, StandardLogger
from tcha.lesson import Lesson
from tcha.resmanager import (
    ResourceTransferObject,
)
from tcha.tablemodel import (
    TableModel,  # CellModel, HeaderDataItem,
)
from tcha.utils import source_id

CURRENT_VERSION: str = "1"


class WriteState(Enum):
    Unserialised = auto()
    SerialisedBuffer = auto()
    SerialisedFile = auto()


@dataclass(frozen=True)
class SaveBuffer:
    struct_buffer: QByteArray
    lesson_data_buffer: QByteArray
    meta_data_buffer: QByteArray
    resobjects: list[ResourceTransferObject]

    def size(self) -> int:
        return sum(
            [
                self.struct_buffer.size(),
                self.lesson_data_buffer.size(),
                self.meta_data_buffer.size(),
            ]
        )


class FileMetaData(TypedDict):
    file_id: uuid.UUID | None
    creation_date: QDateTime
    changed_date: QDateTime


class TchPath:
    """Provides streams to all required files extracted from a .tch-file."""

    def __init__(self, dir: str) -> None:
        self._dir = Path(dir)
        self._has_resources = (self._dir / "resources").exists()
        if not self._dir.exists():
            raise FileNotFoundError("Extracted files not found")

    def has_required_files(self) -> bool:
        files = [file.name for file in self._dir.iterdir()]
        return all(file in files for file in ["structure.xml", "lesson.xml", "metadata.xml"])

    @property
    def dir(self) -> Path:
        """Path to temporary directory with extracted files."""
        return self._dir

    @property
    def structure(self) -> QFile:
        return QFile(str(self._dir / "structure.xml"))

    @property
    def lesson(self) -> QFile:
        return QFile(str(self._dir / "lesson.xml"))

    @property
    def metadata(self) -> QFile:
        return QFile(str(self._dir / "metadata.xml"))

    def resource(self, basename: str) -> str:
        return str(self._dir / "resources" / basename) if self._has_resources else ""


class LessonFile(QObject):
    progressChanged = pyqtSignal(int)
    """Provides file stream for serialised TCH-Documents"""

    def __init__(self):
        super().__init__()
        self._save_buffer: SaveBuffer | None = None

        self._f: ZipFile | None = None
        self._tempdir: tempfile.TemporaryDirectory | None = None
        self._last_saved = None
        self._metadata: FileMetaData = {
            "file_id": None,
            "creation_date": QDateTime(),
            "changed_date": QDateTime(),
        }
        self._state = WriteState.Unserialised
        self._reader = None

    @cache
    @staticmethod
    def max_version() -> QVersionNumber:
        v, _ = QVersionNumber().fromString(CURRENT_VERSION)
        return v

    def open(self, mode: Literal["r", "w"], path: str | None = None) -> bool:
        if mode == "r" and path:
            try:
                self._last_saved = QDateTime.currentDateTime()
                self._logger = IOLogger()
                self._tempdir = tempfile.TemporaryDirectory(".tmp", "TCHA", delete=False)
                StandardLogger.debug(
                    f"Created temporary directory at {self._tempdir.name}",
                    extra={"sender", "LESSONFILE"},
                )
                self._f = ZipFile(path, mode)
                self._f.extractall(self.temppath)
                self._logger.log(
                    logging.INFO, f"Started reading operation for file {osp.basename(path)}"
                )

                self._reader = XmlReader(TchPath(self._tempdir.name), self._logger)
                self._reader.readingProgessChanged.connect(self.progressChanged.emit)
                if self._reader.start_reading():
                    success = self._reader.read_metadata()
                    if success:
                        self._metadata = self._reader.metadata
                        self._state = WriteState.SerialisedFile
                        self._logger.set_file_id(self._metadata["file_id"])
                        self._logger.log(
                            logging.INFO, f"Started reading file of id: {self._metadata['file_id']}"
                        )
                        success &= self._reader.read_lesson()
                        success &= self._reader.read_table()
                        self._reader.finish_reading()
                        self._logger.log(logging.INFO, "Finished reading operation.")
                        self._reader.readingProgessChanged.disconnect()
                        return success
                self._logger.log(logging.CRITICAL, "tch-file is missing components.")
                return False

            except BadZipFile:
                self._logger.log(logging.CRITICAL, "File could not be opened: Permission denied.")
                return False

        elif mode == "w":
            self._metadata["file_id"] = self.generate_file_id()
            self._metadata["creation_date"] = QDateTime.currentDateTime()
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
                try:
                    self._logger = IOLogger(self._metadata["file_id"])
                    self._logger.log(logging.INFO, f"Started write operation to path: {path}")
                    self._f = ZipFile(path, "w", ZIP_DEFLATED)
                except PermissionError:
                    self._logger.log(
                        logging.CRITICAL, "File could not be opened: Permission denied."
                    )
                    return False
            else:
                self._logger.log(logging.INFO, f"Started write operation to path: {self.path}")
                self.change_open_mode("w")

            # Write xml for document structure
            written_bytes = 0
            with self._f.open("structure.xml", "w") as struct_f:
                written_bytes += struct_f.write(self._save_buffer.struct_buffer.data())
            self._logger.log(logging.DEBUG, "Table structure written.")

            # Write lesson.xml
            with self._f.open("lesson.xml", "w") as lesson_f:
                written_bytes += lesson_f.write(self._save_buffer.lesson_data_buffer.data())
            self._logger.log(logging.DEBUG, "Lesson data written.")

            # Write metadata.xml
            with self._f.open("metadata.xml", "w") as metadata_f:
                written_bytes += metadata_f.write(self._save_buffer.meta_data_buffer.data())
            self._logger.log(logging.DEBUG, "Meta data written.")

            if written_bytes != self._save_buffer.size():
                self._logger.log(
                    logging.CRITICAL,
                    "Error during writing of xml-data. Writing operation has been terminated.",
                )
                self.change_open_mode("r")
                return False

            self._logger.log(logging.DEBUG, "All xml data written successfully.")

            # Copy the resources into file or create new file if necessary
            for obj in self._save_buffer.resobjects:
                if not obj.has_data():
                    self._logger.log(
                        logging.INFO, f"Writing '{obj.src_path}' to file as '{obj.filename}'"
                    )
                    self._copy(obj)
                else:
                    self._logger.log(
                        logging.INFO, f"Writing new resource with name '{obj.filename}' to file"
                    )
                    self._write_new(obj)

            self._logger.log(logging.DEBUG, "Resource data successfully written.")

            self.change_open_mode("r")
            self._logger.log(logging.INFO, "Finished writing successfully.")

            self.init_reader()
            self._f.extract("structure.xml", self.temppath)
            self._f.extract("lesson.xml", self.temppath)
            self._f.extract("metadata.xml", self.temppath)

            self._save_buffer = None
            self._state = WriteState.SerialisedFile

            return True
        return False

    def write_buffer(self, lesson: Lesson, tablemodel: TableModel) -> None:
        """Writes the current structure of table model and resource container to a buffer for later serialisation."""
        self._metadata["file_id"] = (
            self.generate_file_id() if not self._metadata["file_id"] else self._metadata["file_id"]
        )

        StandardLogger.info(
            "Prepare save operation: Writing buffer to LessonFile object",
            extra={"sender", "LESSONFILE"},
        )
        struct_buffer = XmlWriter.write_struct_xml(tablemodel)
        lesson_buffer = XmlWriter.write_lesson_xml(lesson)
        meta_data_buffer = XmlWriter.write_metadata_xml(self._metadata)
        self._save_buffer = SaveBuffer(
            struct_buffer, lesson_buffer, meta_data_buffer, tablemodel.rescont.to_transfer_objects()
        )
        StandardLogger.info("Prepare save operation: Finished writing buffer successfully.")
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

    def init_reader(self) -> bool:
        if not self._reader and self._tempdir and self.file_id:
            self._reader = IOLogger(self.file_id)
            return True
        return False

    def get_table(self) -> TableModel | None:
        """Returns TableModel if file is loaded."""
        if self._reader and self._reader.read_state == ReadState.ReadingFinished:
            model = self._reader.table_model
            return model
        else:
            self._reader.start_reading()
            if self._reader.read_table():
                self._reader.finish_reading()
                model = self._reader.table_model
                self._reader.clear_caches()
                return model
        return None

    def get_lesson(self) -> Lesson | None:
        """Returns Lesson model if file is loaded and could be read otherwise returns the default value."""
        if self._reader and self._reader.read_state == ReadState.ReadingFinished:
            model = self._reader.lesson_model
            return model
        else:
            self._reader.start_reading()
            if self._reader.read_lesson():
                self._reader.finish_reading()
                model = self._reader.lesson_model
                self._reader.clear_caches()
                return model
        return None

    def clear_caches(self) -> bool:
        """Clears the reader's cache and returns True. If no reader initialised False is returned."""
        if self._reader:
            self._reader.clear_caches()
            return True
        return False

    def set_metadata(self, metadata: FileMetaData) -> None:
        self._metadata = metadata

    def generate_file_id(self) -> uuid.UUID:
        return uuid.uuid1()

    @property
    def logger(self) -> IOLogger | None:
        return self._logger

    @property
    def file_id(self) -> uuid.UUID:
        return self._metadata["file_id"]

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

    def close(self) -> None:
        if self._f:
            self._f.close()

    def __del__(self) -> None:
        if self._f:
            self._f.close()
            self._tempdir.cleanup()
            self._tempdir = None


class XmlWriter:
    @classmethod
    def write_metadata_xml(cls, metadata: FileMetaData) -> QByteArray:
        writer = QXmlStreamWriter()
        xml_data = QByteArray()
        buffer = QBuffer(xml_data)
        buffer.open(QBuffer.OpenModeFlag.WriteOnly)
        writer.setDevice(buffer)

        writer.writeStartDocument()
        writer.writeStartElement("tch")
        writer.writeAttribute("version", CURRENT_VERSION)

        writer.writeTextElement("file_id", str(metadata["file_id"]))

        writer.writeTextElement(
            "creation_date", metadata["creation_date"].toString(Qt.DateFormat.ISODate)
        )

        writer.writeTextElement(
            "changed_date", QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate)
        )

        writer.writeEndElement()
        writer.writeEndDocument()

        return xml_data

    @classmethod
    def write_struct_xml(cls, tablemodel: TableModel) -> QByteArray:
        writer = QXmlStreamWriter()
        xml_data = QByteArray()
        buffer = QBuffer(xml_data)
        buffer.open(QBuffer.OpenModeFlag.WriteOnly)
        writer.setDevice(buffer)

        writer.writeStartDocument()
        writer.writeStartElement("tch")
        writer.writeAttribute("version", CURRENT_VERSION)

        tablemodel.xml(writer)

        writer.writeEndElement()
        writer.writeEndDocument()

        return xml_data

    @classmethod
    def write_lesson_xml(cls, lesson_model: Lesson) -> QByteArray:
        writer = QXmlStreamWriter()
        xml_data = QByteArray()
        buffer = QBuffer(xml_data)
        buffer.open(QBuffer.OpenModeFlag.WriteOnly)
        writer.setDevice(buffer)

        writer.writeStartDocument()
        writer.writeStartElement("tch")
        writer.writeAttribute("version", CURRENT_VERSION)

        lesson_model.xml(writer)

        writer.writeEndElement()
        writer.writeEndDocument()

        return xml_data


class ReadState(Enum):
    Idling = 0
    Reading = 1
    ReadingFinished = 2


class XmlReader(QObject):
    readingProgessChanged = pyqtSignal(int)

    def __init__(self, extracted_files: TchPath, io_logger: IOLogger):
        super().__init__()
        self._logger = io_logger
        self._tchpath = extracted_files
        self._reading_progess = 0
        self._reading_state = ReadState.Idling

        self._cached_metadata = None
        self._cached_lesson = None
        self._cached_table_model = None

    def start_reading(self) -> bool:
        if self._tchpath.has_required_files():
            self._reading_state = ReadState.Reading
            self._reading_progess = 0
            return True
        self._logger.log(
            logging.CRITICAL,
            f"File is missing required data. Exisiting components: {[file.name for file in self._tchpath.dir.iterdir()]}",
        )
        return False

    def finish_reading(self) -> None:
        self._reading = ReadState.ReadingFinished

    @property
    def logger(self):
        return self._logger

    @property
    def read_state(self) -> ReadState:
        return self._reading_state

    @property
    def metadata(self) -> FileMetaData | None:
        return self._cached_metadata

    @property
    def lesson_model(self) -> Lesson | None:
        return self._cached_lesson

    @property
    def table_model(self) -> TableModel | None:
        return self._cached_table_model

    def clear_caches(self) -> None:
        self._cached_metadata = None
        self._cached_lesson = None
        self._cached_table_model = None
        self._reading_state = ReadState.Idling

    def raise_progress(self, by: int) -> None:
        self._reading_progess += int(by)
        self.readingProgessChanged.emit(self._reading_progess)

    def read_all(self) -> bool:
        if self._reading == ReadState.Reading:
            success = self.read_metadata()
            success &= self.read_lesson()
            success &= self.read_table()
            self.finish_reading()
            return success
        return False

    def read_metadata(self) -> bool:
        if self._reading_state == ReadState.Reading:
            metadata = FileMetaData()
            qfile = self._tchpath.metadata
            if not qfile.open(QFile.OpenModeFlag.ReadOnly):
                self._logger.log(logging.CRITICAL, "Metadata file could not be opened")
                return False
            reader = QXmlStreamReader(qfile)

            if not self.validate_file(reader):
                self._logger.log(logging.CRITICAL, "Xml data incompatible")
                qfile.close()
                return False
            self.raise_progress(4)

            while not reader.atEnd():
                token = reader.readNext()

                try:
                    if token == QXmlStreamReader.TokenType.StartElement:
                        match reader.name():
                            case "file_id":
                                metadata["file_id"] = uuid.UUID(reader.readElementText())
                                self.raise_progress(4)
                            case "creation_date":
                                metadata["creation_date"] = QDateTime.fromString(
                                    reader.readElementText(), Qt.DateFormat.ISODate
                                )
                                if not metadata["creation_date"].isValid():
                                    self._logger.log(
                                        logging.ERROR,
                                        "Invalid Data (creation date) that can be corrected",
                                    )
                                    metadata["creation_date"] = QDateTime.currentDateTime()
                                self.raise_progress(4)
                            case "changed_date":
                                metadata["changed_date"] = QDateTime.fromString(
                                    reader.readElementText(), Qt.DateFormat.ISODate
                                )
                                if not metadata["changed_date"].isValid():
                                    self._logger.log(
                                        logging.ERROR,
                                        "Invalid Data (changed date) that can be corrected",
                                    )
                                    metadata["changed_date"] = QDateTime.currentDateTime()
                                self.raise_progress(4)

                except ValueError:
                    self._logger.log(
                        logging.CRITICAL, f"Missing or invalid file id: {reader.readElementText()}"
                    )
                    qfile.close()
                    return False

                if reader.hasError():
                    self._logger.log(logging.CRITICAL, f"Xml parsing error {reader.error()}")
                    qfile.close()
                    return False

        if FileMetaData.__required_keys__ == set(metadata.keys()) and all(metadata.values()):
            self._cached_metadata = metadata
            return True

        self._logger.log(
            logging.CRITICAL,
            "Metadata could not be sufficiently parsed because values are missing.",
        )
        return False

    def read_lesson(self) -> bool:
        if self._reading_state == ReadState.Reading:
            qfile = self._tchpath.lesson
            if not qfile.open(QFile.OpenModeFlag.ReadOnly):
                self._logger.log(logging.CRITICAL, "Lesson data file could not be opened")
                return False
            reader = QXmlStreamReader(qfile)

            if not self.validate_file(reader):
                self._logger.log(logging.CRITICAL, "Xml data incompatible")
                qfile.close()
                return False

            while not reader.atEnd():
                token = reader.readNext()

                if token == QXmlStreamReader.TokenType.StartElement:  # noqa: SIM102
                    if reader.name() == "lesson":
                        self._cached_lesson = Lesson.read(reader)
                        if reader.hasError():
                            self._logger.log(
                                logging.ERROR, f"Parsing error. Details: {reader.errorString()}"
                            )
                        self.raise_progress(16)
                        return True
            self._logger.log(logging.ERROR, "Missing xml for lesson data")
            self.raise_progress(16)
            self._cached_lesson = Lesson.new(source_id())
            return True

    def read_table(self) -> bool:
        """Reads table and returns a table model. If errors occur the tabel structure is amended if possible otherwise and invalid table will be returned."""
        if self._reading_state == ReadState.Reading:
            qfile = self._tchpath.structure
            if not qfile.open(QFile.OpenModeFlag.ReadOnly):
                self._logger.log(logging.CRITICAL, "Table structure file could not be opened")
                return False
            reader = QXmlStreamReader(qfile)

            if not self.validate_file(reader):
                self._logger.log(logging.CRITICAL, "Xml data incompatible")
                qfile.close()
                return False

            # Defining all required variables
            row, column, header = 0, 0, 0
            progress_increment = 0
            in_table, writing_row, writing_cell = False, False, False
            tmodel, cell = None, None

            while not reader.atEnd():
                token = reader.readNext()

                # Initialise table

                if token == QXmlStreamReader.TokenType.StartElement:
                    if reader.name() == "table":
                        attrs = reader.attributes()
                        try:
                            tmodel: TableModel = TableModel.new_from_xml(attrs)
                            progress_increment = 68 / (
                                tmodel.rowCount() * tmodel.columnCount() + tmodel.columnCount() + 1
                            )
                            in_table = True

                        except (ValueError, TypeError):
                            self._logger.log(
                                logging.CRITICAL, "Row or column number is NaN or values not found."
                            )
                            return False
                        continue

                    # Write Table

                    if in_table:
                        match reader.name():
                            case "header":
                                attrs = reader.attributes()

                                self.read_header(tmodel, header, attrs)
                                header += 1
                                self.raise_progress(progress_increment)

                            case "row":
                                if row < tmodel.rowCount():
                                    column = 0
                                    writing_row = True
                                    continue
                                self._logger.log(
                                    logging.ERROR,
                                    f"The table row was skipped because too many were parsed than specified in the definitions or the column count of the row doesn't match the definition: Specified rows: {tmodel.rowCount()}; Specified columns: {tmodel.columnCount()}",
                                )
                                writing_row = False

                            case "cell" if writing_row:
                                if column < tmodel.columnCount():
                                    cell = tmodel.data(tmodel.index(row, column))
                                    writing_cell = True
                                    continue
                                self._logger.log(
                                    logging.ERROR,
                                    f"The table column was skipped because too many were parsed than specified in the definitions: Specified: {tmodel.columnCount()}; Actual: {tmodel.columnCount() + 1}",
                                )
                                writing_cell = False

                            case "element":
                                if writing_cell and writing_row:
                                    attrs = reader.attributes()

                                    try:
                                        definition = get_definitions(attrs.value("type"))
                                        res_file = attrs.value("file")
                                        if definition and res_file:
                                            res_path = self._tchpath.resource(res_file)
                                            resobj = tmodel.rescont.save(
                                                definition.type(), Path(res_path)
                                            )
                                            model = definition.model_from_xml(attrs, resobj)
                                            if model:
                                                cell.append(model)
                                                continue
                                            else:
                                                self._logger.log(
                                                    logging.ERROR,
                                                    "Invalid values required to parse the element. Element is skipped.",
                                                )
                                                continue
                                        self._logger.log(
                                            logging.ERROR,
                                            f"Cell element of type '{attrs.value('type')}' or resource file is not defined. Element is skipped.",
                                        )

                                    except FileNotFoundError:
                                        self._logger.log(
                                            logging.ERROR,
                                            "Resource file could not be found. Element is skipped.",
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
                            self.raise_progress(progress_increment)
                            continue

                        case "cell" if writing_cell:
                            column += 1
                            writing_cell = False
                            self.raise_progress(progress_increment)
                            continue

                        case "table":
                            if row == tmodel.rowCount():
                                in_table = False
                                self.raise_progress(100 - self._reading_progess)
                                break
                            self._logger.log(
                                logging.ERROR,
                                f"The number of parsed rows does not match the actual number. Some rows' content might be missing. Parsed: {row}. Actual: {tmodel.rowCount()}",
                            )
                            in_table = False
                            break

            self._cached_table_model = tmodel
            return tmodel is not None
        return False

    @staticmethod
    def validate_file(reader: QXmlStreamReader) -> bool:
        """Validates an xml-file to check for the tch-element and version number."""
        reader.readNextStartElement()
        return (
            reader.tokenType() == QXmlStreamReader.TokenType.StartElement
            and reader.name() == "tch"
            and XmlReader.validate_version(reader.attributes().value("version"))
        )

    @staticmethod
    def validate_version(version: str) -> bool:
        return bool(version.isnumeric() and int(CURRENT_VERSION) >= int(version))

    def read_header(
        self, tmodel: TableModel, visual_index: int, attrs: QXmlStreamAttributes
    ) -> bool:
        """Reads header data and writes it to the model if successful"""
        try:
            if visual_index < tmodel.columnCount():
                tmodel.setHeaderData(
                    visual_index,
                    Qt.Orientation.Horizontal,
                    attrs.value("text"),
                    Qt.ItemDataRole.DisplayRole,
                )
                width = int(attrs.value("size")) if int(attrs.value("size")) > 29 else 30
                tmodel.setHeaderData(
                    visual_index,
                    Qt.Orientation.Horizontal,
                    QSize(width, 0),
                    Qt.ItemDataRole.SizeHintRole,
                )
                return True
            self._logger.log(
                logging.ERROR,
                "Skipped horizontal header definition because it would exceed defined column count.",
            )
            return False
        except (ValueError, TypeError):
            self._logger.log(
                logging.ERROR,
                "Invalid value for header size or text. Check if values for header size or text are correct.",
            )
            return False
