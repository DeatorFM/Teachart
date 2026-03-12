from enum import Enum

import PyQt6.uic as uic
from PyQt6.QtCore import QT_TR_NOOP as tr
from PyQt6.QtCore import QItemSelection, QItemSelectionModel, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QDialog,
    QListWidgetItem,
    QMessageBox,
    QStyle,
    QStyledItemDelegate,
    QWidget,
)

from tcha.dbmodels import *
from tcha.settings import Settings
from ui.ui_dbmanager import AssignmentView, DbManagerView


class ScheduleDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        return super().paint(painter, option, index)


class DbManager(QDialog, DbManagerView):
    def __init__(
        self,
        course_model: CourseModel,
        schedule_model: ScheduleModel,
        parent=None,
        flags=Qt.WindowType.Dialog,
    ):
        super().__init__(parent, flags)
        self.setupUi(self)
        print("UI intitiated")
        qsettings = Settings.qsettings()

        self._course_model = course_model
        self._filtered_course_model = FilteredCourseModel(self._course_model, self)
        print("Course model initiated")
        print("Source id is: ", self._course_model.source_id())

        self._student_model = StudentModel(self._course_model.database(), self)
        self._filtered_student_model = FilteredStudentModel(self._student_model, self)
        print("Student model initiated")

        self._schedule_model = schedule_model
        self._filtered_schedule_model = FilteredScheduleModel(
            self._schedule_model, self
        )

        self.tv_courses.setModel(self._filtered_course_model)
        if not qsettings.value("Application/debug", False, bool):
            self.tv_courses.hideColumn(0)
            self.tv_courses.hideColumn(3)
        self.tv_courses.selectionModel().setCurrentIndex(
            self._filtered_course_model.index(0, 1),
            QItemSelectionModel.SelectionFlag.SelectCurrent,
        )
        self.tv_courses.selectionModel().select(
            QItemSelection(
                self._course_model.index(0, 0), self._course_model.index(0, 3)
            ),
            QItemSelectionModel.SelectionFlag.SelectCurrent,
        )

        self.tv_students.setModel(self._filtered_student_model)
        if not qsettings.value("Application/debug", False, bool):
            self.tv_students.hideColumn(0)

        self.tv_schedules.setModel(self._filtered_schedule_model)
        if not qsettings.value("Application/debug", False, bool):
            self.tv_schedules.hideColumn(0)
            self.tv_schedules.hideColumn(4)

        self.le_search.textChanged.connect(
            self._filtered_course_model.set_search_filter
        )
        self.pb_new_course.clicked.connect(self.add_course)
        self.pb_remove_course.clicked.connect(self.remove_course)
        self.tv_courses.selectionModel().currentRowChanged.connect(
            self.on_course_row_changed
        )
        self.tv_courses.selectionModel().selectionChanged.connect(
            self.on_course_selection_changed
        )
        self.pb_assign_students.clicked.connect(self._assign_button_clicked)
        self.pb_unassign_student.clicked.connect(self.unassign_student)
        self.pb_remove_student.clicked.connect(self.remove_student)
        self.le2_search.textChanged.connect(
            self._filtered_student_model.set_search_filter
        )
        self.pb_remove_schedule.clicked.connect(self.remove_schedule)
        self.cb_show_unassigned.checkStateChanged.connect(
            self.set_disable_assigned_students
        )
        self._course_model.courseDataChanged.connect(
            self._student_model.on_course_data_changed
        )
        self._course_model.courseDataChanged.connect(
            self._filtered_schedule_model.sourceModel().on_course_data_changed
        )
        self.tv_students.selectionModel().selectionChanged.connect(
            self.on_student_row_changed
        )
        self.tv_schedules.selectionModel().selectionChanged.connect(
            self.on_schedule_row_changed
        )

    def add_course(self) -> None:
        def isvalid() -> bool:
            if name and duration > 0:
                return True
            return False

        ok, name, duration = AddCourseDialog.get_course_info(self)
        if ok and isvalid():
            self._course_model.add_course(name, duration)
        elif ok and not isvalid():
            QMessageBox.warning(
                self,
                None,
                tr(
                    "Course name is empty or duration set to 0. Please enter a valid course name and duration."
                ),
            )
            self.add_course()
        else:
            return

    def set_course(self, id: int) -> None:
        idx = self._filtered_course_model.index_for_id(id)
        self.tv_courses.setCurrentIndex(idx)

    def remove_course(self) -> None:
        current_idx = self.tv_courses.selectionModel().currentIndex()
        source_idx = self._filtered_course_model.mapToSource(current_idx)
        deleted = self._course_model.removeRow(source_idx.row())
        print("Row has been deleted ", deleted)
        self._course_model.submitAll()
        self._course_model.select()
        self._course_model.courseDataChanged.emit()

    def on_course_row_changed(
        self, current: QModelIndex, previous: QModelIndex
    ) -> None:
        if current.row() == 0:
            self.pb_remove_course.setEnabled(False)
            self.cb_show_unassigned.setEnabled(True)
        else:
            self.pb_remove_course.setEnabled(True)
            self.cb_show_unassigned.setEnabled(False)

    def on_course_selection_changed(
        self, selected: QItemSelection, deselected: QItemSelection
    ) -> None:
        if selected:
            selected_index = selected.indexes()[0]
            source_index = self._filtered_course_model.mapToSource(selected_index)
            course_id = self._course_model.data(
                self._course_model.index(source_index.row(), 0)
            )
            if course_id == 0:
                self._filtered_student_model.set_exclusive_course_id(None)
                self._filtered_schedule_model.set_exclusive_course_id(None)
            else:
                self._filtered_student_model.set_exclusive_course_id(course_id)
                self._filtered_schedule_model.set_exclusive_course_id(course_id)

    def on_student_row_changed(
        self, selected: QItemSelection, deselected: QItemSelection
    ) -> None:
        if not selected.isEmpty():
            self.pb_unassign_student.setEnabled(True)
            self.pb_remove_student.setEnabled(True)
        else:
            self.pb_unassign_student.setEnabled(False)
            self.pb_remove_student.setEnabled(False)

    def set_disable_assigned_students(self, check_state: Qt.CheckState) -> None:
        if check_state == Qt.CheckState.Checked:
            self._filtered_student_model.set_exclude_assigned_students(True)
        else:
            self._filtered_student_model.set_exclude_assigned_students(False)

    def _assign_button_clicked(self) -> None:
        if not self._filtered_student_model.exclusive_course_id():
            self.new_student()
        else:
            self.assign_students()

    def new_student(self) -> None:
        print("Create student for current index")
        ok, name, course_id, email = AddStudentDialog.get_student_info(
            self,
            self._course_model,
            self._filtered_course_model.mapToSource(
                self.tv_courses.selectionModel().currentIndex()
            ).row(),
        )
        if ok:
            print("Add student with info: ", name, course_id, email)
            self._student_model.add_student(name, course_id, email)

    def assign_students(self) -> None:
        current_idx = self.tv_courses.selectionModel().currentIndex()
        source_idx = self._filtered_course_model.mapToSource(current_idx)
        course_id = self._course_model.data(
            self._course_model.index(source_idx.row(), 0)
        )
        course_name = self._course_model.data(
            self._course_model.index(source_idx.row(), 1)
        )
        code, students = AssignmentDialog.get_students(
            self, self._student_model, course_id, course_name
        )
        if code == StudentDialogReturnCode.Assignment and students:
            for student in students:
                student.course_id = course_id
                print(student)
                self._student_model.setData(
                    self._student_model.index_for_id(student.id, 2), course_id
                )
        elif code == StudentDialogReturnCode.Creation:
            self.new_student()

    def unassign_student(self) -> None:
        if self.tv_students.selectionModel().hasSelection():
            current_idx = self.tv_students.selectionModel().currentIndex()
            self._filtered_student_model.setData(
                self._filtered_student_model.index(current_idx.row(), 2),
                0,
                Qt.ItemDataRole.EditRole,
            )

    def remove_student(self) -> None:
        if self.tv_students.selectionModel().hasSelection():
            current_idx = self.tv_students.selectionModel().currentIndex()
            source_idx = self._filtered_student_model.mapToSource(current_idx)
            self._student_model.removeRow(source_idx.row())
            self._student_model.select()

    def on_schedule_row_changed(
        self, selected: QItemSelection, deselected: QItemSelection
    ) -> None:
        if not selected.isEmpty():
            self.pb_remove_schedule.setEnabled(True)
        else:
            self.pb_remove_schedule.setEnabled(False)

    def remove_schedule(self) -> None:
        if self.tv_schedules.selectionModel().hasSelection():
            current_idx = self.tv_schedules.selectionModel().currentIndex()
            source_idx = self._filtered_schedule_model.mapToSource(current_idx)
            self._schedule_model.removeRow(source_idx.row())
            # self._schedule_model.rowsRemoved.emit()
            self._schedule_model.select()

    # def _on_student_clicked(self, index: QModelIndex) -> None:
    #     self._student_model.set_old_value(index)


class AddCourseDialog(QDialog):
    def __init__(self, parent=None, flags=Qt.WindowType.Dialog):
        super().__init__(parent, flags)
        self.ui = uic.loadUi("ui/ui_addcourse.ui", self)

    def name(self) -> str:
        return self.ui.le_cname.text()

    def duration(self) -> int:
        return self.ui.sb_duration.value()

    @staticmethod
    def get_course_info(parent: QWidget) -> tuple[bool, str, int]:
        dialog = AddCourseDialog(parent)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            return True, dialog.name(), dialog.duration()
        return False, dialog.name(), dialog.duration()


class StudentDialogReturnCode(Enum):
    NoAssignment = 0
    Assignment = 1
    Creation = 2


class AddStudentDialog(QDialog):
    def __init__(
        self,
        course_model: CourseModel,
        parent=None,
        current_id=0,
        flags=Qt.WindowType.Dialog,
    ):
        super().__init__(parent, flags)
        self.ui = uic.loadUi("ui/ui_addstudent.ui", self)

        self.ui.cb_courses.setModel(course_model)
        self.ui.cb_courses.setModelColumn(1)
        print(
            "Set current index for id: ",
            current_id,
            "that is ",
            course_model.index_for_id(current_id).row(),
        )
        self.ui.cb_courses.setCurrentIndex(course_model.index_for_id(current_id).row())

    def name(self) -> str:
        return self.ui.le_name.text()

    def email(self) -> str:
        return self.ui.le_email.text()

    def course(self) -> int:
        current_index = self.ui.cb_courses.currentIndex()
        model = self.ui.cb_courses.model()
        return model.data(model.index(current_index, 0), Qt.ItemDataRole.DisplayRole)

    @staticmethod
    def get_student_info(
        parent: QWidget, course_model: CourseModel, current_id: int
    ) -> tuple[StudentDialogReturnCode, str, int, str]:
        dialog = AddStudentDialog(course_model, parent, current_id)
        result = dialog.exec()
        print(result)
        if result == QDialog.DialogCode.Accepted:
            return True, dialog.name(), dialog.course(), dialog.email()
        return False, dialog.name(), dialog.course(), dialog.email()


class AssignmentDialog(QDialog, AssignmentView):
    def __init__(
        self,
        course_id: int,
        student_model: StudentModel,
        parent=None,
        flags=Qt.WindowType.Dialog,
    ):
        super().__init__(parent, flags)
        self.setupUi(self)

        self.items: list[QListWidgetItem] = []
        self.student_creation_requested = False

        self._filtered_student_model = FilteredStudentModel(student_model)
        self._filtered_student_model.set_excluded_course_id(course_id)

        self.tv_students.setModel(self._filtered_student_model)
        self.tv_students.hideColumn(0)

        self.le_search.textChanged.connect(
            self._filtered_student_model.set_search_filter
        )
        self.tv_students.doubleClicked.connect(self.add_student)
        self.lw_selected_students.itemClicked.connect(self.remove_student)
        self.pb_new_student.clicked.connect(self.new_student_creation_requested)

    def add_student(self, index: QModelIndex) -> None:
        student: StudentItem = self._filtered_student_model.getRow(index)
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DockWidgetCloseButton)
        self._filtered_student_model.add_excluded_student_id(student.id)
        item = QListWidgetItem(icon, student.name, self.lw_selected_students)
        item.setData(Qt.ItemDataRole.UserRole, student)
        item.setToolTip(tr("Click to exclude."))
        self.items.append(item)
        self.lw_selected_students.addItem(item)
        self.lw_selected_students.scrollToItem(item)

    def remove_student(self, item: QListWidgetItem) -> None:
        item = self.lw_selected_students.takeItem(
            self.lw_selected_students.indexFromItem(item).row()
        )
        student_id = item.data(Qt.ItemDataRole.UserRole).id
        self.items.remove(item)
        self._filtered_student_model.remove_excluded_student_id(student_id)

    def student_items(self) -> list[StudentItem]:
        return [item.data(Qt.ItemDataRole.UserRole) for item in self.items]

    def new_student_creation_requested(self) -> None:
        self.student_creation_requested = True
        self.reject()

    @staticmethod
    def get_students(
        parent: QWidget, student_model: StudentModel, excluded_course_id: int, name: str
    ) -> tuple[StudentDialogReturnCode, list[StudentItem]]:
        dialog = AssignmentDialog(excluded_course_id, student_model, parent)
        dialog.setWindowTitle("{} {}".format(tr("Assign students to course: "), name))
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            return StudentDialogReturnCode.Assignment, dialog.student_items()
        elif dialog.student_creation_requested:
            return StudentDialogReturnCode.Creation, dialog.student_items()
        else:
            return StudentDialogReturnCode.NoAssignment, dialog.student_items()


class RecordView(QDialog):
    managerCalled = pyqtSignal(int)

    def __init__(
        self,
        course_id: int,
        course_model: CourseModel,
        parent=None,
        flags=Qt.WindowType.Dialog,
    ):
        super().__init__(parent, flags)
        self.ui = uic.loadUi("ui/record_view.ui", self)

        student_model = StudentModel(course_model.database())
        self.filtered_student_model = FilteredStudentModel(student_model)
        self.filtered_student_model.set_exclusive_course_id(course_id)
        self.ui.tv_students.setModel(self.filtered_student_model)
        self.ui.tv_students.hideColumn(0)
        self.ui.tv_students.hideColumn(2)

        name = course_model.data(
            course_model.index(course_model.index_for_id(course_id).row(), 1)
        )
        wtprefix = tr("Course Record: ")
        self.setWindowTitle("{}{}".format(wtprefix, name))

        self.ui.pb_edit.clicked.connect(lambda: self.managerCalled.emit(course_id))
        self.ui.pb_edit.clicked.connect(self.close)
        self.ui.pb_close.clicked.connect(self.close)
