from PyQt6.QtWidgets import QVBoxLayout, QSplitter, QCalendarWidget, QTimeEdit, QCheckBox, QTabWidget, QWidget, QComboBox, QSpinBox, QStyledItemDelegate, QDialog, QHBoxLayout, QFrame, QListWidget, QLineEdit, QTreeView, QSpacerItem, QSizePolicy, QTableView, QDialogButtonBox, QStyleOptionViewItem, QPushButton
from PyQt6.QtCore import QCoreApplication, Qt, QSize, QModelIndex, QT_TR_NOOP as tr
from PyQt6.QtGui import QPainter
from PyQt6.QtSql import QSqlRelationalDelegate
from tcha.dbmodels import CourseModel
from ui.commons import IconButton


class CourseDelegate(QStyledItemDelegate):
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QLineEdit | QSpinBox:
        if index.column() == 1:
            return QLineEdit(parent)
        elif index.column() == 2:
            return QSpinBox(parent)
        
    def setEditorData(self, editor: QLineEdit | QSpinBox, index: QModelIndex):
        if isinstance(editor, QLineEdit):
            editor.setText(index.data(Qt.ItemDataRole.DisplayRole))
        elif isinstance(editor, QSpinBox):
            editor.setMinimum(0)
            editor.setMaximum(1000)
            current_value = index.data(Qt.ItemDataRole.EditRole)
            editor.setValue(int(current_value))

    def updateEditorGeometry(self, editor: QLineEdit | QSpinBox, option: QStyleOptionViewItem, index: QModelIndex):
        editor.setGeometry(option.rect)

    def setModelData(self, editor: QWidget, model: CourseModel, index: QModelIndex):
        super().setModelData(editor, model, index)
        model.sourceModel().submitAll()
        model.sourceModel().courseDataChanged.emit()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return QSize(option.rect.size().width(), 30)

class ProxyStudentDelegate(QSqlRelationalDelegate):
    def createEditor(self, parent, option, index):
        proxy = index.model()
        source_index = proxy.mapToSource(index)
        return super().createEditor(parent, option, source_index)
    
    def setEditorData(self, editor, index):
        proxy = index.model()
        source_index = proxy.mapToSource(index)
        super().setEditorData(editor, source_index)
    
    def setModelData(self, editor, model, index):
        base_model = model.sourceModel()
        source_index =  model.mapToSource(index)
        super().setModelData(editor, base_model, source_index)

class ProxyScheduleDelegate(QSqlRelationalDelegate):
    def createEditor(self, parent, option, index):
        proxy = index.model()
        source_index = proxy.mapToSource(index)
        return super().createEditor(parent, option, source_index)
    
    def setEditorData(self, editor, index):
        proxy = index.model()
        source_index = proxy.mapToSource(index)
        super().setEditorData(editor, source_index)
    
    def setModelData(self, editor, model, index):
        base_model = model.sourceModel()
        source_index =  model.mapToSource(index)
        super().setModelData(editor, base_model, source_index)

    def sizeHint(self, option, index):
        return QSize(option.rect.size().width(), 30)

class DbManagerView:

    def setupUi(self, dbmanager):
        dbmanager.setObjectName("dbmanager")
        dbmanager.resize(900, 600)
        dbmanager.setMinimumSize(QSize(700, 400))

        hl1 = QHBoxLayout(dbmanager)
        hl1.setObjectName("hl1")

        self.splitter = QSplitter(dbmanager)
        self.splitter.setOrientation(Qt.Orientation.Horizontal)

        self.left_side = QWidget(dbmanager)
        self.left_side.setObjectName("left_side")

        vl1 = QVBoxLayout()
        vl1.setContentsMargins(-1, -1, 0, -1)
        vl1.setObjectName("vl1")
        self.splitter.addWidget(self.left_side)

        hl3 = QHBoxLayout()
        hl3.setContentsMargins(-1, 0, -1, -1)
        hl3.setObjectName("hl3")

        self.pb_new_course = IconButton("resources/icons/ic_new.svg", dbmanager)
        self.pb_new_course.setText("")
        self.pb_new_course.setObjectName("pb_new_course")
        hl3.addWidget(self.pb_new_course)

        self.pb_remove_course = IconButton("resources/icons/ic_trash.svg", dbmanager)
        self.pb_remove_course.setText("")
        self.pb_remove_course.setObjectName("pb_remove_course")
        hl3.addWidget(self.pb_remove_course)

        self.le_search = QLineEdit(dbmanager)
        self.le_search.setObjectName("le_search")
        hl3.addWidget(self.le_search)
        vl1.addLayout(hl3)

        self.tv_courses = QTreeView(dbmanager)
        self.tv_courses.setMinimumSize(QSize(0, 0))
        self.tv_courses.setObjectName("tv_courses")
        self.tv_courses.setItemDelegate(CourseDelegate(self.tv_courses))
        self.tv_courses.setSelectionMode(QTreeView.SelectionMode.SingleSelection)
        self.tv_courses.setAlternatingRowColors(True)
        self.tv_courses.setSortingEnabled(True)
        vl1.addWidget(self.tv_courses)

        self.left_side.setLayout(vl1)
        self.splitter.addWidget(self.left_side)

        self.data_tabs = QTabWidget(dbmanager)
        self.data_tabs.setObjectName("data_tabs")
        self.splitter.addWidget(self.data_tabs)

        # Student Tab

        self.student_tab = QWidget()
        self.student_tab.setObjectName("student_tab")

        vl2 = QVBoxLayout(self.student_tab)
        vl2.setContentsMargins(-1, -1, -1, 0)
        vl2.setObjectName("vl2")

        hl2 = QHBoxLayout()
        hl2.setContentsMargins(-1, 0, -1, -1)
        hl2.setObjectName("hl2")

        self.pb_assign_students = IconButton("resources/icons/ic_assign.svg", self.student_tab)
        self.pb_assign_students.setText("")
        self.pb_assign_students.setObjectName("pb_assign_students")
        hl2.addWidget(self.pb_assign_students)

        self.pb_unassign_student = IconButton("resources/icons/ic_unassign.svg", self.student_tab)
        self.pb_unassign_student.setText("")
        self.pb_unassign_student.setObjectName("pb_unassign_student")
        self.pb_unassign_student.setEnabled(False)
        hl2.addWidget(self.pb_unassign_student)

        self.pb_remove_student = IconButton("resources/icons/ic_trash.svg", self.student_tab)
        self.pb_remove_student.setText("")
        self.pb_remove_student.setObjectName("pb_remove_student")
        self.pb_remove_student.setEnabled(False)
        hl2.addWidget(self.pb_remove_student)

        ln1 = QFrame(parent=self.student_tab)
        ln1.setFrameShape(QFrame.Shape.VLine)
        ln1.setFrameShadow(QFrame.Shadow.Sunken)
        ln1.setObjectName("ln1")
        hl2.addWidget(ln1)

        self.le2_search = QLineEdit(self.student_tab)
        self.le2_search.setMinimumSize(QSize(200, 0))
        self.le2_search.setObjectName("le2_search")
        hl2.addWidget(self.le2_search)

        ln2 = QFrame(parent=self.student_tab)
        ln2.setFrameShape(QFrame.Shape.VLine)
        ln2.setFrameShadow(QFrame.Shadow.Sunken)
        ln2.setObjectName("ln2")
        hl2.addWidget(ln2)

        self.cb_show_unassigned = QCheckBox(self.student_tab)
        self.cb_show_unassigned.setObjectName("cb_show_unassigned")
        hl2.addWidget(self.cb_show_unassigned)

        spacerItem = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        hl2.addItem(spacerItem)
        vl2.addLayout(hl2)

        self.tv_students = QTableView(parent=self.student_tab)
        self.tv_students.setObjectName("tv_students")
        self.tv_students.setItemDelegate(ProxyStudentDelegate(self.tv_students))
        self.tv_students.horizontalHeader().setCascadingSectionResizes(True)
        self.tv_students.horizontalHeader().setStretchLastSection(True)
        self.tv_students.setCornerButtonEnabled(False)
        self.tv_students.setSortingEnabled(True)
        vl2.addWidget(self.tv_students)

        self.data_tabs.addTab(self.student_tab, "")

        # Schedules Tab

        self.schedules_tab = QWidget()
        self.schedules_tab.setObjectName("schedules_tab")

        vl3 = QVBoxLayout(self.schedules_tab)
        vl3.setObjectName("vl3")

        hl4 = QHBoxLayout()
        hl4.setContentsMargins(-1, 0, -1, -1)
        hl4.setObjectName("hl4")

        # self.pb_new_schedule = IconButton("resources/icons/ic_new.svg", self.schedules_tab)
        # self.pb_new_schedule.setText("")
        # self.pb_new_schedule.setObjectName("pb_new_schedule")
        # hl4.addWidget(self.pb_new_schedule)

        self.pb_remove_schedule = IconButton("resources/icons/ic_trash.svg", self.schedules_tab)
        self.pb_remove_schedule.setText("")
        self.pb_remove_schedule.setObjectName("pb_remove_schedule")
        self.pb_remove_schedule.setEnabled(False)
        hl4.addWidget(self.pb_remove_schedule)

        spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        hl4.addItem(spacerItem1)
        vl3.addLayout(hl4)

        self.tv_schedules = QTreeView(parent=self.schedules_tab)
        self.tv_schedules.setObjectName("tv_schedules")
        self.tv_schedules.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)
        self.tv_schedules.setItemDelegate(ProxyScheduleDelegate(self.tv_schedules))
        self.tv_schedules.setSortingEnabled(True)
        vl3.addWidget(self.tv_schedules)

        self.data_tabs.addTab(self.schedules_tab, "")
        hl1.addWidget(self.splitter)

        self.retranslateUi(dbmanager)
        self.data_tabs.setCurrentIndex(0)

    def retranslateUi(self, dbmanager):
        _translate = QCoreApplication.translate
        dbmanager.setWindowTitle(_translate("dbmanager", "Manage Courses"))
        self.le_search.setPlaceholderText(_translate("dbmanager", "Search"))
        self.le2_search.setPlaceholderText(_translate("dbmanager", "Search"))
        self.cb_show_unassigned.setText(_translate("dbmanager", "Show unassigned students only"))
        self.data_tabs.setTabText(self.data_tabs.indexOf(self.student_tab), _translate("dbmanager", "Students"))
        self.data_tabs.setTabText(self.data_tabs.indexOf(self.schedules_tab), _translate("dbmanager", "Schedules"))

class AssignmentView:
    def setupUi(self, assign_student_dialog: QDialog):
        assign_student_dialog.setObjectName("assign_student_dialog")
        assign_student_dialog.setMinimumSize(550, 400)

        verticalLayout = QVBoxLayout(assign_student_dialog)
        verticalLayout.setObjectName("verticalLayout")
        horizontalLayout = QHBoxLayout()
        horizontalLayout.setContentsMargins(-1, 0, -1, -1)
        horizontalLayout.setObjectName("horizontalLayout")

        self.le_search = QLineEdit(parent=assign_student_dialog)
        self.le_search.setObjectName("le_search")
        horizontalLayout.addWidget(self.le_search)

        spacerItem = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        horizontalLayout.addItem(spacerItem)
        verticalLayout.addLayout(horizontalLayout)

        self.tv_students = QTreeView(parent=assign_student_dialog)
        self.tv_students.setMinimumSize(QSize(280, 0))
        self.tv_students.setObjectName("tv_assigned_students")
        self.tv_students.setSelectionMode(QTreeView.SelectionMode.SingleSelection)
        delegate = QSqlRelationalDelegate(self.tv_students)
        self.tv_students.setItemDelegate(delegate)
        verticalLayout.addWidget(self.tv_students)

        self.lw_selected_students = QListWidget(assign_student_dialog)
        self.lw_selected_students.setMaximumHeight(30)
        self.lw_selected_students.setObjectName("lw_selected_students")
        self.lw_selected_students.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.lw_selected_students.setFlow(QListWidget.Flow.LeftToRight)
        self.lw_selected_students.setAlternatingRowColors(True)
        self.lw_selected_students.setEditTriggers(QListWidget.EditTrigger.NoEditTriggers)
        self.lw_selected_students.setDragEnabled(False)
        verticalLayout.addWidget(self.lw_selected_students)

        self.button_box = QDialogButtonBox(parent=assign_student_dialog)
        self.button_box.setOrientation(Qt.Orientation.Horizontal)
        self.button_box.setStandardButtons(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.setObjectName("button_box")
        verticalLayout.addWidget(self.button_box)

        self.pb_new_student = QPushButton(assign_student_dialog)
        self.button_box.addButton(self.pb_new_student, QDialogButtonBox.ButtonRole.ResetRole)
        
        self.button_box.accepted.connect(assign_student_dialog.accept)
        self.button_box.rejected.connect(assign_student_dialog.reject)

        assign_student_dialog.setLayout(verticalLayout)

        self.retranslateUi(assign_student_dialog)

    def retranslateUi(self, assign_student_dialog):
        _translate = QCoreApplication.translate
        assign_student_dialog.setWindowTitle(_translate("assign_student_dialog", "Dialog"))
        self.le_search.setPlaceholderText(_translate("assign_student_dialog", "Search"))
        self.pb_new_student.setText(_translate("assign_student_dialog", "New"))