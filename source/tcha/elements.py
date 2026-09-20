import importlib
from functools import cache

from nativeelements.baseelement import (
    BaseElementDefinitions,
    BaseElementToolset,
)
from PyQt6.QtCore import QMimeData

"""
Module to import element modules.
"""

# Change if new elements have been implemented
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


@cache
def get_all_definitions() -> dict[str, BaseElementDefinitions]:
    return {
        key: getattr(importlib.import_module(val["module"]), val["definitions"])
        for key, val in NATIVE_ELEMENTS.items()
    }


@cache
def compatible_mime_types() -> frozenset[str]:
    mime_types = set()
    definitions = get_all_definitions()
    for definition in definitions.values():
        def_mime_types = set(definition.mime_types())
        mime_types.symmetric_difference_update(def_mime_types)
    return frozenset(mime_types)


@cache
def get_definitions(name: str) -> BaseElementDefinitions | None:
    """Returns element definition of name 'name'. Returns None if definition does not exist."""
    try:
        return getattr(
            importlib.import_module(NATIVE_ELEMENTS[name]["module"]),
            NATIVE_ELEMENTS[name]["definitions"],
        )
    except AttributeError:
        return None


def definition_for_mime_data(mime_data: QMimeData) -> BaseElementDefinitions | None:
    """Return the element definition that supports the mime data"""
    definitions = get_all_definitions()
    for definition in definitions.values():
        if definition.supports_mime_data(mime_data):
            return definition
    return None


def get_toolsets() -> dict[str, BaseElementToolset]:
    """Returns all available toolsets as dictionary with element name as key and toolset as value."""
    return {
        key: getattr(importlib.import_module(val["module"]), val["definitions"])
        for key, val in NATIVE_ELEMENTS.items()
    }
