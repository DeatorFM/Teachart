from PyQt6.QtWidgets import QMessageBox, QApplication, QFileDialog
from PyQt6.QtGui import QAction, QClipboard
from PyQt6.QtCore import QModelIndex, QObject, QDateTime, QRunnable, QThreadPool, QT_TR_NOOP as tr, pyqtSlot, pyqtSignal
from ui.ui_editor import EditorWidget
from ui.ui_toolsets import CellActions
from tcha.lesson import Lesson
from tcha.dbmodels import CourseModel, CourseItem, FilteredCourseModel, ScheduleModel
from tcha.dbmanager import AddCourseDialog
from tcha.resmanager import ResourceContainer, ResourceType, ResourceObject
from tcha.toolset import returnToolsets
from tcha.tablemodel import TableModel
from tcha.lfio import LessonFile
from tcha.elements.baseelement import BaseElement
from tcha.status import StatusBarContainer
from typing import Self
from os.path import basename
import enum

class EditorModeError(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class EditorMode(enum.Enum):
    New = 0
    Open = 1

class SaveWorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)

class SaveWorker(QRunnable):
    def __init__(self, lessonfile, lesson, rescont, tablemodel):
        super().__init__()
        self._lessonfile: LessonFile = lessonfile
        self._lesson = lesson
        self._rescont = rescont
        self._tablemodel = tablemodel
        self.signals = SaveWorkerSignals()
        
    @pyqtSlot()
    def run(self):
        self._lessonfile.save(self._lesson, self._rescont, self._tablemodel)
        self.signals.finished.emit()

class EditorTab(EditorWidget):
    nameChanged = pyqtSignal(EditorWidget, str)
    messageChanged = pyqtSignal(str)

    def __init__(self, courses: CourseModel, schedules: ScheduleModel, rescont: ResourceContainer = ResourceContainer(), mode=EditorMode.New, parent=None) -> None:
        super().__init__(parent)
        # Models
        self.courses = FilteredCourseModel(courses, self)
        self.schedules = schedules
        self.lesson = Lesson(self.dt_DateTime.dateTime(), "", source_id=self.courses.source_id())
        self.rescont = rescont
        self.lessonfile: LessonFile | None = None
        
        self.mode = mode
        self.changes_unsaved = True

        self.toolsets: dict[str, int] = self.get_toolsets()
        size, current, goto = self.table.status()
        self.statusbar = StatusBarContainer(size, current, goto)

        self.connect_signals()
        self.cb_course.setModel(self.courses)
        self.cb_course.setModelColumn(1)
        print("Model", self.courses, self.cb_course.count())
        self.set_duration(self.sb_LessonTime.value())
        self.setMouseTracking(True)
        self.check_clipboard()

        if mode == EditorMode.New:
            self.set_table(2, 2)
            self.cb_course.setCurrentIndex(0)

    def connect_signals(self) -> None:
        self.courses.sourceModel().courseDataChanged.connect(self.on_course_data_changed)
        self.courses.rowsRemoved.connect(self.on_course_data_changed)
        self.courses.dataChanged.connect(self.on_course_data_changed)
        self.schedules.rowsAboutToBeRemoved.connect(self.check_schedule)

        self.spb_SaveButton.lbutton.clicked.connect(self.save_lesson)
        self.ac_save.triggered.connect(self.save_lesson)
        self.ac_save_copy.triggered.connect(lambda: self.save_lesson(True))
        self.pb_AddCourse.clicked.connect(self.add_course)
        self.cb_course.activated.connect(self.set_course)
        self.cb_course.lineEdit().textEdited.connect(self.filter_courses)
        self.dt_DateTime.dateTimeChanged.connect(self.set_datetime)
        self.apb_schedule.clicked.connect(self.on_schedule_button_pressed)
        self.sb_LessonTime.valueChanged.connect(self.set_duration)
        self.te_comment.textChanged.connect(self.set_comment)

        self.table.cellEditorOpened.connect(self.on_cell_opened)
        self.table.cellEditorClosed.connect(self.on_cell_closed)
        self.table.elementEditorClosed.connect(lambda: self.set_toolbar(None))
        self.table.elementEditorOpened.connect(self.set_toolbar)
        self.table.changeMade.connect(self.on_change_made)

        self.table_toolset.ac_new_row.triggered.connect(lambda: self.tablemodel.insertRow(self.table.currentIndex().row()))
        self.table_toolset.ac_new_column.triggered.connect(lambda: self.tablemodel.insertColumn(self.table.currentIndex().column()))
        self.table_toolset.ac_delete_row.triggered.connect(self.on_about_to_remove_row)
        self.table_toolset.ac_delete_column.triggered.connect(self.on_about_to_remove_column)
        self.table_toolset.menu_element.triggered.connect(self.on_element_action)

        QApplication.clipboard().dataChanged.connect(self.check_clipboard)

    @classmethod
    def from_saved_file(cls: Self, courses: CourseModel, schedules: ScheduleModel, lesson: Lesson, tablemodel: TableModel, rescont: ResourceContainer, lessonfile: LessonFile, parent=None) -> Self:
        changes = False
        if lesson.source_id != courses.source_id() and lesson.course_id != 0:
            button = QMessageBox.question(
                parent, 
                tr("Course not found"), 
                tr("This document's course has no record. Would you like to add it as a new course?"), 
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
            if button == QMessageBox.StandardButton.Yes:
                courses.add_course(lesson.course_name, lesson.duration)
                lesson.source_id = courses.source_id()
                lesson.course_id = courses.data(courses.index(courses.rowCount() - 1, 0))
                changes = True
        editor = cls(courses, schedules, rescont, EditorMode.Open, parent)
        editor.set_lesson(lesson)
        editor.table.setModel(tablemodel)
        editor.set_lessonfile(lessonfile, changes)
        if schedules.has_file(lessonfile.file_id()):
            editor.apb_schedule.check_fast()
        return editor

    def set_lessonfile(self, lessonfile: LessonFile, changes=False) -> None:
        if self.mode == EditorMode.Open:
            self.lessonfile = lessonfile
            self.changes_unsaved = changes
        else:
            raise EditorModeError(f"Editor is in wrong mode to set a IO to serialised document: {EditorMode.New}")

    def set_lesson(self, lesson: Lesson) -> None:
        self.lesson = lesson
        if lesson.source_id == self.courses.source_id():
            source_idx = self.courses.sourceModel().index_for_id(self.lesson.course_id)
            if source_idx.isValid():
                mapped_idx = self.courses.mapFromSource(source_idx)
                self.cb_course.setCurrentIndex(mapped_idx.row())
            else:
                self.cb_course.setCurrentIndex(0)
        else:
            self.cb_course.setCurrentIndex(0)
        self.dt_DateTime.setDateTime(self.lesson.datetime)
        self.sb_LessonTime.setValue(self.lesson.duration)
        self.te_comment.setText(self.lesson.comment)

    def save_lesson(self, save_copy=False) -> bool:
        def save() -> None:            
            worker = SaveWorker(self.lessonfile, self.lesson, self.rescont, self.table.model())
            worker.signals.finished.connect(self._on_saving_finished)
            QThreadPool.globalInstance().start(worker)

        self.spb_SaveButton.setEnabled(False)
        self.lesson.source_id = self.courses.source_id()
        if self.lessonfile and not save_copy:
            save()
            return True
        else:
            path, _ = QFileDialog.getSaveFileName(self, tr("Save lesson chart"), "", tr("Lesson file (*.lesson)"))
            if path:
                self.lessonfile = LessonFile("w", path)
                save()
                return True
            return False
        
    def _on_saving_finished(self) -> None:
        print("Save successfull")
        self.spb_SaveButton.setEnabled(True)
        self.nameChanged.emit(self, basename(self.lessonfile.path))
        self.changes_unsaved = False
        self.statusbar.show_message(tr("Saving finished"), 2000)
        self.schedule()

    def on_schedule_button_pressed(self) -> None:
        if self.apb_schedule.checked and self.lessonfile != None:
            print("Lesson file exisiting. Schedule.")
            self.schedule()
        else:
            if self.schedules.has_file(self.lessonfile.file_id()):
                idx = self.schedules.index_for_file_id(self.lessonfile.file_id())
                print("Index is valid ", idx.isValid())
                if idx.isValid():
                    self.schedules.removeRow(idx.row())
                    self.schedules.select()
                    print("Deleted scheule with file id: ", self.lessonfile.file_id())

    def schedule(self) -> None:
        """Creates a new schedule if not existing."""
        if self.apb_schedule.checked and not self.schedules.has_file(self.lessonfile.file_id()):
            course_id = self.courses.data(self.courses.index(self.cb_course.currentIndex(), 0))
            self.schedules.add_schedule(course_id, self.dt_DateTime.dateTime(), self.lessonfile.file_id(), self.lessonfile.path)
            self.lesson.source_id = self.courses.source_id()
            print("New schedule created for file_id: ", self.lessonfile.file_id())
        elif self.apb_schedule.checked and self.schedules.has_file(self.lessonfile.file_id()):
            print("File exists. Updating schedule")
            idx = self.schedules.index_for_file_id(self.lessonfile.file_id())
            if idx.isValid():
                schedule_id = self.schedules.data(idx)
                self.schedules.update_schedule(schedule_id, self.lesson.course_id, self.lesson.datetime, self.lessonfile.path)

    def check_schedule(self) -> None:
        """Changes button when schedule removed."""
        print("Schedule removed")
        if self.lessonfile:
            if self.apb_schedule.checked and self.schedules.has_file(self.lessonfile.file_id()):
                self.apb_schedule.start_animation()
 
    def add_course(self) -> None:
        def isvalid() -> bool:
            if name and duration > 0:
                return True
            return False
        ok, name, duration = AddCourseDialog.get_course_info(self)
        if ok and isvalid():
            self.courses.sourceModel().add_course(name, duration)
        elif ok and not isvalid():
            QMessageBox.warning(self, None, tr("Please enter a valid course name and duration."))
            self.add_course()
        else:
            return

    def set_course(self) -> None:
        if self.lesson.source_id != self.courses.source_id():
            self.lesson.source_id = self.courses.source_id()
        item = self.courses.getRow(self.cb_course.currentIndex())
        self.lesson.set_course(item.name, item.id)
        if item.duration > 0:
            self.sb_LessonTime.setValue(item.duration)
        self.print_lesson()
        self.changes_unsaved = True
            
    def filter_courses(self) -> None:
        self.cb_course.showPopup()
        self.courses.set_search_filter(self.cb_course.lineEdit().text())

    def on_course_data_changed(self) -> None:
        if self.courses.has_id(self.lesson.course_id) and self.lesson.course_id != 0:
            idx = self.courses.index_for_id(self.lesson.course_id)
            if idx.isValid():
                self.cb_course.setCurrentIndex(idx.row())
                return
        self.cb_course.setCurrentIndex(0)
        self.lesson.set_course("", 0)
    
    def set_datetime(self, datetime: QDateTime) -> None:
        self.lesson.set_datetime(datetime)
        self.changes_unsaved = True
        self.print_lesson()

    def set_duration(self, minutes: int) -> None:
        self.lesson.set_duration(minutes)
        self.changes_unsaved = True
        self.print_lesson()

    def set_comment(self) -> None:
        self.lesson.set_comment(self.te_comment.toPlainText())
        self.changes_unsaved = True
        self.print_lesson()

    def on_change_made(self) -> None:
        print("Change made")
        self.changes_unsaved = True

    # Table Managing Tools

    @pyqtSlot(int, int)
    def set_table(self, rows: int, columns: int) -> None:
        model = TableModel.new(rows, columns)
        self.table.setModel(model)

    @property
    def tablemodel(self) -> TableModel:
        return self.table.model()

    def on_cell_opened(self) -> None:
        if self.table.currentIndex().isValid() and self.table.editor:
            print("Index", self.table.currentIndex().row(), "|", self.table.currentIndex().column(), "is valid")
            self.table_toolset.cell_editor_actions.setEnabled(True)
    
    def on_cell_closed(self) -> None:
        self.table_toolset.cell_editor_actions.setEnabled(False)
        
    @pyqtSlot(QAction)
    def on_element_action(self, action: QAction) -> None:
        if action.data() != "Clipboard":
            self.add_element(action)
        else:
            self.from_clipboard()

    @pyqtSlot(QAction)
    def on_element_menu_action(self, action: QAction) -> None:
        editor = self.table.editor
        if editor:
            model = editor.model()
            index = editor.currentIndex()
            if action.data() == CellActions.Remove_Element:
                editor.close_current_editor()
                model.removeRow(index.row(), index)
            elif action.data() == CellActions.Move_Up:
                if index.row() > 0:
                    model.moveRow(QModelIndex(), index.row(), QModelIndex(), index.row() - 1)
            elif action.data() == CellActions.Move_Down:
                if not index.row() == model.rowCount() - 1:
                    model.moveRow(QModelIndex(), index.row(), QModelIndex(), index.row() + 1)

    def on_about_to_remove_row(self) -> None:
        current_row = self.table.currentIndex().row()
        self.table.close_current_editor()
        self.tablemodel.removeRow(current_row)

    def on_about_to_remove_column(self) -> None:
        current_column = self.table.currentIndex().column()
        self.table.close_current_editor()
        self.tablemodel.removeColumn(current_column)

    def add_element(self, action: QAction) -> None:
        print("Init adding model")
        toolset = self.toolsets_container.widget(self.toolsets[action.data()])

        if self.table.editor:

            if toolset.restype == ResourceType.TEXT:
                resobj = self.rescont.create(ResourceType.TEXT)
                model = toolset.createElement(resobj)
            elif toolset.restype != ResourceType.NONE:
                path = toolset.getResource()
                if path == None:
                    return
                resobj = self.rescont.save(toolset.restype, path)
                assert isinstance(resobj, ResourceObject)
                model = toolset.createElement(resobj)
            else:
                return

            print(self.rescont)

        
            print("Model add to cell")
            cell_model = self.table.editor.model()
            cell_model.add_model(model)
            

    ### Toolset handling ###
    
    def get_toolsets(self) -> dict: 
        """Imports all Toolsets and integrates them into the ui. Adds actions to add elements to cells."""
        imported_toolsets = returnToolsets(self)
        toolsets = {}
        for i, toolset in enumerate(imported_toolsets, 1):
            print("Added", toolset, "with action", toolset.action())
            self.table_toolset.menu_element.addAction(toolset.action())
            toolset.element_options_menu.triggered.connect(self.on_element_menu_action)
            toolsets[toolset.name] = i
            self.toolsets_container.addWidget(toolset)
        return toolsets

    def set_toolbar(self, widget: BaseElement | None) -> None:
        """Makes the toolset visible for the corresponding element."""
        print("Trying to set toolbar for editor", widget)
        if self.toolsets_container.currentIndex() != 0:
            try:
                self.toolsets_container.currentWidget().disconnect()
            except TypeError:
                pass

        if widget:
            print("Show toolbar")
            self.toolsets_container.setCurrentIndex(self.toolsets[widget.toolset])
            self.toolsets_container.currentWidget().connect_editor(widget)
        else:
            self.toolsets_container.setCurrentIndex(0)

    def print_lesson(self) -> None:
        try:
            print(self.lesson)
        except AttributeError:
            pass

    # Other
    def check_clipboard(self) -> None:
        clipboard = QApplication.clipboard()
        assert isinstance(clipboard, QClipboard)
        if clipboard.image() or clipboard.text():
            self.table_toolset.ac_FromClipboard.setEnabled(True)
            print("Text:", clipboard.mimeData().hasText())
            print("Image", clipboard.mimeData().hasImage())
        else:
            self.table_toolset.ac_FromClipboard.setEnabled(False)

    def from_clipboard(self) -> None:
        """Creates either a TextElement or a PictureElement with the contents of the clipboard."""
        clipboard = QApplication.clipboard()
        if clipboard:
            if clipboard.mimeData().hasImage():
                image = clipboard.image()  
                path = self.rescont.make_path(".png")
                image.save(path, "png")
                resobj = self.rescont.save(ResourceType.IMAGE, path)
                toolset = self.toolsets_container.widget(self.toolsets["PictureToolset"])
                element = toolset.createElement(resobj)
            elif clipboard.mimeData().hasText():
                resobj = self.rescont.create(ResourceType.TEXT)
                toolset = self.toolsets_container.widget(self.toolsets["TextToolset"])
                element = toolset.createElement(resobj)
                element.setPlainText(clipboard.text())

            self.table.add_element(element)

    def close_streams(self):
        self.rescont = None
        if self.lessonfile:
            self.lessonfile = None