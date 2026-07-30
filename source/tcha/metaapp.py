from functools import cache
from threading import Lock
from typing import ClassVar

from PyQt6.QtWidgets import QApplication


@cache
def debug_enabled() -> bool:
    return QApplication.instance().debug_enabled()


@cache
def clean_mode_enabled() -> bool:
    return QApplication.instance().clean_mode_enabled()


class WindowManagerMeta(type):
    _instances: ClassVar[dict] = {}
    _lock: Lock = Lock()

    def __call__(self, *args, **kwds):
        with self._lock:
            if self not in self._instances:
                instance = super().__call__(*args, **kwds)
                self._instance[self] = instance
        return self._instance[self]


class WindowManager(metaclass=WindowManagerMeta):
    _start = None
    _settings = None
    _editors: ClassVar[list] = []


class MetaApp:
    __debug = False
    __clean = False
    __windows = WindowManager()

    @staticmethod
    def debug_enabled() -> bool:
        return MetaApp.__debug

    @staticmethod
    def is_clean_mode() -> bool:
        return MetaApp.__clean
