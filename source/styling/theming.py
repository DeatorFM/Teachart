import json
import os.path as osp
import zipfile
from importlib import import_module
from pathlib import Path

from PyQt6.QtCore import (
    QByteArray,
    QDataStream,
    QIODevice,
    qChecksum,
    qRegisterResourceData,
    qUnregisterResourceData,
)
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication
from styling.properties import NTHEME_PROPERTIES
from tcha.error import BinReadError
from tcha.settings import Values


def load_theme(identifier: str, app: QApplication) -> None:
    if identifier.startswith("native:"):
        name = identifier.removeprefix("native:")
        return _load_native_theme(name, app)

    if not _load_extern_theme(identifier, app):
        return _load_native_theme(Values.default_value("User/appearance"))


def _load_native_theme(name: str, app: QApplication) -> bool:
    if name in NTHEME_PROPERTIES:
        app.setPalette(
            make_palette(
                NTHEME_PROPERTIES[name]["palette"],
                NTHEME_PROPERTIES[name]["applyFullPalette"],
            ),
        )

        if ExternalTheme.has_data():
            ExternalTheme.unregister()
        import_module(f"styling.resources.{name}")

        from styling.stylesheets import STYLESHEETS

        app.setStyleSheet(STYLESHEETS[name])

        return True

    load_theme(Values.default_value("User/appearance"), app)


def _load_extern_theme(fname: str, app: QApplication) -> bool:
    from tcha.settings import Settings

    taste_file = (
        Path(fname)
        if fname.endswith(".taste") and osp.exists(fname)
        else Settings.user_path() / "themes" / f"{fname}.taste"
    )
    try:
        with zipfile.ZipFile(taste_file, "r") as f_taste:
            properties = json.loads(f_taste.read("properties.json"))
            palette = make_palette(properties["palette"], properties["applyFullPalette"])
            app.setPalette(palette)
            res_data = f_taste.read(properties["resources"], "")
            if qChecksum(res_data) == properties["chksum"]:
                qt_resource_data, qt_resource_name, qt_resource_struct = restructure_resource_data(
                    res_data
                )
                if ExternalTheme.has_data():
                    ExternalTheme.unregister()
                ExternalTheme.set_resources(qt_resource_struct, qt_resource_name, qt_resource_data)
                result = ExternalTheme.register()
                print(f"Loaded resource data: {result}")
                stylesheet = f_taste.read(properties["stylesheet"])
                app.setStyleSheet(stylesheet.decode())
                return True
            return False

    except zipfile.BadZipFile:
        print("taste-file is corrupted and cannot be opened.")
    except FileNotFoundError:
        print("taste-file not found in User folder or taste-file is missing subfile")
    except BinReadError:
        print("Resource file corrupted.")
    except (KeyError, ValueError, TypeError):
        print("taste-file has invalid data or structure")
    return False


def restructure_resource_data(data: bytes) -> tuple[bytes, bytes, bytes]:
    bytearr = QByteArray(data)
    stream = QDataStream(bytearr, QIODevice.OpenModeFlag.ReadOnly)
    magic_header = stream.readBytes()
    if magic_header == b"tcha-qrc":
        qt_resource_data = stream.readBytes()
        qt_resource_name = stream.readBytes()
        qt_resource_struct = stream.readBytes()
        if stream.atEnd():
            return qt_resource_data, qt_resource_name, qt_resource_struct
    raise BinReadError("Wrong magic header")


def make_palette(color_def: dict[str, list[int, int, int, int]], apply_all=False) -> QPalette:
    palette = QPalette()

    # Mapping from string names to QPalette.ColorRole enums
    color_role_map = {
        "WindowText": QPalette.ColorRole.WindowText,
        "Button": QPalette.ColorRole.Button,
        "Light": QPalette.ColorRole.Light,
        "Dark": QPalette.ColorRole.Dark,
        "Mid": QPalette.ColorRole.Mid,
        "Text": QPalette.ColorRole.Text,
        "Base": QPalette.ColorRole.Base,
        "Window": QPalette.ColorRole.Window,
        "Shadow": QPalette.ColorRole.Shadow,
        "Highlight": QPalette.ColorRole.Highlight,
        "HighlightedText": QPalette.ColorRole.HighlightedText,
        "Link": QPalette.ColorRole.Link,
        "LinkVisited": QPalette.ColorRole.LinkVisited,
        "AlternateBase": QPalette.ColorRole.AlternateBase,
        "ToolTipBase": QPalette.ColorRole.ToolTipBase,
        "ToolTipText": QPalette.ColorRole.ToolTipText,
        "ButtonText": QPalette.ColorRole.ButtonText,
        "BrightText": QPalette.ColorRole.BrightText,
        "Midlight": QPalette.ColorRole.Midlight,
        "PlaceholderText": QPalette.ColorRole.PlaceholderText,
    }

    # Mapping from string names to QPalette.ColorGroup enums
    color_group_map = {
        "Disabled": QPalette.ColorGroup.Disabled,
        "Inactive": QPalette.ColorGroup.Inactive,
        "Active": QPalette.ColorGroup.Active,
    }

    # Essential roles to apply when apply_full_palette is False
    essential_roles = {
        "Text",
        "Base",
        "Window",
        "WindowText",
        "Button",
        "ButtonText",
        "Highlight",
        "HighlightedText",
        "Link",
        "LinkVisited",
        "AlternateBase",
        "ToolTipBase",
        "ToolTipText",
        "PlaceholderText",
    }

    for key, rgba_values in color_def.items():
        parts = key.split(".")
        if len(parts) == 2:
            # Format: "ColorGroup.ColorRole" (e.g., "Disabled.Text")
            group_name, role_name = parts
            color_group = color_group_map.get(group_name)
            color_role = color_role_map.get(role_name)
        else:
            # Format: "ColorRole" (e.g., "Base")
            role_name = parts[0]
            color_group = None  # All groups
            color_role = color_role_map.get(role_name)
        if color_role is None:
            continue

        if not apply_all and role_name not in essential_roles:
            continue

        if len(rgba_values) == 4:
            r, g, b, a = rgba_values
            color = QColor(r, g, b, a)
        elif len(rgba_values) == 3:
            r, g, b = rgba_values
            color = QColor(r, g, b)
        else:
            continue

        # Set the color in the palette
        if color_group is not None:
            palette.setColor(color_group, color_role, color)
        else:
            # Set for all color groups
            palette.setColor(color_role, color)

    return palette


class ExternalTheme:
    _qt_resource_struct: bytes = b""
    _qt_resource_name: bytes = b""
    _qt_resource_data: bytes = b""

    def __init__(self):
        raise RuntimeError("Static class cannot be initialised.")

    @staticmethod
    def set_resources(struct: bytes, name: bytes, data: bytes) -> None:
        ExternalTheme._qt_resource_struct = struct
        ExternalTheme._qt_resource_name = name
        ExternalTheme._qt_resource_data = data

    @staticmethod
    def register() -> bool:
        return qRegisterResourceData(
            0x03,
            ExternalTheme._qt_resource_struct,
            ExternalTheme._qt_resource_name,
            ExternalTheme._qt_resource_data,
        )

    @staticmethod
    def unregister() -> bool:
        result = qUnregisterResourceData(
            0x03,
            ExternalTheme._qt_resource_struct,
            ExternalTheme._qt_resource_name,
            ExternalTheme._qt_resource_data,
        )
        if result:
            ExternalTheme._qt_resource_struct = b""
            ExternalTheme._qt_resource_name = b""
            ExternalTheme._qt_resource_data = b""
            return True
        return False

    def has_data() -> bool:
        return (
            ExternalTheme._qt_resource_struct
            and ExternalTheme._qt_resource_name
            and ExternalTheme._qt_resource_data,
        )
