import datetime
import logging
import os
import random
import sys
import typing
import uuid
from dataclasses import dataclass
from enum import Enum
from functools import cache
from pathlib import Path
from threading import Lock

from PyQt6.QtCore import QT_TR_NOOP as tr
from PyQt6.QtWidgets import QApplication


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


@dataclass
class LoggableError:
    """Model of element could not be read."""

    log_level: int
    message: str


class LFExceptions:
    class LFException(Exception):
        def __init__(self, critical: bool = False, *args):
            super().__init__(*args)
            self.message: str
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


class BinReadError(Exception):
    def __init__(self, *args):
        super().__init__(*args)


class ErrorCode(Enum):
    NoError = 0
    NonCritical = 1
    Critical = 2


class MetaLogger(type):
    _instances: typing.ClassVar[dict] = {}
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwds):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwds)
                cls._instances[cls] = instance
        return cls._instances[cls]


class IOLogger:
    """Logger for IO operations with .tch-files. Records all events and evaluates the success of the io operation."""

    _session = 0

    def __init__(self, file_id: uuid.UUID | None = None):
        self._file_id = file_id
        self._logfile = (
            IOLogger.logdir() / f"{file_id}.log"
            if file_id
            else IOLogger.logdir() / f"unknown_{random.getrandbits(32)}.log"
        )
        self._level = logging.NOTSET

        self._setup_logger()

    @cache
    @staticmethod
    def logdir() -> Path:
        from tcha.settings import Settings

        return Settings.user_path() / "tchlogs"

    def _setup_logger(self) -> None:
        self._logger = logging.getLogger(str(self._session))
        self._logger.setLevel(logging.INFO)
        self._session += 1
        self._logger.handlers.clear()

        handler = logging.FileHandler(self._logfile)
        formatter = logging.Formatter(
            f"%(asctime)s - {self._file_id} - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)

    def set_file_id(self, file_id: uuid.UUID) -> None:
        """Renames the log file to the given file id. If a file with file_id already exists logs will be appended to the existing file."""
        if self._logger and self._logger.handlers:
            for handler in self._logger.handlers:
                handler.close()
            self._logger.handlers.clear()

        old_logfile = self._logfile
        new_logfile = IOLogger.logdir() / f"{file_id}.log"

        if old_logfile.exists() and not new_logfile.exists():
            old_logfile.rename(new_logfile)
        elif new_logfile.exists():
            old_records = old_logfile.read_text()
            new_records = new_logfile.read_text()
            new_logfile.write_text(new_records + old_records)
            os.remove(old_logfile.as_posix())

        self._logfile = new_logfile
        self._file_id = file_id

        self._setup_logger()

    def log(self, level: int, message: str) -> None:
        """Log messsage with given level and message."""
        from tcha.utils import debug_enabled

        if level == logging.DEBUG and not debug_enabled():
            return
        self._logger.log(level, message)
        self._level = max(self._level, level)

    def evaluate(self) -> ErrorCode:
        """Evaluates the last reading session and returns the appropriate error code."""
        if self._level == logging.CRITICAL:
            self._level = logging.NOTSET
            return ErrorCode.Critical
        elif self._level <= logging.ERROR and self._level >= logging.WARNING:
            self._level = logging.NOTSET
            return ErrorCode.NonCritical
        self._level = logging.NOTSET
        return ErrorCode.NoError


class StandardLogger:
    """Manages logger for current session of AppCore instance."""

    _logger = None

    @staticmethod
    def logdir() -> Path:
        from tcha.settings import Settings

        return Settings.user_path() / "sessionlogs"

    @classmethod
    def init_logger(cls, level: int) -> bool:
        """Initialises the logger for the session."""
        if not cls._logger:
            cls.get_logger(level)
            return True
        return False

    @classmethod
    def get_logger(cls, level: int = 0) -> logging.Logger:
        """Gets the current logger. If no logger set up a new logger is created as long as a QApplication instance exists."""
        from tcha.utils import debug_enabled

        if QApplication.instance():
            if not cls._logger:
                logger = logging.getLogger(QApplication.instance().sessionId())
                logger.setLevel(level)
                logger.propagate = False
                if debug_enabled():
                    stream_handler = logging.StreamHandler(sys.stdout)
                    formatter = logging.Formatter(
                        "%(levelname)s %(sender)s - %(message)s",
                        defaults={"sender": "APP"},
                    )
                    stream_handler.setFormatter(formatter)
                    stream_handler.setLevel(logging.DEBUG)
                    logger.addHandler(stream_handler)

                now = datetime.datetime.now(datetime.UTC)
                if not cls.logdir().exists():
                    cls.logdir().mkdir()
                logpath = cls.logdir() / f"session_{now:%Y%m%d%H%M%S}.log"
                if level > 0:
                    file_handler = logging.FileHandler(str(logpath))
                    formatter = logging.Formatter(
                        "%(asctime)s - %(levelname)s - %(sender)s - %(message)s",
                        defaults={"sender": "APP"},
                    )
                    file_handler.setFormatter(formatter)
                    file_handler.setLevel(level)
                    logger.addHandler(file_handler)
                cls._logger = logger
            return cls._logger
        raise RuntimeError("QApplication not initialised")

    # Convenience methods to log messages without retrieving the current instance

    @classmethod
    def debug(cls, *args, **kwargs):
        if cls._logger:
            cls._logger.debug(*args, **kwargs)

    @classmethod
    def info(cls, *args, **kwargs):
        if cls._logger:
            cls._logger.info(*args, **kwargs)

    @classmethod
    def warning(cls, *args, **kwargs):
        if cls._logger:
            cls._logger.warning(*args, **kwargs)

    @classmethod
    def error(cls, *args, **kwargs):
        if cls._logger:
            cls._logger.error(*args, **kwargs)

    @classmethod
    def critical(cls, *args, **kwargs):
        if cls._logger:
            cls._logger.critical(*args, **kwargs)
