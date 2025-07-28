from __future__ import annotations
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, QPoint, QDate, QRect
from PyQt6.QtGui import QFont
from ui.StyledWidget import *
from tcha.dbmodels import ScheduleModel
import typing

stylesheet = """
QWidget#StartWidget {background-color: white;}
"""

class StartWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setUI()
        self.setObjectName("StartWidget")
        self.setAutoFillBackground(True)

    def setUI(self):       
        self.central_layout = QtWidgets.QHBoxLayout(self)
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_layout.setObjectName("CentralLayout")
        
        self.options_frame = QtWidgets.QFrame(self)
        self.options_frame.setStyleSheet(fromStyle("OptionsBar"))
        self.options_frame.setFrameShape(QtWidgets.QFrame.Shape.Panel)
        self.options_frame.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        self.options_frame.setLineWidth(0)
        self.options_frame.setObjectName("Options")
        
        self.options_layout = QtWidgets.QVBoxLayout(self.options_frame)
        self.options_layout.setContentsMargins(0, 0, 0, 0)
        self.options_layout.setSpacing(0)
        self.options_layout.setObjectName("OptionsLayout")
        
        self.pb_NewLesson = QtWidgets.QPushButton(self.options_frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pb_NewLesson.sizePolicy().hasHeightForWidth())
        self.pb_NewLesson.setSizePolicy(sizePolicy)
        self.pb_NewLesson.setMinimumSize(QtCore.QSize(140, 40))
        self.pb_NewLesson.setMaximumSize(QtCore.QSize(200, 16777215))
        font = QtGui.QFont()
        font.setFamily("Segoe UI Variable Text Semibold")
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.pb_NewLesson.setFont(font)
        self.pb_NewLesson.setIconSize(QtCore.QSize(20, 20))
        self.pb_NewLesson.setObjectName("PB_NewLesson")
        self.options_layout.addWidget(self.pb_NewLesson)
        
        self.pb_OpenLesson = QtWidgets.QPushButton(self.options_frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pb_OpenLesson.sizePolicy().hasHeightForWidth())
        self.pb_OpenLesson.setSizePolicy(sizePolicy)
        self.pb_OpenLesson.setMinimumSize(QtCore.QSize(140, 40))
        self.pb_OpenLesson.setMaximumSize(QtCore.QSize(200, 16777215))
        font = QtGui.QFont()
        font.setFamily("Segoe UI Variable Text Semibold")
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.pb_OpenLesson.setFont(font)
        self.pb_OpenLesson.setFlat(False)
        self.pb_OpenLesson.setObjectName("PB_OpenLesson")
        self.options_layout.addWidget(self.pb_OpenLesson)
        
        self.line_8 = QtWidgets.QFrame(self.options_frame)
        self.line_8.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.line_8.setLayoutDirection(QtCore.Qt.LayoutDirection.LeftToRight)
        self.line_8.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.line_8.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.line_8.setObjectName("line_8")
        self.options_layout.addWidget(self.line_8)

        self.pb_manager = QtWidgets.QPushButton(self.options_frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHeightForWidth(self.pb_OpenLesson.sizePolicy().hasHeightForWidth())
        self.pb_manager.setSizePolicy(sizePolicy)
        self.pb_manager.setMinimumSize(QtCore.QSize(140, 40))
        self.pb_manager.setMaximumSize(QtCore.QSize(200, 16777215))
        font = QtGui.QFont()
        font.setFamily("Segoe UI Variable Text Semibold")
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.pb_manager.setFont(font)
        self.pb_manager.setFlat(False)
        self.pb_manager.setObjectName("pb_manager")
        self.options_layout.addWidget(self.pb_manager)
        
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.options_layout.addItem(spacerItem)
        
        self.pb_Options = QtWidgets.QPushButton(self.options_frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pb_Options.sizePolicy().hasHeightForWidth())
        self.pb_Options.setSizePolicy(sizePolicy)
        self.pb_Options.setMinimumSize(QtCore.QSize(140, 40))
        self.pb_Options.setMaximumSize(QtCore.QSize(140, 40))
        font = QtGui.QFont()
        font.setFamily("Segoe UI Variable Text Semibold")
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.pb_Options.setFont(font)
        self.pb_Options.setObjectName("PB_Options")
        self.options_layout.addWidget(self.pb_Options)
        
        self.central_layout.addWidget(self.options_frame)
        
        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.setContentsMargins(0, -1, -1, -1)
        self.main_layout.setSpacing(0)
        self.main_layout.setObjectName("MainLayout")

        # File Displaying Areas

        self.Upcoming_Lessons = QtWidgets.QHBoxLayout()
        self.Upcoming_Lessons.setContentsMargins(0, 0, 0, 0)
        self.Upcoming_Lessons.setSpacing(0)
        self.Upcoming_Lessons.setObjectName("Upcoming_Lessons")

        self.sublayout1 = QtWidgets.QVBoxLayout()
        
        self.lb_UpcomingLessons = QtWidgets.QLabel(self)
        font = QtGui.QFont()
        font.setFamily("Segoe UI Variable Text Semibold")
        font.setPointSize(22)
        font.setBold(True)
        font.setWeight(75)
        self.lb_UpcomingLessons.setFont(font)
        self.lb_UpcomingLessons.setObjectName("FileLabel")
        self.sublayout1.addWidget(self.lb_UpcomingLessons)
        
        self.tw_UpcomingLessons = QtWidgets.QTreeView(self)
        self.tw_UpcomingLessons.setIndentation(0)
        self.tw_UpcomingLessons.setMinimumSize(QtCore.QSize(0, 0))
        self.tw_UpcomingLessons.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        self.tw_UpcomingLessons.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.tw_UpcomingLessons.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.tw_UpcomingLessons.setObjectName("TW_UpcomingLessons")
        self.tw_UpcomingLessons.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        header = self.tw_UpcomingLessons.header()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.tw_UpcomingLessons.setHeader(header)
        self.tw_UpcomingLessons.resize(720, 120)
        self.sublayout1.addWidget(self.tw_UpcomingLessons)
        self.Upcoming_Lessons.addLayout(self.sublayout1)
        
        self.cw_MyCalendar = LessonCalendar(self)
        self.cw_MyCalendar.setMinimumSize(QtCore.QSize(0, 0))
        self.cw_MyCalendar.setMaximumSize(QtCore.QSize(360, 16777215))
        font = QtGui.QFont()
        font.setFamily("Segoe UI Variable Text")
        self.cw_MyCalendar.setFont(font)
        self.cw_MyCalendar.setGridVisible(False)
        self.cw_MyCalendar.setNavigationBarVisible(True)
        self.cw_MyCalendar.setDateEditEnabled(False)
        self.cw_MyCalendar.setObjectName("CW_MyCalendar")
        self.Upcoming_Lessons.addWidget(self.cw_MyCalendar)
        
        self.main_layout.addLayout(self.Upcoming_Lessons)
        
        line_9 = QtWidgets.QFrame(self)
        line_9.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        line_9.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        line_9.setObjectName("line_9")
        self.main_layout.addWidget(line_9)
        
        self.lb_Pinned = QtWidgets.QLabel(self)
        font = QtGui.QFont()
        font.setFamily("Segoe UI Variable Text Semibold")
        font.setPointSize(22)
        font.setBold(True)
        font.setWeight(75)
        self.lb_Pinned.setFont(font)
        self.lb_Pinned.setObjectName("FileLabel")
        self.main_layout.addWidget(self.lb_Pinned)
        
        self.sa_Pinned = QtWidgets.QScrollArea(self)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sa_Pinned.sizePolicy().hasHeightForWidth())
        self.sa_Pinned.setSizePolicy(sizePolicy)
        self.sa_Pinned.setMinimumSize(QtCore.QSize(0, 0))
        self.sa_Pinned.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.sa_Pinned.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        self.sa_Pinned.setLineWidth(0)
        self.sa_Pinned.setWidgetResizable(True)
        self.sa_Pinned.setObjectName("Scroll_Pinned")
        
        self.pinned_files = QtWidgets.QWidget()
        self.pinned_files.setGeometry(QtCore.QRect(0, 0, 598, 52))
        self.pinned_files.setObjectName("PinnedFiles")
        self.pinned_files_layout = QtWidgets.QVBoxLayout(self.pinned_files)
        self.pinned_files_layout.setObjectName("PinnedFilesLayout")
        self.sa_Pinned.setWidget(self.pinned_files)

        self.lb_NoPinnedData = QtWidgets.QLabel()
        self.lb_NoPinnedData.setObjectName("LB_NoPinnedData")

        self.main_layout.addWidget(self.sa_Pinned)

        self.line_10 = HLine()
        self.main_layout.addWidget(self.line_10)

        self.lb_LastUsed = QtWidgets.QLabel(self)
        font = QtGui.QFont()
        font.setFamily("Segoe UI Variable Text Semibold")
        font.setPointSize(22)
        font.setBold(True)
        font.setWeight(75)
        font.setStyleStrategy(QtGui.QFont.StyleStrategy.PreferAntialias)
        self.lb_LastUsed.setFont(font)
        self.lb_LastUsed.setObjectName("FileLabel")
        self.main_layout.addWidget(self.lb_LastUsed)

        self.sa_LastUsed = QtWidgets.QScrollArea(self)
        self.sa_LastUsed.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.sa_LastUsed.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.sa_LastUsed.setWidgetResizable(True)
        self.sa_LastUsed.setObjectName("Scroll_LastUsed_2")
        self.luf = QtWidgets.QWidget()
        self.luf.setGeometry(QtCore.QRect(0, 0, 200, 126))
        self.luf.setObjectName("luf")
        self.luf_layout = QtWidgets.QVBoxLayout()
        self.luf_layout.setSpacing(0)
        self.luf_layout.setObjectName("luf_layout")
        self.luf.setLayout(self.luf_layout)

        self.lb_NoUsedFiles = QtWidgets.QLabel()
        self.lb_NoUsedFiles.setObjectName("LB_NoUsedFiles")

        self.sa_LastUsed.setWidget(self.luf)
        self.main_layout.addWidget(self.sa_LastUsed)
        self.central_layout.addLayout(self.main_layout)

        self.retranslateUi()

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.pb_NewLesson.setText(_translate("StartWindow", "New Lesson"))
        self.pb_OpenLesson.setText(_translate("StartWindow", "Open Lesson"))
        self.pb_manager.setText(_translate("StartWindow", "Manage Courses"))
        self.pb_Options.setText(_translate("StartWindow", "Settings"))
        self.lb_UpcomingLessons.setText(_translate("StartWindow", "Upcoming Lessons"))
        __sortingEnabled = self.tw_UpcomingLessons.isSortingEnabled()
        self.tw_UpcomingLessons.setSortingEnabled(False)
        self.tw_UpcomingLessons.setSortingEnabled(__sortingEnabled)
        self.lb_Pinned.setText(_translate("StartWindow", "Pinned"))
        self.lb_NoPinnedData.setText(_translate("StartWindow", "No pinned files"))
        self.lb_LastUsed.setText(_translate("StartWindow", "Recently Used"))
        self.lb_NoUsedFiles.setText(_translate("StartWindow", "No recently used files"))
        
class HLine(QtWidgets.QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)

class LessonCalendar(QtWidgets.QCalendarWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.scheduler: ScheduleModel
        self.dates = []

        self.currentPageChanged.connect(self.set_dates_for_month)

    def set_scheduler(self, scheduler: ScheduleModel) -> None:
        self.scheduler = scheduler
        self.setSelectedDate(QDate.currentDate())
        self.scheduler.dataChanged.connect(self.on_data_changed)

    def set_dates_for_month(self, year: int, month: int) -> None:
        self.dates = self.scheduler.schedules_for_month(QDate(year, month, 1))
        self.repaint()

    def on_data_changed(self) -> None:
        self.set_dates_for_month(self.selectedDate().year(), self.selectedDate().month())

    def paintCell(self, painter: QtGui.QPainter, rect: QtCore.QRect, date: QtCore.QDate) -> None:
        super().paintCell(painter, rect, date)
        count = self.scheduler.date_schedule_count(date)
        if count > 0:        
            
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
            painter.setBrush(Qt.GlobalColor.red)
            painter.setPen(Qt.PenStyle.NoPen)
            
            circle_rect = QRect(rect.right() - 15, rect.top() + 2, 12, 12)
            painter.drawEllipse(circle_rect)
            
            
            if count < 100:
                painter.setPen(Qt.GlobalColor.white)
                font = QFont()
                font.setBold(True)
                font.setPixelSize(9)  # Smaller font size
                painter.setFont(font)
                painter.drawText(circle_rect, Qt.AlignmentFlag.AlignCenter, str(count))


class FileWidget(QtWidgets.QFrame):
    clicked = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(fromStyle("FileFrame"))
        self.setProperty("clicked", True)
        self.setContentsMargins(5,5,5,5)
        self.setUI()

    def setUI(self):
        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.setContentsMargins(0, 1, 5, 3)
        self.main_layout.setSpacing(5)
        self.main_layout.setObjectName("MainLayout")
        self.setLayout(self.main_layout)
        self.sublayout = QtWidgets.QVBoxLayout()
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(False)
        font.setUnderline(False)
        font.setWeight(50)
        
        self.lb_Filename = QtWidgets.QLabel(self)
        self.lb_Filename.setFont(font)
        self.lb_Filename.setStyleSheet("background-color: rgba(255, 255, 255, 0)")
        self.sublayout.addWidget(self.lb_Filename)
        
        font.setPointSize(8)
        self.lb_Path = QtWidgets.QLabel(self)
        self.lb_Path.setStyleSheet("background-color: rgba(255, 255, 255, 0)")
        self.lb_Path.setFont(font)
        self.sublayout.addWidget(self.lb_Path)
        self.main_layout.addLayout(self.sublayout)
        
        self.tb_pin = QtWidgets.QToolButton(self)
        self.tb_pin.setMinimumSize(QtCore.QSize(20, 0))
        self.tb_pin.setMaximumSize(QtCore.QSize(20, 20))
        self.tb_pin.setObjectName("Pin")
        self.tb_pin.setCheckable(True)
        self.tb_pin.setStyleSheet("background: none; border: none")
        self.main_layout.addWidget(self.tb_pin)        