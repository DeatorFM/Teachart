import logging
import os.path as osp
from dataclasses import dataclass
from enum import Enum
from functools import cache
from pathlib import Path

from PyQt6.QtCore import QT_TR_NOOP as tr
from PyQt6.QtWidgets import QMessageBox

from tcha.settings import Settings


@dataclass(frozen=True)
class Error:
    message: str
    critical: bool


class FileError(Enum):
    NoError = 0
    MissingXml = 1
    InvalidXml = 2
    MissingResource = 3
    InvalidResource = 4
    BrokenTable = 5
    InvalidElement = 6
    ModelReadError = 7
    MissingFileId = 8
    BadZip = 9


class LFExceptions:
    class LFException(Exception):
        def __init__(self, critical: bool = False, *args):
            super().__init__(*args)
            self.message: str
            self.critical = critical

    class ModelReadError(Exception):
        """Model of element could not be read."""

        def __init__(self, critical: bool = False, *args):
            super().__init__(*args)
            self.message = tr("Model has invalid valuies and could not be read.")
            self.critical = critical

    class MissingXml(Exception):
        """Critical error when necessary xml not found."""

        def __init__(self, critical: bool = False, *args):
            super().__init__(*args)
            self.message: str = tr("Crucial XML definitions missing to parse table.")
            self.critical = critical

    class InvalidXml(Exception):
        """Error when xml is faulty."""

        def __init__(self, critical: bool = False, *args):
            super().__init__(*args)
            self.message: str = tr("XML could not be read.")
            self.critical = critical

    class BrokenTable(Exception):
        """Table data is invalid and cannot be displayed."""

        def __init__(self, critical: bool = False, *args):
            super().__init__(*args)
            self.message: str = tr("Table data is faulty.")
            self.critical = critical

    class MissingResource(Exception):
        """File defined in xml not found."""

        def __init__(self, critical: bool = False, res_path: str | None = None, *args):
            super().__init__(*args)
            self.message: str = tr("Ressource for table element could not be found.")
            self.path = res_path
            self.critical = critical

    class InvalidResource(Exception):
        """Available resource could not be read."""

        def __init__(self, critical: bool = False, *args):
            super().__init__(*args)
            self.message: str = tr("A resource could not be read.")
            self.critical = critical

    class InvalidElement(Exception):
        """Element could not be read due to invalid values."""

        def __init__(self, critical: bool = False, *args):
            super().__init__(*args)
            self.message: str = tr("An element could not be read.")
            self.critical = critical

    class ChecksumMismatch(Exception):
        """Checksum mismatch"""

        def __init__(self, critical: bool = False, *args):
            super().__init__(*args)
            self.message: str = tr("Checksum comparison failed.")
            self.critical = critical

    class ReadError(Exception):
        def __init__(self, *args: tuple[str]):
            super().__init__(*args)
            self.critical = True
            self.message = "File reading failed."
            self.details: str = ", ".join(args)

    class UnsupportedVersion(Exception):
        def __init__(self, version: int, *args):
            super().__init__(*args)
            self.critical = True
            self.message = "Lesson-file version not supported"
            self.version = version

    class MetadataReadError(Exception):
        def __init__(self, critical: bool, *args):
            super().__init__(*args)
            self.critical = critical
            self.message = "Metadata could not be read"


class QtError(Exception):
    """Error related to Qt module."""

    def __init__(self, qterror: int, qterror_string: str, critical: bool, *args):
        super().__init__(*args)
        self.qterror = qterror
        self.error_string = qterror_string
        self.critical = critical

    def __str__(self) -> str:
        return f"QtError: code={self.qterror} string='{self.error_string}'"


class PyException(Exception):
    """Acts as a wrapper for python exception."""

    def __init__(self, pyexception: Exception, critical: bool, *args) -> None:
        super().__init__(*args)
        self.pyexception = pyexception
        self.critical = critical

    def __hash__(self):
        return hash(self.pyexception)


class CriticalError(Exception):
    def __init__(self, *args):
        super().__init__(*args)
        self.critical = False


class CopyError(Exception):
    def __init__(self, *args):
        super().__init__(*args)


class ErrorCode(Enum):
    NoError = 0
    NonCritical = 1
    Critical = 2


class ErrorLogger:
    """Logs errors and evaluates them."""

    def __init__(self, file_name: str | None, raise_critical: bool = False):
        self._errors: set[LFExceptions.LFException] = set()
        self._logger = None
        self._raise_critical = raise_critical
        if file_name:
            self._file = ErrorLogger.logdir() / (osp.basename(file_name) + ".log")
            self._setup_logger(self._file.as_posix())
        else:
            self._file = None

    @cache
    @staticmethod
    def logdir() -> Path:
        return Settings.user_path() / "tchlogs"

    def _setup_logger(self, log_file: str) -> None:
        """Create a unique logger for this ErrorLogger instance"""
        self._logger = logging.getLogger(log_file)  # Create unique logger per file
        self._logger.handlers.clear()  # Clear existing handlers
        self._logger.setLevel(logging.INFO)

        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter("%(asctime)s - %(message)s")
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)

    def set_file(self, file_name: str) -> None:
        self._file = ErrorLogger.logdir() / (osp.basename(file_name) + ".log")
        self._setup_logger(self._file.as_posix())

    def log_msg(self, msg: str) -> None:
        """Logs a message in file if defined."""
        if self._file:
            self._logger.info(msg)

    def log(self, error: Exception, msg: str) -> None:
        """Logs the error as an exception with the message."""
        self._errors.add(error)
        if self._file:
            self._logger.info(msg)
        if self._raise_critical and error.critical:
            raise CriticalError

    def show_result(self, title: str, non_critical_msg: str, critical_msg: str) -> None:
        """Evaluates all errors and shows a MessageBox accordingly."""
        if self.code() == ErrorCode.NoError:
            return
        elif self.code() == ErrorCode.NonCritical:
            QMessageBox.warning(None, title, non_critical_msg)
        elif self.code() == ErrorCode.Critical:
            QMessageBox.warning(None, title, critical_msg)

    def critical(self) -> bool:
        for e in self._errors:
            if e.critical:
                return True

    def clear(self) -> None:
        self._errors.clear()

    @property
    def logfile(self) -> Path | None:
        return self._file

    def code(self) -> ErrorCode:
        """Evalutes all errors and returns error code."""
        if not self._errors:
            return ErrorCode.NoError

        for error in self._errors:
            if error.critical:
                return ErrorCode.Critical
        return ErrorCode.NonCritical
