import json
import logging
import os.path as osp
import tempfile
from turtle import clear
import uuid
from base64 import b64decode, b64encode
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Any, Literal, TypedDict
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile

from PyQt6.QtCore import (
    QBuffer,
    QByteArray,
    QDateTime,
    QFile,
    QObject,
    QSize,
    Qt,
    QXmlStreamAttributes,
    QXmlStreamReader,
    QXmlStreamWriter,
    pyqtSignal,
)
from tcha.elements import get_definitions
from tcha.error import CriticalError, IOLogger, LFExceptions, QtError
from tcha.lesson import Lesson
from tcha.resmanager import (
    ResourceContainer,
    ResourceTransferObject,
    ResourceType,
)
from tcha.tablemodel import (
    HeaderDataItem,
    TableModel,  # CellModel, HeaderDataItem,
)
from tcha.utils import source_id

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
    current_version: int
    file_id: uuid.UUID | None
    creation_date: QDateTime
    changed_date: QDateTime


class LessonFile:
    """Provides file stream for serialised Lesson-Documents"""

    def __init__(self):
        self._save_buffer: SaveBuffer | None = None

        self._f: ZipFile | None = None
        self._tempdir: tempfile.TemporaryDirectory | None = None
        self._last_saved = None
        self._metadata: FileMetaData = {
            "version": 1,
            "file_id": None,
            "creation_date": QDateTime(),
            "changed_date": QDateTime(),
        }
        self._state = WriteState.Unserialised
        self._reader = None

    @property
    def progress(self) -> ProgressLogger:
        return self._progress

    def open(self, mode: Literal["r", "w"], path: str | None = None) -> bool:
        if mode == "r" and path:
            try:
                self._last_saved = QDateTime.currentDateTime()
                self._logger = IOLogger()
                self._tempdir = tempfile.TemporaryDirectory(".tmp", "TCHA", delete=False)
                print("Temporary", self._tempdir)
                self._f = ZipFile(path, mode)
                self._f.extractall(self.temppath)

                self._reader = XmlReader(self._tempdir, self._logger)
                success = self._reader.read_metadata()
                if success:
                    self._metadata = self._reader.metadata
                    self._state = WriteState.SerialisedFile
                    self._logger.set_file_id(self._metadata["file_id"])
                    success &= self._reader.read_lesson()
                    success &= self._reader.read_table()
                    self._reader.finish_reading()             
                    return success
                return False

            except BadZipFile as e:
                # LOGGER Critical: File is corrupted and cannot be opened.
                return False

        elif mode == "w":
            self._metadata["version"] = CURRENT_VERSION
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
                    self._f = ZipFile(path, "w", ZIP_DEFLATED)
                    self._logger = IOLogger(self._metadata["file_id"])
                except PermissionError:
                    # LOGGER Critical: File could not be opened. Permission denied.
                    return False
            else:
                self.change_open_mode("w")

            # LOGGER Info: Starting writing operation

            # Write xml for document structure
            written_bytes = 0
            with self._f.open("structure.xml", "w") as struct_f:
                written_bytes += struct_f.write(self._save_buffer.struct_buffer.data())
            self._error_handler.log_msg("Table structure written.")

            # Write lesson.xml
            with self._f.open("lesson.xml", "w") as lesson_f:
                written_bytes += lesson_f.write(self._save_buffer.lesson_data_buffer.data())
            self._error_handler.log_msg("Lesson data written.")

            # Write metadata.xml
            with self._f.open("metadata.xml", "w") as metadata_f:
                written_bytes += metadata_f.write(self._save_buffer.meta_data_buffer.data())
            self._error_handler.log_msg("Meta data written.")

            if written_bytes != self._save_buffer.size():
                print(written_bytes, self._save_buffer.size())
                # LOGGER Critical: Error during writing of xml-data. Writing operation has been terminated.
                self.change_open_mode("r")
                return False

            # LOGGER Info: All xml data written successfully.

            # Copy the resources into file or create new file if necessary
            for obj in self._save_buffer.resobjects:
                if not obj.has_data():
                    # LOGGER Info: f"Writing '{obj.src_path}' to file as '{obj.filename}'"
                    self._copy(obj)
                else:
                    # LOGGER Info: f"Writing new resource with name '{obj.filename}' to file"
                    self._write_new(obj)

            # LOGGER Info: "Resource data successfully written."

            self.change_open_mode("r")
            # LOGGER Info: "Finished writing successfully."

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

        print("Writing buffer to LessonFile object")
        struct_buffer = XmlWriter.write_struct_xml(tablemodel)
        print("Finished struct buffer")
        lesson_buffer = XmlWriter.write_lesson_xml(lesson)
        print("Finished lesson data buffer")
        meta_data_buffer = XmlWriter.write_metadata_xml(self._metadata)
        print("Finished meta data buffer")
        self._save_buffer = SaveBuffer(
            struct_buffer, lesson_buffer, meta_data_buffer, tablemodel.rescont.to_transfer_objects()
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

    def init_reader(self) -> bool:
        if not self._reader and self._tempdir and self.file_id:
            self._reader = IOLogger(self.file_id)
            return True
        return False

    def get_table(self) -> TableModel | None:
        """Returns TableModel if file is loaded."""
        if self._reader and self._reader.read_state == ReadState.ReadingFinished:
            model =  self._reader.table_model
            self._reader.clear_cache()
            return model
        else:
            self._reader.start_reading()
            if self._reader.read_table():
                self._reader.finish_reading()
                model = self._reader.table_model
                self._reader.clear_cache()
                return model
        return None

    def get_lesson(self) -> Lesson | None:
        """Returns Lesson model if file is loaded and could be read otherwise returns the default value."""
        if self._reader and self._reader.read_state == ReadState.ReadingFinished:
            model =  self._reader.lesson_model
            self._reader.clear_caches()
            return model
        else:
            self._reader.start_reading()
            if self._reader.read_lesson():
                self._reader.finish_reading()
                model = self._reader.lesson_model
                self._reader.clear_caches()
                return model
        return None

    def set_metadata(self, metadata: FileMetaData) -> None:
        self._metadata = metadata

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
    @classmethod
    def write_metadata_xml(cls, metadata: FileMetaData) -> QByteArray:
        writer = QXmlStreamWriter()
        xml_data = QByteArray()
        buffer = QBuffer(xml_data)
        buffer.open(QBuffer.OpenModeFlag.WriteOnly)
        writer.setDevice(buffer)

        writer.writeStartDocument()
        writer.writeStartElement("tch")

        writer.writeTextElement("version", str(CURRENT_VERSION))

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
        print("1")

        tablemodel.xml(writer)
        print("2")

        writer.writeEndElement()
        writer.writeEndDocument()
        print("3")

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

    def __init__(self, extracted_files: tempfile.TemporaryDirectory, io_logger: logging.Logger):
        self._logger = io_logger
        self._tchpath = extracted_files
        self._reading_status = 0
        self._reading_state = ReadState.Idling

        self._cached_metadata = None
        self._cached_lesson = None
        self._cached_table_model = None

    def start_reading(self) -> bool:
        required_files = ["structure.xml", "lesson.xml", "metadata.xml"]
        dir_path = Path(self._tchpath.name)

        if all((dir_path / f).exists() for f in required_files):
            self._reading_state = ReadState.Reading
            return True
        return False

    def finish_reading(self) -> None:
        self._reading = ReadState.ReadingFinished

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

    def read_all(self) -> bool:
        if self._reading == ReadState.Reading:
            success = self.read_metadata()
            success &= self.read_lesson()
            success &= self.read_table()
            self.finish_reading()
            return success
        return False

    def read_metadata(self) -> bool:
        if self._reading == ReadState.Reading:
            metadata = FileMetaData()
            path = Path(self._tchpath.name) / "metadata.xml"
            qfile = QFile(path.as_posix())
            if not qfile.open(QFile.OpenModeFlag.ReadOnly):
                # LOGGER Critical: Metadata file could not be opened
                return False
            reader = QXmlStreamReader(qfile)

            if not self.validate_file(reader):
                # LOGGER Critical: Xml data incompatible
                qfile.close()
                return False

            while not reader.atEnd():
                token = reader.readNext()

                try:
                    if token == QXmlStreamReader.TokenType.StartElement:
                        match reader.name():
                            case "version":
                                metadata["current_version"] = int(reader.text())
                                if metadata["current_version"] > CURRENT_VERSION:
                                    # LOGGER Critical: File version not compatible
                                    qfile.close()
                                    return False
                            case "file_id":
                                metadata["file_id"] = uuid.UUID(reader.text())
                            case "creation_date":
                                metadata["creation_date"] = QDateTime.fromString(
                                    reader.text(), Qt.DateFormat.ISODate
                                )
                                if not metadata["creation_date"].isValid():
                                    # LOGGER Warning: Invalid Data that can be corrected
                                    metadata["creation_date"] = QDateTime.currentDateTime()
                            case "changed_date":
                                metadata["changed_date"] = QDateTime.fromString(
                                    reader.text(), Qt.DateFormat.ISODate
                                )
                                if not metadata["changed_date"].isValid():
                                    # LOGGER: Warning: Invalid Data that can be corrected
                                    metadata["changed_date"] = QDateTime.currentDateTime()

                except ValueError:
                    # LOGGER Critical: Missing file id or version not readable
                    qfile.close()
                    return False
                except CriticalError:
                    qfile.close()
                    return False

                if reader.hasError():
                    # LOGGER Critical:  General Parsing error
                    qfile.close()
                    return False

        if all(metadata.values()):
            self._cached_metadata = metadata
            return True

        # LOGGER Critical: Metadata incomplete
        return False

    def read_lesson(self) -> bool:
        if self._reading == ReadState.Reading:
            path = Path(self._tchpath.name) / "lesson.xml"
            qfile = QFile(path.as_posix())
            if not qfile.open(QFile.OpenModeFlag.ReadOnly):
                # LOGGER Critical: Lesson information file could not be opened
                return False
            reader = QXmlStreamReader(qfile)

            if not self.validate_file(reader):
                # LOGGER Critical: Xml data incompatible
                qfile.close()
                return False

            while not reader.atEnd():
                token = reader.readNext()

                if token == QXmlStreamReader.TokenType.StartElement:  # noqa: SIM102
                    if reader.name() == "lesson":
                        model = Lesson.read(reader)
                        if reader.hasError():
                            ...
                            # LOGGER Error: log reader error from reader.errorString()
                        self._cached_lesson = model
                        return True
            # LOGGER Error: Missing xml for lesson data
            return Lesson.new(source_id())

    def read_table(self) -> bool:
        """Reads table and returns a table model. If errors occur the tabel structure is amended if possible otherwise and invalid table will be returned."""
        if self._reading == ReadState.Reading:
            struct_f = Path(self._tchpath.name) / "struct.xml"
            resources_dir = Path(self._tchpath.name) / "resources"
            qfile = QFile(struct_f.as_posix())
            if qfile.open():
                # LOGGER Critical: Structure file not found
                return False
            reader = QXmlStreamReader(struct_f)

            if not self.validate_file(reader):
                # LOGGER Critical: Xml data incompatible
                qfile.close()
                return False

            row, column, header = 0, 0, 0
            in_table, writing_row, writing_cell = False, False, False

            tmodel = None
            cell = None

            while not reader.atEnd():
                token = reader.readNext()

                # Initialise table

                if token == QXmlStreamReader.TokenType.StartElement:
                    if reader.name() == "table":
                        attrs = reader.attributes()
                        try:
                            tmodel: TableModel = TableModel.new_from_xml(attrs)
                            in_table = True

                        except (ValueError, TypeError) as e:
                            # LOGGER Critical: Row or column number is NaN or values not found.
                            return False
                        continue

                    # Write Table

                    if in_table:
                        match reader.name():
                            case "header":
                                attrs = reader.attributes()

                                try:
                                    if header < tmodel.columnCount():
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
                                    # LOGGER Error: Skipped horizontal header definition because it would exceed defined column count.
                                except (ValueError, TypeError):
                                    # LOGGER Error: Invalid value for header size and text. Check if values for header size or text are correct.
                                    continue

                            case "row":
                                if row < tmodel.rowCount():
                                    column = 0
                                    writing_row = True
                                    continue
                                # LOGGER Error: The table row was skipped because too many were parsed than specified in the definitions or the column count of the row doesn't match the definition: Specified rows: {tmodel.rowCount()}; Specified columns: {tmodel.columnCount()}
                                writing_row = False

                            case "cell":
                                if column < tmodel.columnCount():
                                    cell = tmodel.data(tmodel.index(row, column))
                                    writing_cell = True
                                    continue
                                # LOGGER Error: The table column was skipped because too many were parsed than specified in the definitions: Specified: {tmodel.columnCount()}; Actual: {tmodel.columnCount() + 1}
                                writing_cell = False

                            case "element":
                                if writing_cell and writing_row:
                                    attrs = reader.attributes()

                                    try:
                                        definition = get_definitions(attrs.value("type"))
                                        res_file = attrs.value("file")
                                        if definition and res_file:
                                            res_path = resources_dir / res_file
                                            resobj = tmodel.rescont.save(
                                                definition.type(), res_path
                                            )
                                            model = definition.model_from_xml(attrs, resobj)
                                            if model:
                                                cell.append(model)
                                            else:
                                                # LOGGER Error: Invalid values required to parse the element. Element is skipped.
                                        # LOGGER Error: Cell element of type '{attrs.value("type")}' or resource file is not defined. Element is skipped.

                                    except FileNotFoundError:
                                        # LOGGER Error: Resource file could not be found. Element is skipped.
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
                            continue

                        case "cell" if writing_cell:
                            column += 1
                            writing_cell = False
                            continue

                        case "table":
                            if row == tmodel.rowCount():
                                in_table = False
                                break
                            # LOGGER Error: The number of parsed rows does not match the actual number. Some rows' content might be missing.
                            in_table = False

                            break

            return True

    @staticmethod
    def validate_file(reader: QXmlStreamReader) -> bool:
        token = reader.readNext()
        return token == QXmlStreamReader.TokenType.StartElement and reader.name() == "tch"

    @classmethod
    def read_header(cls, attrs: QXmlStreamAttributes) -> HeaderDataItem: ...
