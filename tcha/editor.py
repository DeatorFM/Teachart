import os
from pathlib import Path
from time import sleep

from PyQt6.QtCore import QT_TR_NOOP as tr
from PyQt6.QtCore import (
    QDateTime,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    QRunnable,
    Qt,
    QThreadPool,
    pyqtSignal,
    pyqtSlot,
)
from PyQt6.QtGui import QAction, QCloseEvent, QScreen
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGraphicsScene,
    QMainWindow,
    QMenu,
    QMessageBox,
    QWidget,
)

from nativeelements.baseelement import BaseElementDefinitions, BaseElementModel
from tcha.consts import AppAction, ResourceFlag, TableViewMode
from tcha.dbmanager import AddCourseDialog, RecordView
from tcha.dbmodels import CourseModel, FilteredCourseModel, ScheduleModel
from tcha.debug import FileView, ResourceView, TableTreeView, XmlView
from tcha.lesson import Lesson
from tcha.lfio import LessonFile, ProgressLogger
from tcha.resmanager import ResourceContainer, ResourceObject
from tcha.settings import Settings
from tcha.table import CellEditor, Table
from tcha.tablemodel import CellModel, TableModel
from tcha.utils import WinApi
from ui.editor_view import Ui_Editor


class SaveWorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)


class SaveWorker(QRunnable):
    def __init__(
        self,
        path: str | None,
        lessonfile: LessonFile,
        lesson: Lesson,
        tablemodel: TableModel,
    ):
        super().__init__()
        self._path = path
        self._lf = lessonfile
        self._lesson = lesson
        self._tablemodel = tablemodel
        self.signals = SaveWorkerSignals()

    @pyqtSlot()
    def run(self):
        self._lf.save(self._lesson, self._tablemodel, self._path)
        self.signals.finished.emit()


class Editor(QMainWindow):
    appActionTriggered = pyqtSignal(
        [AppAction], [AppAction, Path], [AppAction, QWidget]
    )
    fileSaved = pyqtSignal(Path)
    indexCopied = pyqtSignal(QPersistentModelIndex)
    presenterActivated = pyqtSignal(QGraphicsScene, QScreen)  # Scene, Target Screen
    presenterClosed = pyqtSignal()

    def __init__(
        self,
        courses: CourseModel,
        schedules: ScheduleModel,
        edefinitions: dict[str, BaseElementDefinitions],
        lessonfile: LessonFile,
        parent=None,
    ) -> None:
        super().__init__(parent, Qt.WindowType.Widget)
        self.ui = Ui_Editor()
        self.ui.setupUi(self)

        # Models
        self.courses = FilteredCourseModel(courses, self)
        self.schedules = schedules

        self.lessonfile = lessonfile
        self.lesson: Lesson

        self.initialise_editor()

        # Attributes
        self._caller = False
        self.changes_unsaved = False if lessonfile.mode == "r" else True
        self.element_definitions = edefinitions
        self.toolsets = self.ui.add_toolsets(self, self.element_definitions)
        self.def_for_mime_type = None
        self.presenter_mode = False
        self.init_display_mode = WinApi.get_display_mode()
        print(f"Initial display mode: {self.init_display_mode}")

        # Intial methods
        self.ui.add_element_actions(self.element_definitions)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.connect_signals()
        self.ui.cb_course.setModel(self.courses)
        self.ui.cb_course.setModelColumn(1)
        self.setMouseTracking(True)
        self.check_clipboard()

    def initialise_editor(self) -> tuple[LessonFile, ResourceContainer]:
        debug_tag = (
            "(Debug-Mode)"
            if Settings.qsettings().value("Application/debug", False, bool)
            else ""
        )
        if self.lessonfile.mode == "w":
            self.set_lesson(
                Lesson(self.courses.source_id(), self.ui.dt_DateTime.dateTime())
            )
            tablemodel = TableModel.new(2, 2)
            self.table.setModel(tablemodel)
            self.ui.cb_course.setCurrentIndex(0)
            self.setWindowTitle(f"{tr('New Document')} - Teachart {debug_tag}")

        elif self.lessonfile.mode == "r":
            tablemodel = self.lessonfile.get_table()
            self.ui.table.setModel(tablemodel)
            self.check_for_schedule(self.lessonfile.file_id)
            self.set_lesson(self.lessonfile.get_lesson())
            self.lessonfile.error_handler.log_msg(
                f"Finished reading file '{os.path.basename(self.lessonfile.path)}' successfully."
            )
            self.ui.ac_xml_insp.setEnabled(True)
            self.setWindowTitle(
                f"{os.path.basename(self.lessonfile.path)} - Teachart {debug_tag}"
            )

        else:
            raise ValueError("LessonFile's mode is invalid. Must be 'w' or 'r'.")

    def connect_signals(self) -> None:
        self.courses.sourceModel().courseDataChanged.connect(
            self.on_course_data_changed
        )
        self.courses.rowsRemoved.connect(self.on_course_data_changed)
        self.courses.dataChanged.connect(self.on_course_data_changed)
        self.schedules.rowsAboutToBeRemoved.connect(self.check_for_schedule)

        self.ui.ac_new_doc.triggered.connect(
            lambda: self.appActionTriggered[AppAction].emit(AppAction.NewFile)
        )
        self.ui.ac_open_doc.triggered.connect(self.open_file_dialog)
        self.ui.tb_open.clicked.connect(
            lambda: self.appActionTriggered[AppAction].emit(AppAction.OpenDialog)
        )
        self.ui.ac_save.triggered.connect(self.save_document)
        self.ui.tb_save.clicked.connect(self.save_document)
        self.ui.ac_save_as.triggered.connect(lambda: self.save_document(True))
        self.ui.ac_close.triggered.connect(self.close)

        self.ui.ac_add_course.triggered.connect(self.add_course)
        self.ui.ac_course_exp.triggered.connect(
            lambda: self.appActionTriggered[AppAction, QWidget].emit(
                AppAction.CourseExplorer, self
            )
        )
        self.ui.ac_course_rec.triggered.connect(self.open_course_record)
        self.ui.ac_copy.triggered.connect(
            lambda: self.table.copy_index(self.table.currentIndex())
        )
        self.ui.ac_paste.triggered.connect(
            lambda: self.ui.table.paste_index(QApplication.clipboard().mimeData())
        )
        # self.ui.ac_course_rec.triggered.connect()
        self.ui.cb_course.activated.connect(self.set_course)
        self.ui.cb_course.lineEdit().textEdited.connect(self.filter_courses)
        self.ui.dt_DateTime.dateTimeChanged.connect(self.set_datetime)
        self.ui.ac_schedule.triggered.connect(self.set_unsaved)
        self.ui.sb_duration.valueChanged.connect(self.set_duration)
        self.ui.ac_pres_mode.toggled.connect(self.enable_presenter_mode)
        self.ui.ac_vmode_table.toggled.connect(
            lambda: self.table.set_view_mode(TableViewMode.Table)
        )
        self.ui.ac_vmode_row.toggled.connect(
            lambda: self.table.set_view_mode(TableViewMode.SingleRow)
        )
        self.ui.ac_goto_active.triggered.connect(self.table.scroll_to_current)
        self.ui.ac_about.triggered.connect(
            lambda: self.appActionTriggered[AppAction].emit(AppAction.AboutTeachart)
        )
        self.ui.te_comment.textChanged.connect(self.set_comment)

        self.ui.ac_settings.triggered.connect(
            lambda: self.appActionTriggered[AppAction, QWidget].emit(
                AppAction.Settings, self
            )
        )

        self.ui.ac_file_insp.triggered.connect(self.open_file_inspector)
        self.ui.ac_xml_insp.triggered.connect(self.open_xml_inspector)
        self.ui.ac_res_view.triggered.connect(self.open_resource_view)
        self.ui.ac_table_insp.triggered.connect(self.open_table_inspector)

        self.ui.te_comment.textChanged.connect(self.set_comment)

        self.ui.table.cellEditorOpened.connect(self.on_cell_opened)
        self.ui.table.cellEditorClosed.connect(self.on_cell_closed)
        self.ui.table.changeMade.connect(self.set_unsaved)

        self.ui.ac_add_row.triggered.connect(
            lambda: self.tablemodel.insertRow(self.ui.table.currentIndex().row() + 1)
        )
        self.ui.ac_add_column.triggered.connect(
            lambda: self.tablemodel.insertColumn(
                self.ui.table.currentIndex().column() + 1
            )
        )
        self.ui.ac_rmv_row.triggered.connect(
            lambda: self.table.remove_row()
        )  # Move to model
        self.ui.ac_rmv_column.triggered.connect(
            lambda: self.table.remove_column()
        )  # Move to model

        self.ui.ac_del_element.triggered.connect(self.remove_element)  # Move to model
        self.ui.ac_mov_up.triggered.connect(
            self.move_element_up
        )  # Move to table or model
        self.ui.ac_mov_dwn.triggered.connect(
            self.move_element_down
        )  # Move to table or model

        self.ui.bg_tools.buttonClicked.connect(self.ui.canvas.set_tool)
        self.ui.bg_colors.buttonClicked.connect(self.ui.canvas.set_color)

        self.ui.tb_row_up.clicked.connect(lambda: self.table.scroll_by(-1))
        self.ui.tb_row_down.clicked.connect(lambda: self.table.scroll_by(1))

        QApplication.clipboard().dataChanged.connect(self.check_clipboard)

    def path(self) -> str | None:
        return self.lessonfile.path

    @property
    def is_caller(self) -> bool:
        return self._caller

    def unset_caller(self) -> None:
        self._caller = False

    # File Methods

    def set_recent_files(self, menu: QMenu) -> None:
        self.ui_recent = self.ui.menu_file.insertMenu(self.ui.sep1, menu)
        menu.triggered.connect(self.on_file_opened)

    def on_file_opened(self, action: QAction) -> None:
        path = action.data()
        if isinstance(path, Path):
            self.appActionTriggered[AppAction, Path].emit(AppAction.OpenFile, path)

    def open_file_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, tr("Open Sheet"), None, "*.lesson *.tch"
        )
        if path:
            self._caller = True
            self.appActionTriggered[AppAction, Path].emit(
                AppAction.OpenFile, Path(path)
            )

    def set_unsaved(self) -> None:
        self.changes_unsaved = True

    def set_lesson(self, lesson: Lesson) -> None:
        if lesson:
            if lesson.source_id == self.courses.source_id():
                source_idx = self.courses.sourceModel().index_for_id(lesson.course_id)
                if source_idx.isValid():
                    mapped_idx = self.courses.mapFromSource(source_idx)
                    self.ui.cb_course.setCurrentIndex(mapped_idx.row())
                else:
                    self.ui.cb_course.setCurrentIndex(0)
            else:
                button = QMessageBox.question(
                    self,
                    tr("Course not found"),
                    tr(
                        "This document's course has no record. Would you like to add it as a new course?"
                    ),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if button == QMessageBox.StandardButton.Yes:
                    id = self.courses.sourceModel().add_course(
                        lesson.course_name, lesson.duration
                    )
                    lesson = Lesson(
                        self.courses.source_id(),
                        lesson.datetime,
                        lesson.course_name,
                        id,
                        lesson.duration,
                    )
                    self.set_unsaved()
                    self.set_lesson(lesson)
                    return
                else:
                    self.ui.cb_course.setCurrentIndex(0)

            self.ui.dt_DateTime.setDateTime(lesson.datetime)
            self.ui.sb_duration.setValue(lesson.duration)
            self.ui.te_comment.document().setHtml(lesson.comment)
            self.lesson = lesson
        else:
            raise ValueError

    def save_document(self, save_copy=False) -> bool:
        """Saves the entire document to a serialised file."""

        def save(path: str) -> None:
            worker = SaveWorker(path, self.lessonfile, self.lesson, self.tablemodel)
            worker.signals.finished.connect(self._on_saving_finished)
            QThreadPool.globalInstance().start(worker)

        self.ui.ac_save.setEnabled(False)
        self.ui.tb_save.setEnabled(False)
        self.lesson.source_id = self.courses.source_id()
        if self.lessonfile.path and not save_copy:
            save(None)
            return True
        else:
            path, _ = QFileDialog.getSaveFileName(
                self, tr("Save lesson chart"), "", tr("Teachart document (*.tch)")
            )
            if path:
                save(path)
                return True
            self.ui.ac_save.setEnabled(True)
            return False

    def _on_saving_finished(self) -> None:
        debug_tag = (
            "(Debug-Mode)"
            if Settings.qsettings().value("Application/debug", False, bool)
            else ""
        )
        self.ui.ac_save.setEnabled(True)
        self.ui.tb_save.setEnabled(True)
        self.setWindowTitle(
            f"{os.path.basename(self.lessonfile.path)} - Teachart {debug_tag}"
        )
        self.changes_unsaved = False
        self.statusBar().showMessage(tr("Saving finished!"), 3000)
        self.schedule()
        self.ui.ac_xml_insp.setEnabled(True)
        self.fileSaved.emit(Path(self.lessonfile.path))

    def schedule(self) -> None:
        """Creates a new schedule if not existing."""
        if self.ui.ac_schedule.state() == 2 and not self.schedules.has_file(
            self.lessonfile.file_id
        ):
            course_id = self.courses.data(
                self.courses.index(self.ui.cb_course.currentIndex(), 0)
            )
            self.schedules.add_schedule(
                course_id,
                self.ui.dt_DateTime.dateTime(),
                self.lessonfile.file_id,
                self.lessonfile.path,
            )
            self.lesson.source_id = self.courses.source_id()
            print("New schedule created for file_id: ", self.lessonfile.file_id)

        elif self.ui.ac_schedule.state() == 2 and self.schedules.has_file(
            self.lessonfile.file_id
        ):
            print("File exists. Updating schedule")
            idx = self.schedules.index_for_file_id(self.lessonfile.file_id)
            if idx.isValid():
                schedule_id = self.schedules.data(idx)
                self.schedules.update_schedule(
                    schedule_id,
                    self.lesson.course_id,
                    self.lesson.datetime,
                    self.lessonfile.path,
                )

        elif self.ui.ac_schedule.state() == 1 and self.schedules.has_file(
            self.lessonfile.file_id
        ):
            idx = self.schedules.index_for_file_id(self.lessonfile.file_id)
            print("Index is valid ", idx.isValid())
            if idx.isValid():
                self.schedules.removeRow(idx.row())
                self.schedules.select()
                print("Deleted scheule with file id: ", self.lessonfile.file_id())

    def check_for_schedule(self, file_id: int) -> None:
        """Checks the button if schedule found."""
        if self.schedules.has_file(file_id):
            self.ui.ac_schedule.changeState(2)
        else:
            self.ui.ac_schedule.changeState(1)

    # Course related methods

    def add_course(self) -> None:
        def isvalid() -> bool:
            if name and duration > 0:
                return True
            return False

        ok, name, duration = AddCourseDialog.get_course_info(self)
        if ok and isvalid():
            self.courses.sourceModel().add_course(name, duration)
        elif ok and not isvalid():
            QMessageBox.warning(
                self, None, tr("Please enter a valid course name and duration.")
            )
            self.add_course()
        else:
            return

    def set_course(self) -> None:
        if self.lesson.source_id != self.courses.source_id():
            self.lesson.source_id = self.courses.source_id()
        item = self.courses.getRow(self.ui.cb_course.currentIndex())
        self.lesson.set_course(item.name, item.id)
        if item.duration > 0:
            self.ui.sb_duration.setValue(item.duration)
        self.print_lesson()
        self.changes_unsaved = True

    def filter_courses(self) -> None:
        self.ui.cb_course.showPopup()
        self.courses.set_search_filter(self.ui.cb_course.lineEdit().text())

    def on_course_data_changed(self) -> None:
        if self.courses.has_id(self.lesson.course_id) and self.lesson.course_id != 0:
            idx = self.courses.index_for_id(self.lesson.course_id)
            if idx.isValid():
                self.ui.cb_course.setCurrentIndex(idx.row())
                return
        self.ui.cb_course.setCurrentIndex(0)
        self.lesson.set_course("", 0)

    # Other Lesson setters

    def set_datetime(self, datetime: QDateTime) -> None:
        self.lesson.set_datetime(datetime)
        self.changes_unsaved = True
        self.print_lesson()

    def set_duration(self, minutes: int) -> None:
        self.lesson.set_duration(minutes)
        self.changes_unsaved = True
        self.print_lesson()

    def set_comment(self) -> None:
        self.lesson.set_comment(self.ui.te_comment.document().toHtml())
        self.changes_unsaved = True
        self.print_lesson()

    # Table Managing Tools

    @property
    def table(self) -> Table:
        return self.ui.table

    @property
    def tablemodel(self) -> TableModel:
        return self.ui.table.model()

    @property
    def resource_path(self) -> Path:
        return self.tablemodel.rescont.temppath

    def on_cell_opened(self, editor: CellEditor) -> None:
        if self.ui.table.currentIndex().isValid() and editor:
            print(
                "Index",
                self.ui.table.currentIndex().row(),
                "|",
                self.ui.table.currentIndex().column(),
                "is valid",
            )
            self.ui.table_group.setEnabled(True)
            self.ui.menu_elements.setEnabled(True)
            self.ui.ac_copy.setEnabled(True)
            self.ui.ac_paste.setEnabled(self.has_index_copied())
            self.ui.ac_goto_active.setEnabled(True)

            editor.connect_toolsets(self.toolsets)
            editor.currentIndexChanged.connect(self.on_current_changed)

            emodel: CellModel = editor.model()
            self.ui.menu_elements.triggered.connect(
                lambda x: emodel.create_model(x.data())
            )
            self.ui.ac_from_clipboard.triggered.connect(
                lambda: emodel.create_from_clipboard(self.def_for_mime_type)
            )
            # editor.elementActivated.connect(self.on_element_activated)

    def on_cell_closed(self) -> None:
        self.ui.table_group.setDisabled(True)
        self.ui.menu_elements.setDisabled(True)
        self.ui.ac_copy.setEnabled(False)
        self.ui.ac_paste.setEnabled(False)
        self.ui.ac_goto_active.setEnabled(False)

        for signal in (self.ui.menu_elements, self.ui.ac_from_clipboard):
            try:
                signal.disconnect()
            except TypeError:
                pass

        for toolset in self.toolsets.values():
            toolset.setVisible(False)

    @pyqtSlot(QAction)
    def on_element_action(self, action: QAction) -> None:
        if action.property("is_element_action"):
            self.add_element(action)
        else:
            self.from_clipboard()

    def remove_element(self) -> None:
        editor = self.table.editor
        if editor:
            result = QMessageBox.question(
                editor,
                tr("Confirm removal"),
                tr("Are you sure you want to permanently remove this element?"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if result == QMessageBox.StandardButton.Yes:
                model = editor.model()
                index = editor.currentIndex()
                editor.setCurrentIndex(QModelIndex())
                if model.removeRow(index.row()):
                    if not editor.copied_index().isValid():
                        clipboard = QApplication.clipboard()
                        clipboard.mimeData().removeFormat("application/x-teachart")
                        clipboard.dataChanged.emit()

    def move_element_up(self) -> None:
        editor = self.table.editor
        if editor:
            model = editor.model()
            index = editor.currentIndex()
            if index.row() > 0:
                model.moveRow(
                    QModelIndex(), index.row(), QModelIndex(), index.row() - 1
                )

    def move_element_down(self) -> None:
        editor = self.table.editor
        if editor:
            model = editor.model()
            index = editor.currentIndex()
            if not index.row() == model.rowCount() - 1:
                model.moveRow(
                    QModelIndex(), index.row(), QModelIndex(), index.row() + 1
                )

    def on_about_to_remove_row(self) -> None:
        current_row = self.ui.table.currentIndex().row()
        self.ui.table.setCurrentIndex(QModelIndex())
        self.tablemodel.removeRow(current_row)

    def on_about_to_remove_column(self) -> None:
        current_column = self.ui.table.currentIndex().column()
        self.ui.table.setCurrentIndex(QModelIndex())
        self.tablemodel.removeColumn(current_column)

    def add_element(self, action: QAction) -> None:
        print("Init adding model")
        definition = action.data()

        if self.table.editor:
            match definition.resource_flag():
                case ResourceFlag.NoResource:
                    resobj = self.rescont.create(definition.type())

                case ResourceFlag.HasResource:
                    resource = definition.get_file()
                    if resource:
                        resobj = self.rescont.save(definition.type(), resource)
                        assert isinstance(resobj, ResourceObject)
                    else:
                        return

                case ResourceFlag.Optional:
                    resource = definition.get_file()
                    if resource:
                        resobj = self.rescont.save(definition.type(), resource)
                        assert isinstance(resobj, ResourceObject)
                    else:
                        resobj = self.rescont.create(definition.type())

            model = definition.create_model(resobj)

            cell_model = self.table.editor.model()
            print(f"Adding to cell model {cell_model}")
            if cell_model is not None:
                cell_model.add_model(model)
                print("Model added")
                self.table.editor.geometriesChanged.emit()

    def print_lesson(self) -> None:
        try:
            print(self.lesson)
        except AttributeError:
            pass

    def check_clipboard(self) -> None:
        """Checks whether the mime type of the clipboard data is supported by one of the elements"""
        clipboard = QApplication.clipboard()
        print(f"Mime Types: {clipboard.mimeData().formats()}")
        if clipboard:
            mime = clipboard.mimeData()
            for definition in self.element_definitions.values():
                if definition.supports_mime_data(mime):
                    self.def_for_mime_type = definition
                    self.ui.ac_from_clipboard.setEnabled(True)
                    print(
                        f"Supported definition for current mime types: {self.def_for_mime_type}"
                    )
                    return

            if self.has_index_copied() and self.ui.table.editor:
                self.ui.ac_paste.setEnabled(True)
            else:
                self.ui.ac_paste.setEnabled(False)

        self.def_for_mime_type = None
        self.ui.ac_from_clipboard.setEnabled(False)
        print(f"Supported definition of mime type: {self.def_for_mime_type}")

    def has_index_copied(self) -> bool:
        clipboard = QApplication.clipboard()
        if clipboard:
            if "application/x-teachart" in clipboard.mimeData().formats():
                return True
        return False

    # Presenter Functions

    def enable_presenter_mode(self, enabled: bool) -> None:
        self.ui.dw_presenter.setEnabled(enabled)
        self.ui.dw_presenter.setVisible(enabled)
        self.ui.tb_table.setEnabled(not enabled)
        self.presenter_mode = enabled

        if enabled:
            self.ui.dw_comment.setVisible(False)
            self.ui.canvas.set_color(self.ui.bg_colors.checkedButton())
            self.ui.canvas.set_tool(self.ui.bg_tools.checkedButton())
            dwa = self.dockWidgetArea(self.ui.dw_presenter)
            orientation = (
                Qt.Orientation.Horizontal
                if dwa == Qt.DockWidgetArea.LeftDockWidgetArea
                or dwa == Qt.DockWidgetArea.RightDockWidgetArea
                else Qt.Orientation.Vertical
            )
            size = (
                self.width() // 2 - 50
                if orientation == Qt.Orientation.Horizontal
                else self.table.height() // 2
            )
            self.resizeDocks(
                [self.ui.dw_presenter],
                [size],
                orientation,
            )
            self.presenterActivated.emit(self.ui.canvas.scene(), self)
        else:
            self.ui.canvas.clear()
            self.presenterClosed.emit()

        self.ui.table.enable_presenter_mode(enabled)

    # Dialog opener

    def open_course_record(self) -> None:
        dialog = RecordView(self.lesson.course_id, self.courses.sourceModel(), self)
        dialog.managerCalled.connect(
            lambda: self.appActionTriggered[AppAction, QWidget].emit(
                AppAction.CourseExplorer, self
            )
        )
        dialog.open()

    def on_current_changed(self, idx: QModelIndex) -> None:
        if self.presenter_mode:
            model: BaseElementModel = idx.data()
            if model:
                gr_item = model.presentable_item()
                if gr_item:
                    self.ui.canvas.change_item(gr_item)

    # Other controls

    def set_progress_logger(self, file_name: Path, logger: ProgressLogger) -> None:
        self.ui.loading_bar.setVisible(True)
        translated_label = tr("Loading")
        status_label = "{} {}".format(translated_label, file_name.name)
        self.ui.statusbar.showMessage(status_label)
        self.ui.loading_bar.setVisible(True)
        logger.progressChanged.connect(self.ui.loading_bar.setValue)

    def reset_progress(self) -> None:
        self.ui.statusbar.clearMessage()
        self.ui.loading_bar.setVisible(False)
        self.ui.loading_bar.setValue(0)

    # Debug menus

    def open_file_inspector(self) -> None:
        dialog = FileView(self)
        schedule_id = self.schedules.index_for_file_id(self.lessonfile.file_id)
        if schedule_id.isValid():
            dialog.setup_view(self.lessonfile, self.lesson, schedule_id.row())
        else:
            dialog.setup_view(self.lessonfile, self.lesson, None)
        dialog.show()

    def open_xml_inspector(self) -> None:
        dialog = XmlView(self)
        dialog.setup_view(self.lessonfile.xml(), self.lessonfile.xml("resources"))
        dialog.show()

    def open_resource_view(self) -> None:
        dialog = ResourceView(self)
        dialog.setup_view(self.tablemodel.rescont)
        dialog.show()

    def open_table_inspector(self) -> None:
        dialog = TableTreeView(self)
        dialog.setup_view(self.tablemodel)
        dialog.show()

    def close_streams(self):
        self.rescont.close_file_streams()
        if self.lessonfile:
            self.lessonfile.close()

    # Event handlers

    def closeEvent(self, ev: QCloseEvent):
        """THe user is asked if they want to savbe the document when there are unsaved changes"""
        if self.changes_unsaved:
            result = QMessageBox.question(
                self,
                tr("Unsaved Changes"),
                tr("There are unsaved changes. Would you like to save the document?"),
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
            if result == QMessageBox.StandardButton.Save:
                saved = self.save_document()
                if not saved:
                    ev.ignore()
                    return
            elif result == QMessageBox.StandardButton.Discard:
                pass
            else:
                ev.ignore()
                return
        if self.presenter_mode:
            self.presenterClosed.emit()

        self.tablemodel.rescont.close_file_streams()
        super().closeEvent(ev)
