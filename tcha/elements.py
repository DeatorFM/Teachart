from nativeelements.baseelement import BaseElementDefinitions, BaseElementToolset
import importlib

"""
Module to import element modules.
"""
global NATIVE_ELEMENTS
NATIVE_ELEMENTS = {
    "TextElement" : {
        "module" : "nativeelements.textelement",
        "definitions" : "TextElementDefinitions",
        "model" : "TextModel",
        "editor" : "TextEditor",
        "delegate" : "TextDelegate",
        "toolset" : "TextToolset"
    },
    "PictureElement" : {
        "module" : "nativeelements.pictureelement",
        "definitions" : "PictureElementDefinitions",
        "model" : "PictureModel",
        "editor" : "PictureEditor",
        "delegate" : "PictureDelegate",
        "toolset" : "PictureToolset"
    },
    "AudioElement" : {
        "module" : "nativeelements.audioelement",
        "definitions" : "AudioElementDefinitions",
        "model" : "AudioModel",
        "editor" : "AudioEditor",
        "delegate" : "AudioDelegate",
        "toolset" : "AudioToolset"
    }
}

# Native elements' getters

def get_all_definitions() -> dict[str, BaseElementDefinitions]:
    return {key : getattr(importlib.import_module(val["module"]), val["definitions"]) for key, val in NATIVE_ELEMENTS.items()}

def get_definitions(name: str) -> BaseElementDefinitions:
    return getattr(importlib.import_module(NATIVE_ELEMENTS[name]["module"]), NATIVE_ELEMENTS[name]["definitions"])

def get_toolsets() -> dict[str, BaseElementToolset]:
    return {key : getattr(importlib.import_module(val["module"]), val["definitions"]) for key, val in NATIVE_ELEMENTS.items()}