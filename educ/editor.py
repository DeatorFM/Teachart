from PyQt6.QtWidgets import QInputDialog, QMessageBox, QWidget, QApplication
from PyQt6.QtGui import QAction, QClipboard
from PyQt6.QtCore import QT_TR_NOOP as tr, pyqtSlot, pyqtSignal
from ui.UI_Editor import EditorWidget
from educ.lesson import Lesson
from educ.dbmodels import Courses, ScheduleItem
from educ.resmanager import ResourceContainer, ResourceType
from educ.toolset import returnToolsets, BaseToolset
from elements.baseelement import BaseElement
import os


class EditorTab(EditorWidget):
    widgetClicked = pyqtSignal(QWidget)
    focusConfirm = pyqtSignal(QWidget)
    schedule = pyqtSignal(ScheduleItem)

    def __init__(self, courses: Courses, parent=None) -> None:
        super().__init__(parent)
        # Models
        self.courses = courses
        self.lesson = Lesson(self.dt_DateTime.dateTime())
        self.schedule_item: ScheduleItem

        print("Init toolsets")
        self.toolsets: dict[str, BaseToolset] = self.get_toolsets()
        self.rescont = ResourceContainer()
        self._focussed_element = None
        self.issaved = False
        self.path: str

        self.connect_signals()
        self.cb_course.setModel(self.courses)
        self.cb_course.setCurrentIndex(0)
        print("Model", self.courses, self.cb_course.count())
        # self.cb_course.setCurrentIndex(self.cb_course.findData(self.lesson.course))
        self.set_duration()
        self.setMouseTracking(True)
        self.check_clipboard()

    def connect_signals(self) -> None:
        # self.courses.contentChanged.connect(self.on_courses_changed)
        self.spb_SaveButton.lbutton.clicked.connect(self.saveToLes)
        self.ac_save.triggered.connect(self.saveToLes)
        self.pb_AddCourse.clicked.connect(self.add_course)
        self.cb_course.activated.connect(self.set_course)
        self.dt_DateTime.dateTimeChanged.connect(self.lesson.set_datetime)
        self.sb_LessonTime.valueChanged.connect(self.lesson.set_duration)
        self.te_comment.textChanged.connect(self.set_comment)

        self.table_sizer.tableSize.connect(self.set_table)
        self.table.cellSelected.connect(self.activate_table_buttons)
        self.table.cellDeselected.connect(self.deactivate_table_buttons)

        self.pb_NewRow.clicked.connect(self.table.newRow)
        self.pb_NewColumn.clicked.connect(self.table.newColumn)
        self.pb_DeleteRow.clicked.connect(self.table.removeRow)
        self.pb_DeleteColumn.clicked.connect(self.table.removeColumn)
        self.menu_element.triggered.connect(self.on_element_action)
        self.pb_delete_element.clicked.connect(self.delete_element)
        self.pb_move_up.clicked.connect(lambda: self.move_element(-1))
        self.pb_move_down.clicked.connect(lambda: self.move_element(1))
        self.pb_close_elem_toolbar.clicked.connect(self.remove_focussed_element)

        QApplication.clipboard().dataChanged.connect(self.check_clipboard)

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

    def saveToLes(self) -> None:
        print("Saved")

    def schedule_lesson(self, file: str) -> None:
        item = ScheduleItem(self.dt_DateTime.time(), self.dt_DateTime.date(), file, self.lesson.course.ID)
        self.schedule.emit(item)

    # def set_list(self) -> None:
    #     self.cb_course.clear()
    #     self.cb_course.addItem(tr("No course"), CourseItem.no_course())
    #     for course in self.courses:
    #         self.cb_course.addItem(course.name, course)
    #     i = self.cb_course.findData(self.lesson.course, flags=Qt.MatchFlag.MatchContains)
    #     print(i)
    #     self.cb_course.setCurrentIndex(i)

    # def on_courses_changed(self) -> None:
    #     self.set_list()

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
        self.table.new_table(rows, columns)
        self.table_area_layout.setCurrentIndex(1)

    def activate_table_buttons(self) -> None:
        self.table_buttons.setEnabled(True)
        self.pb_add_element.setEnabled(True)
        self.set_focussed_element(None)

    def deactivate_table_buttons(self) -> None:
        self.table_buttons.setEnabled(False)
        self.pb_add_element.setEnabled(False)
        self.set_focussed_element(None)

    def on_element_action(self, action: QAction) -> None:
        if action.data() != "Clipboard":
            self.add_element(action)
        else:
            self.from_clipboard()

    def add_element(self, action: QAction) -> None:
        toolset = self.toolsets[action.data()]

        if toolset.restype == ResourceType.TEXT:
            respath = self.rescont.create(".html", ResourceType.TEXT)
            element = toolset.createElement(respath)
        elif toolset.restype != ResourceType.NONE:
            path = toolset.getResource()
            if path == None:
                return
            respath = self.rescont.save(path, toolset.restype)
            assert isinstance(respath, str)
            element = toolset.createElement(respath)
        else:
            element = toolset.createElement()

        print(self.rescont.contents())

        self.connect_element(element)

        self.table.add_element(element)

    def connect_element(self, element: BaseElement) -> None:
        element.focussed.connect(self.set_focussed_element)
        element.unfocussed.connect(self.remove_focussed_element)
        element.requestToolset.connect(lambda: self.set_toolbar(self._focussed_element))
        self.focusConfirm.connect(element.setFocussed)

    def delete_element(self) -> None:
        if self._focussed_element != None:
            print(self._focussed_element)
            self.table.delete_element(self._focussed_element)
            self.remove_focussed_element()

    def move_element(self, by: int) -> None:
        if self._focussed_element is not None:
            cell = self.table.model.cell_of(self._focussed_element)
            assert cell is not None
            cell.move(self._focussed_element, by)
            

    ### Toolset handling ###
    
    def get_toolsets(self) -> dict: 
        """Imports all Toolsets and integrates them into the ui. Adds actions to add elements to cells."""
        toolsets = returnToolsets(self.element_toolbar)
        for toolset in toolsets.values():
            print("Added", toolset, "with action", toolset.action())
            self.menu_element.addAction(toolset.action())
            self.elem_toolbar_layout.insertWidget(1, toolset)
        print(self.menu_element.actions())
        return toolsets

    def set_toolbar(self, widget: BaseElement|None) -> None:
        """Makes the toolset visible for the corresponding element."""
        for toolset in self.toolsets.values():
            toolset.hide()

        if widget != None:
            self.element_toolbar.show()
            self.element_toolbar.setFixedWidth(self.toolsets[widget.toolset].sizeHint().width()+10)
            self.toolsets[widget.toolset].show()
            print(widget.toolset)
            self.pb_delete_element.setEnabled(True)
            self.pb_move_up.setEnabled(True)
            self.pb_move_down.setEnabled(True)
        else:
            # print("No Element")
            for toolset in self.toolsets.values():
                toolset.hide()
            self.element_toolbar.hide()
            self.pb_delete_element.setEnabled(False)
            self.pb_move_up.setEnabled(False)
            self.pb_move_down.setEnabled(False)

    def set_focussed_element(self, widget: BaseElement|None):
        self._focussed_element = widget
        print(self._focussed_element)
        self.focusConfirm.emit(widget)
        self.set_toolbar(widget)
                
    def remove_focussed_element(self):
        self.set_focussed_element(None)
        self.setFocus()

    def is_focussed(self, widget: QWidget) -> bool:
        if widget == self._focussed_element: return True
        else: return False

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
            self.ac_FromClipboard.setEnabled(True)
            print("Text:", clipboard.mimeData().hasText())
            print("Image", clipboard.mimeData().hasImage())
        else:
            self.ac_FromClipboard.setEnabled(False)

    def from_clipboard(self) -> None:
        """Creates either a TextElement or a PictureElement with the contents of the clipboard."""
        clipboard = QApplication.clipboard()
        assert isinstance(clipboard, QClipboard)
        if clipboard.mimeData().hasImage():
            image = clipboard.image()  
            fname = self.rescont.create(".png", ResourceType.IMAGE)
            path = os.path.join(self.rescont.tempdir.name, fname)  
            image.save(path, "png")
            toolset = self.toolsets["PictureToolset"]
            element = toolset.createElement(path)
        elif clipboard.mimeData().hasText():
            fname = self.rescont.create(".html", ResourceType.TEXT)
            toolset = self.toolsets["TextToolset"]
            element = toolset.createElement(fname)
            element.paste()

        self.connect_element(element)
        self.table.add_element(element)
            
    # Event handler
    # def mousePressEvent(self, a0: QMouseEvent) -> None:
    #     self.remove_focussed_element()
    #     super().mousePressEvent(a0)

    # def resizeEvent(self, a0: QResizeEvent | None) -> None:
    #     rect = self.table.viewport().geometry()
    #     self.table.hheaders.setGeometry(
    #         rect.x(), rect.y() - self.table.margins.top(), rect.width(), self.table.margins.top()
    #     )
    #     self.table.vheaders.setGeometry(
    #         rect.x()  - self.table.margins.left(), rect.y(), self.table.margins.left(), rect.height()
    #     )
    #     super().resizeEvent(a0)