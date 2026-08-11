from __future__ import annotations

from argparse import ArgumentParser
from ctypes import wintypes
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from tkinter import dialog
from typing import Any, ClassVar

import dialogs
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QWidget


@cache
def debug_enabled() -> bool:
    print("Asking for debug mode")
    return QApplication.instance().debug_enabled()


@cache
def clean_mode_enabled() -> bool:
    return QApplication.instance().clean_mode_enabled()


def core() -> QApplication:
    return QApplication.instance()


@cache
def _parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument(
        "path", nargs="?", default="", type=str, help="Path to file to open on launch"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--clean", action="store_true", help="Enable clean mode")
    return parser


def parse_args() -> LaunchConfig:
    parser = _parser()
    parsed = parser.parse_args()
    return LaunchConfig(Path(parsed.path) if parsed.path else None, parsed.debug, parsed.clean)


@dataclass(frozen=True)
class LaunchConfig:
    opened_path: Path | None
    debug: bool
    clean: bool


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
    """Manages top level windows of application that are called from AppCore. Thanks to the Anki dev team for inspiration."""

    _dialogs: ClassVar[dict[str, list[type, QWidget | DialogContainer[str, QWidget] | None]]] = {
        "Editor": [dialogs.Editor, DialogContainer(dialogs.Editor)],
        "StartWindow": [dialogs.StartWindow, None],
        "SettingsDialog": [dialogs.SettingsDialog, None],
        "DbManager": [dialogs.DbManager, None],
        "AboutDialog": [dialogs.AboutDialog, None],
        "PresenterView": [dialogs.PresenterView, None],
    }

    _containers: ClassVar[list[str]] = [
        "Editor"
    ]  # Dialog types that can have more than one instance open

    def define_custom_mapping(self, wtype: str, wclass: type, multi_inst=False) -> bool:
        """Define custom mapping for Dialog with class name 'wtype'. If 'multi_ins't' is True a container"""
        if wtype not in self._dialogs:
            if multi_inst and hasattr(wclass, "wid"):
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
            return self._dialogs[wtype].get(wid)
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
            del self._dialogs[wtype][wid]
        else:
            self._dialogs[wtype] = [self._dialogs[wtype][0], None]

    def all_closed(self) -> bool:
        return not any(
            val[1] for key, val in self._dialogs.items() if key not in self._containers
        ) and not any(self._dialogs[wtype][1] for wtype in self._containers)

    def close_all(self) -> bool:
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
        return wtype in self._dialogs
