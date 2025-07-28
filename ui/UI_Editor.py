from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame, QSizePolicy, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QSpacerItem, QMenu, QDateTimeEdit, QSpinBox, QTextEdit,
    QStackedWidget, QGraphicsDropShadowEffect, QGridLayout, QAbstractSpinBox
)
from PyQt6.QtCore import (
    Qt, QSize, QDateTime, QTimer, QRectF, pyqtSignal, pyqtSlot, QEvent, QCoreApplication
)
from PyQt6.QtGui import (
    QFont, QIcon, QPixmap, QPainter, QPainterPath, QPen, QColor, QMouseEvent, QEnterEvent
)
from PyQt6.QtSvg import QSvgRenderer

from ui.StyledWidget import *
from ui.UI_Commons import SplitButton, SearchableComboBox
from tcha.toolset import TableToolset
from tcha.table import Table

import math
import typing

EditorStyleSheet = """
.QWidget {background-color: #e7f2f0;}
"""

ToolsetFrameStyleSheet = """
QFrame#ToolsetsContainer {background-color: white; border-radius: 6px;}
"""


class EditorWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("Editor")
        self.setProperty("EditorStyleSheet", True)
        self.setStyleSheet(EditorStyleSheet)
        self.setAutoFillBackground(True)
        self.setUI()

    def setUI(self):
        # Main Layout for Editor-Tab
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(0, 0, 0, 5)
        self.main_layout.setObjectName("MainLayout")
        self.setLayout(self.main_layout)

        self.main_info_frame = QFrame(self)
        self.main_info_frame.setFrameShape(QFrame.Shape.NoFrame)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.main_info_frame.setSizePolicy(sizePolicy)
        self.main_info_layout = QVBoxLayout()
        self.main_info_layout.setSpacing(0)
        self.main_info_layout.setContentsMargins(10, 10, 10, 20)
        self.main_info_frame.setLayout(self.main_info_layout)

        # call Top Bar
        self.topbar = QFrame(self.main_info_frame)
        self.topbar.setStyleSheet(fromStyle("TopBar"))
        self.topbar.setFrameShape(QFrame.Shape.NoFrame)
        self.topbar.setFrameShadow(QFrame.Shadow.Plain)
        self.topbar.setLineWidth(0)
        self.topbar.setObjectName("TopBar")

        self.topbar_layout = QHBoxLayout(self.topbar)
        self.topbar_layout.setContentsMargins(10, 10, 10, 10)
        self.topbar_layout.setSpacing(5)
        self.topbar_layout.setObjectName("TopBarLayout")

        self.lb_Courses = QLabel(self.topbar)
        self.lb_Courses.setObjectName("LB_Courses")
        self.topbar_layout.addWidget(self.lb_Courses)

        self.cb_course = SearchableComboBox(self.topbar)
        self.cb_course.setMinimumSize(QSize(180, 30))
        self.cb_course.setFrame(True)
        self.cb_course.setObjectName("CB_Course")
        self.cb_course.setModelColumn(1)
        self.cb_course.lineEdit().setClearButtonEnabled(True)
        self.topbar_layout.addWidget(self.cb_course)

        self.pb_AddCourse = QPushButton(self.topbar)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pb_AddCourse.sizePolicy().hasHeightForWidth())
        self.pb_AddCourse.setSizePolicy(sizePolicy)
        self.pb_AddCourse.setMaximumSize(QSize(18, 18))
        self.pb_AddCourse.setStyleSheet(fromStyle("PB_borderless"))
        icon = QIcon()
        icon.addPixmap(QPixmap("resources/icons/ic_new.svg"), QIcon.Mode.Normal, QIcon.State.Off)
        self.pb_AddCourse.setIcon(icon)
        self.pb_AddCourse.setIconSize(QSize(16, 16))
        self.pb_AddCourse.setObjectName("PB_AddCourse")
        self.topbar_layout.addWidget(self.pb_AddCourse)

        ln4 = QFrame(self.topbar)
        ln4.setFrameShadow(QFrame.Shadow.Sunken)
        ln4.setFrameShape(QFrame.Shape.VLine)
        self.topbar_layout.addWidget(ln4)
        
        self.lb_DateTime = QLabel(self.topbar)
        self.lb_DateTime.setMaximumSize(QSize(60, 20))
        self.lb_DateTime.setObjectName("LB_DateTime")
        self.topbar_layout.addWidget(self.lb_DateTime)

        self.dt_DateTime = QDateTimeEdit(self.topbar)
        self.dt_DateTime.setMinimumSize(85, 30)
        self.dt_DateTime.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.dt_DateTime.setProperty("showGroupSeparator", False)
        self.dt_DateTime.setCalendarPopup(True)
        self.dt_DateTime.setObjectName("DT_DateTime")
        self.dt_DateTime.setDateTime(QDateTime.currentDateTime())
        self.topbar_layout.addWidget(self.dt_DateTime)

        self.apb_schedule = AnimatedCalendarButton(self.topbar)
        self.apb_schedule.setFixedSize(27, 27)
        self.apb_schedule.setObjectName("apb_schedule")
        self.topbar_layout.addWidget(self.apb_schedule)
        self.topbar_layout.setAlignment(self.apb_schedule, Qt.AlignmentFlag.AlignBottom)

        ln10 = QFrame(self.topbar)
        ln10.setFrameShape(QFrame.Shape.VLine)
        ln10.setFrameShadow(QFrame.Shadow.Sunken)
        self.topbar_layout.addWidget(ln10)

        self.lb_LessonTime = QLabel(self.topbar)
        self.lb_LessonTime.setObjectName("LB_LessonTime")
        self.topbar_layout.addWidget(self.lb_LessonTime)
        
        self.sb_LessonTime = QSpinBox(self.topbar)
        self.sb_LessonTime.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.sb_LessonTime.setMinimumSize(0, 30)
        self.sb_LessonTime.setMaximum(300)
        self.sb_LessonTime.setObjectName("SB_LessonTime")
        self.topbar_layout.addWidget(self.sb_LessonTime)

        spi = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.topbar_layout.addItem(spi)

        self.spb_SaveButton = SplitButton(self.topbar)
        self.spb_SaveButton.setMinimumSize(QSize(20, 20))
        icon1 = QIcon()
        icon1.addPixmap(QPixmap("resources/icons/ic_save.svg"), QIcon.Mode.Normal, QIcon.State.Off)
        self.spb_SaveButton.lbutton.setIcon(icon1)
        self.spb_SaveButton.lbutton.setIconSize(QSize(20, 20))
        self.spb_SaveButton.lbutton.setMinimumSize(27, 27)
        self.spb_SaveButton.setObjectName("SaveButton")

        self.menu_save = QMenu(self.spb_SaveButton)
        self.ac_save = self.menu_save.addAction("")
        self.ac_save_copy = self.menu_save.addAction("")

        self.spb_SaveButton.rbutton.setMaximumSize(12, 21)
        self.spb_SaveButton.rbutton.setMenu(self.menu_save)
        self.topbar_layout.addWidget(self.spb_SaveButton)   

        self.pb_ReadMode = QPushButton(self.topbar)
        icon12 = QIcon()
        icon12.addPixmap(QPixmap("resources/icons/ic_readmode.svg"), QIcon.Mode.Normal, QIcon.State.Off)
        self.pb_ReadMode.setIcon(icon12)
        self.pb_ReadMode.setIconSize(QSize(20, 20))
        self.pb_ReadMode.setMinimumSize(27, 27)
        self.pb_ReadMode.setObjectName("PB_ReadMode")
        self.topbar_layout.addWidget(self.pb_ReadMode)
        self.main_info_layout.addWidget(self.topbar)

        # Textbox for learning goals
        self.te_comment = QTextEdit(self)
        self.te_comment.setMinimumSize(QSize(0, 60))
        self.te_comment.setMaximumSize(QSize(16777215, 50))
        font = QFont()
        font.setFamily("Calibri")
        font.setPointSize(12)
        self.te_comment.setFont(font)
        self.te_comment.setStyleSheet("QTextEdit#TE_Comment {background-color: rgb(255, 255, 255); border-color: #a9a9a9;}")
        self.te_comment.setFrameShape(QFrame.Shape.Box)
        self.te_comment.setAcceptRichText(False)
        self.te_comment.setObjectName("TE_Comment")
        self.main_info_layout.addWidget(self.te_comment)

        self.main_layout.addWidget(self.main_info_frame)

        self.edit_frame = QFrame(self)
        self.edit_frame.setFrameShape(QFrame.Shape.NoFrame)

        # Begin of editing area
        self.edit_area_layout = QVBoxLayout()
        self.edit_area_layout.setContentsMargins(10, 0, 10, 0)
        self.edit_area_layout.setObjectName("EditAreaLayout")
        self.edit_area_layout.setSpacing(10)
        self.edit_frame.setLayout(self.edit_area_layout)

        self.toolsets_container = QStackedWidget(self)
        self.toolsets_container.setObjectName("ToolsetsContainer")
        self.toolsets_container.setFrameShape(QFrame.Shape.StyledPanel)
        self.toolsets_container.setFrameShadow(QFrame.Shadow.Raised)
        graphics_effect = QGraphicsDropShadowEffect()
        graphics_effect.setBlurRadius(10)
        graphics_effect.setXOffset(1)
        graphics_effect.setYOffset(1)
        graphics_effect.setColor(Qt.GlobalColor.black)
        self.toolsets_container.setGraphicsEffect(graphics_effect)
        self.toolsets_container.setStyleSheet(ToolsetFrameStyleSheet)
        self.toolsets_container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.table_toolset = TableToolset(self)
        self.toolsets_container.setFixedHeight(self.table_toolset.sizeHint().height()) 
        self.toolsets_container.addWidget(self.table_toolset)

        self.edit_area_layout.addWidget(self.toolsets_container, 0, Qt.AlignmentFlag.AlignTop)

        self.table = Table(self)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.edit_area_layout.addWidget(self.table)

        self.main_layout.addWidget(self.edit_frame)

        self.retranslateUi()

    def retranslateUi(self):
        _translate = QCoreApplication.translate
        self.lb_Courses.setText(_translate("Editor", "Course"))
        self.cb_course.setPlaceholderText(_translate("Editor", "No course"))
        self.lb_DateTime.setText(_translate("Editor", "Date/Time"))
        self.lb_LessonTime.setText(_translate("Editor", "Duration"))
        self.sb_LessonTime.setSuffix(_translate("Editor", " min"))
        self.ac_save.setText(_translate("Editor", "Save"))
        self.ac_save_copy.setText(_translate("Editor", "Save to"))
        self.pb_ReadMode.setToolTip(_translate("Editor", "Read Mode"))
        self.te_comment.setPlaceholderText(_translate("Editor", "Comment"))

class CourseComboBox(QComboBox):
    def __init__(self, parent = ...):
        super().__init__(parent)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

class TableGrid(QWidget):
    tableSize = pyqtSignal(int, int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setUI()

    def setUI(self) -> None:
        self.setStyleSheet(fromStyle("GridButton"))
        self.button_layout = QGridLayout(self)
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

    @pyqtSlot(int, int)
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

class AnimatedCalendarButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.progress = 0.0
        self.animating = False
        self.checked = False

        self.svg_renderer = QSvgRenderer("resources/icons/ic_schedule.svg")

        self.norm_points = [
            (9.38, 14.55),
            (11.5, 16.67),
            (15.036, 13.136)
        ]

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_timeout)

        self.clicked.connect(self.start_animation)
        self.update_icon()

    def start_animation(self):
        if not self.checked:
            if not self.animating: 
                self.checked  = True
                self.progress = 0.0
                self.animating = True
                self.timer.start(16)

        else:
            self.checked = False
            self.progress = 0.0
            self.update_icon()

    def check_fast(self):
        """Instantly show the checkmark without animation."""
        self.progress = 1.0
        self.checked = True
        self.animating = False
        self.update_icon()

    def _on_timeout(self) -> None:
        self.progress += 0.03
        if self.progress >= 1.0:
            self.progress = 1.0
            self.animating = False
            self.timer.stop()
        self.update_icon()
        

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_icon()

    def update_icon(self) -> None:
        w, h = self.size().width() - 5, self.size().height() - 5
        pixmap = QPixmap(w, h)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw the static SVG (calendar only)
        self.svg_renderer.render(painter, QRectF(0, 0, w, h))

        # Scale normalized points to current size
        svg_w, svg_h = 24, 24  # SVG viewBox size
        points = [(x * w / svg_w, y * h / svg_h) for x, y in self.norm_points]

        if self.progress > 0.0 or self.checked:
            pen = QPen(QColor("#000000"), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin)
            pen.setWidthF(0.07 * self.width())
            painter.setPen(pen)
            path = self.partial_path(points, self.progress)
            painter.drawPath(path)

        painter.end()
        self.setIcon(QIcon(pixmap))
        self.setIconSize(pixmap.size())

    def partial_path(self, points, progress) -> QPainterPath:
        if progress <= 0.0:
            return QPainterPath()
        elif progress >= 1.0:
            p = QPainterPath()
            p.moveTo(*points[0])
            for pt in points[1:]:
                p.lineTo(*pt)
            return p

        seg_lengths = []
        total_len = 0
        for i in range(len(points) - 1):
            l = math.hypot(points[i+1][0] - points[i][0], points[i+1][1] - points[i][1])
            seg_lengths.append(l)
            total_len += l

        draw_len = total_len * progress
        p = QPainterPath()
        p.moveTo(*points[0])
        for i, l in enumerate(seg_lengths):
            if draw_len > l:
                p.lineTo(*points[i+1])
                draw_len -= l
            else:
                t = draw_len / l
                x = points[i][0] + t * (points[i+1][0] - points[i][0])
                y = points[i][1] + t * (points[i+1][1] - points[i][1])
                p.lineTo(x, y)
                break
        return p