from __future__ import annotations

import os.path as osp
import platform
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import QT_TR_NOOP as tr
from PyQt6.QtCore import (
    QAbstractTableModel,
    QCoreApplication,
    QDate,
    QLibraryInfo,
    QModelIndex,
    QSortFilterProxyModel,
    Qt,
    pyqtSignal,
)
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHeaderView,
    QMenu,
)
from tcha import utils
from tcha.base import BaseMainWindow
from tcha.dbmodels import FilteredScheduleModel, ScheduleModel
from ui.ui_about import Ui_AboutDialog
from ui.ui_start import Ui_StartWindow


@dataclass
class FileItem:
    path: Path
    recent: bool
    pinned: bool


ABOUT_HTML = r'<html><head/><body><p><span style=" font-size:16pt; font-weight:600;">Teachart</span></p><p><br /><span style=" font-size:10pt;">Teachart is a tool for teachers to create lesson plans in a table structure.<br />Teachart is a free software and currently still in development.</span></p><p><span style=" font-size:10pt;">Version [Version]<br />Python [Python] <br />Qt [Qt]</span></p><p><a href="https://github.com/DeatorFM/Educhart"><span style=" font-size:10pt; text-decoration: underline; color:#0000ff;">Git Hub</span></a></p><p><span style=" font-size:10pt;">Written and translated in German by Florian Münstermann. </span></p><p><span style=" font-size:10pt;">UI Design adapted from PyQtDarkTheme by 5yutan5:<br /></span><a href="https://github.com/5yutan5/PyQtDarkTheme"><span style=" font-size:10pt; text-decoration: underline; color:#0000ff;">PyQtDarkTheme on Git Hub</span></a></p></body></html>'


class FilteredOpenFileModel(QSortFilterProxyModel):
    def __init__(self, file_model: OpenFileModel, parent=None):
        super().__init__(parent)
        self.setSourceModel(file_model)

        self._filter_mode = False  # False = only recent, True = only pinned

    def set_filter_mode(self, mode: bool) -> None:
        self.beginFilterChange()
        self._filter_mode = mode
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        smodel: OpenFileModel = self.sourceModel()
        item = smodel.get_item(source_row)
        if item is None:
            return False

        if self._filter_mode:
            return item.pinned
        else:
            return item.recent


class OpenFileModel(QAbstractTableModel):
    def __init__(self, recent_files: list[str], pinned_file: list[str], parent=None) -> None:
        super().__init__(parent)
        self._data: list[FileItem] = self._build_data(recent_files, pinned_file)

    def _build_data(self, recent: list[str], pinned: list[str]) -> list[FileItem]:
        new_list = []
        for path in recent:
            pathobj = Path(path)
            if pathobj.suffix in (".lesson", ".tch"):
                if path in pinned:
                    new_list.append(FileItem(pathobj, True, True))
                    continue
                new_list.append(FileItem(pathobj, True, False))

        # Add pinned-only files
        pinned_only = list(filter(lambda x: x not in recent, pinned))
        for path in pinned_only:
            new_list.append(FileItem(Path(path), False, True))

        return new_list

    def columnCount(self, parent=QModelIndex()):
        return 2

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def has_file(self, path: str) -> bool:
        return Path(path) in self.paths()

    def paths(self) -> list[str]:
        return [item.path for item in self._data]

    def append_file(self, path: str, strict=True) -> bool:
        """
        Appends file or puts it at the first index if existing.
        If strict is True only files that exist will be added.
        Returns True if the file was added.
        """
        pathobj = Path(path)
        if not self.has_file(path):
            if (pathobj.exists() or not strict) and pathobj.suffix in (".lesson", ".tch"):
                self._data.insert(0, FileItem(pathobj, True, False))
                self.rowsInserted.emit(QModelIndex(), 0, 0)
                return True
            return False

        idx = self.paths().index(pathobj)
        if idx > 0:
            self._data.insert(0, self._data.pop(idx))
            self.rowsMoved.emit(QModelIndex(), idx, idx, QModelIndex(), 0)
        return True

    def get_item(self, row: int) -> FileItem | None:
        try:
            return self._data[row]
        except IndexError:
            return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        try:
            if role == Qt.ItemDataRole.DisplayRole:
                if index.column() == 0:
                    return self._data[index.row()].path
                elif index.column() == 1:
                    return self._data[index.row()].pinned
            if role == Qt.ItemDataRole.ToolTipRole:
                if index.column() == 0:
                    return str(self._data[index.row()].path)
                elif index.column() == 1:
                    if self._data[index.row()].pinned:
                        return tr("Unpin")
                    return tr("Pin")
            return None
        except IndexError:
            return None

    def setData(self, index: QModelIndex, value: bool, role=Qt.ItemDataRole.EditRole):
        if isinstance(value, bool) and index.column() == 1:
            try:
                self._data[index.row()].pinned = value
                self.dataChanged.emit(index, index, [role])
                return True
            except IndexError:
                return False
        return False

    def export_recent(self, max_size=10) -> list[str]:
        filtered = [item.path.as_posix() for item in filter(lambda x: x.recent, self._data)]
        length = len(filtered)
        return filtered[:10] if length >= max_size else filtered[:length]

    def export_recent_as_menu(self, max_size=10) -> QMenu:
        file_list = self.export_recent(max_size)
        menu = QMenu(tr("Recent Files"))
        for file in file_list:
            ac = menu.addAction(osp.basename(file))
            ac.setData(Path(file))
        return menu

    def export_pinned(self) -> list[str]:
        return [item.path.as_posix() for item in filter(lambda x: x.pinned, self._data)]

    def flags(self, index: QModelIndex):
        if index.column() == 1:
            return Qt.ItemFlag.ItemIsEditable
        return super().flags(index)


class StartWindow(BaseMainWindow):
    dialogCalled = pyqtSignal(str)
    fileOpened = pyqtSignal(Path, BaseMainWindow)

    def __init__(
        self,
        file_model: OpenFileModel,
        schedule_model: ScheduleModel,
        file_mode=False,
        parent=None,
        flags=Qt.WindowType.Dialog,
    ):
        super().__init__(parent, flags)
        self.ui = Ui_StartWindow()
        self.ui.setupUi(self)

        if file_mode:
            debug_tag = self.tr("Debug-Mode") if utils.debug_enabled() else ""
            self.ui.ac_new.setVisible(False)
            self.ui.ac_settings.setVisible(False)
            self.setWindowTitle(f"{self.tr('Open File')} {debug_tag}")

        self.resize(700, 400)

        self._schedule_model = FilteredScheduleModel(schedule_model)
        self._schedule_model.setSortRole(Qt.ItemDataRole.EditRole)
        self._schedule_model.sort(3, Qt.SortOrder.AscendingOrder)

        self._recentf_model = FilteredOpenFileModel(file_model)
        self._pinnedf_model = FilteredOpenFileModel(file_model)
        self._pinnedf_model.set_filter_mode(True)

        self.ui.calendar.set_scheduler(schedule_model)
        self._schedule_model.set_exclusive_date(self.ui.de_date_selector.date())

        self.ui.lv_scheduledf.setModel(self._schedule_model)

        self.ui.tv_recent.setModel(self._recentf_model)
        self.ui.tv_recent.header().setStretchLastSection(False)
        self.ui.tv_recent.setColumnWidth(1, 10)
        self.ui.tv_recent.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.ui.tv_recent.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.ui.tv_recent.setHeaderHidden(True)

        self.ui.tv_pinned.setModel(self._pinnedf_model)
        self.ui.tv_pinned.header().setStretchLastSection(False)
        self.ui.tv_pinned.setColumnWidth(1, 10)
        self.ui.tv_pinned.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.ui.tv_pinned.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.ui.tv_pinned.setHeaderHidden(True)

        self.connect_signals()
        self.update_schedule_message()

    def connect_signals(self) -> None:
        self.ui.ac_new.triggered.connect(lambda: self.dialogCalled.emit("Editor"))
        self.ui.ac_open.triggered.connect(self.open_file_dialog)
        self.ui.ac_course_mng.triggered.connect(lambda: self.dialogCalled.emit("DbManager"))
        self.ui.ac_settings.triggered.connect(lambda: self.dialogCalled.emit("SettingsDialog"))
        self.ui.tv_recent.clicked.connect(self.open_file)
        self.ui.tv_pinned.clicked.connect(self.open_file)
        self.ui.lv_scheduledf.clicked.connect(self.open_scheduled)
        self.ui.de_date_selector.dateChanged.connect(self.on_date_changed)
        self.ui.cb_show_past_schedules.checkStateChanged.connect(self.set_past_schedules_visible)
        self.ui.tb_about.clicked.connect(lambda: self.dialogCalled.emit("AboutDialog"))

    @property
    def wid(self):
        return 0

    def open_file(self, index: QModelIndex) -> None:
        if index.column() == 0:
            self.fileOpened.emit(index.data(), self)

    def open_scheduled(self, index: QModelIndex) -> None:
        """Opens a scheduled file at given index in the schedule model."""
        new_idx = self._schedule_model.index(index.row(), 5)
        if new_idx.isValid():
            path = self._schedule_model.data(new_idx)
            self.fileOpened.emit(Path(path), self)

    def open_file_dialog(self) -> None:
        """Opens native file dialog. If a file has been selected a signal will be emitted with the selected path as a 'Path'-object"""
        path, _ = QFileDialog.getOpenFileName(
            self, tr("Open File Dialog"), filter=tr("Teachart document (*.tch)")
        )
        self.fileOpened.emit(Path(path), self)

    def set_past_schedules_visible(self, state: Qt.CheckState) -> None:
        """Handles CheckState of the check box for showing past schedules in the list."""
        if state == Qt.CheckState.Checked:
            self._schedule_model.set_past_schedules_visible(True)
        else:
            self._schedule_model.set_past_schedules_visible(False)

    def on_date_changed(self, date: QDate) -> None:
        """Handler when date in the calendar widget above the schedules list has been changed."""
        self._schedule_model.set_exclusive_date(date)
        self.update_schedule_message()

    def update_schedule_message(self) -> None:
        """Updates the schedule message in the status bar."""
        count = self._schedule_model.rowCount()
        if count == 0:
            message = tr("No upcoming lessons today.")
        else:
            translated = tr("upcoming lessons today")
            message = f"{count} {translated}"

        self.ui.status_bar.showMessage(message)

    def set_status_bar_msg(self, msg: str) -> None:
        self.ui.status_bar.showMessage(msg)

    def set_progress(self, value: int) -> None:
        self.ui.loading_bar.setVisible(True)
        self.ui.loading_bar.setValue(value)

    def reset_progress(self) -> None:
        self.ui.status_bar.clearMessage()
        self.ui.loading_bar.setVisible(False)
        self.ui.loading_bar.setValue(0)

    def closeEvent(self, ev: QCloseEvent):
        self.ui.lv_scheduledf.setModel(None)
        self._schedule_model = None
        self.closed.emit("StartWindow", 0)
        super().closeEvent(ev)


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Dialog)
        self.ui = Ui_AboutDialog()
        self.ui.setupUi(self)

        self.setWindowModality(Qt.WindowModality.NonModal)
        self.resize(750, 380)
        self.set_text()

    def set_text(self) -> None:
        html = ABOUT_HTML
        html = html.replace("[Version]", QCoreApplication.applicationVersion())
        html = html.replace("[Python]", platform.python_version())
        html = html.replace("[Qt]", QLibraryInfo.version().toString())
        self.ui.lb_description.setText(html)
