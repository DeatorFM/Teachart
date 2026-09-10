from __future__ import annotations

import copy
import platform
from xml.etree import ElementTree as ET

from PyQt6.QtCore import (
    QFile,
    QPoint,
    QRect,
    QRectF,
    QSize,
    Qt,
)
from PyQt6.QtGui import (
    QColor,
    QIcon,
    QIconEngine,
    QImage,
    QPainter,
    QPalette,
    QPixmap,
)
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QApplication, QProxyStyle, QStyleOption, QWidget
from styling.resources.standard import STANDARD_ICON_MAP, SVG_RESOURCES

ET.register_namespace("", "http://www.w3.org/2000/svg")


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
        palette = QApplication.palette()

        if mode == QIcon.Mode.Disabled:
            color = palette.color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text)
            print(color.name(QColor.NameFormat.HexArgb))
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

    @property
    def tree(self) -> ET.Element:
        return self._tree

    @classmethod
    def from_file(cls: Svg, path: str) -> Svg:
        path_obj = QFile(path)
        path_obj.open(QFile.OpenModeFlag.ReadOnly)
        return cls(path_obj.readAll().data().decode())

    def colored(self, color: QColor) -> Svg:
        hex_color = color.name(QColor.NameFormat.HexRgb)
        opacity = color.alphaF()

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

    @property
    def rotation(self) -> int:
        value = self._tree.get("transform")
        if value:
            cleaned = value.removeprefix("rotate(").strip("()")
            values = cleaned.split(",")
            if len(values) > 0:
                try:
                    return int(values[0])
                except (ValueError, TypeError):
                    pass
        return 0

    def __str__(self):
        return ET.tostring(self._tree)

    def to_string(self) -> bytes:
        return ET.tostring(self._tree, default_namespace="")
