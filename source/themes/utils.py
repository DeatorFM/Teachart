import json
import zipfile
from importlib import import_module
from xml.etree import ElementTree as ET

from PyQt6.QtCore import (
    QByteArray,
    QDataStream,
    QIODevice,
    qChecksum,
    qRegisterResourceData,
    qUnregisterResourceData,
    QRect,
    QRectF,
    Qt
)
from PyQt6.QtGui import QPalette, QIcon, QIconEngine, QProxyStyle, QPainter, QColor, QImage, QPixmap, QStyleOption
from PyQt6.QtWidgets import QApplication, QWidget
from tcha.error import BinReadError
from tcha.settings import Values
from tcha.styling import make_palette
from themes.properties import NTHEME_PROPERTIES
from themes.resources.common import SVG_RESOURCES, STANDARD_ICON_MAP

ET.register_namespace("", "http://www.w3.org/2000/svg")


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
        import_module(f"themes.resources.{name}")

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


def apply_style(app: QApplication) -> None:
    if isinstance(app.style(), TchaProxyStyle):
        app.style().polish()
    else:
        style = TchaProxyStyle()
        app.setStyle(style)


class TchaProxyStyle(QProxyStyle):
    """Style proxy adapted from QDarkTheme"""

    def standardIcon(
        self,
        standardIcon: QProxyStyle.StandardPixmap,
        option: QStyleOption | None = None,
        widget: QWidget | None = None,
    ) -> QIcon:
        icon_info = STANDARD_ICON_MAP.get(standardIcon)
        if icon_info is None:
            return super().standardIcon(standardIcon, option, widget)

        os_list = icon_info.get("os")
        if os_list is not None and platform.system() not in os_list:
            return super().standardIcon(standardIcon, option, widget)

        rotate = icon_info.get("rotate", 0)
        svg = Svg(SVG_RESOURCES[icon_info["id"]]).rotated(rotate)
        icon_engine = SvgIconEngine(svg)
        return QIcon(icon_engine)


class SvgIcon(QIcon):
    def __init__(self, path: str) -> None:
        engine = SvgIconEngine(Svg.from_file(path))
        super().__init__(engine)


class SvgIconEngine(QIconEngine):
    """Custom Engine to alter and render icons adapted from QDarkTheme."""

    def __init__(self, svg: Svg) -> None:
        super().__init__()
        self._svg = svg
        self._paths: dict[str, QColor] = {}

    def paint(self, painter: QPainter, rect: QRect, mode: QIcon.Mode, state: QIcon.State):
        # Work with a deep copy to avoid mutating the original SVG
        svg = Svg(copy.deepcopy(self._svg._tree))

        if self._paths:
            for path in self._paths:
                svg = svg.path_colored(path, self._paths[path])

        """Paint the icon int ``rect`` using ``painter``."""
        palette = QGuiApplication.palette()

        if mode == QIcon.Mode.Disabled:
            color = palette.color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text)
        else:
            color = palette.text().color()
        svg = svg.colored(color)

        svg_byte = svg.to_string()
        renderer = QSvgRenderer(svg_byte)
        renderer.render(painter, QRectF(rect))

    def set_path_color(self, id: str, color: QColor) -> None:
        self._paths[id] = color

    def clone(self):
        """Required to subclass abstract QIconEngine."""
        return SvgIconEngine(self._svg)

    def pixmap(self, size: QSize, mode: QIcon.Mode, state: QIcon.State):
        """Return the icon as a pixmap with requested size, mode, and state."""
        # Make size to square.
        min_size = min(size.width(), size.height())
        size.setHeight(min_size)
        size.setWidth(min_size)

        img = QImage(size, QImage.Format.Format_ARGB32)
        img.fill(Qt.GlobalColor.transparent)
        pixmap = QPixmap.fromImage(img, Qt.ImageConversionFlag.NoFormatConversion)
        size.width()
        self.paint(QPainter(pixmap), QRect(QPoint(0, 0), size), mode, state)
        return pixmap


class Svg:
    def __init__(self, source: str | ET.Element) -> None:
        if isinstance(source, str):
            self._tree = ET.fromstring(source)
        elif isinstance(source, ET.Element):
            self._tree = source
        else:
            raise TypeError(
                "Source must be either string containing xml or ElementTree.Element object."
            )

    @classmethod
    def from_file(cls: Svg, path: str) -> Svg:
        path_obj = QFile(path)
        opened = path_obj.open(QFile.OpenModeFlag.ReadOnly)
        return cls(path_obj.readAll().data().decode())

    def colored(self, color: QColor) -> Svg:
        hex_color = color.name(QColor.NameFormat.HexRgb)
        opacity = color.alphaF()
        # print(opacity)

        tree = copy.deepcopy(self._tree)

        tree.set("fill", hex_color)

        if opacity < 1.0:
            tree.set("fill-opacity", str(opacity))
        else:
            tree.attrib.pop("fill-opacity,", None)

        return Svg(ET.tostring(tree, "unicode"))

    def path_colored(self, id: str, color: QColor) -> Svg:
        """Returns a Svg object with only the path elements with the given id coloured."""
        hex_color = color.name(QColor.NameFormat.HexRgb)
        opacity = color.alphaF()

        tree = copy.deepcopy(self._tree)

        for child in tree:
            if child.get("id") == id:
                child.set("fill", hex_color)

        if opacity < 1.0:
            for child in tree:
                if child.get("id") == id:
                    child.set("fill-opacity", str(opacity))

        return Svg(ET.tostring(tree, "unicode"))

    def rotated(self, rotation: int | None) -> Svg:
        tree = copy.deepcopy(self._tree)
        if rotation == 0 or rotation is None:
            return Svg(tree)

        tree.set("transform", f"rotate({rotation}, 12, 12)")

        return Svg(ET.tostring(tree, "unicode"))

    def __str__(self):
        return ET.tostring(self._tree)

    def to_string(self) -> bytes:
        return ET.tostring(self._tree, default_namespace="")

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
