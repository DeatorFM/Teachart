import typing
from PyQt6 import QtCore, QtGui, QtWidgets
from ui.StyledWidget import *
from ui.UI_Commons import SplitButton, IconButton
from educ.table import WidgetTable

class EditorWidget(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setUI()
        self.setObjectName("Editor")
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("QWidget#Editor {background-color: #ffffff;}") 
        self.setAcceptDrops(True)

    def setUI(self):
        # Main Layout for Editor-Tab
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(0, 0, 0, 5)
        self.main_layout.setObjectName("MainLayout")
        self.setLayout(self.main_layout)

        self.main_info_frame = QtWidgets.QFrame(self)
        self.main_info_frame.setStyleSheet("QFrame {background-color: #f9f9f9;}")
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
        # self.sb_LessonTime.setStyleSheet(self.fromStyle("SB_LessonTime"))
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
        self.te_comment.setStyleSheet("QTextEdit#TE_Goals {background-color: rgb(255, 255, 255); border-color: #a9a9a9;}")
        self.te_comment.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.te_comment.setAcceptRichText(False)
        self.te_comment.setObjectName("TE_Goals")
        self.main_info_layout.addWidget(self.te_comment)

        self.main_layout.addWidget(self.main_info_frame)

        # Begin of editing area
        self.edit_area_layout = QtWidgets.QVBoxLayout()
        self.edit_area_layout.setContentsMargins(10, 0, 10, -1)
        self.edit_area_layout.setObjectName("EditAreaLayout")

        self.table_toolbar = QtWidgets.QFrame(self)
        self.table_toolbar.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.table_toolbar.sizePolicy().hasHeightForWidth())
        self.table_toolbar.setSizePolicy(sizePolicy)
        self.table_toolbar.setStyleSheet(fromStyle("Toolbar"))
        self.table_toolbar.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.table_toolbar.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        self.table_toolbar.setLineWidth(0)
        self.table_toolbar.setObjectName("TableToolbar")

        self.table_toolbar_layout = QtWidgets.QHBoxLayout(self.table_toolbar)
        self.table_toolbar_layout.setContentsMargins(3, 0, 3, 0)
        self.table_toolbar_layout.setSpacing(3)
        self.table_toolbar_layout.setObjectName("TableToolbarLayout")  
        self.table_toolbar.setLayout(self.table_toolbar_layout)

        self.table_buttons = QtWidgets.QWidget(self.table_toolbar)
        self.table_buttonsLayout = QtWidgets.QHBoxLayout(self.table_buttons)
        self.table_buttons.setLayout(self.table_buttonsLayout)

        # Inserts new row under selected row
        self.pb_NewRow = QtWidgets.QPushButton(self.table_toolbar)
        self.pb_NewRow.setMinimumSize(QtCore.QSize(16, 16))
        self.pb_NewRow.setText("")
        icon8 = QtGui.QIcon()
        icon8.addPixmap(QtGui.QPixmap("resources/icons/ic_insertRowBottom.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_NewRow.setIcon(icon8)
        self.pb_NewRow.setIconSize(QtCore.QSize(20, 20))
        self.pb_NewRow.setObjectName("PB_NewRow")
        self.table_buttonsLayout.addWidget(self.pb_NewRow)

        # Inserts new column to the right of the selected column
        self.pb_NewColumn = QtWidgets.QPushButton(self.table_toolbar)
        self.pb_NewColumn.setMinimumSize(QtCore.QSize(16, 16))
        self.pb_NewColumn.setText("")
        icon9 = QtGui.QIcon()
        icon9.addPixmap(QtGui.QPixmap("resources/icons/ic_insertColumnRight.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_NewColumn.setIcon(icon9)
        self.pb_NewColumn.setIconSize(QtCore.QSize(20, 20))
        self.pb_NewColumn.setObjectName("PB_NewColumn")
        self.table_buttonsLayout.addWidget(self.pb_NewColumn)

        ln11 = QtWidgets.QFrame(self.table_toolbar)
        ln11.setFrameShape(QtWidgets.QFrame.Shape.VLine)
        ln11.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.table_buttonsLayout.addWidget(ln11)

        # Delete row of selected cell
        self.pb_DeleteRow = QtWidgets.QPushButton(self.table_toolbar)
        self.pb_DeleteRow.setMinimumSize(QtCore.QSize(16, 16))
        self.pb_DeleteRow.setText("")
        icon10 = QtGui.QIcon()
        icon10.addPixmap(QtGui.QPixmap("resources/icons/ic_deleterow.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_DeleteRow.setIcon(icon10)
        self.pb_DeleteRow.setIconSize(QtCore.QSize(20, 20))
        self.pb_DeleteRow.setObjectName("PB_DeleteRow")
        self.table_buttonsLayout.addWidget(self.pb_DeleteRow)

        # Delete column of selected cell
        self.pb_DeleteColumn = QtWidgets.QPushButton(self.table_toolbar)
        self.pb_DeleteColumn.setText("")
        icon11 = QtGui.QIcon()
        icon11.addPixmap(QtGui.QPixmap("resources/icons/ic_deletecolumn.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_DeleteColumn.setIcon(icon11)
        self.pb_DeleteColumn.setIconSize(QtCore.QSize(20, 20))
        self.pb_DeleteColumn.setObjectName("PB_DeleteColumn")
        self.table_buttonsLayout.addWidget(self.pb_DeleteColumn)

        ln12 = QtWidgets.QFrame(self.table_toolbar)
        ln12.setFrameShape(QtWidgets.QFrame.Shape.VLine)
        ln12.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.table_buttonsLayout.addWidget(ln12)

        self.pb_LockSize = QtWidgets.QPushButton(self.table_toolbar)
        self.pb_LockSize.setMinimumSize(QtCore.QSize(16, 16))
        self.pb_LockSize.setText("")
        icon12 = QtGui.QIcon()
        icon12.addPixmap(QtGui.QPixmap("resources/icons/ic_notpinned.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_LockSize.setIcon(icon12)
        self.pb_LockSize.setIconSize(QtCore.QSize(20, 20))
        self.pb_LockSize.setObjectName("PB_LockSize")
        self.table_buttonsLayout.addWidget(self.pb_LockSize)

        self.table_buttons.setEnabled(False)
        self.table_toolbar_layout.addWidget(self.table_buttons)

        spi2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.table_toolbar_layout.addItem(spi2)

        self.pb_add_element = QtWidgets.QPushButton(self.table_toolbar)
        self.pb_add_element.setMinimumSize(QtCore.QSize(80, 25))
        self.pb_add_element.setText("")
        # self.pb_add_element.setProperty("text", True)
        self.pb_add_element.setStyleSheet(fromStyle("PB_text"))
        self.pb_add_element.setObjectName("PB_add_element")

        self.menu_element = QtWidgets.QMenu()
        self.ac_FromClipboard = self.menu_element.addAction("")
        self.ac_FromClipboard.setEnabled(False)
        self.ac_FromClipboard.setData("Clipboard")
        self.menu_element.addSeparator()

        self.pb_add_element.setMenu(self.menu_element)
        self.pb_add_element.setEnabled(False)
        self.table_toolbar_layout.addWidget(self.pb_add_element)

        self.pb_delete_element = QtWidgets.QPushButton(self.table_toolbar)
        self.pb_delete_element.setMinimumSize(QtCore.QSize(16, 16))
        self.pb_delete_element.setText("")
        icon13 = QtGui.QIcon()
        icon13.addPixmap(QtGui.QPixmap("resources/icons/ic_trash.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_delete_element.setIcon(icon13)
        self.pb_delete_element.setIconSize(QtCore.QSize(20, 20))
        self.pb_delete_element.setObjectName("PB_delete_element")
        self.pb_delete_element.setEnabled(False)
        self.table_toolbar_layout.addWidget(self.pb_delete_element)

        ln13 = QtWidgets.QFrame(self.table_toolbar)
        ln13.setFixedHeight(20)
        ln13.setFrameShape(QtWidgets.QFrame.Shape.VLine)
        ln13.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.table_toolbar_layout.addWidget(ln13)

        self.pb_move_up = IconButton("resources/icons/ic_move_up.svg", self.table_toolbar)
        self.pb_move_up.setObjectName("pb_move_up")
        self.pb_move_up.setEnabled(False)
        self.table_toolbar_layout.addWidget(self.pb_move_up)

        self.pb_move_down = IconButton("resources/icons/ic_move_down.svg", self.table_toolbar)
        self.pb_move_down.setObjectName("pb_move_up")
        self.pb_move_down.setEnabled(False)
        self.table_toolbar_layout.addWidget(self.pb_move_down)

        self.edit_area_layout.addWidget(self.table_toolbar)

        self.view_layout = QtWidgets.QHBoxLayout(self) 
        self.view_layout.setSpacing(0)

        self.table_background = QtWidgets.QWidget(self)
        self.table_background.setObjectName("TableBackground")
        self.table_background.setStyleSheet("QWidget#TableBackground {background-color: #c9d3e2;}")
        self.table_background.setContentsMargins(20, 20, 20, 20)

        self.table_area_layout = QtWidgets.QStackedLayout(self.table_background)
        self.table_area_layout.setContentsMargins(0, 0, 0, 0)
        self.table_background.setLayout(self.table_area_layout)

        self.table_sizer = TableGrid(self.table_background)
        self.table_area_layout.addWidget(self.table_sizer)

        self.table = WidgetTable(self)
        self.table_area_layout.addWidget(self.table)

        self.table_area_layout.setCurrentIndex(0)

        self.view_layout.addWidget(self.table_background)

        self.element_toolbar = QtWidgets.QFrame(self)
        self.element_toolbar.setStyleSheet(fromStyle("Toolbar"))
        self.element_toolbar.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.element_toolbar.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        self.element_toolbar.setAttribute(QtCore.Qt.WidgetAttribute.WA_NoMousePropagation, True)
        self.element_toolbar.setFixedWidth(230)
        self.element_toolbar.setObjectName("ElementToolbar")
        self.element_toolbar.setVisible(False)

        self.elem_toolbar_layout = QtWidgets.QVBoxLayout(self.element_toolbar)
        self.elem_toolbar_layout.setSpacing(7)
        self.elem_toolbar_layout.setObjectName("LToolbarLayout")
        self.element_toolbar.setLayout(self.elem_toolbar_layout)

        self.pb_close_elem_toolbar = QtWidgets.QPushButton(self.element_toolbar)
        self.pb_close_elem_toolbar.setMinimumSize(QtCore.QSize(22, 22))
        self.pb_close_elem_toolbar.setText("")
        icon14 = QtGui.QIcon()
        icon14.addPixmap(QtGui.QPixmap("resources/icons/ic_close.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_close_elem_toolbar.setIcon(icon14)
        self.pb_close_elem_toolbar.setIconSize(QtCore.QSize(20, 20))
        self.pb_close_elem_toolbar.setObjectName("pb_close_elem_toolbar")
        self.pb_close_elem_toolbar.setAttribute(QtCore.Qt.WidgetAttribute.WA_NoMousePropagation, True)
        self.elem_toolbar_layout.addWidget(self.pb_close_elem_toolbar)

        spi3 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.elem_toolbar_layout.addItem(spi3)

        self.view_layout.addWidget(self.element_toolbar)

        self.edit_area_layout.addLayout(self.view_layout)

        self.main_layout.addLayout(self.edit_area_layout)

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
        self.pb_NewRow.setToolTip(_translate("Editor", "Insert new row under selected cell"))
        self.pb_NewColumn.setToolTip(_translate("Editor", "Insert new Column next to selected cell"))
        self.pb_DeleteRow.setToolTip(_translate("Editor", "Delete row of selected cell"))
        self.pb_DeleteColumn.setToolTip(_translate("Editor", "Delete column of selected cell"))
        self.pb_add_element.setText(_translate("Editor", "Add to cell"))
        self.ac_FromClipboard.setText(_translate("Editor", "Add from clipboard"))
        self.pb_delete_element.setToolTip(_translate("Editor", "Delete focussed element"))
        self.pb_move_up.setToolTip(_translate("Editor", "Move active element up"))
        self.pb_move_down.setToolTip(_translate("Editor", "Move active element down"))

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        return super().closeEvent(a0)

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