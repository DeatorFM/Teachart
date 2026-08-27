from typing import Any, ClassVar

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget
from tcha.dbmanager import DbManager
from tcha.editor import Editor
from tcha.settings import SettingsDialog
from tcha.start import AboutDialog, StartWindow
from tcha.table import PresenterView


class DialogContainer(dict):
    """Can save multiple window of same type by assigning it to unique key."""

    def __init__(self, wclass: type):
        super().__init__()
        self._wclass = wclass

    def wclass(self) -> type:
        return self._wclass

    def __setitem__(self, key, value):
        if key not in self and isinstance(value, self._wclass):
            super().__setitem__(key, value)


class DialogManager:
    """Manages top level windows of application that are called from AppCore. Thanks to the Anki dev team for inspiration :-)"""

    _dialogs: ClassVar[dict[str, list[type, QWidget | DialogContainer[str, QWidget] | None]]] = {
        "Editor": [Editor, DialogContainer(Editor)],
        "StartWindow": [StartWindow, None],
        "SettingsDialog": [SettingsDialog, None],
        "DbManager": [DbManager, None],
        "AboutDialog": [AboutDialog, None],
        "PresenterView": [PresenterView, None],
    }

    _containers: ClassVar[list[str]] = [
        "Editor"
    ]  # Dialog types that can have more than one instance open

    def define_custom_mapping(self, wtype: str, wclass: type, container=False) -> bool:
        """Define custom mapping for Dialog with class name 'wtype'. If 'multi_ins't' is True a container"""
        if wtype not in self._dialogs:
            if container and hasattr(wclass, "wid"):
                self._dialogs[wtype] = DialogContainer(wclass)
                self._containers.append(wtype)
                return True
            else:
                self._dialogs[wtype] = [wclass, None]
                return True
        return False

    def get_dialog(self, wtype: str, wid: int = 0) -> QWidget | None:
        """Get single instance only dialog if existing else None."""
        if wtype in self._containers:
            return self._dialogs[wtype][1].get(wid)
        return self._dialogs.get(wtype, [None, None])[1]

    def get_container(self, wtype: str) -> DialogContainer:
        if wtype in self._containers:
            return self._dialogs.get(wtype)[1]
        return DialogContainer(None)

    def open(self, wtype: str, *args: Any, **kwargs: Any) -> QWidget | None:
        """Creates a new dialog of class 'wclass' for dialog of 'wtype'.
        For single instance dialogs if an active dialog is already present it will be returned.
        For multi instance windows a new window is always created."""
        if wtype in self._dialogs:
            wclass, winst = self._dialogs.get(wtype, [None, None])
            if wtype not in self._containers:
                if winst:
                    if winst.windowState() & Qt.WindowState.WindowMinimized:
                        winst.setWindowState(winst.windowState() & ~Qt.WindowState.WindowMinimized)
                    winst.activeWindow()
                    winst.raise_()
                else:
                    winst = wclass(*args, **kwargs)
                    self._dialogs[wtype][1] = winst

            else:
                inst = wclass(*args, **kwargs)
                winst[inst.wid] = inst
                return inst

            return winst
        return None

    def mark_closed(self, wtype: str, wid: int = 0) -> None:
        if wtype in self._containers:
            del self._dialogs[wtype][1][wid]
        else:
            self._dialogs[wtype] = [self._dialogs[wtype][0], None]

    def all_closed(self) -> bool:
        return not any(
            val[1] for key, val in self._dialogs.items() if key not in self._containers
        ) and not any(self._dialogs[wtype][1] for wtype in self._containers)

    def close_all(self) -> bool:
        """
        Tries to close all active top level windows.
        Return True if all windows could be closed otherwise returns False if even one could not be closed.
        """
        result = True
        for wtype in self._dialogs:
            if wtype in self._containers:
                cont: DialogContainer = self._dialogs[wtype]
                for key, value in cont.items():
                    if value.close():
                        del cont[key]
                        continue
                    result = False
            else:
                _, winst = self._dialogs[wtype]
                if winst.close():
                    self._dialogs[wtype] = [self._dialogs[wtype][0], None]
                    continue
                result = False
        return result

    def is_opened(self, wtype: str) -> bool:
        return bool(self._dialogs.get(wtype, [None, None])[1])

    def is_defined(self, wtype: str) -> bool:
        """Returns True if the window type 'wtype' has been logged to the Dialog Manager."""
        return wtype in self._dialogs

    