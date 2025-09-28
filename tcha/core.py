from PyQt6.QtWidgets import QApplication, QTabBar, QMessageBox, QInputDialog
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtCore import QDateTime, QSettings, pyqtSignal, QT_TR_NOOP as tr
from PyQt6.QtSql import QSqlDatabase
from ui.UI_Core import MainView
from tcha.start import Start
from tcha.editor import EditorTab
from tcha.dbmodels import CourseModel, ScheduleModel, StudentModel, create_database, check_database
from tcha.lfio import LessonFile, XmlReader
from tcha.resmanager import ResourceContainer
from tcha.status import StatusBar
from tcha.settings import Defaults, Locale, Settings, SettingsDialog, ReturnFlags
from os.path import basename, exists, abspath
import typing
import os
import sys


def test_lesson_models(db) -> tuple[CourseModel, ScheduleModel, StudentModel]:
    cmodel = CourseModel(db)
    cmodel.add_course("A1 Business (Oct 2023)", 90)
    cmodel.add_course("Feng", 45)
    cmodel.add_course("A1 Intensiv Aug 2024", 150)
    cmodel.add_course("Aoki", 60)

    smodel = ScheduleModel(db)
    smodel.add_schedule(1, QDateTime(2025, 6, 15, 14, 30, 0), 1263039429114341325, "D:/Dokumente/thislesson1.lesson")
    smodel.add_schedule(2, QDateTime(2025, 9, 6, 10, 15, 0), -232133682615210308, "D:/Dokumente/thislesson2.lesson") 
    smodel.add_schedule(3, QDateTime(2025, 8, 31, 12, 0, 0), -4626562671928849836, "D:/Dokumente/thislesson3.lesson")
    smodel.add_schedule(4, QDateTime(2025, 12, 20, 11, 20, 0), 3514653705253326921, "D:/Dokumente/thislesson4.lesson")

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

class AppCore(QApplication):
    def __init__(self, argv: typing.List[str]) -> None:
        super().__init__(argv)
        self.setStyle("windows11")

        self.qsettings = QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, "Teachart", "settings")
        self._db: QSqlDatabase | None = None

        if not self.qsettings.allKeys():
            print("Empty Settings: First initialisation")
            self._first_time()
        else:
            self._startup_checks()

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
            print(f"Data base file in '{dbpath}' not found.")
            db = QSqlDatabase.addDatabase("QSQLITE")
            db.setDatabaseName(dbpath)
            if db.open() and check_database(db):
                self._db = db
            else:
                QMessageBox.information(None, tr("Database error"), tr("The database found is invalid. A new database will be created."))
                self._db = create_database(Defaults.AppInfo.db_ver)
                self.qsettings.setValue("User/dbpath", abspath(self._db.databaseName()))
        else:
            QMessageBox.information(None, tr("Database error"), tr("The database could not be found. A new database will be created."))
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
        
    def language_dialog(self) -> Locale:
        language, result = QInputDialog.getItem(
            None, 
            "Language", 
            "Select your language",
            [value.value.name for value in list(Locale)]
            )
        if result:
            for i, value in enumerate(list(Locale)):
                if value.value.name == language:
                    return Locale.from_int(i)
        return getattr(Defaults, "language")
    
    def db(self) -> QSqlDatabase | None:
        return self._db        
    
    def restart(self) -> None:
        self.quit()
        os.execv(sys.executable, ['python'] + sys.argv)

class MainWindow(MainView):
    restartRequested = pyqtSignal()

    def __init__(self, db: QSqlDatabase, parent=None) -> None:
        super().__init__(parent)
        self.tab_counter = 0
        self.open_paths = []
        # cmodel, smodel, tmodel = test_lesson_models(database)
        # cmodel.cleanup()
        self.schedules = ScheduleModel(db, self)
        self.courses = CourseModel(db, self)

        self.setStatusBar(StatusBar(self))
        self.create_start()
        self.connect_signals()
        self.set_close_buttons()

    def connect_signals(self) -> None:
        self.tab_widget.tabCloseRequested.connect(self.delete_tab)
        self.tab_widget.currentChanged.connect(self.set_current_status_bar)

    def evoke_error(self, code: int, info: str = "") -> None:
        match code:
            case 1:
                print("Database not open")
            case 2: 
                print("")
            case 3:
                print("Structure wrong")

    def set_close_buttons(self) -> None:
        self.tab_widget.tabBar().tabButton(0, QTabBar.ButtonPosition.RightSide).deleteLater()
        self.tab_widget.tabBar().setTabButton(0, QTabBar.ButtonPosition.RightSide, None)

    def set_current_status_bar(self) -> None:
        print("Status bar changed")
        self.statusBar().set_container(self.tab_widget.currentWidget().statusbar)
        self.statusBar().reformat()

    def create_start(self):
        startInst = Start(self.schedules, self.courses, self)
        startInst.editorRequest.connect(self.create_editor)
        startInst.openFileRequest.connect(self.load_editor)
        startInst.settingsRequest.connect(self.open_settings)
        self.tab_widget.addTab(startInst, tr("Start"))
        self.tab_widget.setCurrentIndex(self.tab_widget.indexOf(startInst))
        self.set_current_status_bar()

    def create_editor(self) -> None:
        editorInst = EditorTab(self.courses, self.schedules, parent=self)
        editorInst.nameChanged.connect(self.change_tab_name)
        self.tab_widget.addTab(editorInst, tr("Unnamed"))
        self.tab_widget.setCurrentIndex(self.tab_widget.indexOf(editorInst))

    def load_editor(self, path: str) -> None:
        if not path in self.open_paths:
            self.open_paths.append(path)
            lessonfile = LessonFile("r", path)
            xml_data = lessonfile.xml()
            rescont = ResourceContainer()
            lesson, tablemodel = XmlReader.read_xml(xml_data, rescont, lessonfile)
            editorInst = EditorTab.from_saved_file(self.courses, self.schedules, lesson, tablemodel, rescont, lessonfile, self)
            editorInst.nameChanged.connect(self.change_tab_name)
            self.tab_widget.addTab(editorInst, basename(path))
            self.tab_widget.setCurrentIndex(self.tab_widget.indexOf(editorInst))
        else:
            QMessageBox.information(self, tr("Open lesson-file"), tr("File is already open."))

    def isopen(self, path: str) -> bool:
        self.tab_widget

    def delete_tab(self, i: int) :
        """Deletes a tab and in case of EditorTab checks if progess is unsaved."""
        print("Closing tab", i)
        widget = self.tab_widget.widget(i)
        if isinstance(widget, EditorTab):
            # Detach widget from tab first
            widget.table.close_current_editor()
            if widget.lessonfile:
                self.open_paths.remove(widget.lessonfile.path)
            if widget.changes_unsaved:
                msgBox = QMessageBox(QMessageBox.Icon.Information, "Teachart", tr("The document has been modified. Do you want to save your changes?"), QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel, self)
                rtrn = msgBox.exec()
                if rtrn == QMessageBox.StandardButton.Save:
                    saved = widget.save_lesson()
                    if saved:
                        pass
                    else:
                        return
                elif rtrn == QMessageBox.StandardButton.Discard:
                    pass
                elif rtrn == QMessageBox.StandardButton.Cancel:
                    return
                else:
                    raise ValueError("Messagebox returned unreadble value")
                
            self.tab_widget.removeTab(i)
            widget.close_streams()  # Then clean up resources
            widget.deleteLater() 

    def change_tab_name(self, tab: EditorTab, name: str) -> None:
        index = self.tab_widget.indexOf(tab)
        self.tab_widget.setTabText(index, name)
        self.open_paths.append(tab.lessonfile.path)

    def open_settings(self) -> None:
        return_flags = SettingsDialog.get_settings(self, self.courses.database(), Settings.qsettings())
        print("Return flags: ", return_flags)
        if ReturnFlags.Restart in return_flags:
            print("Restarting application")
            self.restartRequested.emit()
            return
        if ReturnFlags.UpdateStyle in return_flags:
            print("Updating application style")
            pass
        if ReturnFlags.UpdateLocale in return_flags:
            print("Updating language")
            pass

    def _update_appearance(self) -> None:
        ...

    def _update_style(self) -> None:
        ...

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        for i in range(self.tab_widget.count()):
            self.delete_tab(i)
        super().closeEvent(a0)