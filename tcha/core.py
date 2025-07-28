from PyQt6.QtWidgets import QApplication, QTabBar, QMessageBox
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtCore import QDateTime, QSettings, QT_TR_NOOP as tr
from PyQt6.QtSql import QSqlDatabase
from ui.UI_Core import MainView
from tcha.start import Start
from tcha.editor import EditorTab
from tcha.dbmodels import CourseModel, ScheduleModel, StudentModel
from tcha.lfio import LessonFile, XmlReader
from tcha.resmanager import ResourceContainer
from tcha.status import StatusBar
from os.path import basename, exists, abspath
import typing

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

        self.setOrganizationName("Florian Münstermann")
        self.setApplicationVersion("0.1")
        self.setApplicationName("Teachart")     

        settings = QSettings(self)
        settings.setDefaultFormat(QSettings.Format.IniFormat)
        init = settings.value("initiated")
        if not init:
            self.set_default_settings()

    def set_default_settings(self) -> None:
        ...


class MainWindow(MainView):
    __queries = {
        "metadata" : 
        """
        CREATE TABLE metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """,
        "Courses" :
        """
        CREATE TABLE Courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            duration INTEGER,
            temporary INTEGER DEFAULT 0 CHECK (temporary = 0 OR temporary = 1)
        )
        """,
        "Schedules" :
        """
        CREATE TABLE Schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            date INTEGER NOT NULL,
            time INTEGER NOT NULL,
            file_id TEXT NOT NULL,
            path TEXT NOT NULL,
            FOREIGN KEY (course_id) REFERENCES Courses(id) ON DELETE SET NULL
        )
        """,
        "Students" :
        """
        CREATE TABLE Students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            course_id INTEGER,
            email TEXT,
            FOREIGN KEY (course_id) REFERENCES Courses(id) ON DELETE SET NULL
        )
        """
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.tab_counter = 0
        database = self.open_database()
        # cmodel, smodel, tmodel = test_lesson_models(database)
        # cmodel.cleanup()
        self.schedules = ScheduleModel(database, self)
        self.courses = CourseModel(database, self)

        self.setStatusBar(StatusBar(self))
        self.create_start()
        self.connect_signals()
        self.set_close_buttons()

    def connect_signals(self) -> None:
        self.tab_widget.tabCloseRequested.connect(self.delete_tab)
        self.tab_widget.currentChanged.connect(self.set_current_status_bar)

    def open_database(self) -> QSqlDatabase:
        dbpath = QSettings().value("dbpath")
        if dbpath:
            if exists(dbpath):
                db = QSqlDatabase.addDatabase("QSQLITE")
                db.setDatabaseName(dbpath)
                db.open()
                if not self.check_database(db):
                    # ERR HANDLE
                    QMessageBox.information(self, tr("Invalid database file"), tr("The database has an invalid structure. \nA new file will be created."))
                    db = self.create_database()
            
        else:
            # ERR HANDLE
            QMessageBox.information(self, tr("Database could not be found"), tr("The database file does not exist or could not be found. \nA new file will be created."))
            db = self.create_database()

        if not db.isOpen():
            db.open()

        return db

    def create_database(self) -> QSqlDatabase:
        db = QSqlDatabase.addDatabase("QSQLITE")
        num = QDateTime.currentDateTime().toString("yyyyMMddHHmmss")
        db.setDatabaseName(f"db/tcha{num}.db")
        settings = QSettings()
        settings.setValue("dbpath", abspath(db.databaseName()))
        settings.sync()
        ok = db.open()
        print("Success", ok)

        for query in self.__queries.values():
            db.exec(query) 

        db.exec("""
            INSERT INTO metadata (key, value)
            VALUES ('source_id', hex(randomblob(16)))
        """)

        query = db.exec("SELECT value FROM metadata WHERE key = 'db_id'")
        if query.exec() and query.next():
            settings.setValue("source_id", query.value("value")) 
            settings.sync()

        db.exec("""
            INSERT OR IGNORE INTO Courses (id, name, duration, temporary) 
            VALUES (0, '', 0, 0)
        """)  

        if not self.check_database(db):
            #ERR HANDLE
            self.create_database()
        return db   

    def check_database(self, db: QSqlDatabase) -> bool:
        if not db.isOpen():
            db.open()

        query = db.exec("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        while query.next():
            print("Table", query.value("name"), ":", query.value("sql"))
            name = query.value("name")
            if self.__queries[name].strip() == query.value("sql").strip():
                return True
            else:
                self.evoke_error(3)
                return False

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
        self.tab_widget.addTab(startInst, tr("Start"))
        self.tab_widget.setCurrentIndex(self.tab_widget.indexOf(startInst))
        self.set_current_status_bar()

    def create_editor(self) -> None:
        editorInst = EditorTab(self.courses, self.schedules, parent=self)
        editorInst.nameChanged.connect(self.change_tab_name)
        self.tab_widget.addTab(editorInst, tr("Unnamed"))
        self.tab_widget.setCurrentIndex(self.tab_widget.indexOf(editorInst))

    def load_editor(self, path: str) -> None:
        lessonfile = LessonFile("r", path)
        xml_data = lessonfile.xml()
        rescont = ResourceContainer()
        lesson, tablemodel = XmlReader.read_xml(xml_data, rescont, lessonfile)
        editorInst = EditorTab.from_saved_file(self.courses, self.schedules, lesson, tablemodel, rescont, lessonfile, self)
        editorInst.nameChanged.connect(self.change_tab_name)
        self.tab_widget.addTab(editorInst, basename(path))
        self.tab_widget.setCurrentIndex(self.tab_widget.indexOf(editorInst))

    def delete_tab(self, i: int) :
        """Deletes a tab and in case of EditorTab checks if progess is unsaved."""
        print("Closing tab", i)
        widget = self.tab_widget.widget(i)
        if isinstance(widget, EditorTab):
            # Detach widget from tab first
            widget.table.close_current_editor()
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

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        for i in range(self.tab_widget.count()):
            self.delete_tab(i)
        super().closeEvent(a0)