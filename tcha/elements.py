import importlib

from PyQt6.QtCore import QByteArray, QDataStream

from nativeelements.baseelement import (
    BaseElementDefinitions,
    BaseElementModel,
    BaseElementToolset,
)

"""
Module to import element modules.
"""

NATIVE_ELEMENTS = {
    "TextElement": {
        "module": "nativeelements.textelement",
        "definitions": "TextElementDefinitions",
        "model": "TextModel",
        "editor": "TextEditor",
        "delegate": "TextDelegate",
        "toolset": "TextToolset",
    },
    "PictureElement": {
        "module": "nativeelements.pictureelement",
        "definitions": "PictureElementDefinitions",
        "model": "PictureModel",
        "editor": "PictureEditor",
        "delegate": "PictureDelegate",
        "toolset": "PictureToolset",
    },
    "AudioElement": {
        "module": "nativeelements.audioelement",
        "definitions": "AudioElementDefinitions",
        "model": "AudioModel",
        "editor": "AudioEditor",
        "delegate": "AudioDelegate",
        "toolset": "AudioToolset",
    },
}

# Native elements' getters


def get_all_definitions() -> dict[str, BaseElementDefinitions]:
    return {
        key: getattr(importlib.import_module(val["module"]), val["definitions"])
        for key, val in NATIVE_ELEMENTS.items()
    }


def get_definitions(name: str) -> BaseElementDefinitions | None:
    try:
        return getattr(
            importlib.import_module(NATIVE_ELEMENTS[name]["module"]),
            NATIVE_ELEMENTS[name]["definitions"],
        )
    except AttributeError:
        return None


def get_toolsets() -> dict[str, BaseElementToolset]:
    return {
        key: getattr(importlib.import_module(val["module"]), val["definitions"])
        for key, val in NATIVE_ELEMENTS.items()
    }
