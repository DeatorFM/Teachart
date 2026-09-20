from abc import abstractmethod

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QMainWindow


class BaseMainWindow(QMainWindow):
    """Base class for QMainWindow objects that have a unique id and can show a progress bar"""

    closed = pyqtSignal(str, int)

    @property
    @abstractmethod
    def wid(self) -> int:
        return 0

    @abstractmethod
    def set_status_bar_msg(self, msg: str) -> None: ...

    @abstractmethod
    def set_progress(self, value: int) -> None: ...

    @abstractmethod
    def reset_progress(self) -> None: ...
