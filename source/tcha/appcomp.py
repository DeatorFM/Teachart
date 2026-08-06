from __future__ import annotations

from argparse import ArgumentParser
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import ClassVar

from PyQt6.QtWidgets import QApplication


@cache
def debug_enabled() -> bool:
    print("Asking for debug mode")
    return QApplication.instance().debug_enabled()


@cache
def clean_mode_enabled() -> bool:
    return QApplication.instance().clean_mode_enabled()


@cache
def _parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("path", nargs="?", default="", type=str, help="Path to open on launch")
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


@dataclass
class DialogVariant:
    dtype: type
    singleton: bool
    val: list | None = field(init=False)

    def __post_init__(self):
        self.val = None if self.singleton else []


class EditorContainer(dict): ...


class DialogManager:
    """Manages top level windows of application"""

    _dialogs: ClassVar[dict[str, DialogVariant]] = {
        "Editor": EditorContainer(),
        "Start": None,
        "Settings": None,
        "DBManager": None,
        "About": None,
        "Presenter": None,
    }

    _multi_window: ClassVar[list[str]] = [
        "Editor"
    ]  # Dialog types that can have more than one instance open

    def define_custom_mapping(self, wid: str, multi_window=False) -> None:
        if wid not in self._dialogs:
            self._dialogs[wid] = None
            if multi_window:
                self._multi_window.append(wid)


class MetaApp:
    __debug = False
    __clean = False

    @staticmethod
    def debug_enabled() -> bool:
        return MetaApp.__debug

    @staticmethod
    def is_clean_mode() -> bool:
        return MetaApp.__clean
