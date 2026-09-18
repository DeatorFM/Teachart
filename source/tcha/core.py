from __future__ import annotations

import typing
from functools import cache
from os.path import abspath
from pathlib import Path
from shutil import rmtree
from threading import Lock

from PyQt6.QtCore import QT_TR_NOOP as tr
from PyQt6.QtCore import QDateTime, QObject, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtSql import QSqlDatabase, QSqlQuery
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QGraphicsScene,
    QInputDialog,
    QMessageBox,
)
from styling.theming import load_theme
from styling.utils import apply_style
from tcha.base import BaseMainWindow
from tcha.consts import AppState, DisplayMode
from tcha.dbmodels import (
    CourseModel,
    ScheduleModel,
    StudentModel,
    check_database,
    create_database,
)
from tcha.dialogs import DialogManager, Editor, PresenterView
from tcha.elements import get_all_definitions
from tcha.error import ErrorCode, IOLogger, StandardLogger
from tcha.lfio import LessonFile
from tcha.settings import AppInfo, Locale, ReturnFlags, Settings, Values
from tcha.start import OpenFileModel
from tcha.utils import WinApi, parse_args


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


class StateManager(QObject):
    """Object that manages states to control if certain operations in an app are allowed"""

    restartAuthorised = (
        pyqtSignal()
    )  # Is emitted when all files saving operations are completed and a restart is scheduled
    restartReqested = pyqtSignal()  # Emitted when a restart is scheduled but not authorised

    def __init__(self, dialog_manager: DialogManager, parent=None):
        super().__init__(parent)
        self._dmanager = dialog_manager
        self._states = AppState.Launching
        self._saving_ops = 0

    @property
    def states(self) -> AppState:
        return self._states

    def add_state(self, state: AppState) -> None:
        self._states |= state

    def remove_state(self, state: AppState) -> None:
        StandardLogger.info(
            f"Removed state: {state}",
            extra={"sender": "STATEMANAGER"},
        )
        self._states &= ~state

    def restart_allowed(self) -> bool:  # Add new conditions if necessary
        return (
            self._states & AppState.Restarting
            and self._saving_ops < 1
            and self._dmanager.all_closed()
        )

    def schedule_restart(self):
        self._states |= AppState.Restarting
        self.restartReqested.emit()
        StandardLogger.debug(
            "Restart as been scheduled and will be executed when possible",
            extra={"sender": "STATEMANAGER"},
        )
        if self.restart_allowed():
            self.restartAuthorised.emit()
            return

    def log_saving_operation(self) -> None:
        self._states |= AppState.Saving
        self._saving_ops += 1

    def remove_saving_operation(self) -> None:
        self._saving_ops -= 1

        if self._saving_ops < 1:
            self.remove_state(AppState.Saving)

        if self.restart_allowed():
            self.restartAuthorised.emit()

    def attempt_restart(self):
        if self.restart_allowed():
            self.restartAuthorised.emit()


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
    restartInitiated = pyqtSignal()

    def __init__(self, argv: list[str]) -> None:
        super().__init__(argv)
        self.setApplicationVersion(AppInfo.app_ver)
        self.setWindowIcon(QIcon(":/logo/logo_main"))

        self._db: QSqlDatabase | None = None
        self._dialog_manager = DialogManager()
        self._state_manager = StateManager(self._dialog_manager, self)
        self._presenter_view: PresenterView | None = None
        self._edefinitions = get_all_definitions()
        self._clean_up_list: list[Path] = []
        self._launch_config = parse_args()

        StandardLogger.init_logger(self._launch_config.logging_level)
        StandardLogger.info(
            f"Launched app with arguments: {self._launch_config}", extra={"sender": "APPCORE"}
        )

        self._load_settings()

        self._course_model = CourseModel(self._db)
        self._schedule_model = ScheduleModel(self._db)
        self._file_model = OpenFileModel(
            Settings.value("Application/recent"),
            Settings.value("Application/pinned"),
        )

        self.init_display_mode = WinApi.get_display_mode()
        StandardLogger.info(
            f"Initial display mode: {self.init_display_mode}", extra={"sender": "APPCORE"}
        )

        self.aboutToQuit.connect(self.on_quitting)
        self.screenAdded.connect(self.on_screen_changed)
        self.screenRemoved.connect(self.on_screen_changed)

        self._state_manager.restartReqested.connect(self._on_restart_requested)
        self._state_manager.restartAuthorised.connect(self.restart)

    @cache
    @staticmethod
    def arguments() -> list[str]:
        return super().arguments()

    def session_info(self) -> str:
        return f"""
Session-ID:    {self.sessionId()}
Debug ON:      {self._launch_config.debug}
Database file: {self._launch_config.test_params.get("db", Settings.value("User/dbpath"))}
Source-ID:     {self.source_id()}
Language:      {self._launch_config.test_params.get("language", Settings.value("User/language").name)}
Appearance:    {self._launch_config.test_params.get("theme", Settings.value("User/appearance"))}
"""

    def _load_settings(self) -> None:
        if not Settings.qsettings().allKeys() or self._launch_config.clean:
            self._first_time()
        if self._launch_config.test:
            self._set_launch_settings(
                dbpath=self._launch_config.test_params.get(
                    "db", Path(Settings.value("User/dbpath"))
                ),
                appearance=self._launch_config.test_params.get(
                    "theme", Settings.value("User/appearance")
                ),
                language=self._launch_config.test_params.get(
                    "language", Settings.value("User/language")
                ),
            )
        else:
            self._set_launch_settings(
                dbpath=Path(Settings.value("User/dbpath")),
                appearance=Settings.value("User/appearance"),
                language=Settings.value("User/language"),
            )
        self._state_manager.add_state(AppState.Running)

    def _set_launch_settings(self, *, dbpath: Path, appearance: str, language: Locale) -> None:
        """Applies settings of arguments"""
        if not Settings.qsettings().allKeys() or self._launch_config.clean:
            self._first_time()
            return

        if not IOLogger.logdir().exists():
            IOLogger.logdir().mkdir(parents=True, exist_ok=True)

        # Check database
        if dbpath.exists() and dbpath.is_file():
            db = QSqlDatabase.addDatabase("QSQLITE")
            db.setDatabaseName(str(dbpath))
            if db.open() and check_database(db):
                self._db = db
            else:
                StandardLogger.error(
                    f"Database invalid under path: {dbpath}", extra={"sender": "APPCORE"}
                )
                QMessageBox.information(
                    None,
                    tr("Database error"),
                    tr("The database found is invalid. A new database will be created."),
                )
                self._db = create_database(AppInfo.db_ver)
                Settings.set_value("User/dbpath", abspath(self._db.databaseName()))
        else:
            StandardLogger.error(
                f"Database not found under path: {dbpath}", extra={"sender": "APPCORE"}
            )
            QMessageBox.information(
                None,
                tr("Database error"),
                tr("The database could not be found. A new database will be created."),
            )
            self._db = create_database()
            Settings.set_value("User/dbpath", abspath(self._db.databaseName()))

        load_theme(appearance, self)
        apply_style(self)
        StandardLogger.debug(
            f"Launched with following settings:\n{self.session_info()}", extra={"sender": "APPCORE"}
        )

    def _first_time(self) -> None:
        qsettings = Values.default_qsettings(clean=self._launch_config.clean)
        Settings.set_qsettings(qsettings)
        Settings.set_value("Application/first_startup", False)
        self._db = create_database()
        Settings.set_value("User/dbpath", abspath(self._db.databaseName()))
        language = self.language_dialog()
        Settings.set_value("User/language", language.name)

    def connect_signals(self) -> None:
        self.aboutToQuit.connect(self.on_quitting)

    def debug_enabled(self) -> bool:
        return self._launch_config.debug

    def clean_mode_enabled(self) -> bool:
        return self._launch_config.clean

    @cache  # noqa: B019
    def source_id(self) -> str:
        def from_db() -> str:
            if self._db:
                query = QSqlQuery(self._db)
                query.prepare("SELECT value FROM metadata WHERE key = 'source_id'")
                if query.exec() and query.next():
                    return query.value(0)
                return "0"
            return "0"

        return self._launch_config.test_params.get("source_id", from_db())

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

    def show_startup_window(self) -> bool:
        """Returns startup window based on arguments on startup"""
        if not self._launch_config.opened_path:
            self.open_start_dialog()
            return True

        elif self._launch_config.opened_path.exists():
            if (
                self._launch_config.opened_path.is_file()
                and self._launch_config.opened_path.suffix == ".tch"
            ):
                wid = self.open_file(self._launch_config.opened_path)
                if not wid:
                    self.create_editor()
                    return True
                return True

        self.open_start_dialog()
        return True

    def opened_editors(self) -> list[Editor]:
        return self._dialog_manager.get_container("Editor").values()

    def open_paths(self) -> list[Path]:
        return [Path(editor.path()) for editor in self.opened_editors()]

    def open_dialog(self, wtype: str) -> None:
        match wtype:
            case "Editor":
                self.create_editor()
            case "StartWindow":
                self.open_start_dialog(True)
            case "DbManager":
                self.open_course_explorer()
            case "SettingsDialog":
                self.open_settings()
            case "AboutDialog":
                self.open_about_dialog()

    def _on_window_closed(self, wtype: str, wid: int):
        window: BaseMainWindow = self._dialog_manager.get_dialog(wtype, wid)
        StandardLogger.debug(f"Trying to close window  '{window}'.", extra={"sender": "APPCORE"})
        self._dialog_manager.mark_closed(wtype, wid)

        if not self.opened_editors():
            self._state_manager.remove_state(AppState.Editing)

        if self._state_manager.states & AppState.Restarting:
            self._state_manager.attempt_restart()

    def create_editor(self) -> int:
        """Creates an editor with a new LessonFile object and returns its window is (wid)"""
        lf = LessonFile()
        lf.open("w")
        editor_window: Editor = self._dialog_manager.open(
            "Editor", self._course_model, self._schedule_model, self._edefinitions, lf
        )
        editor_window.dialogCalled.connect(self.open_dialog)
        editor_window.fileOpened.connect(self.open_file)
        editor_window.fileSaving.connect(self._state_manager.log_saving_operation)
        editor_window.fileSaved.connect(self._state_manager.remove_saving_operation)
        editor_window.presenterActivated.connect(self.open_presenter)
        editor_window.presenterClosed.connect(self.close_presenter)
        editor_window.closed.connect(self._on_window_closed)
        editor_window.set_recent_files(self._file_model.export_recent_as_menu(6))
        self._clean_up_list.append(editor_window.resource_path)

        start_dialog = self._dialog_manager.get_dialog("StartWindow")
        if start_dialog:
            start_dialog.close()

        self._state_manager.add_state(AppState.Editing)
        editor_window.show()
        return editor_window.wid

    def open_file(self, path: Path, caller: BaseMainWindow | None = None) -> int:
        if path and path.exists() and path not in self.open_paths():
            editor_window = None
            wid = 0

            lf = LessonFile()
            if caller:
                lf.progressChanged.connect(caller.set_progress)
                translated_label = self.tr("Loading")
                status_label = f"{translated_label} {path.name}"
                caller.set_status_bar_msg(status_label)

            if lf.open("r", str(path)):
                editor_window: Editor = self._dialog_manager.open(
                    "Editor", self._course_model, self._schedule_model, self._edefinitions, lf
                )
                editor_window.dialogCalled.connect(self.open_dialog)
                editor_window.fileOpened.connect(self.open_file)
                editor_window.fileSaving.connect(self._state_manager.log_saving_operation)
                editor_window.fileSaved.connect(self._state_manager.remove_saving_operation)
                editor_window.presenterActivated.connect(self.open_presenter)
                editor_window.presenterClosed.connect(self.close_presenter)
                editor_window.ui.ac_recent.setMenu(self._file_model.export_recent_as_menu(6))

                self._clean_up_list.append(Path(lf.temppath))
                self._clean_up_list.append(editor_window.resource_path)

                if lf.logger.evaluate() == ErrorCode.NonCritical:
                    StandardLogger.error(
                        f"A file operation finished with errors for file at: {path}",
                        extra={"sender": "APPCORE"},
                    )
                    QMessageBox.warning(
                        editor_window,
                        self.tr("File reading error"),
                        self.tr(
                            "There was an error while reading the file. The document may not be displayed correctly."
                        ),
                    )

                if caller:
                    caller.reset_progress()
                start_dialog = self._dialog_manager.get_dialog("StartWindow")
                if start_dialog:
                    start_dialog.close()
                self._file_model.append_file(str(path))
                if editor_window:
                    editor_window.set_recent_files(self._file_model.export_recent_as_menu(6))
                    self._state_manager.add_state(AppState.Editing)
                    editor_window.show()
                    wid = editor_window.wid

            else:
                StandardLogger.critical(
                    f"A file operation failed for file at: {path}", extra={"sender": "APPCORE"}
                )
                QMessageBox.critical(
                    None,
                    self.tr("File reading error"),
                    self.tr(
                        "The file could not be read because it's either corrupted or has an invalid structure."
                    ),
                )

        else:
            QMessageBox.information(
                None,
                tr("Open lesson-file"),
                tr("File is already open or does not exist."),
            )

        return wid

    def open_course_explorer(self) -> None:
        dialog = self._dialog_manager.open(
            "DbManager", self._course_model, self._schedule_model, None
        )
        for editor in self.opened_editors():
            if editor == self.activeWindow():
                cid = editor.lesson.course_id
                if cid > 0:
                    dialog.set_course(cid)
                break
        dialog.exec()
        self._dialog_manager.mark_closed("DbManager")

    def open_settings(self, parent=None) -> None:
        dialog = self._dialog_manager.open(
            "SettingsDialog", self._course_model.database(), Settings.qsettings()
        )
        code = dialog.exec()
        if code == QDialog.DialogCode.Accepted:
            if dialog.return_flags & ReturnFlags.Restart:
                button = QMessageBox.question(
                    dialog,
                    self.tr("Changes require restart"),
                    self.tr("Changes will only take effect after a restart. Restart now?"),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if button == QMessageBox.StandardButton.Yes:
                    self._state_manager.schedule_restart()
                self._dialog_manager.mark_closed("SettingsDialog")
                return
            if dialog.return_flags & ReturnFlags.UpdateStyle:
                load_theme(Settings.value("User/appearance"), self)
            # ADD HANDLER FOR UpdateLocale AFTER TRANSLATIONS HAVE BEEN INPLEMENTED
        self._dialog_manager.mark_closed("SettingsDialog")

    def open_start_dialog(self, file_mode=False) -> None:
        window = self._dialog_manager.open(
            "StartWindow", self._file_model, self._schedule_model, file_mode
        )
        window.dialogCalled.connect(self.open_dialog)
        window.fileOpened.connect(self.open_file)
        window.closed.connect(self._on_window_closed)
        window.show()

    def open_about_dialog(self) -> None:
        dialog = self._dialog_manager.open("AboutDialog")
        dialog.exec()
        self._dialog_manager.mark_closed("AboutDialog")

    def open_presenter(self, scene: QGraphicsScene, editor: Editor) -> None:
        presenter_view = self._dialog_manager.open("PresenterView", scene, editor)
        presenter_view.view.setScene(scene)
        presenter_view.set_current_editor(editor)
        presenter_view.rescale()
        presenter_view.finished.connect(self._disable_presenter_mode)
        self.show_presenter()

    def show_presenter(self) -> None:
        if self._dialog_manager.is_opened("PresenterView"):
            pv = self._dialog_manager.get_dialog("PresenterView")
            if WinApi.get_display_mode() == DisplayMode.Extended:
                pv.showFullScreen()

            elif WinApi.get_display_mode() == DisplayMode.Duplicated:
                WinApi.set_display_mode(DisplayMode.Extended)
                QTimer.singleShot(500, lambda: pv.showFullScreen())

    def close_presenter(self) -> None:
        presenter_view = self._dialog_manager.get_dialog("PresenterView")
        if presenter_view:
            presenter_view.view.setScene(None)
            presenter_view.close()
            self._dialog_manager.mark_closed("PresenterView")
            if self.init_display_mode != WinApi.get_display_mode():
                WinApi.set_display_mode(self.init_display_mode)

    def _disable_presenter_mode(self) -> None:
        for editor in self.opened_editors():
            editor.enable_presenter_mode(False)

    def on_screen_changed(self) -> None:
        if self._dialog_manager.is_opened("PresenterView"):
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
        StandardLogger.info("Restarting")
        if self._db is not None and self._db.isOpen():
            connection_name = self._db.connectionName()
            self._db.close()
            QSqlDatabase.removeDatabase(connection_name)

        self._load_settings()
        self._course_model = CourseModel(self._db)
        self._schedule_model = ScheduleModel(self._db)
        self._file_model = OpenFileModel(
            Settings.value("Application/recent"),
            Settings.value("Application/pinned"),
        )
        self._state_manager.remove_state(AppState.Restarting)
        self.show_startup_window()
        # self.setQuitOnLastWindowClosed(True)

    def _on_restart_requested(self):
        # self.setQuitOnLastWindowClosed(False)
        self._dialog_manager.close_all()
        self._state_manager.attempt_restart()

    def on_quitting(self) -> None:
        recent = self._file_model.export_recent()
        pinned = self._file_model.export_pinned()
        StandardLogger.debug(
            f"Saved recent and pinned files.\nRecent: {recent}\nPinned: {pinned}",
            extra={"sender": "APPCORE"},
        )
        Settings.set_value("Application/recent", recent)
        Settings.set_value("Application/pinned", pinned)

        for path in self._clean_up_list:
            rmtree(path.as_posix(), True)
