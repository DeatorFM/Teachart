from functools import lru_cache
from pathlib import Path

from PyQt6.QtGui import QPalette, QRgba64

from resources.palette import make_palette
from tcha.styling import ColorModifier

PATH = Path("nativethemes/light")

PALETTE_COLORS: dict[str, QRgba64] = {
    '<c k="treeSectionHeader.background"/>': QRgba64.fromRgba64(218, 220, 224, 255),
    '<c k="primary:base" state="list.inactiveSelectionBackground"/>': QRgba64.fromRgba64(
        26, 115, 232, 23
    ),
    '<c k="background:base"/>': QRgba64.fromRgba64(248, 249, 250, 255),
    '<c k="foreground:base" state="input.placeholder"/>': QRgba64.fromRgba64(
        77, 81, 87, 153
    ),
    '<c k="foreground:base" state="disabledSelectionBackground"/>': QRgba64.fromRgba64(
        77, 81, 87, 64
    ),
    '<c k="border:base"/>': QRgba64.fromRgba64(218, 220, 224, 255),
    '<c k="foreground:base" state="disabled"/>': QRgba64.fromRgba64(77, 81, 87, 102),
    '<c k="list.alternateBackground"/>': QRgba64.fromRgba64(0, 0, 0, 9),
    '<c k="primary:base"/>': QRgba64.fromRgba64(26, 115, 232, 255),
    '<c k="foreground:base"/>': QRgba64.fromRgba64(77, 81, 87, 255),
    '<c k="linkVisited"/>': QRgba64.fromRgba64(102, 0, 152, 255),
    '<c k="foreground:base" state="icon"/>': QRgba64.fromRgba64(77, 81, 87, 255),
    '<c k="background:base" state="popup"/>': QRgba64.fromRgba64(248, 249, 250, 255),
}

THEME_COLORS = {
    "background": {
        "base": "#f8f9fa",
        "list": ColorModifier(0.0, 0.0, 0.0),
        "panel": ColorModifier(0.0, 0.0, 0.5),
        "popup": ColorModifier(0.0, 0.0, 0.2),
        "table": ColorModifier(0.0, 0.0, 0.5),
        "textarea": ColorModifier(0.0, 0.0, 0.25),
        "title": ColorModifier(0.0, 0.04, 0.0),
    },
    "border": {
        "base": "#dadce0",
        "input": ColorModifier(0.0, 0.0, 0.0),
    },
    "foreground": {
        "base": "#4d5157",
        "defaultButton.disabledBackground": ColorModifier(0.25, 0.0, 0.0),
        "disabled": ColorModifier(0.4, 0.0, 0.0),
        "disabledSelectionBackground": ColorModifier(0.25, 0.0, 0.0),
        "icon": ColorModifier(0.0, 0.05, 0.0),
        "icon.unfocused": ColorModifier(0.6, 0.0, 0.0),
        "input.placeholder": ColorModifier(0.6, 0.0, 0.0),
        "progressBar.disabledBackground": ColorModifier(0.25, 0.0, 0.0),
        "slider.disabledBackground": ColorModifier(0.25, 0.0, 0.0),
        "sliderTrack.inactiveBackground": ColorModifier(0.2, 0.0, 0.0),
    },
    "input.background": "#f8f9fa",
    "inputButton.hoverBackground": "#00000018",
    "linkVisited": "#660098",
    "list.alternateBackground": "#00000009",
    "list.hoverBackground": "#00000013",
    "menubar.selectionBackground": "#00000020",
    "popupItem.checkbox.background": "#00000019",
    "popupItem.selectionBackground": "#00000022",
    "primary": {
        "base": "#1a73e8",
        "button.activeBackground": ColorModifier(0.24, 0.03, 0.0),
        "button.hoverBackground": ColorModifier(0.1, 0.03, 0.0),
        "defaultButton.activeBackground": ColorModifier(0.0, 0.0, 0.3),
        "defaultButton.hoverBackground": ColorModifier(0.0, 0.0, 0.1),
        "list.inactiveSelectionBackground": ColorModifier(0.09, 0.43, 0.0),
        "list.selectionBackground": ColorModifier(0.35, 0.0, 0.2),
        "progressBar.background": ColorModifier(0.0, 0.0, 0.2),
        "selection.background": ColorModifier(0.5, 0.0, 0.3),
        "sliderHandle.activeBackground": ColorModifier(0.0, 0.0, 0.2),
        "table.inactiveSelectionBackground": ColorModifier(0.09, 0.43, 0.0),
        "table.selectionBackground": ColorModifier(0.5, 0.0, 0.1),
        "textarea.selectionBackground": ColorModifier(0.5, 0.0, 0.3),
    },
    "scrollbar.background": "#00000010",
    "scrollbarSlider.activeBackground": "#00000060",
    "scrollbarSlider.background": "#00000040",
    "scrollbarSlider.disabledBackground": "#00000015",
    "scrollbarSlider.hoverBackground": "#00000050",
    "statusBar.background": "#dfe1e5",
    "statusBarItem.activeBackground": "#00000024",
    "statusBarItem.hoverBackground": "#00000015",
    "tab.activeBackground": "#00000000",
    "tab.hoverBackground": "#00000015",
    "tabCloseButton.hoverBackground": "#00000020",
    "table.alternateBackground": "#00000012",
    "tableSectionHeader.background": "#dadce0",
    "textarea.inactiveSelectionBackground": "#00000015",
    "toolbar.activeBackground": "#00000024",
    "toolbar.background": "#ebebeb",
    "toolbar.hoverBackground": "#00000015",
    "tree.inactiveIndentGuidesStroke": "#00000030",
    "tree.indentGuidesStroke": "#00000050",
    "treeSectionHeader.background": "#dadce0",
}

STYLESHEET = "light.qss"

RCC = "light.rcc"


def palette() -> QPalette:
    return make_palette(PALETTE_COLORS)


@lru_cache
def stylesheet() -> str:
    stylesheet_path = PATH / "light.qss"
    return stylesheet_path.read_text()


@lru_cache
def rcc() -> bytes:
    rcc_path = PATH / "light.rcc"
    return rcc_path.read_bytes()
