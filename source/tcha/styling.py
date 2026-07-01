from __future__ import annotations

import copy
import os
import os.path as osp
import platform
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import NewType
from xml.etree import ElementTree as ET

from PyQt6.QtCore import QFile, QPoint, QRect, QRectF, QSize, Qt, QXmlStreamWriter
from PyQt6.QtGui import (
    QColor,
    QGuiApplication,
    QIcon,
    QIconEngine,
    QImage,
    QPainter,
    QPalette,
    QPixmap,
    QRgba64,
)
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QProxyStyle, QStyleOption, QWidget

from resources.svg import STANDARD_ICON_MAP, SVG_RESOURCES

ColorModifier = NewType("ColorModifier", tuple[float, float, float])

ET.register_namespace("", "http://www.w3.org/2000/svg")


def make_palette(color_def: dict[str, QRgba64]) -> QPalette:
    palette = QPalette()
    # palette.setColor(
    #     QPalette.ColorRole.WindowText,
    #     QColor.fromRgba64(color_def.get('<c k="foreground:base"/>')),
    # )
    # palette.setColor(
    #     QPalette.ColorRole.Button,
    #     QColor.fromRgba64(color_def.get('<c k="treeSectionHeader.background"/>')),
    # )
    # palette.setColor(
    #     QPalette.ColorRole.ButtonText,
    #     QColor.fromRgba64(color_def.get('<c k="primary:base"/>')),
    # )
    # palette.setColor(
    #     QPalette.ColorRole.Base,
    #     QColor.fromRgba64(color_def.get('<c k="background:base"/>')),
    # )
    # palette.setColor(
    #     QPalette.ColorRole.Window,
    #     QColor.fromRgba64(color_def.get('<c k="background:base"/>')),
    # )
    # palette.setColor(
    #     QPalette.ColorRole.Highlight,
    #     QColor.fromRgba64(color_def.get('<c k="primary:base"/>')),
    # )
    # palette.setColor(
    #     QPalette.ColorRole.HighlightedText,
    #     QColor.fromRgba64(color_def.get('<c k="background:base"/>')),
    # )
    # palette.setColor(
    #     QPalette.ColorRole.AlternateBase,
    #     QColor.fromRgba64(color_def.get('<c k="list.alternateBackground"/>')),
    # )
    # palette.setColor(
    #     QPalette.ColorRole.ToolTipBase,
    #     QColor.fromRgba64(color_def.get('<c k="background:base" state="popup"/>')),
    # )
    # palette.setColor(
    #     QPalette.ColorRole.ToolTipText,
    #     QColor.fromRgba64(color_def.get('<c k="foreground:base"/>')),
    # )
    # if hasattr(QPalette.ColorRole, "Foreground"):
    #     palette.setColor(
    #         QPalette.ColorRole.Foreground,  # type: ignore
    #         QColor.fromRgba64(color_def.get('<c k="foreground:base"/>')),
    #     )

    # palette.setColor(
    #     QPalette.ColorRole.Light,
    #     QColor.fromRgba64(color_def.get('<c k="border:base"/>')),
    # )
    # palette.setColor(
    #     QPalette.ColorRole.Midlight,
    #     QColor.fromRgba64(color_def.get('<c k="border:base"/>')),
    # )
    # palette.setColor(
    #     QPalette.ColorRole.Dark,
    #     QColor.fromRgba64(color_def.get('<c k="background:base"/>')),
    # )
    # palette.setColor(
    #     QPalette.ColorRole.Mid, QColor.fromRgba64(color_def.get('<c k="border:base"/>'))
    # )
    # palette.setColor(
    #     QPalette.ColorRole.Shadow,
    #     QColor.fromRgba64(color_def.get('<c k="border:base"/>')),
    # )

    # # disabled
    # palette.setColor(
    #     QPalette.ColorGroup.Disabled,
    #     QPalette.ColorRole.WindowText,
    #     QColor.fromRgba64(color_def.get('<c k="foreground:base" state="disabled"/>')),
    # )
    # palette.setColor(
    #     QPalette.ColorGroup.Disabled,
    #     QPalette.ColorRole.ButtonText,
    #     QColor.fromRgba64(color_def.get('<c k="foreground:base" state="disabled"/>')),
    # )
    # palette.setColor(
    #     QPalette.ColorGroup.Disabled,
    #     QPalette.ColorRole.Highlight,
    #     QColor.fromRgba64(
    #         color_def.get(
    #             '<c k="foreground:base" state="disabledSelectionBackground"/>'
    #         )
    #     ),
    # )
    # palette.setColor(
    #     QPalette.ColorGroup.Disabled,
    #     QPalette.ColorRole.HighlightedText,
    #     QColor.fromRgba64(color_def.get('<c k="foreground:base" state="disabled"/>')),
    # )

    # # inactive
    # palette.setColor(
    #     QPalette.ColorGroup.Inactive,
    #     QPalette.ColorRole.Highlight,
    #     QColor.fromRgba64(
    #         color_def.get(
    #             '<c k="primary:base" state="list.inactiveSelectionBackground"/>'
    #         )
    #     ),
    # )
    # palette.setColor(
    #     QPalette.ColorGroup.Inactive,
    #     QPalette.ColorRole.HighlightedText,
    #     QColor.fromRgba64(color_def.get('<c k="foreground:base"/>')),
    # )

    palette.setColor(
        QPalette.ColorRole.Text,
        QColor.fromRgba64(color_def.get('<c k="foreground:base" state="icon"/>')),
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.Text,
        QColor.fromRgba64(color_def.get('<c k="foreground:base" state="disabled"/>')),
    )
    palette.setColor(
        QPalette.ColorRole.Link,
        QColor.fromRgba64(color_def.get('<c k="primary:base"/>')),
    )
    palette.setColor(
        QPalette.ColorRole.LinkVisited,
        QColor.fromRgba64(color_def.get('<c k="linkVisited"/>')),
    )
    if hasattr(QPalette.ColorRole, "PlaceholderText"):
        palette.setColor(
            QPalette.ColorRole.PlaceholderText,
            QColor.fromRgba64(
                color_def.get('<c k="foreground:base" state="input.placeholder"/>')
            ),
        )

    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.Link,
        QColor.fromRgba64(
            color_def.get(
                '<c k="foreground:base" state="disabledSelectionBackground"/>'
            )
        ),
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.LinkVisited,
        QColor.fromRgba64(color_def.get('<c k="foreground:base" state="disabled"/>')),
    )

    return palette


def transform_color(color: QColor, alteration: tuple[int, int, int]) -> QColor:
    """Applies the transformation values to a QColor class."""
    for i, val in enumerate(alteration):
        if val > 0.0:
            if i == 0:
                color.setAlphaF(val)
            elif i == 1:
                color = color.darker(int(val))
            elif i == 3:
                color = color.lighter(int(val))
    return Color(color)


def get_color(color_val: str, color_state: tuple[int, int, int]) -> str:
    color = Color.fromString(color_val)
    color = transform_color(color, color_state)
    return color


def cmp_os(os_: str) -> bool:
    if os_.lower() == sys.platform:
        return True
    return False


class Color(QColor):
    @classmethod
    def from_hex(cls: Color, hex_color: str) -> Color:
        """Converts hex color with or without color value to Color object."""
        clean_str = hex_color.lstrip("#")
        if len(clean_str) > 6:
            color = f"#{clean_str[:5]}"
            alpha = int(f"0x{clean_str[-2:]}", base=16)
            # print("Color:", color)
            # print("Alpha:", alpha)
            color_obj = cls(color)
            color_obj.setAlpha(alpha)
            return color_obj
        else:
            return Color(f"#{clean_str}")

    def to_hex(self) -> str:
        """Converts to string with Format #RRGGBBAA"""
        return "#{r:0<2}{g:0<2}{b:0<2}".format(
            r=hex(self.red())[2:], g=hex(self.green())[2:], b=hex(self.blue())[2:]
        )

    def to_hex_rgba(self) -> str:
        return "#{r:0<2}{g:0<2}{b:0<2}{alpha:0<2}".format(
            r=hex(self.red())[2:],
            g=hex(self.green())[2:],
            b=hex(self.blue())[2:],
            alpha=hex(self.alpha())[2:],
        )

    def to_rgba(self) -> str:
        return f"rgba({self.red()}, {self.green()}, {self.blue()}, {self.alpha()})"


@dataclass(frozen=True)
class Placeholder:
    match_text: str
    dom: ET.Element


class QssTemplate:
    _TEMPLATE_XML = re.compile(r"\<t\>.*?\</t\>")

    def __init__(self, template: str, color_def: dict, icon_path: str | None = None):
        self._template = template
        self._color_def = color_def
        if icon_path:
            self._icon_cache = icon_path
        else:
            self._icon_cache = tempfile.mkdtemp()

    @property
    def icon_dir(self) -> None:
        return self._icon_cache

    @staticmethod
    def parse_xmls(raw_elements: set[str]) -> set[Placeholder]:
        """Makes a set of Placholder objects containing the xml-string and the an Element object from the first subelement: c, img, env..."""
        placeholders: set[Placeholder] = set()
        for element in raw_elements:
            inner_xml = element[3:-4]
            xml_element = ET.fromstring(inner_xml)
            placeholders.add(Placeholder(element, xml_element))
        return placeholders

    def get_color(self, xml: ET.Element) -> Color:
        raw_key = xml.get("k")
        key, subkey = raw_key.split(":") if ":" in raw_key else (raw_key, None)
        state = xml.get("state")
        if subkey:
            color_str = self._color_def[key][subkey]
        else:
            color_str = self._color_def[key]
        color = Color.from_hex(color_str)

        if state:
            modifiers: tuple[int, int, int] = self._color_def[key][state]
            color = transform_color(color, modifiers)

        return color

    def _parse_color(self, xml: ET.Element) -> str:
        color = self.get_color(xml)
        return color.to_rgba()

    def _parse_img(self, xml: ET.Element) -> str:
        color = None
        for child in xml:
            if child.tag == "c":
                color = self.get_color(child)
            elif child.tag == "url" and color:
                id = child.get("id")
                rotate = int(child.get("rotate", 0))
                svg = Svg(SVG_RESOURCES[id]).colored(color).rotated(rotate)
                filename = f"{id}_{color.to_hex_rgba()}_{rotate}.svg"
                path = Path(self._icon_cache) / filename
                path.write_bytes(svg.to_string())

        return f"url(:/{filename})"

    def _parse_env(self, xml: ET.Element) -> None:
        if xml.tag == "env":
            else_val = xml.find("else")
            for child in xml:
                if child.tag == "if":
                    os = child.get("os")
                    if cmp_os(os):
                        return child.get("value")

            if else_val:
                return else_val.get("value")
            return ""

        raise ValueError("Xml element's tag not 'env'.")

    def compile_stylesheet(self) -> str:
        """Compiles the stylesheet and saves it to the location at 'path'."""
        template: str = self._template
        raw_placeholders = set(re.findall(QssTemplate._TEMPLATE_XML, self._template))
        placeholders = QssTemplate.parse_xmls(raw_placeholders)
        for placeholder in placeholders:
            match placeholder.dom.tag:
                case "c":  # Color attribute
                    replacement = self._parse_color(placeholder.dom)
                case "img":  # Image url()
                    replacement = self._parse_img(placeholder.dom)
                case "env":  # Conditional attribute due to OS and version.
                    replacement = self._parse_env(placeholder.dom)
                case _:
                    raise AttributeError(
                        f"Xml attribute {placeholder.dom.tag} could not be identified."
                    )
            template = template.replace(placeholder.match_text, replacement)
        return template

    def write_qrc(self, filename: str) -> None:
        """Writes qrc-file containing all compiled icons that can by converted by 'pyside6-rcc'."""
        f = QFile(filename)
        f.open(QFile.OpenModeFlag.WriteOnly)
        writer = QXmlStreamWriter(f)
        writer.writeStartElement("RCC")
        writer.writeStartElement("qresource")
        for filename in os.listdir(self._icon_cache):
            print(f"Write {filename}")
            writer.writeStartElement("file")
            writer.writeAttribute("alias", osp.basename(filename))
            writer.writeCharacters(f"{self._icon_cache}/{filename}")
            writer.writeEndElement()
        writer.writeEndElement()
        writer.writeEndElement()


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

    def paint(
        self, painter: QPainter, rect: QRect, mode: QIcon.Mode, state: QIcon.State
    ):
        # Work with a deep copy to avoid mutating the original SVG
        svg = Svg(copy.deepcopy(self._svg._tree))

        if self._paths:
            for path in self._paths.keys():
                svg = svg.path_colored(path, self._paths[path])

        """Paint the icon int ``rect`` using ``painter``."""
        palette = QGuiApplication.palette()

        if mode == QIcon.Mode.Disabled:
            color = palette.color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text)
        else:
            color = palette.text().color()
        # print("Color", color.name(), color.alpha())
        svg = svg.colored(color)

        svg_byte = svg.to_string()
        # print(svg_byte)
        renderer = QSvgRenderer(svg_byte)
        # print("Svg is valid ", renderer.isValid())
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
        path_obj = Path(path)
        return cls(path_obj.read_text("utf-8"))

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
