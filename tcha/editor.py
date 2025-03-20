from PyQt6.QtWidgets import QInputDialog, QMessageBox, QApplication, QFileDialog
from PyQt6.QtGui import QAction, QClipboard
from PyQt6.QtCore import QModelIndex, QObject, QEvent, Qt, QRunnable, QThreadPool, QT_TR_NOOP as tr, pyqtSlot, pyqtSignal
from ui.ui_editor import EditorWidget
from ui.ui_toolsets import CellActions
from tcha.lesson import Lesson
from tcha.dbmodels import Courses, ScheduleItem
from tcha.resmanager import ResourceContainer, ResourceType, ResourceObject
from tcha.toolset import returnToolsets
from tcha.tablemodel import TableModel
from tcha.lfio import LessonFile
from tcha.elements.baseelement import BaseElement
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
    schedule = pyqtSignal(ScheduleItem)
    nameChanged = pyqtSignal(EditorWidget, str)

    def __init__(self, courses: Courses, rescont: ResourceContainer = ResourceContainer(), mode=EditorMode.New, parent=None) -> None:
        super().__init__(parent)
        # Models
        self.courses = courses
        self.lesson = Lesson(self.dt_DateTime.dateTime())
        self.schedule_item: ScheduleItem
        self.rescont = rescont
        self.lessonfile: LessonFile | None = None
        
        self.mode = mode

        self.toolsets: dict[str, int] = self.get_toolsets()

        self.connect_signals()
        self.cb_course.setModel(self.courses)
        self.cb_course.setCurrentIndex(0)
        print("Model", self.courses, self.cb_course.count())
        # self.cb_course.setCurrentIndex(self.cb_course.findData(self.lesson.course))
        self.set_duration()
        self.setMouseTracking(True)
        self.check_clipboard()

        if mode == EditorMode.New:
            self.set_table(2, 2)

    def connect_signals(self) -> None:
        self.spb_SaveButton.lbutton.clicked.connect(self.save_lesson)
        self.ac_save.triggered.connect(self.save_lesson)
        self.ac_save_copy.triggered.connect(lambda: self.save_lesson(True))
        self.pb_AddCourse.clicked.connect(self.add_course)
        self.cb_course.activated.connect(self.set_course)
        self.dt_DateTime.dateTimeChanged.connect(self.lesson.set_datetime)
        self.sb_LessonTime.valueChanged.connect(self.lesson.set_duration)
        self.te_comment.textChanged.connect(self.set_comment)

        self.table.cellEditorOpened.connect(self.on_cell_opened)
        self.table.cellEditorClosed.connect(self.on_cell_closed)
        self.table.elementEditorClosed.connect(lambda: self.set_toolbar(None))
        self.table.elementEditorOpened.connect(self.set_toolbar)

        self.table_toolset.ac_new_row.triggered.connect(lambda: self.tablemodel.insertRow(self.table.currentIndex().row()))
        self.table_toolset.ac_new_column.triggered.connect(lambda: self.tablemodel.insertColumn(self.table.currentIndex().column()))
        self.table_toolset.ac_delete_row.triggered.connect(self.on_about_to_remove_row)
        self.table_toolset.ac_delete_column.triggered.connect(self.on_about_to_remove_column)
        self.table_toolset.menu_element.triggered.connect(self.on_element_action)

        QApplication.clipboard().dataChanged.connect(self.check_clipboard)

    @classmethod
    def from_saved_file(cls: Self, courses: Courses, lesson: Lesson, tablemodel: TableModel, rescont: ResourceContainer, lessonfile: LessonFile, parent=None) -> Self:
        editor = cls(courses, rescont, EditorMode.Open, parent)
        editor.set_lesson(lesson)
        editor.table.setModel(tablemodel)
        editor.set_lessonfile(lessonfile)
        return editor

    def set_lessonfile(self, lessonfile: LessonFile) -> None:
        if self.mode == EditorMode.Open:
            self.lessonfile = lessonfile
        else:
            raise EditorModeError(f"Editor is in wrong mode to set a IO to serialised document: {EditorMode.New}")

    def set_lesson(self, lesson: Lesson) -> None:
        self.lesson = lesson
        # self.on_courses_changed()
        self.dt_DateTime.setDateTime(self.lesson.datetime)
        self.sb_LessonTime.setValue(self.lesson.duration)
        self.te_comment.setText(self.lesson.comment)
        if lesson.course not in self.courses:
            lesson.course.set_temporary(True)
            self.courses.add(lesson.course)
            self.cb_course.setCurrentIndex(-1)
        else:
            i = self.courses.index_from_id(lesson.course.ID)
            self.cb_course.setCurrentIndex(i)

    def save_lesson(self, save_copy=False) -> None:
        def save() -> None:
            self.spb_SaveButton.setDisabled(True)
            worker = SaveWorker(self.lessonfile, self.lesson, self.rescont, self.table.model())
            worker.signals.finished.connect(self._on_saving_finished)
            QThreadPool.globalInstance().start(worker)

        if self.lessonfile and not save_copy:
            save()
        else:
            path, suffix = QFileDialog.getSaveFileName(self, tr("Save lesson chart"), "", tr("Lesson file (*.lesson)"))
            if path:
                self.lessonfile = LessonFile("w", path)
                save()
        
    def _on_saving_finished(self) -> None:
        print("Save successfull")
        self.spb_SaveButton.setEnabled(True)
        self.nameChanged.emit(self, basename(self.lessonfile.path))

    def schedule_lesson(self, file: str) -> None:
        item = ScheduleItem(self.dt_DateTime.time(), self.dt_DateTime.date(), file, self.lesson.course.ID)
        self.schedule.emit(item)


    def add_course(self) -> None:
        cname, ok = QInputDialog.getText(None, tr("New Course"), tr("Course name"))

        if len(cname) == 0 and ok:
            dialog = QMessageBox(None)
            dialog.setWindowTitle(tr("No name entered"))
            dialog.setText(tr("Please enter a valid name."))
            dialog.setIcon(QMessageBox.Icon.Information)
            dialog.exec()
            self.add_course()
        elif cname not in self.courses.names() and ok:
            self.courses.new(cname)
        elif cname in self.courses.names() and ok:
            dialog = QMessageBox(None)
            dialog.setWindowTitle(tr("Existing course"))
            dialog.setText(tr("There is already a course with the same name.\nPlease enter a different name."))
            dialog.setIcon(QMessageBox.Icon.Information)
            dialog.exec()
            self.add_course()
        else:
            return

    def set_course(self) -> None:
        if self.cb_course.currentIndex != -1:
            self.lesson.set_course(self.cb_course.currentData())
            self.print_lesson()

    def set_duration(self) -> None:
        self.lesson.set_duration(self.sb_LessonTime.value())
        self.print_lesson()

    def set_comment(self) -> None:
        self.lesson.set_comment(self.te_comment.toPlainText())
        self.print_lesson()

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