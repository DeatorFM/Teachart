from os.path import basename

from PyQt6.QtWidgets import QWidget, QMessageBox, QApplication, QFileDialog, QMainWindow
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QModelIndex, QObject, QDateTime, QRunnable, QThreadPool, Qt, QT_TR_NOOP as tr, pyqtSlot, pyqtSignal

from tcha.table import CellEditor, Table
from ui.ui_editor import EditorView, BaseElementDefinitions
from ui.element_toolsets import CellActions
from tcha.lesson import Lesson
from tcha.dbmodels import CourseModel, FilteredCourseModel, ScheduleModel
from tcha.dbmanager import AddCourseDialog
from tcha.resmanager import ResourceContainer, ResourceType, ResourceObject
from tcha.tablemodel import TableModel
from tcha.lfio import LessonFile
from tcha.status import StatusBarContainer
from tcha.error import LFExceptions



class SaveWorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)

class SaveWorker(QRunnable):
    def __init__(self, path: str | None, lessonfile: LessonFile, lesson: Lesson, rescont: ResourceContainer, tablemodel: TableModel):
        super().__init__()
        self._path = path
        self._lf = lessonfile
        self._lesson = lesson
        self._rescont = rescont
        self._tablemodel = tablemodel
        self.signals = SaveWorkerSignals()
        
    @pyqtSlot()
    def run(self):
        self._lf.save(self._lesson, self._rescont, self._tablemodel, self._path)
        self.signals.finished.emit()

class EditorTab(QMainWindow):
    nameChanged = pyqtSignal(QWidget, str)
    messageChanged = pyqtSignal(str)

    def __init__(self, 
                 courses: CourseModel, 
                 schedules: ScheduleModel, 
                 edefinitions: dict[str, BaseElementDefinitions], 
                 lessonfile: LessonFile = LessonFile("w"), 
                 parent=None
                 ) -> None:
        super().__init__(parent, Qt.WindowType.Widget)
        self.ui = EditorView()
        self.ui.setUI(self)

        # Models
        self.courses = FilteredCourseModel(courses, self)
        self.schedules = schedules

        self.lessonfile = lessonfile
        self.lesson: Lesson
        self.rescont: ResourceContainer
        
        self.initialise_editor()

        # Attributes
        self.changes_unsaved = False if lessonfile.mode == "r" else True
        self.statusbar = StatusBarContainer(*self.ui.table.status())
        self.element_definitions = edefinitions
        self.toolsets = self.ui.add_toolsets(self, self.element_definitions)

        # Intial methods
        self.ui.add_element_actions(self.element_definitions)
        self.connect_signals()
        self.ui.cb_course.setModel(self.courses)
        self.ui.cb_course.setModelColumn(1)
        print("Model", self.courses, self.ui.cb_course.count())
        self.setMouseTracking(True)
        self.check_clipboard()

    def initialise_editor(self) -> tuple[LessonFile, ResourceContainer]:
        if self.lessonfile.mode == "w":
            self.set_lesson(Lesson(self.courses.source_id(), self.ui.dt_DateTime.dateTime()))
            self.rescont = ResourceContainer()
            self.set_table(2, 2)
            self.ui.cb_course.setCurrentIndex(0)
        
        elif self.lessonfile.mode == "r":
            self.rescont = self.lessonfile.get_resource_container()
            if self.rescont:
                tablemodel = self.lessonfile.get_table(self.rescont)
                if not self.lessonfile.error_handler.critical():
                    self.ui.table.setModel(tablemodel)
                    self.check_for_schedule(self.lessonfile.file_id)
   
                else:
                    raise LFExceptions.ReadError("Table structure")
                
                self.set_lesson(self.lessonfile.get_lesson())
            else:
                raise LFExceptions.ReadError("Resources")
        else:
            raise ValueError("LessonFile's mode is invalid. Must be 'w' or 'r'.")

    def connect_signals(self) -> None:
        self.courses.sourceModel().courseDataChanged.connect(self.on_course_data_changed)
        self.courses.rowsRemoved.connect(self.on_course_data_changed)
        self.courses.dataChanged.connect(self.on_course_data_changed)
        self.schedules.rowsAboutToBeRemoved.connect(self.check_for_schedule)

        self.ui.ac_save.triggered.connect(self.save_document)
        self.ui.ac_save_.triggered.connect(self.save_document)
        self.ui.ac_save_copy.triggered.connect(lambda: self.save_document(True))
        self.ui.ac_add_course.triggered.connect(self.add_course)
        self.ui.cb_course.activated.connect(self.set_course)
        self.ui.cb_course.lineEdit().textEdited.connect(self.filter_courses)
        self.ui.dt_DateTime.dateTimeChanged.connect(self.set_datetime)
        self.ui.ac_schedule.triggered.connect(self.set_unsaved)
        self.ui.sb_LessonTime.valueChanged.connect(self.set_duration)
        self.ui.te_comment.textChanged.connect(self.set_comment)

        self.ui.table.cellEditorOpened.connect(self.on_cell_opened)
        self.ui.table.cellEditorClosed.connect(self.on_cell_closed)
        self.ui.table.changeMade.connect(self.set_unsaved)

        self.ui.ac_new_row.triggered.connect(lambda: self.tablemodel.insertRow(self.ui.table.currentIndex().row()))
        self.ui.ac_new_column.triggered.connect(lambda: self.tablemodel.insertColumn(self.ui.table.currentIndex().column()))
        self.ui.ac_delete_row.triggered.connect(self.on_about_to_remove_row)
        self.ui.ac_delete_column.triggered.connect(self.on_about_to_remove_column)
        self.ui.menu_element.triggered.connect(self.on_element_action)

        QApplication.clipboard().dataChanged.connect(self.check_clipboard)
        
    def set_unsaved(self) -> None:
        self.changes_unsaved = True

    def set_lesson(self, lesson: Lesson) -> None:
        if lesson:
            if lesson.source_id == self.courses.source_id():
                source_idx = self.courses.sourceModel().index_for_id(lesson.course_id)
                if source_idx.isValid():
                    mapped_idx = self.courses.mapFromSource(source_idx)
                    self.ui.cb_course.setCurrentIndex(mapped_idx.row())
                else:
                    self.ui.cb_course.setCurrentIndex(0)
            else:
                button = QMessageBox.question(
                            self, 
                            tr("Course not found"), 
                            tr("This document's course has no record. Would you like to add it as a new course?"), 
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                            )
                if button == QMessageBox.StandardButton.Yes:
                    id = self.courses.sourceModel().add_course(lesson.course_name, lesson.duration)
                    lesson = Lesson(self.courses.source_id(), lesson.datetime, lesson.course_name, id, lesson.duration)
                    self.set_unsaved()
                    self.set_lesson(lesson)
                    return
                else:
                    self.ui.cb_course.setCurrentIndex(0)

            self.ui.dt_DateTime.setDateTime(lesson.datetime)
            self.ui.sb_LessonTime.setValue(lesson.duration)
            self.ui.te_comment.setText(lesson.comment)
            self.lesson = lesson
        else:
            raise ValueError
        
    def save_document(self, save_copy=False) -> bool:
        """Saves the entire document to a serialised file."""
        def save(path: str) -> None:            
            worker = SaveWorker(path, self.lessonfile, self.lesson, self.rescont, self.tablemodel)
            worker.signals.finished.connect(self._on_saving_finished)
            QThreadPool.globalInstance().start(worker)

        self.ui.ac_save.setEnabled(False)
        self.lesson.source_id = self.courses.source_id()
        if self.lessonfile.path and not save_copy:
            save(None)
            return True
        else:
            path, _ = QFileDialog.getSaveFileName(self, tr("Save lesson chart"), "", tr("Lesson file (*.lesson)"))
            if path:
                save(path)
                return True
            self.ui.ac_save.setEnabled(True)
            return False
        
    def _on_saving_finished(self) -> None:
        print("Save successfull")
        self.ui.ac_save.setEnabled(True)
        self.nameChanged.emit(self, basename(self.lessonfile.path))
        self.changes_unsaved = False
        self.statusbar.show_message(tr("Saving finished"), 2000)
        self.schedule()


    def schedule(self) -> None:
        """Creates a new schedule if not existing."""
        if self.ui.ac_schedule.state() == 2 and not self.schedules.has_file(self.lessonfile.file_id):
            course_id = self.courses.data(self.courses.index(self.ui.cb_course.currentIndex(), 0))
            self.schedules.add_schedule(course_id, self.dt_DateTime.dateTime(), self.lessonfile.file_id, self.lessonfile.path)
            self.lesson.source_id = self.courses.source_id()
            print("New schedule created for file_id: ", self.lessonfile.file_id)
            
        elif self.ui.ac_schedule.state() == 2 and self.schedules.has_file(self.lessonfile.file_id):
            print("File exists. Updating schedule")
            idx = self.schedules.index_for_file_id(self.lessonfile.file_id)
            if idx.isValid():
                schedule_id = self.schedules.data(idx)
                self.schedules.update_schedule(schedule_id, self.lesson.course_id, self.lesson.datetime, self.lessonfile.path)

        elif self.ui.ac_schedule.state() == 1 and self.schedules.has_file(self.lessonfile.file_id):
            idx = self.schedules.index_for_file_id(self.lessonfile.file_id)
            print("Index is valid ", idx.isValid())
            if idx.isValid():
                self.schedules.removeRow(idx.row())
                self.schedules.select()
                print("Deleted scheule with file id: ", self.lessonfile.file_id())

    def check_for_schedule(self, file_id: int) -> None:
        """Checks the button if schedule found."""
        if self.schedules.has_file(file_id):
            self.ui.ac_schedule.changeState(2)
        else:
            self.ui.ac_schedule.changeState(1)

    # Course related methods

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
        self.ui.cb_course.showPopup()
        self.courses.set_search_filter(self.cb_course.lineEdit().text())

    def on_course_data_changed(self) -> None:
        if self.courses.has_id(self.lesson.course_id) and self.lesson.course_id != 0:
            idx = self.courses.index_for_id(self.lesson.course_id)
            if idx.isValid():
                self.ui.cb_course.setCurrentIndex(idx.row())
                return
        self.ui.cb_course.setCurrentIndex(0)
        self.lesson.set_course("", 0)

    # Other Lesson setters
    
    def set_datetime(self, datetime: QDateTime) -> None:
        self.lesson.set_datetime(datetime)
        self.changes_unsaved = True
        self.print_lesson()

    def set_duration(self, minutes: int) -> None:
        self.lesson.set_duration(minutes)
        self.changes_unsaved = True
        self.print_lesson()

    def set_comment(self) -> None:
        self.lesson.set_comment(self.ui.te_comment.toPlainText())
        self.changes_unsaved = True
        self.print_lesson()


    # Table Managing Tools

    @property
    def table(self) -> Table:
        return self.ui.table

    @pyqtSlot(int, int)
    def set_table(self, rows: int, columns: int) -> None:
        model = TableModel.new(rows, columns)
        self.ui.table.setModel(model)

    @property
    def tablemodel(self) -> TableModel:
        return self.ui.table.model()

    def on_cell_opened(self, editor: CellEditor) -> None:
        if self.ui.table.currentIndex().isValid() and editor:
            print("Index", self.ui.table.currentIndex().row(), "|", self.ui.table.currentIndex().column(), "is valid")
            self.ui.cell_editor_actions.setEnabled(True)
            editor.connect_toolsets(self.toolsets)
    
    def on_cell_closed(self) -> None:
        self.ui.cell_editor_actions.setEnabled(False)
        for toolset in self.toolsets.values():
            toolset.setVisible(False)
        
    @pyqtSlot(QAction)
    def on_element_action(self, action: QAction) -> None:
        if action.data() != "Clipboard":
            self.add_element(action)
        else:
            self.from_clipboard()

    @pyqtSlot(QAction)
    def on_element_menu_action(self, action: QAction) -> None:
        editor = self.ui.table.editor
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
        current_row = self.ui.table.currentIndex().row()
        self.ui.table.close_current_editor()
        self.tablemodel.removeRow(current_row)

    def on_about_to_remove_column(self) -> None:
        current_column = self.ui.table.currentIndex().column()
        self.ui.table.close_current_editor()
        self.tablemodel.removeColumn(current_column)

    def add_element(self, action: QAction) -> None:
        print("Init adding model")
        definition = self.element_definitions[action.data()]

        if self.table.editor:

            resource = definition.get_file()                
            if resource:
                resobj = self.rescont.save(definition.type(), resource)
                assert isinstance(resobj, ResourceObject)
            else:
                resobj = self.rescont.create(definition.type())

            model = definition.create_model(resobj)

            print(self.rescont)
        
            print("Model add to cell")
            cell_model = self.table.editor.model()
            cell_model.add_model(model)
            

    def print_lesson(self) -> None:
        try:
            print(self.lesson)
        except AttributeError:
            pass

    def check_clipboard(self) -> None:
        mime = QApplication.clipboard().mimeData()
        if mime and (mime.hasImage() or mime.hasText()):
            self.ui.ac_from_clipboard.setEnabled(True)
        else:
            self.ui.ac_from_clipboard.setEnabled(False)

    def from_clipboard(self) -> None:
        """Creates either a TextElement or a PictureElement with the contents of the clipboard."""
        clipboard = QApplication.clipboard()
        if clipboard:
            if clipboard.mimeData().hasImage():
                image = clipboard.image()  
                path = self.rescont.make_path(".png")
                print(f"Save clipboard image to {path}")
                image.save(path, "png")
                resobj = self.rescont.save(ResourceType.IMAGE, path)
                definition = self.element_definitions["PictureElement"]
                model = definition.create_model(resobj)
            elif clipboard.mimeData().hasText():
                resobj = self.rescont.create(ResourceType.TEXT)
                definition = self.element_definitions["TextElement"]
                model = definition.create_model(resobj)
                model.setPlainText(clipboard.text())

            self.ui.table.add_element(model)

    def close_streams(self):
        self.rescont.close_file_streams()
        if self.lessonfile:
            self.lessonfile.close()