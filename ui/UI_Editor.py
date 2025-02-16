import typing
from PyQt6 import QtCore, QtGui, QtWidgets
from ui.StyledWidget import *
from ui.UI_Commons import SplitButton
from tcha.toolset import TableToolset
from tcha.table import Table

EditorStyleSheet = """
.QWidget {background-color: #e7f2f0;}
"""

ToolsetFrameStyleSheet = """
QFrame#ToolsetsContainer {background-color: white; border-radius: 6px;}
"""


class EditorWidget(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("Editor")
        self.setProperty("EditorStyleSheet", True)
        self.setStyleSheet(EditorStyleSheet)
        self.setAutoFillBackground(True)
        self.setUI()

    def setUI(self):
        # Main Layout for Editor-Tab
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(0, 0, 0, 5)
        self.main_layout.setObjectName("MainLayout")
        self.setLayout(self.main_layout)

        self.main_info_frame = QtWidgets.QFrame(self)
        self.main_info_frame.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.main_info_frame.setSizePolicy(sizePolicy)
        self.main_info_layout = QtWidgets.QVBoxLayout()
        self.main_info_layout.setSpacing(0)
        self.main_info_layout.setContentsMargins(10, 10, 10, 20)
        self.main_info_frame.setLayout(self.main_info_layout)

        # call Top Bar
        self.topbar = QtWidgets.QFrame(self.main_info_frame)
        self.topbar.setStyleSheet(fromStyle("TopBar"))
        self.topbar.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.topbar.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        self.topbar.setLineWidth(0)
        self.topbar.setObjectName("TopBar")

        self.topbar_layout = QtWidgets.QHBoxLayout(self.topbar)
        self.topbar_layout.setContentsMargins(10, 10, 10, 10)
        self.topbar_layout.setSpacing(5)
        self.topbar_layout.setObjectName("TopBarLayout")

        self.lb_Courses = QtWidgets.QLabel(self.topbar)
        self.lb_Courses.setObjectName("LB_Courses")
        self.topbar_layout.addWidget(self.lb_Courses)

        self.cb_course = QtWidgets.QComboBox(self.topbar)
        self.cb_course.setMinimumSize(QtCore.QSize(170, 22))
        self.cb_course.setFrame(True)
        self.cb_course.setObjectName("CB_Course")
        self.topbar_layout.addWidget(self.cb_course)

        self.pb_AddCourse = QtWidgets.QPushButton(self.topbar)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pb_AddCourse.sizePolicy().hasHeightForWidth())
        self.pb_AddCourse.setSizePolicy(sizePolicy)
        self.pb_AddCourse.setMaximumSize(QtCore.QSize(18, 18))
        self.pb_AddCourse.setStyleSheet(fromStyle("PB_borderless"))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("resources/icons/ic_new.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_AddCourse.setIcon(icon)
        self.pb_AddCourse.setIconSize(QtCore.QSize(16, 16))
        self.pb_AddCourse.setObjectName("PB_AddCourse")
        self.topbar_layout.addWidget(self.pb_AddCourse)

        ln4 = QtWidgets.QFrame(self.topbar)
        ln4.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        ln4.setFrameShape(QtWidgets.QFrame.Shape.VLine)
        self.topbar_layout.addWidget(ln4)
        
        self.lb_DateTime = QtWidgets.QLabel(self.topbar)
        self.lb_DateTime.setMaximumSize(QtCore.QSize(60, 20))
        self.lb_DateTime.setObjectName("LB_DateTime")
        self.topbar_layout.addWidget(self.lb_DateTime)

        self.dt_DateTime = QtWidgets.QDateTimeEdit(self.topbar)
        self.dt_DateTime.setMinimumSize(80, 22)
        self.dt_DateTime.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.dt_DateTime.setProperty("showGroupSeparator", False)
        self.dt_DateTime.setCalendarPopup(True)
        self.dt_DateTime.setObjectName("DT_DateTime")
        self.dt_DateTime.setDateTime(QtCore.QDateTime.currentDateTime())
        self.topbar_layout.addWidget(self.dt_DateTime)

        ln10 = QtWidgets.QFrame(self.topbar)
        ln10.setFrameShape(QtWidgets.QFrame.Shape.VLine)
        ln10.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.topbar_layout.addWidget(ln10)

        self.lb_LessonTime = QtWidgets.QLabel(self.topbar)
        self.lb_LessonTime.setObjectName("LB_LessonTime")
        self.topbar_layout.addWidget(self.lb_LessonTime)
        
        self.sb_LessonTime = QtWidgets.QSpinBox(self.topbar)
        self.sb_LessonTime.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.sb_LessonTime.setMinimumSize(0, 22)
        self.sb_LessonTime.setMaximum(300)
        self.sb_LessonTime.setObjectName("SB_LessonTime")
        self.topbar_layout.addWidget(self.sb_LessonTime)

        spi = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.topbar_layout.addItem(spi)

        self.spb_SaveButton = SplitButton(self.topbar)
        self.spb_SaveButton.setMinimumSize(QtCore.QSize(20, 20))
        # self.spb_SaveButton.setAutoFillBackground(False)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("resources/icons/ic_save.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.spb_SaveButton.lbutton.setIcon(icon1)
        self.spb_SaveButton.lbutton.setIconSize(QtCore.QSize(20, 20))
        self.spb_SaveButton.lbutton.setMinimumSize(21, 21)
        self.spb_SaveButton.setObjectName("SaveButton")

        self.menu_save = QtWidgets.QMenu(self.spb_SaveButton)
        self.ac_save = self.menu_save.addAction("")
        self.ac_saveTo = self.menu_save.addAction("")

        self.spb_SaveButton.rbutton.setMaximumSize(12, 21)
        self.spb_SaveButton.rbutton.setMenu(self.menu_save)
        self.topbar_layout.addWidget(self.spb_SaveButton)   

        self.pb_ReadMode = QtWidgets.QPushButton(self.topbar)
        icon12 = QtGui.QIcon()
        icon12.addPixmap(QtGui.QPixmap("resources/icons/ic_readmode.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_ReadMode.setIcon(icon12)
        self.pb_ReadMode.setIconSize(QtCore.QSize(20, 20))
        self.pb_ReadMode.setMinimumSize(24, 24)
        self.pb_ReadMode.setObjectName("PB_ReadMode")
        self.topbar_layout.addWidget(self.pb_ReadMode)
        self.main_info_layout.addWidget(self.topbar)

        # Textbox for learning goals
        self.te_comment = QtWidgets.QTextEdit(self)
        self.te_comment.setMinimumSize(QtCore.QSize(0, 60))
        self.te_comment.setMaximumSize(QtCore.QSize(16777215, 50))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(12)
        self.te_comment.setFont(font)
        self.te_comment.setStyleSheet("QTextEdit#TE_Comment {background-color: rgb(255, 255, 255); border-color: #a9a9a9;}")
        self.te_comment.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.te_comment.setAcceptRichText(False)
        self.te_comment.setObjectName("TE_Comment")
        self.main_info_layout.addWidget(self.te_comment)

        self.main_layout.addWidget(self.main_info_frame)

        self.edit_frame = QtWidgets.QFrame(self)
        self.edit_frame.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)

        # Begin of editing area
        self.edit_area_layout = QtWidgets.QVBoxLayout()
        self.edit_area_layout.setContentsMargins(10, 0, 10, 0)
        self.edit_area_layout.setObjectName("EditAreaLayout")
        self.edit_area_layout.setSpacing(10)
        self.edit_frame.setLayout(self.edit_area_layout)

        self.toolsets_container = QtWidgets.QStackedWidget(self)
        self.toolsets_container.setObjectName("ToolsetsContainer")
        self.toolsets_container.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.toolsets_container.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        graphics_effect = QtWidgets.QGraphicsDropShadowEffect()
        graphics_effect.setBlurRadius(10)
        graphics_effect.setXOffset(1)
        graphics_effect.setYOffset(1)
        graphics_effect.setColor(QtCore.Qt.GlobalColor.black)
        self.toolsets_container.setGraphicsEffect(graphics_effect)
        self.toolsets_container.setStyleSheet(ToolsetFrameStyleSheet)
        self.toolsets_container.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        self.table_toolset = TableToolset(self)
        self.toolsets_container.setFixedHeight(self.table_toolset.sizeHint().height()) 
        self.toolsets_container.addWidget(self.table_toolset)

        self.edit_area_layout.addWidget(self.toolsets_container, 0, QtCore.Qt.AlignmentFlag.AlignTop)

        # self.view_layout = QtWidgets.QHBoxLayout(self) 
        # self.view_layout.setContentsMargins(0, 0, 0, 0)
        # self.view_layout.setSpacing(0)

        self.table = Table(self)
        self.table.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.edit_area_layout.addWidget(self.table)

        # self.edit_area_layout.addLayout(self.view_layout)

        self.main_layout.addWidget(self.edit_frame)

        self.retranslateUi()

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.lb_Courses.setText(_translate("Editor", "Course"))
        self.lb_DateTime.setText(_translate("Editor", "Date/Time"))
        self.lb_LessonTime.setText(_translate("Editor", "Duration"))
        self.sb_LessonTime.setSuffix(_translate("Editor", " min"))
        self.ac_save.setText(_translate("Editor", "Save"))
        self.ac_saveTo.setText(_translate("Editor", "Save to"))
        self.pb_ReadMode.setToolTip(_translate("Editor", "Read Mode"))
        self.te_comment.setPlaceholderText(_translate("Editor", "Comment"))

class TableGrid(QtWidgets.QWidget):
    tableSize = QtCore.pyqtSignal(int, int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setUI()

    def setUI(self) -> None:
        self.setStyleSheet(fromStyle("GridButton"))
        self.button_layout = QtWidgets.QGridLayout(self)
        self.button_layout.setHorizontalSpacing(0)
        self.button_layout.setVerticalSpacing(0)

        for iline in range(8):
            for icolumn in range(11):
                button = GridButton(self)
                button.line = iline+1
                button.column = icolumn+1
                button.entered.connect(self.setMarkedButtons)
                button.sizeSet.connect(self.getTableSize)
                button.left.connect(self.clearMarkings)
                self.button_layout.addWidget(button, iline, icolumn)

        self.setLayout(self.button_layout)

    @QtCore.pyqtSlot(int, int)
    def setMarkedButtons(self, line: int, column: int) -> None:
        for i in range(self.button_layout.count()-1):
            button = self.button_layout.itemAt(i).widget()
            if button.column <= column and button.line <= line:
                # print(button, button.line, button.column)
                button.setProperty("hovered", True)
                self.showTableSize(line, column)

            else:
                button.setProperty("hovered", False)
            button.style().polish(button)    

    def clearMarkings(self):
        for i in range(self.button_layout.count()-1):
            button = self.button_layout.itemAt(i).widget()
            button.setProperty("hovered", False)
            button.style().polish(button)

    @QtCore.pyqtSlot(int, int)
    def getTableSize(self, line: int, column: int) -> None:
        self.tableSize.emit(line, column)

    def showTableSize(self, line: int, column: int) -> None:
        self.setToolTip(f"{line} x {column}")

class GridButton(QtWidgets.QFrame):
    entered = QtCore.pyqtSignal(int, int)
    sizeSet = QtCore.pyqtSignal(int, int)
    left = QtCore.pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setProperty("hovered", False)
        self.line: int
        self.column: int

    def enterEvent(self, event: QtGui.QEnterEvent) -> None:
        self.entered.emit(self.line, self.column)
        super().enterEvent(event)

    def leaveEvent(self, a0: QtCore.QEvent) -> None:
        self.setProperty("hovered", False)
        self.style().polish(self)
        self.left.emit()
        super().leaveEvent(a0)        

    def mouseReleaseEvent(self, e: QtGui.QMouseEvent) -> None:
        self.sizeSet.emit(self.line, self.column)
        super().mouseReleaseEvent(e)