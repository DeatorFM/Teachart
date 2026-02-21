from dataclasses import asdict, dataclass, field, fields, make_dataclass
from enum import Enum, Flag, IntEnum, StrEnum
from os.path import abspath, dirname, exists
from typing import Any, Callable, Self

import PyQt6.uic as uic
from PyQt6.QtCore import QT_TR_NOOP as tr
from PyQt6.QtCore import QLocale, QSettings, Qt
from PyQt6.QtSql import QSqlDatabase
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QMessageBox,
    QWidget,
)

from tcha.dbmodels import create_database, reset_database

# Constants


@dataclass(frozen=True)
class LocaleValue:
    name: str
    language: QLocale.Language
    region: QLocale.Country

    def __str__(self):
        return self.name


class Locale(Enum):
    EnglishUK = LocaleValue(
        "English (UK)", QLocale.Language.English, QLocale.Country.UnitedKingdom
    )
    German = LocaleValue("Deutsch", QLocale.Language.German, QLocale.Country.Germany)
    Japanese = LocaleValue("日本語", QLocale.Language.Japanese, QLocale.Country.Japan)

    def to_qlocale(self) -> QLocale:
        return QLocale(self.value.language, self.value.region)

    def to_int(self) -> int:
        return self.__class__._member_names_.index(self.name)

    @classmethod
    def from_int(cls, i: int) -> Self:
        """Returns the value on the 'i'th place in initialisation order."""
        try:
            return list(cls)[i]
        except IndexError:
            cls.EnglishUK


class TimeFormat(StrEnum):
    TF24 = "HH:mm"
    TF12 = "H:mm ap"


class Appearance(IntEnum):
    Light = 0
    Dark = 1
    System = 2


class ReturnFlags(Flag):
    Invalid = 0
    Restart = 1
    UpdateLocale = 2
    UpdateStyle = 3


class SettingsDialog(QDialog):
    def __init__(
        self,
        db: QSqlDatabase,
        qsettings: QSettings,
        parent=None,
        flags=Qt.WindowType.Dialog,
    ):
        super().__init__(parent, flags)
        self.ui = uic.loadUi("ui/settings.ui", self)
        self.qsettings = qsettings
        self.database: QSqlDatabase = db
        self.settings = Settings.read_settings(qsettings)
        self._return_flag: ReturnFlags = ReturnFlags.Invalid
        self._settings_map: dict[str, Callable] = {
            "appearance": self._tick_appearance,
            "language": self._select_language,
            "time_format": self._select_time_format,
            "always_schedule": self._tick_always_schedule,
            "dbpath": self._set_dblocation,
        }
        self._import_options()
        self._set_ui_for_values()
        self.connect_signals()

    def connect_signals(self) -> None:
        self.ui.rb_light.toggled.connect(lambda: self.set_appearance(Appearance.Light))
        self.ui.rb_dark.toggled.connect(lambda: self.set_appearance(Appearance.Dark))
        self.ui.cb_language.activated.connect(self.set_language)
        self.ui.cb_time_format.activated.connect(self.set_time_format)
        self.ui.cb_always_schedule.toggled.connect(self.set_always_schedule)
        self.ui.pb_file_dialog.clicked.connect(self.set_dbpath)
        self.ui.pb_new_database.clicked.connect(self.create_new_db)
        self.ui.pb_reset_database.clicked.connect(self.reset_db)
        self.ui.settings_buttonbox.clicked.connect(self._handle_button)

    def _handle_button(self, button: QDialogButtonBox.StandardButton) -> None:
        if (
            self.ui.settings_buttonbox.standardButton(button)
            == QDialogButtonBox.StandardButton.Apply
        ):
            self.accept()
        elif (
            self.ui.settings_buttonbox.standardButton(button)
            == QDialogButtonBox.StandardButton.Cancel
        ):
            self.reject()
        elif (
            self.ui.settings_buttonbox.standardButton(button)
            == QDialogButtonBox.StandardButton.RestoreDefaults
        ):
            self.restore_defaults()

    @staticmethod
    def get_settings(
        parent: QWidget | None, db: QSqlDatabase, qsettings: QSettings
    ) -> ReturnFlags:
        dialog = SettingsDialog(db, qsettings, parent)
        code = dialog.exec()
        if code == QDialog.DialogCode.Accepted:
            return dialog._return_flag
        return ReturnFlags.Invalid

    def done(self, a0: int):
        print("Last Settings", self.settings)
        if a0 == QDialog.DialogCode.Accepted:
            self.save_all()
        return super().done(a0)

    # UI setup to settings

    def _import_options(self) -> None:
        """Populates combo boxes for language and time format"""
        for value in Locale.__members__.values():
            self.ui.cb_language.addItem(value.name, value)

        self.ui.cb_time_format.addItem("24h", TimeFormat.TF24)
        self.ui.cb_time_format.addItem("12h", TimeFormat.TF12)

    def _set_ui_for_values(self) -> None:
        """Makes UI reflect the settings' values"""
        for key, value in asdict(self.settings).items():
            print(key, value)
            self._settings_map[key](value)

    def _tick_appearance(self, value: Appearance | int) -> None:
        """Set appearance option based on Appearance value or int."""
        if value == Appearance.Light:
            self.ui.rb_light.setChecked(True)
        elif value == Appearance.Dark:
            self.ui.rb_dark.setChecked(True)
        else:
            self.ui.rb_dark.setChecked(True)

    def _select_language(self, locale: Locale) -> None:
        """Set language ComboBox for Locale value"""
        assert isinstance(self.ui.cb_language, QComboBox)
        idx = self.ui.cb_language.findData(locale)
        self.ui.cb_language.setCurrentIndex(idx)

    def _select_time_format(self, tformat: TimeFormat) -> None:
        assert isinstance(self.ui.cb_time_format, QComboBox)
        idx = self.ui.cb_time_format.findData(tformat)
        self.ui.cb_time_format.setCurrentIndex(idx)

    def _tick_always_schedule(self, ticked: bool) -> None:
        self.ui.cb_always_schedule.setChecked(ticked)

    def _set_dblocation(self, path: str) -> None:
        self.ui.le_path.setText(path)

    # Setter methods

    def set_appearance(self, value: Appearance) -> None:
        self.settings.appearance = value
        self._return_flag |= ReturnFlags.UpdateStyle

    def set_language(self) -> None:
        self.settings.language = self.ui.cb_language.currentData()
        self._return_flag |= ReturnFlags.UpdateLocale

    def set_time_format(self) -> None:
        self.settings.time_format = self.ui.cb_time_format.currentData()
        self._return_flag |= ReturnFlags.UpdateLocale

    def set_always_schedule(self) -> None:
        self.settings.always_schedule = self.ui.cb_always_schedule.isChecked()

    # Database settings

    def set_dbpath(self) -> None:
        if self.settings.dbpath and exists(self.settings.dbpath):
            path, _ = QFileDialog.getOpenFileName(
                self,
                tr("Open Lesson Database"),
                dirname(self.settings.dbpath),
            )
        else:
            path, _ = QFileDialog.getOpenFileName(
                self, tr("Open Lesson Database"), "/home", "Database files (*.db)"
            )
        self.settings.dbpath = path
        self.ui.le_path.setText(path)
        self._return_flag |= ReturnFlags.Restart

    def create_new_db(self) -> None:
        """Creates new database file without deleting the old one in the standard folder and sets it as the used database."""
        db = create_database(Defaults.AppInfo.app_ver)
        self.settings.dbpath = abspath(db.databaseName())
        self.ui.le_path.setText(self.settings.dbpath)
        self._return_flag |= ReturnFlags.Restart

    def reset_db(self) -> None:
        """Deletes all data from the database in dbpath."""
        response = QMessageBox.question(
            self,
            tr("Resetting database"),
            tr(
                "Resetting the database will delete all course, schedule and student record.\nDo you still want to proceed?"
            ),
        )
        if response == QMessageBox.StandardButton.Yes:
            ok = reset_database(self.database)
            print("Comitted", ok)
            self._return_flag |= ReturnFlags.Restart

    def save_all(self) -> None:
        """Saves all current settings in the native format"""
        for key, value in asdict(self.settings).items():
            if issubclass(type(value), Enum):
                self.qsettings.setValue(f"User/{key}", value.name)
            else:
                self.qsettings.setValue(f"User/{key}", value)

    def restore_defaults(self) -> None:
        dbpath = self.settings.dbpath
        self.settings = Defaults.user()
        self.settings.dbpath = dbpath
        self._set_ui_for_values()
        self._return_flag |= ReturnFlags.Restart


# Settings object classes


@dataclass
class Settings:
    """QSettings as a dataclass and extension to return values from an ini-file with the correct type.
    Convenience class to manage user settings of User-group]"""

    appearance: Appearance
    language: Locale
    time_format: TimeFormat
    always_schedule: bool
    dbpath: str

    @classmethod
    def read_settings(cls, qsettings: QSettings) -> Self:
        """Loads settings from a QSettings class into a Settings dataclass
        and replaces invalid values with default values."""
        values = []
        for field in fields(Settings):
            print("Field name", field.name)
            if issubclass(field.type, Enum):
                rvalue = qsettings.value(f"User/{field.name}", type=str)
                try:
                    values.append(field.type[rvalue])
                except KeyError:
                    print("Invalid value")
                    values.append(getattr(Defaults.User, field.name))
                continue
            elif field.name == "dbpath":
                rvalue = qsettings.value(f"User/{field.name}")
                print("Actual dbpath value", rvalue)
                values.append(
                    str(rvalue) if rvalue else getattr(Defaults.User, "dbpath")
                )
            else:
                rvalue = qsettings.value(
                    f"User/{field.name}",
                    defaultValue=getattr(Defaults.User, field.name),
                    type=field.type,
                )
                values.append(rvalue)
            print("Value", rvalue)

        return cls(*values)

    @staticmethod
    def check_values(qsettings: QSettings) -> str | None:
        """Checks if the QSettings object's values are valid. If not returns the first wrong key."""
        checks = asdict(Checks())
        for key in qsettings.allKeys():
            print("Checking key", key)
            rawkey = key.split("/")[1]
            try:
                if isinstance(checks[rawkey], Callable):
                    if checks[rawkey](qsettings, key):
                        continue
                    return key
                else:
                    if qsettings.value(key, type=str) in checks[rawkey]:
                        continue
                    return key
            except KeyError:
                # Some keys are checked in a different manner at another place in the appliccation
                continue
        return None

    @staticmethod
    def value(name: str) -> Any:
        """Convenience method to immediately access 'User' settings."""
        qsettings = QSettings(
            QSettings.Format.IniFormat,
            QSettings.Scope.UserScope,
            "Teachart",
            "Settings",
        )
        raw_value = qsettings.value(f"User/{name}")
        try:
            if raw_value and issubclass(Enum, Settings.__annotations__[name]):
                # Handling enum-type values
                try:
                    return Settings.__annotations__[name][raw_value]
                except KeyError:
                    return getattr(Defaults.User, name)
            else:
                # Handling any other type exept arrays
                return qsettings.value(
                    f"User/{name}",
                    defaultValue=getattr(Defaults.User, name),
                    type=Settings.__annotations__[name],
                )
        except AttributeError:
            return None

    @staticmethod
    def qsettings(
        format: QSettings.Format = QSettings.Format.IniFormat,
        scope: QSettings.Scope = QSettings.Scope.UserScope,
    ) -> QSettings:
        return QSettings(format, scope, "Teachart", "settings")


class DefaultValue:
    value: Any
    type: Any
    check: str | None


class Defaults(object):
    @dataclass(frozen=True)
    class AppInfo:
        app_ver: str = "0.1"
        db_ver: str = "1"

    @dataclass(frozen=True)
    class User:
        appearance: Appearance = Appearance.Light
        language: Locale = Locale.EnglishUK
        time_format: TimeFormat = TimeFormat.TF24
        always_schedule: bool = False
        dbpath: str = "NoDB"

    @dataclass
    class Application:
        pinned: list[str] = field(default_factory=[])
        recent: list[str] = field(default_factory=[])
        first_startup: bool = True
        debug: bool = False

    @staticmethod
    def __class_getitem__(key: str) -> Any:
        if "/" in key:
            group_name, k = key.split("/", 2)
            try:
                group = Defaults.__dict__[group_name]
                # field = group.__dataclass_fields__[k]
                print(group, k, field)
                value = getattr(group, k)
                return value  # if value != None else field.default_factory
            except (KeyError, AttributeError):
                return None
        return None

    @staticmethod
    def unified() -> dataclass:
        """Returns a unified dataclass containing all default values."""
        unified_fields = []

        for f in fields(Defaults.AppInfo):
            unified_fields.append(
                (f.name, f.type, field(default=getattr(Defaults.AppInfo, f.name)))
            )

        for f in fields(Defaults.User):
            unified_fields.append(
                (f.name, f.type, field(default=getattr(Defaults.User, f.name)))
            )

        for f in fields(Defaults.Application):
            unified_fields.append(
                (f.name, f.type, field(default=getattr(Defaults.Application, f.name)))
            )

        UnifiedDefaults = make_dataclass("UnifiedDefaults", unified_fields, frozen=True)
        return UnifiedDefaults()

    @staticmethod
    def user() -> Settings:
        """Returns Settings-object with all default values."""
        return Settings(*asdict(Defaults.User()).values())

    @staticmethod
    def keys() -> tuple[str]:
        keylist = []

        for field in fields(Defaults.AppInfo):
            keylist.append(f"AppInfo/{field.name}")

        for field in fields(Defaults.User):
            keylist.append(f"User/{field.name}")

        for field in fields(Defaults.Application):
            keylist.append(f"Application/{field.name}")

        return tuple(keylist)

    @staticmethod
    def set_default(qsettings: QSettings, key: str) -> bool:
        """Sets the key to the default value. The key is a group/attribute pair."""
        value = Defaults[key]
        print("Set default to", value)
        if value != None:
            if isinstance(value, Enum):
                value = value.name
            qsettings.setValue(key, value)
            qsettings.sync()
            return True
        return False

    @staticmethod
    def qsettings(
        format: QSettings.Format = QSettings.Format.IniFormat,
        scope: QSettings.Scope = QSettings.Scope.UserScope,
    ) -> QSettings:
        settings = QSettings(format, scope, "Teachart", "settings")
        settings.beginGroup("AppInfo")
        settings.setValue("app_ver", Defaults.AppInfo.app_ver)
        settings.setValue("db_ver", Defaults.AppInfo.db_ver)
        settings.endGroup()

        settings.beginGroup("User")
        settings.setValue("appearance", Defaults.User.appearance.name)
        settings.setValue("language", Defaults.User.language.name)
        settings.setValue("time_format", Defaults.User.time_format.name)
        settings.setValue("always_schedule", Defaults.User.dbpath)
        settings.setValue(
            "dbpath", "D:/Dokumente/Python Scripts/Educhart/db/tcha20250713215136.db"
        )
        settings.endGroup()

        settings.beginGroup("Application")
        settings.setValue("pinned", [])
        settings.setValue("recent", [])
        settings.setValue("first_startup", True)
        settings.setValue("debug", False)
        settings.endGroup()
        settings.sync()
        return settings


@dataclass
class Checks:
    appearance: list[str] = field(
        default_factory=lambda: [value.name for value in Appearance]
    )
    language: list[str] = field(
        default_factory=lambda: [value.name for value in Locale]
    )
    time_format: list[str] = field(
        default_factory=lambda: [value.name for value in TimeFormat]
    )
    always_schedule: tuple[str] = ("true", "false")
    first_startup: tuple[str] = ("true", "false")
    debug: tuple[str] = ("true", "false")
