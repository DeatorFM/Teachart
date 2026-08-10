from __future__ import annotations

import os
import sys
import typing
from functools import cache
from os.path import abspath, exists
from pathlib import Path
from shutil import rmtree
from threading import Lock

from PyQt6.QtCore import QT_TR_NOOP as tr
from PyQt6.QtCore import QDateTime, QPersistentModelIndex, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtSql import QSqlDatabase
from PyQt6.QtWidgets import (
    QApplication,
    QGraphicsScene,
    QGraphicsView,
    QInputDialog,
    QMessageBox,
    QWidget,
)
from styling.theming import load_theme
from styling.utils import apply_style
from tcha.components import DialogManager, parse_args
from tcha.consts import RESOURCE_PATH, AppAction, DisplayMode
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
from tcha.error import CriticalError, ErrorLogger, PyException
from tcha.lfio import LessonFile
from tcha.settings import AppInfo, Locale, ReturnFlags, Settings, SettingsDialog, Values
from tcha.start import AboutDialog, OpenFileModel, StartWindow
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


class MetaApp(type(QApplication)):
    _instances: typing.ClassVar[dict] = {}
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwds):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwds)
                cls._instances[cls] = instance
        return cls._instances[cls]


class AppCore(QApplication, metaclass=MetaApp):
    restartRequested = pyqtSignal()

    def __init__(self, argv: list[str]) -> None:
        super().__init__(argv)
        self.setApplicationVersion(AppInfo.app_ver)
        self.setWindowIcon(QIcon(str(RESOURCE_PATH / "images" / "logo.svg")))

        self._db: QSqlDatabase | None = None
        self._dialog_manager = DialogManager()
        self._start_dialog: StartWindow | None = None
        self._presenter_view: PresenterView | None = None
        self._edefinitions = get_all_definitions()
        self._clean_up_list: list[Path] = []
        self._launch_config = parse_args()

        self._startup_checks()

        load_theme(Settings.value("User/appearance"), self)
        apply_style(self)

        self._course_model = CourseModel(self._db)
        self._schedule_model = ScheduleModel(self._db)
        self._file_model = OpenFileModel(
            Settings.value("Application/recent"),
            Settings.value("Application/pinned"),
        )

        self.init_display_mode = WinApi.get_display_mode()
        print(f"Initial display mode: {self.init_display_mode}")
        self.setProperty("globalIndex", QPersistentModelIndex())

        self.aboutToQuit.connect(self.on_quitting)
        self.screenAdded.connect(self.on_screen_changed)
        self.screenRemoved.connect(self.on_screen_changed)

    @cache
    @staticmethod
    def arguments() -> list[str]:
        return super().arguments()

    def _startup_checks(self) -> None:
        if not Settings.qsettings().allKeys() or self._launch_config.clean:
            self._first_time()
            return

        if not ErrorLogger.logdir().exists():
            ErrorLogger.logdir().mkdir(parents=True, exist_ok=True)

        # Check database
        dbpath = Settings.value("User/dbpath")

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
                    tr("The database found is invalid. A new database will be created."),
                )
                self._db = create_database(AppInfo.db_ver)
                Settings.set_value("User/dbpath", abspath(self._db.databaseName()))
        else:
            QMessageBox.information(
                None,
                tr("Database error"),
                tr("The database could not be found. A new database will be created."),
            )
            self._db = create_database()
            Settings.set_value("User/dbpath", abspath(self._db.databaseName()))

    def _first_time(self) -> None:
        qsettings = Values.default_qsettings(clean=self._launch_config.clean)
        Settings.set_qsettings(qsettings)
        Settings.set_value("Application/first_startup", False)
        self._db = create_database()
        print("Database at", abspath(self._db.databaseName()))
        Settings.set_value("User/dbpath", abspath(self._db.databaseName()))
        language = self.language_dialog()
        print("Selected language", language)
        Settings.set_value("User/language", language.name)

    def connect_signals(self) -> None:
        self.aboutToQuit.connect(self.on_quitting)

    def debug_enabled(self) -> bool:
        return self._launch_config.debug

    def clean_mode_enabled(self) -> bool:
        return self._launch_config.clean

    def setup_logger(self) -> None: ...

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
        return Values.default_value("User/language")

    def on_app_action(self, action: AppAction, value: typing.Any = None) -> None:
        match action:
            case AppAction.NoAction:
                return
            case AppAction.NewFile:
                editor = self.create_editor()
                editor.show()
            case AppAction.OpenFile:
                editor = self.open_file(value)
                if editor:
                    editor.show()
            case AppAction.Settings:
                self.open_settings(value)
            case AppAction.StartDialog:
                start = self.open_start_dialog(True)
                start.show()
            case AppAction.CourseExplorer:
                self.open_course_exp(value)
            case AppAction.AboutTeachart:
                self.open_about_dialog()

    def startup_window(self) -> QWidget:
        """Returns startup window based on arguments on startup"""
        print(f"Parsed arguments: {self._launch_config}")
        if not self._launch_config.opened_path:
            start = self.open_start_dialog()
            return start

        elif self._launch_config.opened_path.exists():
            if (
                self._launch_config.opened_path.is_file()
                and self._launch_config.opened_path.suffix == ".tch"
            ):
                editor = self.open_file(self._launch_config.opened_path)
                return editor if editor else self.create_editor()
            return self.create_editor()

        return self.open_start_dialog()

    def opened_editors(self) -> list[Editor]:
        return self._dialog_manager.get_container("Editor").values()

    def opened_start_dialog(self) -> StartWindow | None:
        return self._start_dialog

    def opened_presenter(self) -> QGraphicsView | None:
        return self._presenter_view

    def open_dialog(self, wtype: str) -> None: ...

    def create_editor(
        self,
    ) -> Editor:
        """Creates an editor with a new LessonFile object."""
        lf = LessonFile()
        lf.open("w")
        editor_window = self._dialog_manager.open(
            "Editor", self._course_model, self._schedule_model, self._edefinitions, lf
        )
        editor_window.dialogCalled.connect(self.open_dialog)
        editor_window.fileOpened.connect(self.open_file)
        editor_window.presenterActivated.connect(self.open_presenter)
        editor_window.presenterClosed.connect(self.close_presenter)
        editor_window.set_recent_files(self._file_model.export_recent_as_menu(6))
        self._clean_up_list.append(editor_window.resource_path)

        start_dialog = self._dialog_manager.get_dialog("Start")
        if start_dialog:
            start_dialog.close()
            self._dialog_manager.mark_closed("StartWindow")

        return editor_window

    def open_file(self, path: Path) -> Editor | None:
        if (
            path
            and path.exists()
            and str(path) not in [editor.path for editor in self.opened_editors()]
        ):
            caller = self.caller()
            editor_window = None

            try:
                lf = LessonFile()
                lf.open("r", str(path))

                if caller:
                    caller.set_progress_logger(Path(lf.path), lf.progress)
                    caller.unset_caller()

                editor_window = self._dialog_manager.open(
                    "Editor", self._course_model, self._schedule_model, self._edefinitions, lf
                )
                editor_window.dialogCalled.connect(self.open_dialog)
                editor_window.fileOpened.connect(self.open_file)
                editor_window.presenterActivated.connect(self.open_presenter)
                editor_window.presenterClosed.connect(self.close_presenter)
                editor_window.ui.ac_recent.setMenu(self._file_model.export_recent_as_menu(6))

                self._clean_up_list.append(Path(lf.temppath))
                self._clean_up_list.append(editor_window.resource_path)

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

                if caller:
                    caller.reset_progress()
                if self._start_dialog:
                    self._start_dialog.close()
                    self._start_dialog = None
                self._file_model.append_file(str(path))
                if editor_window:
                    editor_window.set_recent_files(self._file_model.export_recent_as_menu(6))
                return editor_window  # noqa: B012

        else:
            QMessageBox.information(
                None,
                tr("Open lesson-file"),
                tr("File is already open or file does not exist."),
            )
            return None

    def open_course_exp(self, parent=None) -> None:
        dialog = DbManager(self._course_model, self._schedule_model, parent)
        if isinstance(parent, Editor):
            cid = parent.lesson.course_id
            if cid > 0:
                dialog.set_course(cid)
        dialog.exec()

    def open_settings(self, parent=None) -> None:
        return_flags = SettingsDialog.get_settings(
            None, self._course_model.database(), Settings.qsettings()
        )
        if return_flags & ReturnFlags.Restart:
            print("Restarting application")
            self.restartRequested.emit()
            return
        if return_flags & ReturnFlags.UpdateStyle:
            print("Updating application style")
            load_theme(Settings.value("User/appearance"), self)
        if return_flags & ReturnFlags.UpdateLocale:
            print("Updating language")

    def on_settings_closed(self, flags: ReturnFlags) -> None: ...

    def open_start_dialog(self, file_mode=False) -> None:
        if not self.opened_start_dialog():
            window = StartWindow(self._file_model, self._schedule_model, file_mode)
            window.appActionTriggered[AppAction, QWidget].connect(self.on_app_action)
            window.appActionTriggered[AppAction, Path].connect(self.on_app_action)
            window.appActionTriggered[AppAction].connect(self.on_app_action)
            self._start_dialog = window
            return window
        else:
            return self.opened_start_dialog()

    def open_about_dialog(self) -> None:
        for widget in self.topLevelWidgets():
            if isinstance(widget, AboutDialog):
                return
        dialog = AboutDialog()
        dialog.exec()
        dialog.deleteLater()

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

    @staticmethod
    def set_shared_index(idx: QPersistentModelIndex) -> bool:
        """Sets a persistent index that can be shared across different models"""
        inst: AppCore = AppCore.instance()
        if inst:
            inst.setProperty("globalIndex", idx)
            return True
        return False

    @staticmethod
    def shared_index() -> QPersistentModelIndex:
        inst: AppCore = AppCore.instance()
        if inst:
            return inst.property("globalIndex")

    def db(self) -> QSqlDatabase | None:
        return self._db

    def restart(self) -> None:
        self.quit()
        os.execv(sys.executable, ["python"] + sys.argv)

    def on_quitting(self) -> None:
        print("Saving recent and pinned files")
        Settings.set_value("Application/recent", self._file_model.export_recent())
        Settings.set_value("Application/pinned", self._file_model.export_pinned())

        for path in self._clean_up_list:
            rmtree(path.as_posix(), True)
