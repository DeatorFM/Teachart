from abc import abstractmethod

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QMainWindow


class BaseMainWindow(QMainWindow):
    closed = pyqtSignal(str, int)

    @property
    @abstractmethod
    def wid(self) -> int:
        return 0
