from PyQt6.QtCore import (
    QCoreApplication,
    QDateTime,
    QEvent,
    QLocale,
    QSize,
    Qt,
    pyqtSignal,
    pyqtSlot,
)
from PyQt6.QtGui import QActionGroup, QEnterEvent, QFont, QIcon, QMouseEvent, QPixmap
from PyQt6.QtWidgets import (
    QAbstractSpinBox,
    QComboBox,
    QDateTimeEdit,
    QFrame,
    QGridLayout,
    QMainWindow,
    QMenu,
    QSizePolicy,
    QSpinBox,
    QTextEdit,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from nativeelements.baseelement import BaseElementDefinitions, BaseElementToolset
from tcha.settings import Locale, Settings, TimeFormat
from tcha.table import Table
from ui.commons import LabeledWidget, SearchableComboBox, SwitchAction
from ui.StyledWidget import *

EditorStyleSheet = """
.QWidget {background-color: #e7f2f0;}
"""

ToolsetFrameStyleSheet = """
QFrame#ToolsetsContainer {background-color: white; border-radius: 6px;}
"""


class EditorView:
    def setUI(self, agent: QMainWindow):
        # Main Layout for Editor-Tab
        agent.setObjectName("Editor")
        agent.setProperty("EditorStyleSheet", True)
        agent.setAutoFillBackground(True)

        self.central_widget = QWidget(agent)
        self.central_widget.setObjectName("central_widget")
        agent.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setSpacing(1)
        self.main_layout.setContentsMargins(0, 0, 0, 5)
        self.main_layout.setObjectName("MainLayout")

        self.courses_tools = QToolBar(agent)
        self.courses_tools.setObjectName("courses_tools")
        self.courses_tools.setAllowedAreas(Qt.ToolBarArea.TopToolBarArea)
        self.courses_tools.setMovable(False)

        self.cb_course = SearchableComboBox(agent)
        self.cb_course.setMinimumSize(QSize(180, 30))
        self.cb_course.setFrame(True)
        self.cb_course.setObjectName("CB_Course")
        self.cb_course.setModelColumn(1)
        self.cb_course.lineEdit().setClearButtonEnabled(True)
        self.lw1 = LabeledWidget("", self.cb_course)

        self.courses_tools.addWidget(self.lw1)

        icon = QIcon()
        icon.addPixmap(
            QPixmap("resources/icons/ic_new.svg"), QIcon.Mode.Normal, QIcon.State.Off
        )
        self.ac_add_course = self.courses_tools.addAction(icon, "")

        agent.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.courses_tools)

        self.datetime_tools = QToolBar(agent)
        self.datetime_tools.setObjectName("datetime_tools")
        self.datetime_tools.setAllowedAreas(Qt.ToolBarArea.TopToolBarArea)
        self.datetime_tools.setMovable(False)

        qsettings = Settings.qsettings()
        self.dt_DateTime = QDateTimeEdit(agent)
        locale = Locale[qsettings.value("User/language", type=str)].value
        tformat = TimeFormat[qsettings.value("User/time_format", type=str)].value
        qlocale = QLocale(locale.language, locale.region)
        self.dt_DateTime.setDisplayFormat(
            f"{qlocale.dateFormat(QLocale.FormatType.ShortFormat)} {tformat}"
        )
        self.dt_DateTime.setLocale(qlocale)
        self.dt_DateTime.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.dt_DateTime.setProperty("showGroupSeparator", False)
        self.dt_DateTime.setCalendarPopup(True)
        self.dt_DateTime.setObjectName("DT_DateTime")
        self.dt_DateTime.setDateTime(QDateTime.currentDateTime())
        self.lw2 = LabeledWidget("", self.dt_DateTime)

        self.datetime_tools.addWidget(self.lw2)

        icon1 = QIcon()
        icon1.addPixmap(
            QPixmap("resources/icons/ic_schedule.svg"),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        icon2 = QIcon()
        icon2.addPixmap(
            QPixmap("resources/icons/ic_scheduled.svg"),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.ac_schedule = SwitchAction(icon1, icon2)
        self.datetime_tools.addAction(self.ac_schedule)

        agent.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.datetime_tools)

        self.duration_tools = QToolBar(agent)
        self.duration_tools.setObjectName("duration_tools")
        self.duration_tools.setAllowedAreas(Qt.ToolBarArea.TopToolBarArea)
        self.duration_tools.setMovable(False)

        self.sb_LessonTime = QSpinBox(agent)
        self.sb_LessonTime.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.sb_LessonTime.setMinimumSize(0, 30)
        self.sb_LessonTime.setMaximum(300)
        self.sb_LessonTime.setObjectName("SB_LessonTime")
        self.lw3 = LabeledWidget("", self.sb_LessonTime)

        self.duration_tools.addWidget(self.lw3)

        agent.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.duration_tools)

        self.other_options = QToolBar(agent)
        self.other_options.setObjectName("other_options")
        self.other_options.setAllowedAreas(Qt.ToolBarArea.TopToolBarArea)
        self.other_options.setMovable(False)

        icon3 = QIcon()
        icon3.addPixmap(
            QPixmap("resources/icons/ic_save.svg"), QIcon.Mode.Normal, QIcon.State.Off
        )
        self.ac_save = self.other_options.addAction(icon3, "")
        tb_save: QToolButton = self.other_options.widgetForAction(self.ac_save)
        tb_save.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)

        self.menu_save = QMenu()
        self.ac_save_ = self.menu_save.addAction("")
        self.ac_save_copy = self.menu_save.addAction("")
        tb_save.setMenu(self.menu_save)

        icon4 = QIcon()
        icon4.addPixmap(
            QPixmap("resources/icons/ic_readmode.svg"),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.ac_present_mode = self.other_options.addAction(icon4, "")

        self.ac_debug = self.other_options.addAction("Debug")
        tb_debug: QToolButton = self.other_options.widgetForAction(self.ac_debug)
        tb_debug.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        self.menu_debug = QMenu()
        self.ac_file_info = self.menu_debug.addAction("File Inspector")
        self.ac_table_view = self.menu_debug.addAction("Table Inspector")
        self.ac_xml_view = self.menu_debug.addAction("XML Inspector")
        self.ac_xml_view.setEnabled(False)
        self.ac_res_view = self.menu_debug.addAction("Resource View")
        tb_debug.setMenu(self.menu_debug)

        if qsettings.value("Application/debug", False, bool):
            self.ac_debug.setVisible(True)
        else:
            self.ac_debug.setVisible(False)

        agent.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.other_options)
        agent.addToolBarBreak(Qt.ToolBarArea.TopToolBarArea)

        # Textbox for additional comments
        self.comment_bar = QToolBar(agent)
        self.comment_bar.setObjectName("comment_bar")
        self.comment_bar.setAllowedAreas(Qt.ToolBarArea.TopToolBarArea)
        self.comment_bar.setMovable(False)

        self.te_comment = QTextEdit(agent)
        self.te_comment.setMaximumHeight(80)
        font = QFont()
        font.setFamily("Calibri")
        font.setPointSize(12)
        self.te_comment.setFont(font)
        self.te_comment.setFrameShape(QFrame.Shape.Box)
        self.te_comment.setAcceptRichText(False)
        self.te_comment.setObjectName("TE_Comment")
        self.comment_bar.addWidget(self.te_comment)

        agent.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.comment_bar)
        agent.addToolBarBreak(Qt.ToolBarArea.TopToolBarArea)

        self.table_toolset = QToolBar(agent)
        self.table_toolset.setObjectName("table_toolset")
        self.table_toolset.setAllowedAreas(Qt.ToolBarArea.TopToolBarArea)
        self.table_toolset.setMovable(False)

        self.cell_editor_actions = QActionGroup(agent)

        self.ac_add_element = self.table_toolset.addAction("")
        self.cell_editor_actions.addAction(self.ac_add_element)

        self.table_toolset.addSeparator()

        self.menu_element = QMenu(agent)
        self.ac_from_clipboard = self.menu_element.addAction("")
        self.ac_from_clipboard.setEnabled(False)
        self.ac_from_clipboard.setData("Clipboard")
        self.menu_element.addSeparator()

        tb_add_element: QToolButton = self.table_toolset.widgetForAction(
            self.ac_add_element
        )
        tb_add_element.setMenu(self.menu_element)
        tb_add_element.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        icon5 = QIcon()
        icon5.addPixmap(
            QPixmap("resources/icons/ic_insertRowBottom.svg"),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.ac_new_row = self.table_toolset.addAction(icon5, None)
        self.cell_editor_actions.addAction(self.ac_new_row)

        icon6 = QIcon()
        icon6.addPixmap(
            QPixmap("resources/icons/ic_insertColumnRight.svg"),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.ac_new_column = self.table_toolset.addAction(icon6, None)
        self.cell_editor_actions.addAction(self.ac_new_column)

        self.table_toolset.addSeparator()

        icon7 = QIcon()
        icon7.addPixmap(
            QPixmap("resources/icons/ic_deleterow.svg"),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.ac_delete_row = self.table_toolset.addAction(icon7, None)
        self.cell_editor_actions.addAction(self.ac_delete_row)

        icon8 = QIcon()
        icon8.addPixmap(
            QPixmap("resources/icons/ic_deletecolumn.svg"),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.ac_delete_column = self.table_toolset.addAction(icon8, None)
        self.cell_editor_actions.addAction(self.ac_delete_column)

        self.cell_editor_actions.setEnabled(False)

        agent.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.table_toolset)
        agent.addToolBarBreak(Qt.ToolBarArea.TopToolBarArea)

        self.table = Table(self.central_widget)
        self.table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.main_layout.addWidget(self.table)

        self.retranslateUi()

    def retranslateUi(self):
        _translate = QCoreApplication.translate
        self.lw1.set_label_text(_translate("Editor", "Course"))
        self.cb_course.setPlaceholderText(_translate("Editor", "No course"))
        self.ac_add_course.setToolTip(_translate("Editor", "Add new course"))
        self.lw2.set_label_text(_translate("Editor", "Date/Time"))
        self.ac_schedule.setToolTip(_translate("Editor", "Schedule this lesson"))
        self.lw3.set_label_text(_translate("Editor", "Duration"))
        self.sb_LessonTime.setSuffix(_translate("Editor", " min"))
        self.ac_save.setText(_translate("Editor", "Save"))
        self.ac_save_.setText(_translate("Editor", "Save"))
        self.ac_save_copy.setText(_translate("Editor", "Save to"))
        self.ac_present_mode.setToolTip(_translate("Editor", "Presentation Mode"))
        self.te_comment.setPlaceholderText(_translate("Editor", "Comment"))

        self.ac_add_element.setText(_translate("Editor", "Add to cell"))
        self.ac_from_clipboard.setText(_translate("Editor", "From Clipboard"))

    def add_toolsets(
        self, window: QMainWindow, definitions: dict[str, BaseElementDefinitions]
    ) -> dict[str, BaseElementToolset]:
        d = {}
        for key in definitions.keys():
            toolset = definitions[key].toolset()
            window.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolset)
            window.addToolBarBreak(Qt.ToolBarArea.TopToolBarArea)
            toolset.setVisible(False)
            d[key] = toolset
        return d

    def add_element_actions(
        self, definitions: dict[str, BaseElementDefinitions]
    ) -> None:
        for key in definitions.keys():
            action = definitions[key].action(self.menu_element)
            print("Add Action from element", action.data())
            self.menu_element.addAction(action)
            print("Current menu actions", self.menu_element.actions())


class CourseComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)


class TableGrid(QWidget):
    tableSize = pyqtSignal(int, int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setUI()

    def setUI(self) -> None:
        self.button_layout = QGridLayout(self)
        self.button_layout.setHorizontalSpacing(0)
        self.button_layout.setVerticalSpacing(0)

        for iline in range(8):
            for icolumn in range(11):
                button = GridButton(self)
                button.line = iline + 1
                button.column = icolumn + 1
                button.entered.connect(self.setMarkedButtons)
                button.sizeSet.connect(self.getTableSize)
                button.left.connect(self.clearMarkings)
                self.button_layout.addWidget(button, iline, icolumn)

        self.setLayout(self.button_layout)

    @pyqtSlot(int, int)
    def setMarkedButtons(self, line: int, column: int) -> None:
        for i in range(self.button_layout.count() - 1):
            button = self.button_layout.itemAt(i).widget()
            if button.column <= column and button.line <= line:
                # print(button, button.line, button.column)
                button.setProperty("hovered", True)
                self.showTableSize(line, column)

            else:
                button.setProperty("hovered", False)
            button.style().polish(button)

    def clearMarkings(self):
        for i in range(self.button_layout.count() - 1):
            button = self.button_layout.itemAt(i).widget()
            button.setProperty("hovered", False)
            button.style().polish(button)

    @pyqtSlot(int, int)
    def getTableSize(self, line: int, column: int) -> None:
        self.tableSize.emit(line, column)

    def showTableSize(self, line: int, column: int) -> None:
        self.setToolTip(f"{line} x {column}")


class GridButton(QFrame):
    entered = pyqtSignal(int, int)
    sizeSet = pyqtSignal(int, int)
    left = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setProperty("hovered", False)
        self.line: int
        self.column: int

    def enterEvent(self, event: QEnterEvent) -> None:
        self.entered.emit(self.line, self.column)
        super().enterEvent(event)

    def leaveEvent(self, a0: QEvent) -> None:
        self.setProperty("hovered", False)
        self.style().polish(self)
        self.left.emit()
        super().leaveEvent(a0)

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        self.sizeSet.emit(self.line, self.column)
        super().mouseReleaseEvent(e)
