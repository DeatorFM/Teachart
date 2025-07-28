from sqlite3 import Time
from PyQt6.QtCore import QLocale
from PyQt6.QtWidgets import QDialog
from PyQt6.uic import loadUI
from dataclasses import dataclass
from enum import Enum, StrEnum, IntEnum, Flag
from typing import Self
import tomllib


def loadSettings() -> dict:
    with open("settings.toml", "r", encoding="utf-8") as f:
        settings = tomllib.load(f)
        return settings

def get(table: str, key=None|str):
    settings = loadSettings()
    try:
        if key != None:
            return settings[table][key]
        else: 
            return settings[table]
    except KeyError:
        return None
    
class SettingsReturnFlags(Flag):
    Invalid = 0
    Restart = 1
    UpdateLocale = 2
    UpdateStyle = 3


class SettingsDialog(QDialog):
    def __init__(self, parent = None, flags = ...):
        super().__init__(parent, flags)
        self.ui = loadUI("ui/settings.ui")
        self.settings = Settings()

# Constants

@dataclass(frozen=True)
class LocaleValue:
    name: str
    language: QLocale.Language
    region: QLocale.Country

class Locale(Enum):
    EnglishUK = LocaleValue("English (UK)", QLocale.Language.English, QLocale.Country.UnitedKingdom)
    German = LocaleValue("Deutsch", QLocale.Language.German, QLocale.Country.Germany)
    Japanese = LocaleValue("\u65E5\u672C\u8A9E", QLocale.Language.Japanese, QLocale.Country.Japan)

    def to_qlocale(self) -> QLocale:
        return QLocale(self.value.language, self.value.region)
    
    def to_int(self) -> int:
        return self.__class__._member_names_.index(self.name)
    
    @classmethod
    def from_int(cls, value: int) -> Self:
        try:
            return cls._value2member_map_[value]
        except IndexError:
            cls.EnglishUK

class TimeFormat(StrEnum):
    TF12 = "H:mm ap"
    TF24 = "HH:mm"

class Appearance(IntEnum):
    Light = 0
    Dark = 1

# Settings object classes

@dataclass
class Settings:
    apearance: Appearance
    language: Locale
    time_format: TimeFormat
    always_schedule: bool
    dbpath: str | None

@dataclass(frozen=True)
class Defaults:
    APPEARANCE: Appearance = Appearance.Light
    LOCALE: Locale = Locale.EnglishUK
    TIME_FORMAT: TimeFormat = TimeFormat.TF24
    ALWAYS_SCHEDULE: bool = False
    DBPATH: str | None = None