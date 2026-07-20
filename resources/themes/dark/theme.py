from pathlib import Path

from PyQt6.QtGui import QRgba64

from tcha.styling import ColorModifier

PATH = Path("nativethemes/dark")


PALETTE_COLORS: dict[str, QRgba64] = {
    '<c k="border:base"/>': QRgba64.fromRgba(63, 64, 66, 255),
    '<c k="foreground:base" state="disabledSelectionBackground"/>': QRgba64.fromRgba(
        228, 231, 235, 51
    ),
    '<c k="background:base" state="popup"/>': QRgba64.fromRgba(32, 33, 36, 255),
    '<c k="background:base"/>': QRgba64.fromRgba(32, 33, 36, 255),
    '<c k="primary:base" state="list.inactiveSelectionBackground"/>': QRgba64.fromRgba(
        138, 180, 247, 38
    ),
    '<c k="foreground:base" state="input.placeholder"/>': QRgba64.fromRgba(
        228, 231, 235, 153
    ),
    '<c k="primary:base"/>': QRgba64.fromRgba(138, 180, 247, 255),
    '<c k="foreground:base" state="icon"/>': QRgba64.fromRgba(228, 231, 235, 255),
    '<c k="linkVisited"/>': QRgba64.fromRgba(197, 138, 248, 255),
    '<c k="foreground:base" state="disabled"/>': QRgba64.fromRgba(228, 231, 235, 102),
    '<c k="list.alternateBackground"/>': QRgba64.fromRgba(0, 0, 0, 12),
    '<c k="foreground:base"/>': QRgba64.fromRgba(228, 231, 235, 255),
    '<c k="treeSectionHeader.background"/>': QRgba64.fromRgba(63, 64, 66, 255),
}

THEME_COLORS = {
    "background": {
        "base": "#202124",
        "list": ColorModifier((0.0, 0.0, 0.0)),
        "panel": ColorModifier((0.0, 0.3, 0.0)),
        "popup": ColorModifier((0.0, 0.0, 0.3)),
        "table": ColorModifier((0.0, 0.5, 0.0)),
        "textarea": ColorModifier((0.0, 0.13, 0.0)),
        "title": ColorModifier((0.0, 0.3, 0.0)),
    },
    "border": {
        "base": "#3f4042",
        "input": ColorModifier((0.0, 0.0, 0.0)),
    },
    "foreground": {
        "base": "#e4e7eb",
        "defaultButton.disabledBackground": ColorModifier((0.2, 0.0, 0.0)),
        "disabled": ColorModifier((0.4, 0.0, 0.0)),
        "disabledSelectionBackground": ColorModifier((0.2, 0.0, 0.0)),
        "icon": ColorModifier((0.0, 0.01, 0.0)),
        "icon.unfocused": ColorModifier((0.6, 0.0, 0.0)),
        "input.placeholder": ColorModifier((0.6, 0.0, 0.0)),
        "progressBar.disabledBackground": ColorModifier((0.2, 0.0, 0.0)),
        "slider.disabledBackground": ColorModifier((0.2, 0.0, 0.0)),
        "sliderTrack.inactiveBackground": ColorModifier((0.1, 0.0, 0.0)),
    },
    "input.background": "#3f4042",
    "inputButton.hoverBackground": "#ffffff25",
    "linkVisited": "#c58af8",
    "list.alternateBackground": "#ffffff0c",
    "list.hoverBackground": "#ffffff13",
    "menubar.selectionBackground": "#ffffff25",
    "popupItem.checkbox.background": "#ffffff19",
    "popupItem.selectionBackground": "#ffffff22",
    "primary": {
        "base": "#8ab4f7",
        "button.activeBackground": ColorModifier((0.23, 0.14, 0.0)),
        "button.hoverBackground": ColorModifier((0.11, 0.1, 0.0)),
        "defaultButton.activeBackground": ColorModifier((0.0, 0.12, 0.0)),
        "defaultButton.hoverBackground": ColorModifier((0.0, 0.06, 0.0)),
        "list.inactiveSelectionBackground": ColorModifier((0.15, 0.0, 0.2)),
        "list.selectionBackground": ColorModifier((0.4, 0.2, 0.0)),
        "progressBar.background": ColorModifier((0.0, 0.1, 0.0)),
        "selection.background": ColorModifier((0.4, 0.2, 0.1)),
        "sliderHandle.activeBackground": ColorModifier((0.0, 0.09, 0.0)),
        "table.inactiveSelectionBackground": ColorModifier((0.18, 0.0, 0.2)),
        "table.selectionBackground": ColorModifier((0.55, 0.2, 0.0)),
        "textarea.selectionBackground": ColorModifier((0.4, 0.2, 0.1)),
    },
    "scrollbar.background": "#ffffff10",
    "scrollbarSlider.activeBackground": "#ffffff60",
    "scrollbarSlider.background": "#ffffff30",
    "scrollbarSlider.disabledBackground": "#ffffff15",
    "scrollbarSlider.hoverBackground": "#ffffff45",
    "statusBar.background": "#2a2b2e",
    "statusBarItem.activeBackground": "#ffffff34",
    "statusBarItem.hoverBackground": "#ffffff22",
    "tab.activeBackground": "#ffffff00",
    "tab.hoverBackground": "#ffffff18",
    "tabCloseButton.hoverBackground": "#ffffff25",
    "table.alternateBackground": "#ffffff15",
    "tableSectionHeader.background": "#3f4042",
    "textarea.inactiveSelectionBackground": "#ffffff20",
    "toolbar.activeBackground": "#ffffff34",
    "toolbar.background": "#333333",
    "toolbar.hoverBackground": "#ffffff22",
    "tree.inactiveIndentGuidesStroke": "#ffffff35",
    "tree.indentGuidesStroke": "#ffffff60",
    "treeSectionHeader.background": "#3f4042",
}

STYLESHEET = "dark.qss"

RCC = "dark.rcc"
