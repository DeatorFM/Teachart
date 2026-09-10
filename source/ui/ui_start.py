import os.path as osp
from pathlib import Path

from PyQt6.QtCore import QT_TR_NOOP as tr
from PyQt6.QtCore import (
    QAbstractItemModel,
    QCoreApplication,
    QDate,
    QEvent,
    QModelIndex,
    QPoint,
    QRect,
    QSize,
    Qt,
    QTime,
)
from PyQt6.QtGui import QAction, QFont, QPainter
from PyQt6.QtWidgets import (
    QApplication,
    QCalendarWidget,
    QCheckBox,
    QDateEdit,
    QDockWidget,
    QListView,
    QMainWindow,
    QProgressBar,
    QSizePolicy,
    QStatusBar,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionButton,
    QStyleOptionViewItem,
    QTabWidget,
    QToolBar,
    QToolButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)
from styling.utils import SvgIcon
from tcha.dbmodels import FilteredScheduleModel, ScheduleModel
from tcha.utils import debug_enabled


class Ui_StartWindow(object):
    def setupUi(self, start_window: QMainWindow):
        start_window.setObjectName("start_window")
        start_window.resize(522, 342)

        self.central_widget = QWidget(parent=start_window)
        self.central_widget.setObjectName("central_widget")
        self.vl = QVBoxLayout(self.central_widget)
        self.vl.setObjectName("vl")

        self.file_tabs = QTabWidget(parent=self.central_widget)
        font = QFont()
        font.setPointSize(10)
        self.file_tabs.setFont(font)
        self.file_tabs.setObjectName("file_tabs")

        self.tab_recent = QWidget()
        self.tab_recent.setObjectName("tab_recent")

        self.vl2 = QVBoxLayout(self.tab_recent)
        self.vl2.setContentsMargins(0, 0, 0, 0)
        self.vl2.setSpacing(0)
        self.vl2.setObjectName("vl2")

        self.tv_recent = QTreeView(parent=self.tab_recent)
        self.tv_recent.setObjectName("tv_recent")
        recent_delegate = OpenFileDelegate(self.tv_recent)
        self.tv_recent.setItemDelegate(recent_delegate)
        self.vl2.addWidget(self.tv_recent)

        self.file_tabs.addTab(self.tab_recent, "")

        self.tab_pinned = QWidget()
        self.tab_pinned.setObjectName("tab_pinned")
        self.vl4 = QVBoxLayout(self.tab_pinned)
        self.vl4.setContentsMargins(0, 0, 0, 0)
        self.vl4.setObjectName("vl4")

        self.tv_pinned = QTreeView(parent=self.tab_pinned)
        self.tv_pinned.setObjectName("tv_pinned")
        pinned_delegate = OpenFileDelegate(self.tv_pinned)
        self.tv_pinned.setItemDelegate(pinned_delegate)
        self.vl4.addWidget(self.tv_pinned)
        self.file_tabs.addTab(self.tab_pinned, "")
        self.vl.addWidget(self.file_tabs)

        start_window.setCentralWidget(self.central_widget)

        self.tb_file_actions = QToolBar(parent=start_window)
        self.tb_file_actions.setMovable(False)
        self.tb_file_actions.setAllowedAreas(Qt.ToolBarArea.TopToolBarArea)
        self.tb_file_actions.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.tb_file_actions.setFloatable(False)
        self.tb_file_actions.setObjectName("tb_file_actions")
        start_window.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.tb_file_actions)

        self.dw_scheduledf = QDockWidget(parent=start_window)
        self.dw_scheduledf.setMinimumSize(QSize(200, 250))
        font = QFont()
        font.setPointSize(8)
        self.dw_scheduledf.setFont(font)
        self.dw_scheduledf.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.dw_scheduledf.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)
        self.dw_scheduledf.setObjectName("dw_scheduledf")

        self.dw_widget = QWidget()
        self.dw_widget.setObjectName("dw_widget")
        self.vl3 = QVBoxLayout(self.dw_widget)
        self.vl3.setObjectName("vl3")

        self.de_date_selector = QDateEdit(parent=self.dw_widget)
        self.de_date_selector.setCalendarPopup(True)
        self.de_date_selector.setObjectName("de_date_selector")
        self.de_date_selector.setDate(QDate.currentDate())
        self.calendar = LessonCalendar(self.dw_widget)
        self.de_date_selector.setCalendarWidget(self.calendar)
        self.vl3.addWidget(self.de_date_selector)

        self.lv_scheduledf = QListView(parent=self.dw_widget)
        self.lv_scheduledf.setMinimumSize(QSize(150, 0))
        self.lv_scheduledf.setObjectName("lv_scheduledf")
        delegate = ScheduledFileDelegate(self.lv_scheduledf)
        self.lv_scheduledf.setItemDelegate(delegate)
        self.lv_scheduledf.setModelColumn(3)
        self.lv_scheduledf.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
        self.vl3.addWidget(self.lv_scheduledf)

        self.cb_show_past_schedules = QCheckBox(self.dw_widget)
        self.cb_show_past_schedules.setObjectName("cb_show_past_schedules")
        self.vl3.addWidget(self.cb_show_past_schedules)

        self.dw_scheduledf.setWidget(self.dw_widget)
        start_window.addDockWidget(Qt.DockWidgetArea(1), self.dw_scheduledf)

        self.ac_open = QAction(parent=start_window)
        self.ac_open.setObjectName("ac_open")
        icon1 = start_window.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        self.ac_open.setIcon(icon1)

        self.ac_new = QAction(parent=start_window)
        self.ac_new.setObjectName("ac_new")
        icon2 = start_window.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
        self.ac_new.setIcon(icon2)

        self.ac_course_mng = QAction(parent=start_window)
        self.ac_course_mng.setObjectName("ac_course_mng")
        icon4 = SvgIcon(":/common/edu")
        self.ac_course_mng.setIcon(icon4)

        self.ac_settings = QAction(parent=start_window)
        self.ac_settings.setObjectName("ac_settings")
        icon3 = SvgIcon(":/common/settings")
        self.ac_settings.setIcon(icon3)

        self.tb_file_actions.addAction(self.ac_new)
        self.tb_file_actions.addAction(self.ac_open)

        spa1 = QWidget(self.tb_file_actions)
        spa1.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.tb_file_actions.addWidget(spa1)

        self.tb_file_actions.addAction(self.ac_course_mng)
        self.tb_file_actions.addAction(self.ac_settings)

        self.status_bar = QStatusBar(start_window)
        self.status_bar.setMaximumHeight(25)
        start_window.setStatusBar(self.status_bar)

        self.loading_bar = QProgressBar(start_window)
        self.loading_bar.setMaximum(100)
        self.loading_bar.setFixedWidth(80)
        self.loading_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.loading_bar)

        self.tb_about = QToolButton(self.status_bar)
        self.tb_about.setObjectName("tb_about")
        icon5 = SvgIcon(":/common/about")
        self.tb_about.setIcon(icon5)
        self.tb_about.setIconSize(QSize(22, 22))
        self.status_bar.addPermanentWidget(self.tb_about)

        self.retranslateUi(start_window)
        self.file_tabs.setCurrentIndex(0)

    def retranslateUi(self, start_window: QMainWindow):
        _translate = QCoreApplication.translate
        if debug_enabled():
            start_window.setWindowTitle(start_window.tr("Start - Teachart (Debug-Mode)"))
        else:
            start_window.setWindowTitle(start_window.tr("Start - Teachart"))
        self.file_tabs.setTabText(
            self.file_tabs.indexOf(self.tab_recent),
            start_window.tr("Recent Files"),
        )
        self.file_tabs.setTabText(
            self.file_tabs.indexOf(self.tab_pinned),
            _translate("start_window", "Pinned Files"),
        )
        self.tb_file_actions.setWindowTitle(_translate("start_window", "File Actions"))
        self.dw_scheduledf.setWindowTitle(_translate("start_window", "Scheduled Files"))
        self.cb_show_past_schedules.setText(_translate("start_window", "Show past lessons"))
        self.ac_open.setText(_translate("start_window", "Browse"))
        self.ac_new.setText(_translate("start_window", "New Sheet"))
        self.ac_course_mng.setText(_translate("start_window", "Course Explorer"))
        self.tb_about.setToolTip(_translate("start_window", "About Teachart"))


class LessonCalendar(QCalendarWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.scheduler: ScheduleModel | None = None
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

    def paintCell(self, painter: QPainter, rect: QRect, date: QDate) -> None:
        super().paintCell(painter, rect, date)
        if self.scheduler:
            count = self.scheduler.date_schedule_count(date)
            if count > 0:
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
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


class ScheduledFileDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.COURSE_FONT = QFont()
        self.COURSE_FONT.setPixelSize(14)

        self.TIME_FONT = QFont()
        self.TIME_FONT.setPixelSize(11)

        self.PATH_FONT = QFont()
        self.PATH_FONT.setPixelSize(11)
        self.PATH_FONT.setItalic(True)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.save()
        super().paint(painter, option, QModelIndex())
        painter.restore()

        painter.save()

        option.rect = option.rect.adjusted(3, 2, 3, 2)

        model: FilteredScheduleModel = index.model()
        course_idx, time_idx, path_idx = (
            model.index(index.row(), 1),
            model.index(index.row(), 3),
            model.index(index.row(), 5),
        )

        course_name = course_idx.data() if course_idx.data() else tr("No course")

        painter.setFont(self.COURSE_FONT)
        painter.drawText(option.rect, 0, course_name)

        option.rect = option.rect.adjusted(0, 18, 0, 18)

        item_time = time_idx.data(Qt.ItemDataRole.EditRole)
        current = QTime.currentTime().msecsSinceStartOfDay()
        remaining = item_time - current if item_time > current else 0
        qtime = QTime.fromMSecsSinceStartOfDay(remaining)

        if remaining < 3_600_000:
            remaining_str = tr(f"in {qtime.minute()} min")
        else:
            remaining_str = tr(f"in {qtime.hour()}h{qtime.minute()}min")

        time_str = f"{time_idx.data()} ({remaining_str})"
        painter.setFont(self.TIME_FONT)
        painter.drawText(option.rect, 0, time_str)

        option.rect = option.rect.adjusted(0, 15, 0, 15)

        painter.setFont(self.PATH_FONT)
        painter.drawText(option.rect, 0, Path(path_idx.data()).name)

        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex):
        return QSize(option.rect.width(), 53)


class OpenFileDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.BASENAME_FONT = QFont()
        self.BASENAME_FONT.setPixelSize(14)

        self.ABSPATH_PATH = QFont()
        self.ABSPATH_PATH.setPixelSize(11)

        self.ICON_ON = SvgIcon(":/common/pinned")

        self.ICON_OFF = SvgIcon(":/common/not_pinned")

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.save()
        super().paint(painter, option, QModelIndex())
        painter.restore()

        painter.save()

        if index.column() == 0:
            option.rect = option.rect.adjusted(3, 5, 3, 5)
            painter.setFont(self.BASENAME_FONT)
            painter.drawText(option.rect, 0, osp.basename(index.data()))

            option.rect = option.rect.adjusted(0, 16, 0, 16)
            painter.setFont(self.ABSPATH_PATH)
            path_str = index.data().as_posix().replace("/", " >> ")
            painter.drawText(option.rect, 0, path_str)

        elif index.column() == 1:
            option.rect.adjusted(3, 15, 3, 15)

            opts = QStyleOptionButton()
            opts.rect = self.getCheckBoxRect(option)
            opts.state |= QStyle.StateFlag.State_Enabled
            opts.iconSize = QSize(18, 18)

            if index.data():
                opts.icon = self.ICON_ON

            else:
                opts.icon = self.ICON_OFF

            QApplication.style().drawControl(QStyle.ControlElement.CE_CheckBoxLabel, opts, painter)

        painter.restore()

    def createEditor(self, parent, option, index):
        return None

    def editorEvent(
        self,
        event: QEvent,
        model: QAbstractItemModel,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ):
        if index.column() == 1 and event.button() == Qt.MouseButton.LeftButton:
            if event.type() == QEvent.Type.MouseButtonRelease:
                if self.getCheckBoxRect(option).contains(event.pos()):
                    self.setModelData(None, model, index)
                    return True
            elif event.type() == QEvent.Type.MouseButtonDblClick:
                if self.getCheckBoxRect(option).contains(event.pos()):
                    return True
        return False

    def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex):
        if index.column() == 1:
            checked = not bool(index.data())
            model.setData(index, checked)

    def getCheckBoxRect(self, option):
        """Get rect for checkbox centered in option.rect."""
        # Get size of a standard checkbox.
        opts = QStyleOptionButton()
        checkBoxRect = QApplication.style().subElementRect(
            QStyle.SubElement.SE_CheckBoxIndicator, opts, None
        )

        # Center checkbox in option.rect.
        x = option.rect.x()
        y = option.rect.y()
        w = option.rect.width()
        h = option.rect.height()
        checkBoxTopLeftCorner = QPoint(
            x + w // 2 - checkBoxRect.width() // 2,
            y + h // 2 - checkBoxRect.height() // 2,
        )
        return QRect(checkBoxTopLeftCorner, checkBoxRect.size())

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex):
        if index.column() == 0:
            return QSize(option.rect.width(), 40)
        else:
            return QSize(10, 40)
