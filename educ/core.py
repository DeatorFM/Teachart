from PyQt6 import QtWidgets
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtCore import QT_TR_NOOP as tr
from ui.UI_Core import MainView
from educ.start import Start
from educ.editor import EditorTab
from educ.dbmodels import Scheduler, Courses
import typing

class HTCore(QtWidgets.QApplication):
    def __init__(self, argv: typing.List[str]) -> None:
        super().__init__(argv)

    def import_settings(self):
        pass

class MainWindow(MainView):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.editors = []
        self.scheduler = Scheduler("D:/Dokumente/Python Scripts/HotTeacher/db/lessondata.db")
        self.courses = Courses("D:/Dokumente/Python Scripts/HotTeacher/db/lessondata.db")
        print(self.scheduler)
        print(self.courses)

        self.create_start()
        self.connect_signals()
        self.set_close_buttons()

    def connect_signals(self) -> None:
        self.tab_widget.tabCloseRequested.connect(self.delete_tab)

    def set_close_buttons(self) -> None:
        self.tab_widget.tabBar().tabButton(0, QtWidgets.QTabBar.ButtonPosition.RightSide).deleteLater()
        self.tab_widget.tabBar().setTabButton(0, QtWidgets.QTabBar.ButtonPosition.RightSide, None)

    def create_start(self):
        startInst = Start(self.scheduler, self.courses, self)
        startInst.editorRequest.connect(self.create_editor)
        self.tab_widget.addTab(startInst, tr("Start"))
        self.tab_widget.setCurrentIndex(self.tab_widget.indexOf(startInst))

    def create_editor(self) -> None:
        editorInst = EditorTab(self.courses, self)
        editorInst.schedule.connect(self.scheduler.add_item)
        self.tab_widget.addTab(editorInst, tr("Unnamed"))
        self.tab_widget.setCurrentIndex(self.tab_widget.indexOf(editorInst))
        self.courses.write_to_db()

    def delete_tab(self, i: int) :
        self.tab_widget.removeTab(i)

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        self.courses.write_to_db()
        super().closeEvent(a0)