import json
import zipfile
from importlib import import_module

from PyQt6.QtCore import (
    QByteArray,
    QDataStream,
    QIODevice,
    qChecksum,
    qRegisterResourceData,
    qUnregisterResourceData,
)
from PyQt6.QtWidgets import QApplication
from tcha.error import BinReadError
from tcha.settings import Values
from tcha.styling import make_palette
from themes.properties import NTHEME_PROPERTIES


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

        # result = QResource.registerResource(
        #     str(RESOURCE_PATH / "themes" / "compiled" / f"{name}.rcc")
        # )
        # print(f"Loaded RCC: {result}")
        if ExternalTheme.has_data():
            ExternalTheme.unregister()
        import_module(f"themes.{name}")

        from themes.stylesheets import STYLESHEETS

        app.setStyleSheet(STYLESHEETS[name])

        return True

    load_theme(Values.default_value("User/appearance"), app)


def _load_extern_theme(fname: str, app: QApplication) -> bool:
    from tcha.settings import Settings

    taste_file = Settings.user_path() / "themes" / f"{fname}.taste"
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


class ExternalTheme:
    _qt_resource_struct: bytes = b""
    _qt_resource_name: bytes = b""
    _qt_resource_data: bytes = b""

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
