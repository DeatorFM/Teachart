from __future__ import annotations

import os.path as osp
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import QT_TR_NOOP as tr
from PyQt6.QtCore import (
    QAbstractTableModel,
    QDate,
    QModelIndex,
    QSortFilterProxyModel,
    Qt,
    pyqtSignal,
)
from PyQt6.QtWidgets import QFileDialog, QHeaderView, QMainWindow, QMenu, QWidget

from tcha.consts import AppAction
from tcha.dbmodels import FilteredScheduleModel, ScheduleModel
from ui.start_view import Ui_StartWindow


@dataclass
class FileItem:
    path: Path
    recent: bool
    pinned: bool


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
    def __init__(
        self, recent_files: list[str], pinned_file: list[str], parent=None
    ) -> None:
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
            new_list.append(FileItem(pathobj, False, True))

        return new_list

    def columnCount(self, parent=QModelIndex()):
        return 2

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def has_file(self, path: str) -> bool:
        return Path(path) in self.paths()

    def paths(self) -> list[str]:
        return [item.path for item in self._data]

    def append_file(self, path: str) -> bool:
        """Appends file or puts it at the first index if existing."""
        pathobj = Path(path)
        if not self.has_file(path):
            if pathobj.exists() and pathobj.suffix in (".lesson", ".tch"):
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
                print("Setting pinned")
                self._data[index.row()].pinned = value
                self.dataChanged.emit(index, index, [role])
                return True
            except IndexError:
                return False
        return False

    def export_recent(self, max_size=10) -> list[str]:
        filtered = [
            item.path.as_posix() for item in filter(lambda x: x.recent, self._data)
        ]
        length = len(filtered)
        return filtered[:10] if length >= max_size else filtered[: length - 1]

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


class StartWindow(QMainWindow):
    appActionTriggered = pyqtSignal(
        [AppAction, Path], [AppAction, QWidget], [AppAction]
    )

    def __init__(
        self,
        file_model: OpenFileModel,
        schedule_model: ScheduleModel,
        parent=None,
        flags=Qt.WindowType.Dialog,
    ):
        super().__init__(parent, flags)
        self.ui = Ui_StartWindow()
        self.ui.setupUi(self)

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
        self.ui.tv_recent.header().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.ui.tv_recent.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.ui.tv_recent.setHeaderHidden(True)

        self.ui.tv_pinned.setModel(self._pinnedf_model)
        self.ui.tv_pinned.header().setStretchLastSection(False)
        self.ui.tv_pinned.setColumnWidth(1, 10)
        self.ui.tv_pinned.header().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.ui.tv_pinned.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.ui.tv_pinned.setHeaderHidden(True)

        self.connect_signals()

    def connect_signals(self) -> None:
        self.ui.ac_new.triggered.connect(
            lambda: self.appActionTriggered[AppAction].emit(AppAction.NewFile)
        )
        self.ui.ac_open.triggered.connect(self.open_file_dialog)
        self.ui.ac_course_mng.triggered.connect(
            lambda: self.appActionTriggered[AppAction, QWidget].emit(
                AppAction.CourseExplorer, self
            )
        )
        self.ui.ac_settings.triggered.connect(
            lambda: self.appActionTriggered[AppAction, QWidget].emit(
                AppAction.Settings, self
            )
        )
        self.ui.tv_recent.clicked.connect(self.open_file)
        self.ui.tv_pinned.clicked.connect(self.open_file)
        self.ui.lv_scheduledf.clicked.connect(self.open_scheduled)
        self.ui.de_date_selector.dateChanged.connect(self.on_date_changed)
        self.ui.cb_show_past_schedules.checkStateChanged.connect(
            self.set_past_schedules_visible
        )

    def open_file(self, index: QModelIndex) -> None:
        if index.column() == 0:
            self.appActionTriggered.emit(AppAction.OpenFile, index.data())

    def open_scheduled(self, index: QModelIndex) -> None:
        new_idx = self._schedule_model.index(index.row(), 5)
        path = self._schedule_model.data(new_idx)
        self.appActionTriggered.emit(AppAction.OpenFile, Path(path))

    def open_file_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, tr("Open File Dialog"), filter="*.lesson *.tch"
        )
        self.appActionTriggered.emit(AppAction.OpenFile, Path(path))

    def set_past_schedules_visible(self, state: Qt.CheckState) -> None:
        if state == Qt.CheckState.Checked:
            self._schedule_model.set_past_schedules_visible(True)
        else:
            self._schedule_model.set_past_schedules_visible(False)

    def on_date_changed(self, date: QDate) -> None:
        self._schedule_model.set_exclusive_date(date)
