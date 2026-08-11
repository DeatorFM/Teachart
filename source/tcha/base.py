from abc import ABCMeta, abstractmethod

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QMainWindow
from tcha.consts import CloseState


class BaseMainWindow(QMainWindow, metaclass=ABCMeta):
    closed = pyqtSignal(str, int)

    @property
    @abstractmethod
    def wid(self) -> int:
        return 0

    @property
    @abstractmethod
    def close_state(self) -> CloseState:
        return CloseState.CanClose
