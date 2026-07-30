import json
import zipfile
from importlib import import_module

from PyQt6.QtCore import (
    QByteArray,
    QDataStream,
    QIODevice,
    QResource,
    qChecksum,
    qRegisterResourceData,
)
from PyQt6.QtWidgets import QApplication
from tcha.consts import RESOURCE_PATH
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
        import_module(f"themes.{name}")
        stylesheets_path = RESOURCE_PATH / "themes" / name / f"{name}.qss"
        app.setStyleSheet(stylesheets_path.read_text())

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
                qRegisterResourceData(0x03, qt_resource_data, qt_resource_name, qt_resource_struct)
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
