from PyQt6 import QtGui
from PyQt6.QtWidgets import QVBoxLayout, QSpacerItem, QSizePolicy, QTreeWidgetItem, QFileDialog
from PyQt6.QtCore import pyqtSignal, QT_TR_NOOP as tr
from ui.UI_Start import StartWidget, FileWidget
from tcha.settings import loadSettings, saveSettings
from tcha.dbmodels import Scheduler, Courses
import os

class Start(StartWidget):
    editorRequest = pyqtSignal()
    openFileRequest = pyqtSignal(str)
    settingsRequest = pyqtSignal()

    def __init__(self, scheduler: Scheduler, courses: Courses, parent=None) -> None:
        super().__init__(parent)
        # Models
        self.settings = loadSettings()
        self.scheduler = scheduler
        self.courses = courses

        # Initial routines
        self.cw_MyCalendar.set_scheduler(self.scheduler)
        self.connect_signals()
        self.set_file_list(self.pinned_files_layout)
        self.set_file_list(self.luf_layout)

    def connect_signals(self) -> None:
        self.scheduler.contentChanged.connect(self.on_scheduler_content_changed)
        self.cw_MyCalendar.selectionChanged.connect(self.set_list)
        self.pb_NewLesson.clicked.connect(self.editorRequest.emit)
        self.pb_OpenLesson.clicked.connect(self.openFile)
        self.tw_UpcomingLessons.itemDoubleClicked.connect(lambda: self.openFile(self.tw_UpcomingLessons.selectedItems()[0].path))

    def on_scheduler_content_changed(self) -> None:
        self.cw_MyCalendar.repaint()
        self.set_list()

    def set_list(self) -> None:
        self.tw_UpcomingLessons.clear()
        selected_date = self.cw_MyCalendar.selectedDate()
        for item in self.scheduler.return_items_of_date(selected_date):
            tree_item = QTreeWidgetItem()
            name = self.courses.get_by_id(item.course).name
            if not name and item.course == 0:
                name = tr("Undefined course")
            tree_item.setText(0, self.courses.get_by_id(item.course).name)
            tree_item.setText(1, item.time.toString("hh:mm"))
            self.tw_UpcomingLessons.addTopLevelItem(tree_item)
            print("Added")

    def openFile(self) -> None:
        path, filter = QFileDialog.getOpenFileName(self, tr("Open Lesson-File"), "/home", "Lesson (*.lesson)")
        if path:
            self.openFileRequest.emit(path)

    def set_file_list(self, layout: QVBoxLayout) -> None:
        self.clear_layout(layout)
        if layout == self.pinned_files_layout:
            filelist: list = self.settings["Files"]["Pinned"]
            nofile = self.lb_NoPinnedData
            # print("PinnedFiles", filelist)
        else:
            filelist: list = self.settings["Files"]["LastUsed"]
            nofile = self.lb_NoUsedFiles
            # print("LUF", filelist)
        # print(filelist)

        if len(filelist) > 0:
            for fPath in filelist:
                fItem = self.create_file_item(fPath, self.is_pinned(fPath))
                fItem.change_pin_state(self.is_pinned(fPath))
                fItem.tb_pin.pressed.connect(lambda f=fPath: self.handle_pin(f))
                layout.addWidget(fItem)
            layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        else:
            layout.addWidget(nofile)
            layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

    def handle_pin(self, fPath: str) -> None:
        if self.is_pinned(fPath):
            # print("Unpinned", fPath)
            self.settings["Files"]["Pinned"].remove(fPath)
        elif self.is_pinned(fPath) == False:
            # print("Pinned", fPath)
            self.settings["Files"]["Pinned"].append(fPath)
        self.set_file_list(self.pinned_files_layout)
        self.set_file_list(self.luf_layout)

    def is_pinned(self, val: str) -> bool:
        if val in self.settings["Files"]["Pinned"]:
            return True
        else: 
            return False

    def create_file_item(self, fPath: str, checked: bool):
        # print(fPath)
        fItem = FileItem(fPath, self)
        fItem.setLabels()
        fItem.tb_pin.setChecked(checked)
        return fItem

    def clear_layout(self, layout: QVBoxLayout) -> None:
        if layout.count() > 0:
            for i in reversed(range(layout.count())): 
                item = layout.takeAt(i)
                if item.widget() != None:
                    item.widget().close()
                layout.removeItem(item)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        saveSettings(self.settings)
        return super().closeEvent(a0)

class FileItem(FileWidget):
    def __init__(self, path: str, parent=None):
        super().__init__(parent)
        self._path = path

    def setLabels(self) -> None:
        self.lb_Filename.setText(os.path.basename(self._path))
        self.lb_Path.setText(self._path)

    def change_pin_state(self, state: bool) -> None:
        icon = QtGui.QIcon()
        if state == False:
            icon.addPixmap(QtGui.QPixmap("resources/icons/ic_notpinned.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
            self.tb_pin.setIcon(icon)
        elif state == True:
            icon.addPixmap(QtGui.QPixmap("resources/icons/ic_pinned.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
            self.tb_pin.setIcon(icon)

    def path(self) -> str:
        return self._path

    def set_path(self, path: str) -> None:
        self._path = path
        
    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        self.setProperty("clicked", False)
        self.style().polish(self)
        self.clicked.emit(self._path) 
        super().mousePressEvent(a0)

    def mouseReleaseEvent(self, a0: QtGui.QMouseEvent) -> None:
        self.setProperty("clicked", True)
        self.style().polish(self)
        super().mouseReleaseEvent(a0)