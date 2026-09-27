from __future__ import annotations

from collections.abc import Callable, Iterator, KeysView
from dataclasses import dataclass, field
from enum import Enum, Flag, StrEnum
from functools import cache
from os.path import abspath, dirname, exists
from pathlib import Path
from typing import Any, ClassVar

from PyQt6.QtCore import QT_TR_NOOP as tr
from PyQt6.QtCore import QLocale, QSettings, QSize, Qt
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtSql import QSqlDatabase
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
)
from styling.properties import NTHEME_PROPERTIES
from tcha.dbmodels import create_database, reset_database
from tcha.error import StandardLogger
from tcha.utils import debug_enabled, word_as_bool
from ui.ui_settings import Ui_SettingsDialog


# In settings.py, add this function and remove the import
def get_external_theme_names() -> Iterator[tuple[str, str]]:
    import json
    import zipfile

    theme_path = Settings.user_path() / "themes"

    if not theme_path.exists():
        return

    for file in theme_path.iterdir():
        if file.suffix == ".taste" and "native:" not in file.stem:
            try:
                with zipfile.ZipFile(file, "r") as zf:
                    properties_data = zf.read("properties.json")
                    properties = json.loads(properties_data)

                    if "name" in properties:
                        yield file.stem, properties["name"]
            except (zipfile.BadZipFile, KeyError, json.JSONDecodeError) as e:
                StandardLogger.warning(
                    f"Warning: Could not read theme from {file.name}: {e}",
                    extra={"sender": "SETTINGS"},
                )
                continue


def get_themes() -> list[ThemeValue]:
    themes = []
    for name, theme in NTHEME_PROPERTIES.items():
        themes.append(ThemeValue(theme["name"].get("EnglishUK"), f"native:{name}"))

    for fname, theme_name in get_external_theme_names():
        themes.append(ThemeValue(theme_name, fname))
    return themes


@dataclass(frozen=True)
class ThemeValue:
    name: str
    value: str


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


class TimeFormat(StrEnum):
    TF24 = "HH:mm"
    TF12 = "h:mm ap"


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
    ):
        super().__init__(parent, Qt.WindowType.Dialog)
        self.ui = Ui_SettingsDialog()
        self.ui.setupUi(self)

        self.qsettings = qsettings
        self.database: QSqlDatabase = db
        self.settings = Settings.get_settings()
        self._return_flag: ReturnFlags = ReturnFlags.Invalid
        self._settings_map: dict[str, Callable] = {
            "User/appearance": self._select_appearance,
            "User/time_format": self._select_time_format,
            "User/always_schedule": self._tick_always_schedule,
            "User/editor.compress_image": self._tick_compress_image,
            "User/editor.single_selection": self._tick_single_selection,
            "User/dbpath": self._set_dblocation,
        }
        self.ui.pb_edit_ini.setVisible(debug_enabled())
        self._import_options()
        self._set_ui_for_values()
        self.connect_signals()

    def connect_signals(self) -> None:
        self.ui.cb_themes.activated.connect(self.set_appearance)
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

    def done(self, a0: int):
        if a0 == QDialog.DialogCode.Accepted:
            self.save_all()
        return super().done(a0)

    @property
    def return_flags(self) -> ReturnFlags:
        return self._return_flag

    # UI setup to settings

    def _import_options(self) -> None:
        """Populates combo boxes for language and time format and themes"""
        for theme in get_themes():
            self.ui.cb_themes.insertItem(self.ui.cb_themes.count(), theme.name, theme.value)

        self.ui.cb_time_format.addItem("24h", TimeFormat.TF24)
        self.ui.cb_time_format.addItem("12h", TimeFormat.TF12)

    def _set_ui_for_values(self) -> None:
        """Makes UI reflect the settings' values"""
        for key, value in filter(lambda x: x[0].startswith("User/"), self.settings.items()):
            self._settings_map[key](value)

    def _select_appearance(self, value: str) -> None:
        """Set appearance option based on Appearance value or int."""
        i = self.ui.cb_themes.findData(value)
        if i > -1:
            self.ui.cb_themes.setCurrentIndex(i)
        else:
            self.ui.cb_themes.setCurrentIndex(0)

    def _select_time_format(self, tformat: TimeFormat) -> None:
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

    def set_appearance(self, index: int) -> None:
        self.settings["User/appearance"] = self.ui.cb_themes.itemData(index)
        self._return_flag |= ReturnFlags.UpdateStyle

    def _on_time_format_set(self) -> None:
        self.settings["User/time_format"] = self.ui.cb_time_format.currentData().name
        self._return_flag |= ReturnFlags.UpdateLocale

    def _on_always_schedule_set(self) -> None:
        self.settings["User/always_schedule"] = self.ui.cb_always_schedule.isChecked()

    def _on_compress_images_set(self) -> None:
        self.settings["User/editor.compress_image"] = self.ui.cb_compress_images.isChecked()

    def _on_single_selection_set(self) -> None:
        self.settings["User/editor.single_selection"] = self.ui.cb_single_selection.isChecked()

    # Database settings

    def set_dbpath(self) -> None:
        dbpath = self.settings.get("User/dbpath")
        if dbpath and exists(dbpath):
            path, _ = QFileDialog.getOpenFileName(
                self,
                tr("Open Lesson Database"),
                dirname(dbpath),
            )
        else:
            path, _ = QFileDialog.getOpenFileName(
                self, tr("Open Lesson Database"), "/home", "Database files (*.tdb)"
            )
        if path:
            self.settings["User/dbpath"] = path
            self.ui.le_path.setText(path)
            self._return_flag |= ReturnFlags.Restart

    def create_new_db(self) -> None:
        """Creates new database file without deleting the old one in the standard folder and sets it as the used database."""
        db = create_database(AppInfo.db_ver)
        self.settings.dbpath = abspath(db.databaseName())
        self.ui.le_path.setText(self.settings.get("User/dbpath"))
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
        if response == QMessageBox.StandardButton.Yes and reset_database(self.database):
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

        for key in Values.keys():  # noqa: SIM118
            values[key] = Settings.value(key)

        return values

    @staticmethod
    def value[T](key: str) -> T:
        """Convenience method to immediately access settings's value."""
        qsettings = Settings.qsettings()
        definition = Values.definition(key)
        if definition:
            if definition.qvariant:
                value = qsettings.value(key, type=definition.type, defaultValue=definition.default)
                if value is not None:
                    return value
            else:
                raw_value = qsettings.value(key)
                try:
                    return definition.get(raw_value)
                except (ValueError, TypeError):
                    pass
            StandardLogger.error(
                f"Value of setting '{key}' not existing. Adding as default",
                extra={"sender": "SETTINGS"},
            )
            Settings.set_default(key)
            return Settings.value(key)
        return None

    @staticmethod
    def set_value(key: str, value: Any) -> None:
        if key in Values.keys():  # noqa: SIM118
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

    @staticmethod
    def set_qsettings(qsettings: QSettings) -> None:
        Settings.__qsettings = qsettings

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
    type: type
    qvariant: bool
    get: Callable | None = field(default=None)


class Values:
    __VALUES: ClassVar[dict[str, Value]] = {
        "AppInfo/app_ver": Value(AppInfo.app_ver, str, True),
        "AppInfo/db_ver": Value(AppInfo.db_ver, str, True),
        "User/appearance": Value("native:light", str, True),
        "User/time_format": Value(TimeFormat.TF24, TimeFormat, False, lambda val: TimeFormat[val]),
        "User/always_schedule": Value(False, bool, False, lambda val: word_as_bool(val)),
        "User/editor.compress_image": Value(False, bool, False, lambda val: word_as_bool(val)),
        "User/editor.single_selection": Value(False, bool, False, lambda val: word_as_bool(val)),
        "User/dbpath": Value(" ", str, True),
        "Application/pinned": Value([], list, True),
        "Application/recent": Value([], list, True),
        "Application/first_startup": Value(True, bool, False, lambda val: word_as_bool(val)),
        "Application/editor.window_size": Value(QSize(850, 500), QSize, True),
    }

    def __init__(self):
        raise NotImplementedError("Defaults cannot be initialised.")

    @staticmethod
    def definition(key: str) -> Value | None:
        """Returns the value definition for key 'key' if existinf else returns None"""
        return Values.__VALUES.get(key)

    @cache
    @staticmethod
    def default_value(key: str, qsettings_value=False) -> Any:
        value = Values.__VALUES.get(key)
        if qsettings_value and isinstance(value.default, Enum):
            return value.default.name
        return value.default if value else None

    @staticmethod
    def keys() -> KeysView[str]:
        return Values.__VALUES.keys()

    @staticmethod
    def defaults() -> dict[str, Any]:
        """Returns all default value as dictionary with settings key as key and default value as value."""
        return {key: value.default for key, value in Values.__VALUES}

    @staticmethod
    def default_qsettings(
        format: QSettings.Format = QSettings.Format.IniFormat,
        scope: QSettings.Scope = QSettings.Scope.UserScope,
        clean=False,
    ) -> QSettings:
        """
        Creates a new QSettings instance with default values.
        The ini-file will be created in the directory at Settings.user_path().
        If 'clean' is True a new file will be created without overwriting an existing settings file.
        """
        settings = (
            QSettings(format, scope, "Teachart", "settings")
            if not clean
            else QSettings(format, scope, "Teachart", "settings_clean")
        )
        settings.beginGroup("AppInfo")
        settings.setValue("app_ver", AppInfo.app_ver)
        settings.setValue("db_ver", AppInfo.db_ver)
        settings.endGroup()

        settings.beginGroup("User")
        settings.setValue("appearance", Values.default_value("User/appearance"))
        settings.setValue("time_format", Values.default_value("User/time_format", True))
        settings.setValue("always_schedule", Values.default_value("User/always_schedule"))
        settings.setValue(
            "editor.compress_image", Values.default_value("User/editor.compress_image")
        )
        settings.setValue(
            "editor.single_selection",
            Values.default_value("User/editor.compress_image"),
        )

        # TODO: Change before production
        settings.setValue("dbpath", Path(" "))
        settings.endGroup()

        settings.beginGroup("Application")
        settings.setValue("pinned", [])
        settings.setValue("recent", [])
        settings.setValue("first_startup", Values.default_value("Application/first_startup"))
        settings.setValue(
            "editor.window_size", Values.default_value("Application/editor.window_size")
        )
        settings.endGroup()
        settings.sync()
        return settings
