from PyQt6.QtWidgets import QApplication, QTabBar
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtCore import QT_TR_NOOP as tr
from ui.UI_Core import MainView
from tcha.start import Start
from tcha.editor import EditorTab
from tcha.dbmodels import Scheduler, Courses
from tcha.lfio import LessonFile, XmlReader
from tcha.resmanager import ResourceContainer
from os.path import basename
import typing

class AppCore(QApplication):
    def __init__(self, argv: typing.List[str]) -> None:
        print("This is the app")
        super().__init__(argv)
        self.setStyle("windows11")

    def import_settings(self):
        pass

class MainWindow(MainView):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.tab_counter = 0
        self.scheduler = Scheduler("D:/Dokumente/Python Scripts/Educhart/db/lessondata.db")
        self.courses = Courses("D:/Dokumente/Python Scripts/Educhart/db/lessondata.db")
        print(self.scheduler)
        print(self.courses)

        self.create_start()
        self.connect_signals()
        self.set_close_buttons()

    def connect_signals(self) -> None:
        self.tab_widget.tabCloseRequested.connect(self.delete_tab)

    def set_close_buttons(self) -> None:
        self.tab_widget.tabBar().tabButton(0, QTabBar.ButtonPosition.RightSide).deleteLater()
        self.tab_widget.tabBar().setTabButton(0, QTabBar.ButtonPosition.RightSide, None)

    def create_start(self):
        startInst = Start(self.scheduler, self.courses, self)
        startInst.editorRequest.connect(self.create_editor)
        startInst.openFileRequest.connect(self.load_editor)
        self.tab_widget.addTab(startInst, tr("Start"))
        self.tab_widget.setCurrentIndex(self.tab_widget.indexOf(startInst))

    def create_editor(self) -> None:
        editorInst = EditorTab(self.courses, parent=self)
        editorInst.schedule.connect(self.scheduler.add_item)
        editorInst.nameChanged.connect(self.change_tab_name)
        self.tab_widget.addTab(editorInst, tr("Unnamed"))
        self.tab_widget.setCurrentIndex(self.tab_widget.indexOf(editorInst))
        self.courses.write_to_db()

    def load_editor(self, path: str) -> None:
        lessonfile = LessonFile("r", path)
        xml_data = lessonfile.xml()
        rescont = ResourceContainer()
        lesson, tablemodel = XmlReader.read_xml(xml_data, rescont, lessonfile)
        editorInst = EditorTab.from_saved_file(self.courses, lesson, tablemodel, rescont, lessonfile, self)
        editorInst.schedule.connect(self.scheduler.add_item)
        editorInst.nameChanged.connect(self.change_tab_name)
        self.tab_widget.addTab(editorInst, basename(path))
        self.tab_widget.setCurrentIndex(self.tab_widget.indexOf(editorInst))
        self.courses.write_to_db()

    def delete_tab(self, i: int) :
        print("Closing tab", i)
        widget = self.tab_widget.widget(i)
        if isinstance(widget, EditorTab):
            # Detach widget from tab first
            self.tab_widget.removeTab(i)
            widget.close_streams()  # Then clean up resources
            widget.deleteLater() 

    def change_tab_name(self, tab: EditorTab, name: str) -> None:
        index = self.tab_widget.indexOf(tab)
        self.tab_widget.setTabText(index, name)

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if isinstance(widget, EditorTab):
                widget.close()
        self.courses.write_to_db()
        super().closeEvent(a0)