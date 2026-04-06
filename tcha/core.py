from __future__ import annotations

import importlib.util as iu
import os
import sys
import typing
from os.path import abspath, exists
from pathlib import Path
from zipimport import zipimporter

from PyQt6.QtCore import QT_TR_NOOP as tr
from PyQt6.QtCore import QDateTime, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmapCache
from PyQt6.QtSql import QSqlDatabase
from PyQt6.QtWidgets import (
    QApplication,
    QGraphicsScene,
    QGraphicsView,
    QInputDialog,
    QMessageBox,
    QWidget,
)

from tcha.consts import AppAction, DisplayMode
from tcha.dbmanager import DbManager
from tcha.dbmodels import (
    CourseModel,
    ScheduleModel,
    StudentModel,
    check_database,
    create_database,
)
from tcha.editor import Editor
from tcha.elements import get_all_definitions
from tcha.error import CriticalError, PyException
from tcha.lfio import LessonFile
from tcha.settings import Defaults, Locale, ReturnFlags, Settings, SettingsDialog
from tcha.start import AboutDialog, OpenFileModel, StartWindow
from tcha.styling import TchaProxyStyle, make_palette
from tcha.table import PresenterView
from tcha.utils import WinApi


def test_lesson_models(db) -> tuple[CourseModel, ScheduleModel, StudentModel]:
    cmodel = CourseModel(db)
    cmodel.add_course("A1 Business (Oct 2023)", 90)
    cmodel.add_course("Feng", 45)
    cmodel.add_course("A1 Intensiv Aug 2024", 150)
    cmodel.add_course("Aoki", 60)

    smodel = ScheduleModel(db)
    smodel.add_schedule(
        1,
        QDateTime(2025, 6, 15, 14, 30, 0),
        1263039429114341325,
        "D:/Dokumente/thislesson1.lesson",
    )
    smodel.add_schedule(
        2,
        QDateTime(2025, 9, 6, 10, 15, 0),
        -232133682615210308,
        "D:/Dokumente/thislesson2.lesson",
    )
    smodel.add_schedule(
        3,
        QDateTime(2025, 8, 31, 12, 0, 0),
        -4626562671928849836,
        "D:/Dokumente/thislesson3.lesson",
    )
    smodel.add_schedule(
        4,
        QDateTime(2025, 12, 20, 11, 20, 0),
        3514653705253326921,
        "D:/Dokumente/thislesson4.lesson",
    )

    tmodel = StudentModel(db)
    tmodel.add_student("Yuta Katsumata", 1, "yuta.katsumata@toppan-europe.com")
    tmodel.add_student("Yukiko Wada", 1, "germany.dus922@gmail.com")
    tmodel.add_student("Hiroki Shinoda", 1, "shinoda-h@marubeni.com")
    tmodel.add_student("Hongyu Feng", 2, "tianzhongzhishu37@gmail.com")
    tmodel.add_student("Chika Okura", 3, "okura.c@yahoo.jp")
    tmodel.add_student("Akihisa Yamada", 3, "akihisa.yamada@gmail.com")
    tmodel.add_student("Ayumi Oshima", 3, "ayushi93@gmail.com")
    tmodel.add_student("Aya Shinozaki", 3, "shinooya1138@icloud.com")
    tmodel.add_student("Hiromi Fujisawa", 3, "hiromi.love89@gmail.com")
    tmodel.add_student("Amane Tomita", 3, "amnto96@yahoo.jp")
    tmodel.add_student("Ayako Kimura", 3, "ayakk8290@icloud.com")
    tmodel.add_student("Hisayuki Aoki", 4, "hisa10532@gmail.com")

    return cmodel, smodel, tmodel


RECENT = [
    "D:/Documents/Math/algebra_basics.lesson",
    "D:/Documents/Science/physics_101.lesson",
    "D:/Documents/History/world_war_2.lesson",
    "D:/Documents/Math/calculus_intro.lesson",
    "D:/Documents/English/shakespeare.lesson",
    "D:/Documents/Science/chemistry_lab.lesson",
    "D:/Documents/Geography/continents.lesson",
    "D:/Documents/Math/geometry_shapes.lesson",
]

PINNED = [
    "D:/Documents/Math/algebra_basics.lesson",
    "D:/Documents/Science/physics_101.lesson",
    "D:/Documents/Art/painting_techniques.lesson",
    "D:/Documents/Music/music_theory.lesson",
    "D:/Documents/Math/calculus_intro.lesson",
    "D:/Documents/Programming/python_basics.lesson",
]


class AppCore(QApplication):
    restartRequested = pyqtSignal()

    def __init__(self, argv: list[str]) -> None:
        super().__init__(argv)
        self.setApplicationVersion(Defaults.AppInfo.app_ver)

        self.qsettings = Settings.qsettings()
        self._db: QSqlDatabase | None = None
        self._start_dialog: StartWindow | None = None
        self._presenter_view: PresenterView | None = None
        self._edefinitions = get_all_definitions()

        if not self.qsettings.allKeys():
            print("Empty Settings: First initialisation")
            self._first_time()
        else:
            self._startup_checks()
        self._load_theme(self.qsettings.value("User/appearance"))

        self._course_model = CourseModel(self._db)
        self._schedule_model = ScheduleModel(self._db)
        self._file_model = OpenFileModel(
            self.qsettings.value("Application/recent", [], list),
            self.qsettings.value("Application/pinned", [], list),
        )

        self.init_display_mode = WinApi.get_display_mode()
        print(f"Initial display mode: {self.init_display_mode}")
        QPixmapCache.setCacheLimit(50000)

        self.aboutToQuit.connect(self.on_quitting)
        self.screenAdded.connect(self.on_screen_changed)
        self.screenRemoved.connect(self.on_screen_changed)

    def _startup_checks(self) -> None:
        keys = self.qsettings.allKeys()

        # Check keys
        for key in Defaults.keys():
            if key in keys:
                continue
            else:
                print(f"Creating key {key}")
                Defaults.set_default(self.qsettings, key)

        # Check values
        while True:
            result = Settings.check_values(self.qsettings)
            if result:
                print(f"Invalid value for {result}. Setting default value.")
                Defaults.set_default(self.qsettings, result)
                continue
            print("No invalid values found.")
            break

        # Check database
        dbpath = self.qsettings.value("User/dbpath", type=str)

        if exists(dbpath):
            print(f"Data base file in '{dbpath}' found.")
            db = QSqlDatabase.addDatabase("QSQLITE")
            db.setDatabaseName(dbpath)
            if db.open() and check_database(db):
                self._db = db
            else:
                QMessageBox.information(
                    None,
                    tr("Database error"),
                    tr(
                        "The database found is invalid. A new database will be created."
                    ),
                )
                self._db = create_database(Defaults.AppInfo.db_ver)
                self.qsettings.setValue("User/dbpath", abspath(self._db.databaseName()))
        else:
            QMessageBox.information(
                None,
                tr("Database error"),
                tr("The database could not be found. A new database will be created."),
            )
            self._db = create_database(Defaults.AppInfo.db_ver)
            self.qsettings.setValue("User/dbpath", abspath(self._db.databaseName()))

    def _first_time(self) -> None:
        self.qsettings = Defaults.qsettings()
        self.qsettings.setValue("Application/first_startup", False)
        db = create_database()
        print("Database at", abspath(db.databaseName()))
        self.qsettings.setValue("User/dbpath", abspath(db.databaseName()))
        language = self.language_dialog()
        print("Selected language", language)
        self.qsettings.setValue("User/language", language.name)

    def _load_theme(self, theme: str, native=True) -> None:
        if native:
            path = Path("nativethemes") / f"{theme}.zip"
            importer = zipimporter(str(path))

            spec = importer.find_spec("theme")
            module = iu.module_from_spec(spec)
            sys.modules["theme"] = module
            spec.loader.exec_module(module)

            res_spec = importer.find_spec("res")
            res_module = iu.module_from_spec(res_spec)
            sys.modules["res"] = res_module
            spec.loader.exec_module(res_module)

            stylesheet_data = importer.get_data(module.STYLESHEET)
            self.setStyleSheet(str(stylesheet_data, encoding="utf-8"))
            palette = make_palette(module.PALETTE_COLORS)
            self.setPalette(palette)

            if isinstance(self.style(), TchaProxyStyle):
                self.style().polish()
            else:
                style = TchaProxyStyle()
                self.setStyle(style)

    def connect_signals(self) -> None:
        self.aboutToQuit.connect(self.on_quitting)

    def language_dialog(self) -> Locale:
        language, result = QInputDialog.getItem(
            None,
            "Language",
            "Select your language",
            [value.value.name for value in list(Locale)],
        )
        if result:
            for i, value in enumerate(list(Locale)):
                if value.value.name == language:
                    return Locale.from_int(i)
        return getattr(Defaults, "language")

    def on_app_action(self, action: AppAction, value: typing.Any = None) -> None:
        match action:
            case AppAction.NoAction:
                return
            case AppAction.NewFile:
                self.create_editor()
            case AppAction.OpenFile:
                self.open_file(value)
            case AppAction.Settings:
                self.open_settings(value)
            case AppAction.StartDialog:
                self.open_start_dialog(True)
            case AppAction.CourseExplorer:
                self.open_course_exp(value)
            case AppAction.AboutTeachart:
                self.open_about_dialog()

    def startup_window(self, argv=None) -> QWidget:
        # TODO: Implement argument evaluation on application start
        startup_window = StartWindow(self._file_model, self._schedule_model)
        startup_window.appActionTriggered[AppAction, QWidget].connect(
            self.on_app_action
        )
        startup_window.appActionTriggered[AppAction, Path].connect(self.on_app_action)
        startup_window.appActionTriggered[AppAction].connect(self.on_app_action)
        self._start_dialog = startup_window
        return startup_window

    def opened_editors(self) -> list[Editor]:
        windows = QApplication.topLevelWidgets()
        return list(filter(lambda x: isinstance(x, Editor), windows))

    def opened_start_dialog(self) -> StartWindow | None:
        return self._start_dialog

    def opened_presenter(self) -> QGraphicsView | None:
        return self._presenter_view

    def create_editor(
        self,
    ) -> None:
        """Creates an editor with a new LessonFile object."""
        lf = LessonFile()
        lf.open("w")
        editor_window = Editor(
            self._course_model, self._schedule_model, self._edefinitions, lf
        )
        editor_window.appActionTriggered[AppAction].connect(self.on_app_action)
        editor_window.appActionTriggered[AppAction, Path].connect(self.on_app_action)
        editor_window.appActionTriggered[AppAction, QWidget].connect(self.on_app_action)
        editor_window.presenterActivated.connect(self.open_presenter)
        editor_window.presenterClosed.connect(self.close_presenter)
        editor_window.show()
        editor_window.set_recent_files(self._file_model.export_recent_as_menu(6))

        if self._start_dialog:
            self._start_dialog.close()
            self._start_dialog = None

    def open_file(self, path: Path) -> None:
        if (
            path
            and path.exists()
            and str(path) not in [editor.path for editor in self.opened_editors()]
        ):
            editor_window = None
            try:
                lf = LessonFile()
                lf.open("r", str(path))

                if self._start_dialog:
                    self._start_dialog.set_progress_logger(Path(lf.path), lf.progress)

                editor_window = Editor(
                    self._course_model, self._schedule_model, self._edefinitions, lf
                )
                editor_window.appActionTriggered[AppAction].connect(self.on_app_action)
                editor_window.appActionTriggered[AppAction, Path].connect(
                    self.on_app_action
                )
                editor_window.appActionTriggered[AppAction, QWidget].connect(
                    self.on_app_action
                )
                editor_window.presenterActivated.connect(self.open_presenter)
                editor_window.presenterClosed.connect(self.close_presenter)
                editor_window.show()
                editor_window.ui.ac_recent.setMenu(
                    self._file_model.export_recent_as_menu(6)
                )

            except ValueError as e:
                wrapped_error = PyException(e, True)
                lf.error_handler.log(wrapped_error, "Lesson model could not be loaded")
                lf.close()

            except CriticalError:
                lf.error_handler.log_msg(
                    "The reading operation was terminated because of a previous critical error."
                )
                lf.close()

            finally:
                lf.error_handler.show_result(
                    tr("File reading error"),
                    tr(
                        "There was a problem when reading the file. The file can be opened but the document cannot be displayed correctly."
                    ),
                    tr(
                        "The file could not be read because it is either corrupted or has an invalid structure."
                    ),
                )

                if self._start_dialog:
                    self._start_dialog.reset_progress()
                    self._start_dialog.close()
                    self._start_dialog = None
                self._file_model.append_file(str(path))
                if editor_window:
                    editor_window.set_recent_files(
                        self._file_model.export_recent_as_menu(6)
                    )

        else:
            QMessageBox.information(
                None,
                tr("Open lesson-file"),
                tr("File is already open or file does not exist."),
            )

    def open_course_exp(self, parent=None) -> None:
        dialog = DbManager(self._course_model, self._schedule_model, parent)
        if isinstance(parent, Editor):
            cid = parent.lesson.course_id
            if cid > 0:
                dialog.set_course(cid)
        dialog.exec()

    def open_settings(self, parent=None) -> None:
        print("Open Settings")
        return_flags = SettingsDialog.get_settings(
            parent, self._course_model.database(), Settings.qsettings()
        )
        print("Return flags: ", return_flags)
        if return_flags & ReturnFlags.Restart:
            print("Restarting application")
            self.restartRequested.emit()
            return
        if return_flags & ReturnFlags.UpdateStyle:
            print("Updating application style")
            self._load_theme(
                Settings.qsettings().value("User/appearance", "light", str)
            )
        if return_flags & ReturnFlags.UpdateLocale:
            print("Updating language")
            pass

    def open_start_dialog(self, file_mode=False) -> None:
        if not self.opened_start_dialog():
            window = StartWindow(self._file_model, self._schedule_model)
            window.appActionTriggered[AppAction, QWidget].connect(self.on_app_action)
            window.appActionTriggered[AppAction, Path].connect(self.on_app_action)
            window.appActionTriggered[AppAction].connect(self.on_app_action)
            self._start_dialog = window
            if file_mode:
                debug_tag = (
                    "Debug-Mode"
                    if Settings.qsettings().value("Application/debug", False, bool)
                    else ""
                )
                window.ui.ac_new.setVisible(False)
                window.ui.ac_settings.setVisible(False)
                window.setWindowTitle(f"{tr('Open File')} {debug_tag}")
            window.show()
        else:
            self.opened_start_dialog().show()

    def open_about_dialog(self) -> None:
        for widget in self.topLevelWidgets():
            if isinstance(widget, AboutDialog):
                return
        dialog = AboutDialog()
        dialog.open()

    def open_presenter(self, scene: QGraphicsScene, editor: Editor) -> None:
        if not self._presenter_view:
            self._presenter_view = PresenterView(scene, editor)
            self._presenter_view.finished.connect(self._disable_presenter_mode)
            self.show_presenter()
        else:
            self._presenter_view.view.setScene(scene)
            self._presenter_view.set_current_editor(editor)
            self._presenter_view.rescale()

    def show_presenter(self) -> None:
        if self._presenter_view:
            if WinApi.get_display_mode() == DisplayMode.Extended:
                self._presenter_view.showFullScreen()

            elif WinApi.get_display_mode() == DisplayMode.Duplicated:
                print("Display is duplicated. Set display mode to extended.")
                WinApi.set_display_mode(DisplayMode.Extended)
                QTimer.singleShot(500, lambda: self._presenter_view.showFullScreen())

    def close_presenter(self) -> None:
        if self._presenter_view:
            self._presenter_view.view.setScene(None)
            self._presenter_view.close()
            self._presenter_view = None
            if self.init_display_mode != WinApi.get_display_mode():
                WinApi.set_display_mode(self.init_display_mode)

    def _disable_presenter_mode(self) -> None:
        for editor in self.opened_editors():
            editor.enable_presenter_mode(False)

    def on_screen_changed(self) -> None:
        if self._presenter_view:
            if WinApi.get_display_mode() == DisplayMode.Single:
                self.init_display_mode = DisplayMode.Single
                self._disable_presenter_mode()
            else:
                if self._presenter_view.isHidden():
                    self.init_display_mode = WinApi.get_display_mode()
                    self.show_presenter()
            return

        self.init_display_mode = WinApi.get_display_mode()

    def db(self) -> QSqlDatabase | None:
        return self._db

    def restart(self) -> None:
        self.quit()
        os.execv(sys.executable, ["python"] + sys.argv)

    def on_quitting(self) -> None:
        print("Saving recent and pinned files")
        self.qsettings.setValue("Application/recent", self._file_model.export_recent())
        self.qsettings.setValue("Application/pinned", self._file_model.export_pinned())
