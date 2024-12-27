from dataclasses import dataclass
from enum import Enum
import tomlkit

def loadSettings() -> tomlkit.TOMLDocument:
    with open("settings.toml", "r", encoding="utf-8") as f:
        settings = tomlkit.load(f)
        return settings

def saveSettings(settings: tomlkit.TOMLDocument) -> None:
    with open("settings.toml", "w", encoding="utf-8") as f:
        tomlkit.dump(settings, f)

def get(table: str, key=None|str):
    settings = loadSettings()
    try:
        if key != None:
            return settings[table][key]
        else: 
            return settings[table]
    except tomlkit.exceptions.NonExistentKey:
        return None

# Constants

@dataclass(frozen=True)
class TimeFormat():
    TF12 = "H:mm ap"
    TF24 = "HH:mm"

@dataclass(frozen=True)
class DateFormat():
    DE = "dd.MM.yyyy"
    DMY = "dd/MM/yyyy"
    USA = "MM.dd.yyyy"
    ISO = "yyyy/MM/dd"

class Locale(Enum):
    EN = 1
    DE = 2
    JP = 3