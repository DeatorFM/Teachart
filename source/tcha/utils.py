from __future__ import annotations

import ctypes
from argparse import SUPPRESS, ArgumentParser
from collections.abc import Iterable
from ctypes import wintypes
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import NotRequired, TypedDict

from PyQt6.QtWidgets import QApplication
from tcha.consts import DisplayMode
from tcha.error import StandardLogger

# AppCore values convenience access


@cache
def debug_enabled() -> bool:
    return QApplication.instance().debug_enabled()


@cache
def clean_mode_enabled() -> bool:
    return QApplication.instance().clean_mode_enabled()


@cache
def source_id() -> str:
    return QApplication.instance().source_id() if QApplication.instance() else "0"


def core() -> QApplication:
    return QApplication.instance()


@dataclass(frozen=True)
class LaunchConfig:
    opened_path: Path | None  # Opens editor with path on launch
    debug: bool  #  Activates debug features on launch
    logging_level: int
    clean: bool  # Starts the application in a initialised state
    test: bool
    test_params: TestParameters  # Define test parameters the app should launch with


class TestParameters(TypedDict):
    source_id: NotRequired[str]  # Launch with custom source id for the session
    db: NotRequired[Path]  # Launch with a specific database file
    theme: NotRequired[
        str
    ]  # Launch with a specified theme or theme file: e.g. "native:dark", "lollipop", "themes/matcha.taste"
    language: NotRequired[
        str
    ]  # Launch with specified language or language file: e.g. "German", "langs/German.ts"
    confetti: NotRequired[bool]  # Shows a confetti at startup


@cache
def _test_parser(exit_on_error=True) -> ArgumentParser:
    parser = ArgumentParser(
        prog="--test", add_help=False, argument_default=SUPPRESS, exit_on_error=exit_on_error
    )
    parser.add_argument("--source_id", type=str)
    parser.add_argument("--db", type=Path, help="Path to .tdb ot .db file with valid structure.")
    parser.add_argument(
        "--theme",
        type=str,
        help="Native theme (e.g. 'native:light'), theme from theme-folder or path to .taste-file.",
    )
    parser.add_argument("--confetti", type=lambda arg: arg.lower() == "true", choices=[True, False])

    return parser


@cache
def _parser(exit_on_error=True) -> ArgumentParser:
    parser = ArgumentParser(exit_on_error=exit_on_error)
    parser.add_argument(
        "path", nargs="?", default=None, type=Path, help="Path to file to open on launch"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        default=False,
        help="Launch application with initialised settings.",
    )
    parser.add_argument(
        "--test",
        action="extend",
        nargs="*",
        type=lambda arg: f"--{arg}",
        help="Enable test features and change parameters by specifying in the arguments (e.g. --test source_id=B473DE34A)",
    )
    parser.add_argument(
        "--debug",
        type=int,
        nargs="?",
        const=0,
        default=30,
        choices=[0, 10, 20, 30, 40, 50],
        help="Specify to enable debug features. You can set the logging level by passing and int otherwise it will be set to 30.",
    )
    return parser


def parse_args(args: Iterable | None = None, *, exit_on_error=True) -> LaunchConfig:
    parser = _parser(exit_on_error)
    parsed = parser.parse_args() if args is None else parser.parse_args(args)

    test_params = {}
    if parsed.test:
        test_parser = _test_parser(exit_on_error)
        test_params = test_parser.parse_args(parsed.test).__dict__

    return LaunchConfig(
        Path(parsed.path) if parsed.path else None,
        parsed.debug > 0,
        parsed.debug,
        parsed.clean,
        any(test_params),
        test_params,
    )


def evened(dec: float) -> int | float:
    """Returns a float as an even integer if possible else input and output are the same"""
    return dec if dec % 1 > 0 else int(dec)


def word_as_bool(word: str) -> bool:
    return {"true": True, "false": False}.get(word, False)


class WinApi:
    SDC_TOPOLOGY_INTERNAL = 0x00000001
    SDC_TOPOLOGY_CLONE = 0x00000002  # Duplicate mode
    SDC_TOPOLOGY_EXTEND = 0x00000004  # Extended mode
    SDC_TOPOLOGY_EXTERNAL = 0x00000008
    SDC_APPLY = 0x00000080
    QDC_ONLY_ACTIVE_PATHS = 0x00000002

    @staticmethod
    def display_count() -> int:
        user32 = ctypes.windll.LoadLibrary("user32")

        num_paths = wintypes.UINT(0)
        num_modes = wintypes.UINT(0)

        # Query buffer sizes
        user32.GetDisplayConfigBufferSizes(
            WinApi.QDC_ONLY_ACTIVE_PATHS,
            ctypes.byref(num_paths),
            ctypes.byref(num_modes),
        )

        return num_paths.value

    @staticmethod
    def get_display_mode() -> DisplayMode:
        user32 = ctypes.windll.LoadLibrary("user32")

        num_paths = wintypes.UINT(0)
        num_modes = wintypes.UINT(0)

        # Query buffer sizes
        result = user32.GetDisplayConfigBufferSizes(
            WinApi.QDC_ONLY_ACTIVE_PATHS,
            ctypes.byref(num_paths),
            ctypes.byref(num_modes),
        )

        if result != 0:
            return DisplayMode.Single

        # num_paths.value tells you how many active display paths exist
        display_count = num_paths.value

        virtual_width = user32.GetSystemMetrics(78)
        primary_width = user32.GetSystemMetrics(0)

        if display_count > 1:
            if virtual_width > primary_width:
                return DisplayMode.Extended
            else:
                return DisplayMode.Duplicated
        return DisplayMode.Single

    @staticmethod
    def set_display_mode(mode: DisplayMode) -> None:
        StandardLogger.info(f"Set display mode to {mode.name}", extra={"sender": "WINAPI"})
        user32 = ctypes.windll.LoadLibrary("user32")
        if mode == DisplayMode.Single:
            return
        elif mode == DisplayMode.Extended:
            user32.SetDisplayConfig(0, None, 0, None, WinApi.SDC_APPLY | WinApi.SDC_TOPOLOGY_EXTEND)
        else:
            user32.SetDisplayConfig(0, None, 0, None, WinApi.SDC_APPLY | WinApi.SDC_TOPOLOGY_CLONE)
