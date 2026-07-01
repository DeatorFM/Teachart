from ast import Call
from dataclasses import asdict, dataclass, field
from enum import Enum, Flag, IntEnum, StrEnum
from functools import cache
from os.path import abspath, dirname, exists
from pathlib import Path
from re import L
from typing import Any, Callable, KeysView, Self, Type

import PyQt6.uic as uic
from PyQt6.QtCore import QT_TR_NOOP as tr
from PyQt6.QtCore import QLocale, QSettings, QSize, Qt
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtSql import QSqlDatabase
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from tcha.dbmodels import create_database, reset_database
from tcha.utils import word_as_bool

# Constants


class AppInfo:
    app_ver = "1.0.0-a.1"
    db_ver = "1"

    def __init__(self):
        raise NotImplementedError("Cannot be initialised")


@dataclass(frozen=True)
class LocaleValue:
    name: str
    language: QLocale.Language
    region: QLocale.Country


class Locale(Enum):
    EnglishUK = LocaleValue(
        "English UK", QLocale.Language.English, QLocale.Country.UnitedKingdom
    )
    German = LocaleValue("German", QLocale.Language.German, QLocale.Country.Germany)
    Japanese = LocaleValue("Japanese", QLocale.Language.Japanese, QLocale.Country.Japan)

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
    TF12 = "h:mm ap"


class Appearance(IntEnum):
    Light = 0
    Dark = 1
    System = 2


class ReturnFlags(Flag):
    Invalid = 0
    Restart = 1
    UpdateLocale = 2
    UpdateStyle = 4


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
        self.settings = Settings.get_settings()
        self._return_flag: ReturnFlags = ReturnFlags.Invalid
        self._settings_map: dict[str, Callable] = {
            "User/appearance": self._tick_appearance,
            "User/language": self._select_language,
            "User/time_format": self._select_time_format,
            "User/always_schedule": self._tick_always_schedule,
            "User/editor.compress_image": self._tick_compress_image,
            "User/editor.single_selection": self._tick_single_selection,
            "User/dbpath": self._set_dblocation,
        }
        self.ui.pb_edit_ini.setVisible(
            qsettings.value("Application/debug", False, bool)
        )
        self._import_options()
        self._set_ui_for_values()
        self.connect_signals()

    def connect_signals(self) -> None:
        self.ui.rb_light.toggled.connect(lambda: self.set_appearance(Appearance.Light))
        self.ui.rb_dark.toggled.connect(lambda: self.set_appearance(Appearance.Dark))
        self.ui.cb_language.activated.connect(self._on_language_set)
        self.ui.cb_time_format.activated.connect(self._on_time_format_set)
        self.ui.cb_always_schedule.toggled.connect(self._on_always_schedule_set)
        self.ui.cb_compress_images.toggled.connect(self._on_compress_images_set)
        self.ui.cb_single_selection.toggled.connect(self._on_single_selection_set)
        self.ui.pb_file_dialog.clicked.connect(self.set_dbpath)
        self.ui.pb_new_database.clicked.connect(self.create_new_db)
        self.ui.pb_reset_database.clicked.connect(self.reset_db)
        self.ui.settings_buttonbox.clicked.connect(self._handle_button)
        self.ui.pb_edit_ini.clicked.connect(self.open_ini)

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
        for key, value in filter(
            lambda x: x[0].startswith("User/"), self.settings.items()
        ):
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

    def _tick_compress_image(self, ticked: bool) -> None:
        self.ui.cb_compress_images.setChecked(ticked)

    def _tick_single_selection(self, ticked: bool) -> None:
        self.ui.cb_single_selection.setChecked(ticked)

    def _set_dblocation(self, path: str) -> None:
        self.ui.le_path.setText(path)

    # Setter methods

    def set_appearance(self, value: Appearance) -> None:
        self.settings["User/appearance"] = value.name
        self._return_flag |= ReturnFlags.UpdateStyle

    def _on_language_set(self) -> None:
        self.settings["User/language"] = self.ui.cb_language.currentData().name
        self._return_flag |= ReturnFlags.UpdateLocale

    def _on_time_format_set(self) -> None:
        self.settings["User/time_format"] = self.ui.cb_time_format.currentData().name
        self._return_flag |= ReturnFlags.UpdateLocale

    def _on_always_schedule_set(self) -> None:
        self.settings["User/always_schedule"] = self.ui.cb_always_schedule.isChecked()

    def _on_compress_images_set(self) -> None:
        self.settings["User/editor.compress_image"] = (
            self.ui.cb_compress_images.isChecked()
        )

    def _on_single_selection_set(self) -> None:
        self.settings["User/editor.single_selection"] = (
            self.ui.cb_single_selection.isChecked()
        )

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
        if path:
            self.settings.dbpath = path
            self.ui.le_path.setText(path)
            self._return_flag |= ReturnFlags.Restart

    def create_new_db(self) -> None:
        """Creates new database file without deleting the old one in the standard folder and sets it as the used database."""
        db = create_database(AppInfo.db_ver)
        self.settings.dbpath = abspath(db.databaseName())
        self.ui.le_path.setText(self.settings.dbpath)
        self._return_flag |= ReturnFlags.Restart

    def reset_db(self) -> None:
        """Deletes all data from the database in dbpath."""
        response = QMessageBox.question(
            self,
            tr("Resetting database"),
            tr(
                "Resetting the database will delete all course, schedule and student records.\nDo you still want to proceed?"
            ),
        )
        if response == QMessageBox.StandardButton.Yes:
            ok = reset_database(self.database)
            print("Comitted", ok)
            self._return_flag |= ReturnFlags.Restart

    def save_all(self) -> None:
        """Saves all current settings in the native format"""
        for key, value in self.settings.items():
            if key.startswith("User"):
                Settings.set_value(key, value)
        self.qsettings.sync()

    def restore_defaults(self) -> None:
        dbpath = self.settings["User/dbpath"]
        self.settings = Values.defaults()
        self.settings["User/dbpath"] = dbpath
        self._set_ui_for_values()
        self._return_flag |= ReturnFlags.Restart

    # Debug options

    def open_ini(self) -> None:
        dialog = IniEditor(self.qsettings.fileName(), self)
        dialog.exec()
        self.qsettings = Settings.qsettings()
        self.settings = Settings.get_settings()
        self._set_ui_for_values()
        self._return_flag |= ReturnFlags.Restart


class IniEditor(QDialog):
    def __init__(self, ini_path: str, parent=None):
        super().__init__(parent)

        self.setWindowFlag(Qt.WindowType.Tool, True)
        self.setWindowTitle(tr("Edit Ini-File"))

        self.pte = QPlainTextEdit(self)
        lo = QVBoxLayout(self)
        lo.addWidget(self.pte)
        self.resize(500, 400)

        self.ini = Path(ini_path)
        self._text_changed = False

        text = self.ini.read_text("utf-8")
        self.pte.insertPlainText(text)

        self.pte.textChanged.connect(self.on_text_changed)

    def on_text_changed(self):
        self._text_changed = True

    def closeEvent(self, ev: QCloseEvent):
        if self._text_changed:
            self.ini.write_text(self.pte.toPlainText(), "utf-8")
        super().closeEvent(ev)


# Settings object classes


class Settings:
    __qsettings = QSettings(
        QSettings.Format.IniFormat, QSettings.Scope.UserScope, "Teachart", "settings"
    )
    """Convenience class to manage settings"""

    @staticmethod
    def get_settings() -> dict:
        """Loads settings from a QSettings class into a dictionary
        and replaces invalid values with default values."""
        values = {}

        for key in Values.keys():
            print(f"Getting key {key}")
            values[key] = Settings.value(key)

        return values

    @staticmethod
    def value[T](key: str) -> T:
        """Convenience method to immediately access settings's value."""
        qsettings = Settings.qsettings()
        definition = Values.definition(key)
        if definition:
            if definition.qvariant:
                value = qsettings.value(key, type=definition.type)
                if value:
                    return value
            else:
                raw_value = qsettings.value(key)
                try:
                    return definition.get(raw_value)
                except (ValueError, TypeError):
                    pass
            print(f"Key {key} not existing. Adding as default")
            Settings.set_default(key)
            return Settings.value(key)
        return None

    @staticmethod
    def set_value(key: str, value: Any) -> None:
        if key in Values.keys():
            if isinstance(value, Enum):
                value = value.name
            qsettings = Settings.qsettings()
            qsettings.setValue(key, value)
            qsettings.sync()

    @staticmethod
    def set_default(key: str) -> None:
        value = Values.default_value(key)
        if value:
            Settings.set_value(key, value)

    @staticmethod
    def qsettings(
        format: QSettings.Format = QSettings.Format.IniFormat,
        scope: QSettings.Scope = QSettings.Scope.UserScope,
    ) -> QSettings:
        return Settings.__qsettings

    @cache
    @staticmethod
    def user_path() -> Path:
        qsettings = Settings.qsettings()
        path = Path(qsettings.fileName())
        return path.parent


@dataclass(frozen=True)
class Value:
    """Definition for value handling"""

    default: Any
    type: Type
    qvariant: bool
    get: Callable | None = field(default=None)


class Values:
    __VALUES: dict[str, Value] = {
        "AppInfo/app_ver": Value(AppInfo.app_ver, str, True),
        "AppInfo/db_ver": Value(AppInfo.db_ver, str, True),
        "User/appearance": Value(
            Appearance.Light, Appearance, False, lambda val: Appearance[val]
        ),
        "User/language": Value(
            Locale.EnglishUK, Locale, False, lambda val: Locale[val]
        ),
        "User/time_format": Value(
            TimeFormat.TF24, TimeFormat, False, lambda val: TimeFormat[val]
        ),
        "User/always_schedule": Value(
            False, bool, False, lambda val: word_as_bool(val)
        ),
        "User/editor.compress_image": Value(
            False, bool, False, lambda val: word_as_bool(val)
        ),
        "User/editor.single_selection": Value(
            False, bool, False, lambda val: word_as_bool(val)
        ),
        "User/dbpath": Value("NoDB", str, True),
        "Application/pinned": Value([], list, True),
        "Application/recent": Value([], list, True),
        "Application/first_startup": Value(
            True, bool, False, lambda val: word_as_bool(val)
        ),
        "Application/debug": Value(False, bool, False, lambda val: word_as_bool(val)),
        "Application/editor.window_size": Value(QSize(850, 500), QSize, True),
    }

    def __init__(self):
        raise NotImplementedError("Defaults cannot be initialised.")

    @staticmethod
    def definition(key: str) -> Value | None:
        return Values.__VALUES.get(key)

    @cache
    @staticmethod
    def default_value(key: str) -> Any:
        value = Values.__VALUES.get(key)
        return value.default if value else None

    @staticmethod
    def keys() -> KeysView[str]:
        return Values.__VALUES.keys()

    @staticmethod
    def defaults() -> dict[str, Any]:
        return {key: value.default for key, value in Values.__VALUES}

    @staticmethod
    def default_qsettings(
        format: QSettings.Format = QSettings.Format.IniFormat,
        scope: QSettings.Scope = QSettings.Scope.UserScope,
    ) -> QSettings:
        settings = QSettings(format, scope, "Teachart", "settings")
        settings.beginGroup("AppInfo")
        settings.setValue("app_ver", AppInfo.app_ver)
        settings.setValue("db_ver", AppInfo.db_ver)
        settings.endGroup()

        settings.beginGroup("User")
        settings.setValue("appearance", Values.default_value("User/appearance"))
        settings.setValue("language", Values.default_value("User/language"))
        settings.setValue("time_format", Values.default_value("User/time_format"))
        settings.setValue(
            "always_schedule", Values.default_value("User/always_schedule")
        )
        settings.setValue(
            "editor.compress_image", Values.default_value("User/editor.compress_image")
        )
        settings.setValue(
            "editor.single_selection",
            Values.default_value("User/editor.compress_image"),
        )

        # TODO: Change before production
        settings.setValue("dbpath", "NoDB")
        settings.endGroup()

        settings.beginGroup("Application")
        settings.setValue("pinned", [])
        settings.setValue("recent", [])
        settings.setValue(
            "first_startup", Values.default_value("Application/first_startup")
        )
        settings.setValue("debug", Values.default_value("Application/debug"))
        settings.setValue(
            "editor.window_size", Values.default_value("Application/editor.window_size")
        )
        settings.endGroup()
        settings.sync()
        return settings
