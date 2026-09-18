from nativeelements.baseelement import BaseElementDefinitions, BaseElementToolset
from PyQt6.QtCore import (
    QCoreApplication,
    QDateTime,
    QLocale,
    QMetaObject,
    QSize,
    Qt,
)
from PyQt6.QtGui import QAction, QActionGroup, QKeySequence
from PyQt6.QtWidgets import (
    QAbstractSpinBox,
    QButtonGroup,
    QDateTimeEdit,
    QDockWidget,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMenuBar,
    QProgressBar,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QStyle,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from styling.utils import SvgIcon
from tcha.consts import CanvasTool, CellAction
from tcha.error import StandardLogger
from tcha.settings import Locale, Settings, TimeFormat
from tcha.table import PresenterCanvas, Table
from tcha.utils import debug_enabled
from ui.commons import MultiLabelAction, NoteEdit, SearchableComboBox, SwitchAction


class Ui_Editor(object):
    def setupUi(self, MainWindow: QMainWindow):
        MainWindow.setObjectName("EditorView")
        MainWindow.resize(Settings.value("Application/editor.window_size"))
        MainWindow.setDocumentMode(True)
        MainWindow.setDockOptions(
            QMainWindow.DockOption.AllowTabbedDocks
            | QMainWindow.DockOption.AnimatedDocks
            | QMainWindow.DockOption.ForceTabbedDocks
            | QMainWindow.DockOption.VerticalTabs
        )
        # MainWindow.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.centralwidget = QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.vl2 = QVBoxLayout(self.centralwidget)
        self.vl2.setObjectName("vl2")

        self.split_table = QSplitter(Qt.Orientation.Vertical, self.centralwidget)

        self.table = Table(self.centralwidget)
        self.table.setObjectName("Table")
        self.table.sizesSplitted.connect(lambda x: self.split_table.moveSplitter(x, 0))

        self.split_table.addWidget(self.table.frozen_table)
        self.split_table.addWidget(self.table)

        self.vl2.addWidget(self.split_table)

        MainWindow.setCentralWidget(self.centralwidget)

        qsettings = Settings.qsettings()

        # Menu bar

        self.menubar = QMenuBar(parent=MainWindow)
        self.menubar.setContentsMargins(0, 0, 0, 0)
        self.menubar.setMaximumHeight(28)
        self.menubar.setDefaultUp(False)
        self.menubar.setObjectName("menubar")
        self.menu_file = QMenu(parent=self.menubar)
        self.menu_file.setObjectName("menu_file")
        self.menu_edit = QMenu(parent=self.menubar)
        self.menu_edit.setObjectName("menu_edit")
        self.menu_elements = QMenu(self.menubar)
        self.menu_elements.setObjectName("menu_elements")
        self.menu_elements.setEnabled(False)
        self.menu_view = QMenu(parent=self.menubar)
        self.menu_view.setObjectName("menu_view")
        self.menu_opt = QMenu(parent=self.menubar)
        self.menu_opt.setObjectName("menu_opt")
        self.menu_debug = QMenu(parent=self.menubar)
        self.menu_debug.setObjectName("menu_debug")

        if debug_enabled():
            self.menu_debug.setVisible(False)

        self.menuHelp = QMenu(parent=self.menubar)
        self.menuHelp.setObjectName("menuHelp")

        # Corner Widget at right side of menu bar

        self.corner_widget = QWidget(MainWindow)
        self.corner_widget.setMaximumHeight(25)
        cw_layout = QHBoxLayout(self.corner_widget)
        cw_layout.setContentsMargins(0, 0, 0, 0)
        cw_layout.setSpacing(0)
        self.corner_widget.setLayout(cw_layout)

        self.tb_open = QToolButton(MainWindow)
        icon10 = MainWindow.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        self.tb_open.setIcon(icon10)
        cw_layout.addWidget(self.tb_open)

        self.tb_save = QToolButton(MainWindow)
        icon9 = MainWindow.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton)
        self.tb_save.setIcon(icon9)
        cw_layout.addWidget(self.tb_save)

        self.menubar.setCornerWidget(self.corner_widget, Qt.Corner.TopLeftCorner)
        MainWindow.setMenuBar(self.menubar)

        self.statusbar = QStatusBar(parent=MainWindow)
        self.statusbar.setObjectName("statusbar")
        self.statusbar.setMaximumHeight(25)

        self.lb_counts = self.table.count_label
        self.statusbar.addWidget(self.lb_counts)

        line1 = QFrame(parent=MainWindow)
        line1.setFrameShape(QFrame.Shape.VLine)
        line1.setFrameShadow(QFrame.Shadow.Plain)
        line1.setObjectName("line1")
        self.statusbar.addWidget(line1)

        self.lb_row = QLabel(parent=MainWindow)
        self.lb_row.setObjectName("lb_row")
        self.statusbar.addWidget(self.lb_row)

        self.row_list = self.table.row_list
        self.row_list.setStyleSheet(
            """QComboBox {
                padding: 0 0 0 2px; 
                min-height: 1.1em; 
                border: 1px;
                border-radius: 4px;
                }
                
                QComboBox::down-arrow {image: none}"""
        )
        self.row_list.setMaximumWidth(35)
        self.row_list.view().setFixedWidth(50)
        self.statusbar.addWidget(self.row_list)

        icon20 = SvgIcon(":/common/arrow_down_small")
        self.ac_row_down = MainWindow.addAction(None)
        self.ac_row_down.setIcon(icon20)
        self.ac_row_down.setShortcut(QKeySequence(Qt.Key.Key_Control, Qt.Key.Key_Down))
        self.ac_row_down.setShortcutContext(Qt.ShortcutContext.WindowShortcut)

        self.tb_row_down = QToolButton(self.statusbar)
        self.tb_row_down.setDefaultAction(self.ac_row_down)
        self.tb_row_down.setObjectName("tb_row_down")
        self.statusbar.addWidget(self.tb_row_down)

        icon21 = SvgIcon(":/common/up")
        self.ac_row_up = MainWindow.addAction(None)
        self.ac_row_up.setIcon(icon21)
        self.ac_row_up.setShortcut(QKeySequence(Qt.Key.Key_Control, Qt.Key.Key_Up))
        self.ac_row_up.setShortcutContext(Qt.ShortcutContext.WindowShortcut)

        self.tb_row_up = QToolButton(self.statusbar)
        self.tb_row_up.setObjectName("tb_row_up")
        self.tb_row_up.setDefaultAction(self.ac_row_up)
        self.statusbar.addWidget(self.tb_row_up)

        self.loading_bar = QProgressBar(MainWindow)
        self.loading_bar.setMaximum(100)
        self.loading_bar.setFixedWidth(80)
        self.loading_bar.setVisible(False)
        self.statusbar.addPermanentWidget(self.loading_bar)

        MainWindow.setStatusBar(self.statusbar)

        # Dock Widgets: PresenterCanvas and Notes

        self.dw_presenter = QDockWidget(parent=MainWindow)
        self.dw_presenter.setEnabled(False)
        self.dw_presenter.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.dw_presenter.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea
            | Qt.DockWidgetArea.RightDockWidgetArea
            | Qt.DockWidgetArea.BottomDockWidgetArea
        )
        self.dw_presenter.setObjectName("dw_presenter")
        self.dw_presenter.hide()

        self.widget_dw_contents2 = QWidget()
        self.widget_dw_contents2.setObjectName("widget_dw_contents2")

        self.dw_lo2 = QVBoxLayout(self.widget_dw_contents2)
        self.dw_lo2.setObjectName("dw_lo2")

        self.dw_lo3 = QHBoxLayout()
        self.dw_lo3.setObjectName("dw_lo3")

        self.bg_tools = QButtonGroup()

        # self.tb_pointer = QToolButton(self.widget_dw_contents2)
        # self.tb_pointer.setObjectName("tb_pointer")
        # self.tb_pointer.setCheckable(True)
        # self.tb_pointer.setChecked(True)
        # self.tb_pointer.setProperty("tool", CanvasTool.Pointer)
        # icon19 = SvgIcon(":/common/ic_pointer.svg")
        # self.tb_pointer.setIcon(icon19)
        # self.dw_lo3.addWidget(self.tb_pointer)
        # self.bg_tools.addButton(self.tb_pointer)

        self.tb_pen = QToolButton(self.widget_dw_contents2)
        self.tb_pen.setObjectName("tb_pen")
        self.tb_pen.setCheckable(True)
        self.tb_pen.setChecked(True)
        self.tb_pen.setProperty("tool", CanvasTool.Pen)
        icon16 = SvgIcon(":/common/pen")
        self.tb_pen.setIcon(icon16)
        self.dw_lo3.addWidget(self.tb_pen)
        self.bg_tools.addButton(self.tb_pen)

        self.tb_arrow = QToolButton(self.widget_dw_contents2)
        self.tb_arrow.setObjectName("tb_arrow")
        self.tb_arrow.setCheckable(True)
        self.tb_arrow.setProperty("tool", CanvasTool.Arrow)
        icon18 = SvgIcon(":/common/arrow_tool")
        self.tb_arrow.setIcon(icon18)
        self.dw_lo3.addWidget(self.tb_arrow)
        self.bg_tools.addButton(self.tb_arrow)

        self.tb_rubber = QToolButton(self.widget_dw_contents2)
        self.tb_rubber.setObjectName("tb_rubber")
        self.tb_rubber.setCheckable(True)
        self.tb_rubber.setProperty("tool", CanvasTool.Rubber)
        icon17 = SvgIcon(":/common/rubber")
        self.tb_rubber.setIcon(icon17)
        self.dw_lo3.addWidget(self.tb_rubber)
        self.bg_tools.addButton(self.tb_rubber)

        self.dw_lo3.addSpacing(5)

        self.bg_colors = QButtonGroup()

        tb_style = """
        QToolButton {
            min-width: 14px;
            min-height: 14px;
            max-width: 14px;
            max-height: 14px;
            border: 1px solid black;
            border-radius: 7px; 
            padding: 0px; 
            margin: 1px; 
            background-color: [color];
            }

        QToolButton:checked, QToolButton:hover {
            min-width: 16px;
            min-height: 16px;
            max-width: 16px;
            max-height: 16px;
            border: 1px solid black;
            border-radius: 8px;
            padding: 0px;
            margin: 0px;
            }
        """

        self.tb_red = QToolButton(self.widget_dw_contents2)
        self.tb_red.setObjectName("tb_red")
        self.tb_red.setCheckable(True)
        self.tb_red.setChecked(True)
        # self.tb_red.setFixedSize(16, 16)
        style1 = tb_style.replace("[color]", "red")
        self.tb_red.setStyleSheet(style1)
        self.tb_red.setProperty("color", Qt.GlobalColor.red)
        self.dw_lo3.addWidget(self.tb_red)
        self.bg_colors.addButton(self.tb_red)

        self.tb_blue = QToolButton(self.widget_dw_contents2)
        self.tb_blue.setObjectName("tb_blue")
        self.tb_blue.setCheckable(True)
        # self.tb_blue.setFixedSize(16, 16)
        style2 = tb_style.replace("[color]", "blue")
        self.tb_blue.setStyleSheet(style2)
        self.tb_blue.setProperty("color", Qt.GlobalColor.blue)
        self.dw_lo3.addWidget(self.tb_blue)
        self.bg_colors.addButton(self.tb_blue)

        self.tb_yellow = QToolButton(self.widget_dw_contents2)
        self.tb_yellow.setObjectName("tb_yellow")
        self.tb_yellow.setCheckable(True)
        # self.tb_yellow.setFixedSize(16, 16)
        style3 = tb_style.replace("[color]", "yellow")
        self.tb_yellow.setStyleSheet(style3)
        self.tb_yellow.setProperty("color", Qt.GlobalColor.darkYellow)
        self.dw_lo3.addWidget(self.tb_yellow)
        self.bg_colors.addButton(self.tb_yellow)

        spa2 = QSpacerItem(100, 18, QSizePolicy.Policy.Expanding)
        self.dw_lo3.addItem(spa2)

        self.dw_lo2.addLayout(self.dw_lo3)

        self.canvas = PresenterCanvas()
        self.canvas.setObjectName("canvas")
        self.canvas.setCursor(Qt.CursorShape.CrossCursor)

        self.dw_lo2.addWidget(self.canvas)
        self.dw_presenter.setWidget(self.widget_dw_contents2)
        MainWindow.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dw_presenter)

        self.dw_comment = QDockWidget(parent=MainWindow)
        self.dw_comment.setEnabled(True)
        self.dw_comment.setMinimumSize(QSize(100, 155))
        self.dw_comment.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        self.dw_comment.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea
            | Qt.DockWidgetArea.RightDockWidgetArea
            | Qt.DockWidgetArea.TopDockWidgetArea
        )
        self.dw_comment.setObjectName("dw_comment")

        self.widget_dw_contents = QWidget()
        self.widget_dw_contents.setObjectName("widget_dw_contents")

        self.dw_lo1 = QVBoxLayout(self.widget_dw_contents)
        self.dw_lo1.setObjectName("dw_lo1")

        self.dw_lo4 = QHBoxLayout()
        self.dw_lo4.setObjectName("dw_lo4")

        self.tb_link = QToolButton(self.widget_dw_contents)
        self.tb_link.setObjectName("tb_link")

        self.te_comment = NoteEdit(parent=self.widget_dw_contents)
        self.te_comment.setMinimumSize(QSize(100, 100))
        self.te_comment.setObjectName("te_comment")

        self.dw_lo1.addWidget(self.te_comment)
        self.dw_comment.setWidget(self.widget_dw_contents)
        MainWindow.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dw_comment)

        # Tool Bars

        self.tb_lesson = QToolBar(parent=MainWindow)
        self.tb_lesson.setEnabled(True)
        self.tb_lesson.setMovable(False)
        self.tb_lesson.setIconSize(QSize(22, 22))
        self.tb_lesson.setObjectName("tb_lesson")
        MainWindow.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.tb_lesson)

        self.tb_table = QToolBar(parent=MainWindow)
        self.tb_table.setAllowedAreas(Qt.ToolBarArea.TopToolBarArea)
        self.tb_table.setIconSize(QSize(22, 22))
        self.tb_table.setFloatable(False)
        self.tb_table.setObjectName("tb_table")
        MainWindow.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.tb_table)
        MainWindow.insertToolBarBreak(self.tb_table)

        self.tb_cell = QToolBar(parent=MainWindow)
        self.tb_cell.setAllowedAreas(
            Qt.ToolBarArea.LeftToolBarArea
            | Qt.ToolBarArea.RightToolBarArea
            | Qt.ToolBarArea.TopToolBarArea
        )
        self.tb_cell.setIconSize(QSize(22, 22))
        self.tb_cell.setFloatable(False)
        self.tb_cell.setObjectName("tb_cell")
        self.tb_cell.hide()
        MainWindow.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.tb_cell)

        # File actions

        self.ac_new_doc = QAction(parent=MainWindow)
        self.ac_new_doc.setObjectName("ac_new_doc")
        self.ac_new_doc.setShortcut(QKeySequence.StandardKey.New)
        self.ac_open_doc = QAction(parent=MainWindow)
        self.ac_open_doc.setObjectName("ac_open_doc")
        self.ac_open_doc.setIcon(icon10)
        self.ac_open_doc.setShortcut(QKeySequence.StandardKey.Open)
        self.ac_recent = QAction(parent=MainWindow)
        self.ac_recent.setObjectName("ac_recent")
        self.ac_scheduledf = QAction(parent=MainWindow)  # Unused
        self.ac_scheduledf.setObjectName("ac_scheduledf")  # Unused
        self.ac_save = QAction(parent=MainWindow)
        self.ac_save.setObjectName("ac_save")
        self.ac_save.setIcon(icon9)
        self.ac_save.setShortcut(QKeySequence.StandardKey.Save)
        self.ac_save_as = QAction(parent=MainWindow)
        self.ac_save_as.setObjectName("ac_save_as")
        self.ac_save_as.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.ac_close = QAction(parent=MainWindow)
        self.ac_close.setObjectName("ac_close")
        self.ac_close.setShortcut(QKeySequence.StandardKey.Close)

        # Course Actions

        self.ac_add_course = QAction(parent=MainWindow)
        icon3 = SvgIcon(":/common/new")
        self.ac_add_course.setIcon(icon3)
        self.ac_add_course.setObjectName("ac_add_course")

        self.ac_course_exp = QAction(parent=MainWindow)
        self.ac_course_exp.setObjectName("ac_course_exp")
        self.ac_course_rec = QAction(parent=MainWindow)
        self.ac_course_rec.setObjectName("ac_course_rec")
        icon11 = SvgIcon(":/common/info")
        self.ac_course_rec.setIcon(icon11)

        icon12 = SvgIcon(":/common/schedule")
        icon13 = SvgIcon(":/common/scheduled")

        self.ac_schedule = SwitchAction(icon12, icon13, MainWindow)
        self.ac_schedule.setObjectName("ac_schedule")

        # View actions

        self.ac_show_notes = QAction(parent=MainWindow)
        self.ac_show_notes.setCheckable(True)
        self.ac_show_notes.setChecked(True)
        self.ac_show_notes.setObjectName("ac_show_notes")
        icon14 = SvgIcon(":/common/notes")
        self.ac_show_notes.setIcon(icon14)

        self.ac_pres_mode = QAction(parent=MainWindow)
        self.ac_pres_mode.setObjectName("ac_pres_mode")
        self.ac_pres_mode.setCheckable(True)
        self.ac_pres_mode.setChecked(False)
        self.ac_pres_mode.setShortcut(Qt.Key.Key_F11)
        icon15 = SvgIcon(":/common/presenter_mode")
        self.ac_pres_mode.setIcon(icon15)

        self.ac_show_ttbar = QAction(parent=MainWindow)
        self.ac_show_ttbar.setCheckable(True)
        self.ac_show_ttbar.setObjectName("ac_show_ttbar")

        self.view_mode_group = QActionGroup(MainWindow)
        self.view_mode_group.setObjectName("view_mode_group")

        self.ac_vmode_table = QAction(parent=MainWindow)
        self.ac_vmode_table.setCheckable(True)
        self.ac_vmode_table.setChecked(True)
        self.ac_vmode_table.setObjectName("ac_vmode_table")
        icon22 = SvgIcon(":/common/table")
        self.ac_vmode_table.setIcon(icon22)
        self.ac_vmode_table.setIconVisibleInMenu(False)

        self.ac_vmode_row = QAction(parent=MainWindow)
        self.ac_vmode_row.setCheckable(True)
        self.ac_vmode_row.setObjectName("ac_vmode_row")
        icon23 = SvgIcon(":/common/row_view")
        self.ac_vmode_row.setIcon(icon23)
        self.ac_vmode_row.setIconVisibleInMenu(False)

        self.view_mode_group.addAction(self.ac_vmode_table)
        self.view_mode_group.addAction(self.ac_vmode_row)

        self.ac_goto_active = QAction(parent=MainWindow)
        self.ac_goto_active.setObjectName("ac_goto_active")
        self.ac_goto_active.setDisabled(True)

        self.ac_freeze_row = MultiLabelAction(parent=MainWindow)
        self.ac_freeze_row.setObjectName("ac_freeze_row")
        self.ac_freeze_row.setDisabled(True)

        # Debugging actions

        self.ac_file_insp = QAction(parent=MainWindow)
        self.ac_file_insp.setObjectName("ac_file_insp")
        self.ac_res_view = QAction(parent=MainWindow)
        self.ac_res_view.setObjectName("ac_res_view")
        self.ac_table_insp = QAction(parent=MainWindow)
        self.ac_table_insp.setObjectName("ac_table_insp")
        self.ac_xml_insp = QAction(parent=MainWindow)
        self.ac_xml_insp.setObjectName("ac_xml_insp")
        self.ac_xml_insp.setDisabled(True)

        # Table Actions
        self.ac_copy = QAction(parent=MainWindow)
        self.ac_copy.setObjectName("ac_copy")
        self.ac_copy.setDisabled(True)
        self.ac_copy.setShortcut(QKeySequence.StandardKey.Copy)
        self.ac_copy.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
        icon27 = SvgIcon(":/common/copy")
        self.ac_copy.setIcon(icon27)

        self.ac_paste = QAction(parent=MainWindow)
        self.ac_paste.setObjectName("ac_paste")
        self.ac_paste.setDisabled(True)
        self.ac_paste.setShortcut(QKeySequence.StandardKey.Paste)
        self.ac_paste.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
        icon28 = SvgIcon(":/common/paste")
        self.ac_paste.setIcon(icon28)

        self.ac_append_row = QAction(parent=MainWindow)
        self.ac_append_row.setObjectName("ac_append_row")
        self.ac_append_row.setShortcut("Ctrl+R")
        self.ac_append_row.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
        icon29 = SvgIcon(":/common/append_row")
        self.ac_append_row.setIcon(icon29)

        self.ac_append_column = QAction(parent=MainWindow)
        self.ac_append_column.setObjectName("ac_append_column")
        self.ac_append_column.setShortcut("Ctrl+T")
        self.ac_append_column.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
        icon30 = SvgIcon(":/common/append_column")
        self.ac_append_column.setIcon(icon30)

        self.table_group = QActionGroup(MainWindow)

        self.ac_add_to_cell = QAction(parent=MainWindow)
        icon = SvgIcon(":/common/add_block")
        self.ac_add_to_cell.setIcon(icon)
        self.ac_add_to_cell.setObjectName("ac_add_to_cell")
        self.table_group.addAction(self.ac_add_to_cell)

        self.elem_menu = QMenu()

        self.ac_from_clipboard = QAction(parent=MainWindow)
        self.ac_from_clipboard.setObjectName("ac_from_clipboard")
        self.ac_from_clipboard.setData(None)
        self.elem_menu.addAction(self.ac_from_clipboard)

        self.ac_add_to_cell.setMenu(self.elem_menu)

        self.ac_cell_finish_editing = QAction(parent=MainWindow)
        icon24 = MainWindow.style().standardIcon(QStyle.StandardPixmap.SP_DialogOkButton)
        self.ac_cell_finish_editing.setIcon(icon24)
        self.ac_cell_finish_editing.setObjectName("ac_cell_finish_editing")
        self.table_group.addAction(self.ac_cell_finish_editing)

        self.ac_add_row = QAction(parent=MainWindow)
        icon1 = SvgIcon(":/common/add_row")
        self.ac_add_row.setIcon(icon1)
        self.ac_add_row.setObjectName("ac_add_row")
        self.table_group.addAction(self.ac_add_row)

        self.ac_add_column = QAction(parent=MainWindow)
        icon2 = SvgIcon(":/common/add_column")
        self.ac_add_column.setObjectName("ac_add_column")
        self.ac_add_column.setIcon(icon2)
        self.table_group.addAction(self.ac_add_column)

        self.ac_rmv_row = QAction(parent=MainWindow)
        icon4 = SvgIcon(":/common/remove_row")
        self.ac_rmv_row.setIcon(icon4)
        self.ac_rmv_row.setObjectName("ac_rmv_row")
        self.table_group.addAction(self.ac_rmv_row)

        self.ac_rmv_column = QAction(parent=MainWindow)
        icon5 = SvgIcon(":/common/remove_column")
        self.ac_rmv_column.setIcon(icon5)
        self.ac_rmv_column.setObjectName("ac_rmv_column")
        self.table_group.addAction(self.ac_rmv_column)

        self.table_group.setDisabled(True)

        self.cell_group = QActionGroup(MainWindow)

        self.ac_elem_finish_editing = QAction(parent=MainWindow)
        self.ac_elem_finish_editing.setObjectName("elem_finish_editing")
        self.ac_elem_finish_editing.setIcon(icon24)
        # self.ac_elem_finish_editing.setShortcuts(
        #     [QKeySequence("Return"), QKeySequence("Ctrl+Return")]
        # )
        self.ac_elem_finish_editing.setData(CellAction.Accept)
        self.cell_group.addAction(self.ac_elem_finish_editing)

        self.ac_elem_discard_changes = QAction(parent=MainWindow)
        self.ac_elem_discard_changes.setObjectName("elem_discard_changes")
        icon25 = MainWindow.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton)
        self.ac_elem_discard_changes.setIcon(icon25)
        self.ac_elem_discard_changes.setShortcut(QKeySequence(Qt.Key.Key_Escape))
        self.ac_elem_discard_changes.setData(CellAction.Discard)
        self.cell_group.addAction(self.ac_elem_discard_changes)

        self.ac_mov_up = QAction(parent=MainWindow)
        icon6 = SvgIcon(":/common/move_up")
        self.ac_mov_up.setIcon(icon6)
        self.ac_mov_up.setObjectName("ac_mov_up")
        self.ac_mov_up.setData(CellAction.MoveUp)
        self.cell_group.addAction(self.ac_mov_up)

        self.ac_mov_dwn = QAction(parent=MainWindow)
        icon7 = SvgIcon(":/common/move_down")
        self.ac_mov_dwn.setIcon(icon7)
        self.ac_mov_dwn.setObjectName("ac_mov_dwn")
        self.ac_mov_dwn.setData(CellAction.MoveDown)
        self.cell_group.addAction(self.ac_mov_dwn)

        self.ac_del_element = QAction(parent=MainWindow)
        icon8 = MainWindow.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon)
        self.ac_del_element.setIcon(icon8)
        self.ac_del_element.setObjectName("ac_del_element")
        self.ac_del_element.setData(CellAction.RemoveElement)
        self.cell_group.addAction(self.ac_del_element)

        self.ac_clear_cell = QAction(parent=MainWindow)
        self.ac_clear_cell.setObjectName("ac_clear_cell")
        icon26 = SvgIcon(":/common/clear")
        self.ac_clear_cell.setIcon(icon26)
        self.ac_clear_cell.setData(CellAction.Clear)
        self.ac_clear_cell.setEnabled(False)
        self.cell_group.addAction(self.ac_clear_cell)

        # Other Actions

        self.ac_settings = QAction(parent=MainWindow)
        self.ac_settings.setObjectName("ac_settings")

        self.ac_about = QAction(parent=MainWindow)
        self.ac_about.setObjectName("ac_about")
        icon19 = SvgIcon(":/common/about")
        self.ac_about.setIcon(icon19)

        # Menu Definitions

        self.menu_file.addAction(self.ac_new_doc)
        self.menu_file.addAction(self.ac_open_doc)
        # self.menu_file.addAction(self.ac_recent)
        self.sep1 = self.menu_file.addSeparator()
        self.menu_file.addAction(self.ac_save)
        self.menu_file.addAction(self.ac_save_as)
        self.menu_file.addAction(self.ac_schedule)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.ac_close)
        self.menu_file.addSeparator()

        # self.menu_edit.addAction(self.ac_new_table)
        self.menu_edit.addAction(self.ac_append_row)
        self.menu_edit.addAction(self.ac_append_column)
        self.menu_edit.addSeparator()
        self.menu_edit.addMenu(self.menu_elements)
        self.menu_edit.addAction(self.ac_copy)
        self.menu_edit.addAction(self.ac_paste)
        self.menu_edit.addSeparator()
        self.menu_edit.addAction(self.ac_add_row)
        self.menu_edit.addAction(self.ac_add_column)
        self.menu_edit.addAction(self.ac_rmv_row)
        self.menu_edit.addAction(self.ac_rmv_column)
        self.menu_edit.addSeparator()
        self.menu_edit.addAction(self.ac_clear_cell)

        self.menu_elements.addAction(self.ac_from_clipboard)

        self.menu_view.addAction(self.ac_pres_mode)
        self.menu_view.addSeparator()
        self.menu_view.addAction(self.ac_show_notes)
        self.menu_view.addSeparator()
        self.menu_view.addAction(self.ac_vmode_table)
        self.menu_view.addAction(self.ac_vmode_row)
        self.menu_view.addSeparator()
        self.menu_view.addAction(self.ac_goto_active)
        self.menu_view.addAction(self.ac_freeze_row)
        # self.menu_view.addAction(self.ac_show_ttbar)

        self.menu_opt.addAction(self.ac_settings)
        self.menu_opt.addSeparator()
        self.menu_opt.addAction(self.ac_course_exp)
        self.menu_opt.addAction(self.ac_course_rec)
        self.menu_opt.addAction(self.ac_add_course)

        self.menu_debug.addAction(self.ac_file_insp)
        self.menu_debug.addAction(self.ac_res_view)
        self.menu_debug.addAction(self.ac_table_insp)
        self.menu_debug.addAction(self.ac_xml_insp)

        self.menuHelp.addAction(self.ac_about)

        self.menubar.addAction(self.menu_file.menuAction())
        self.menubar.addAction(self.menu_edit.menuAction())
        self.menubar.addAction(self.menu_view.menuAction())
        self.menubar.addAction(self.menu_opt.menuAction())
        self.menubar.addAction(self.menu_debug.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

        # Construct Lesson Toolbar

        self.lb_course = QLabel("", MainWindow)
        self.tb_lesson.addWidget(self.lb_course)

        self.cb_course = SearchableComboBox(MainWindow)
        self.cb_course.setMinimumWidth(180)
        self.cb_course.setModelColumn(1)
        self.cb_course.lineEdit().setClearButtonEnabled(True)
        self.tb_lesson.addWidget(self.cb_course)

        self.tb_lesson.addAction(self.ac_add_course)
        self.tb_lesson.addAction(self.ac_course_rec)
        self.tb_lesson.addSeparator()

        self.lb_date_time = QLabel("", MainWindow)
        self.tb_lesson.addWidget(self.lb_date_time)

        qsettings = Settings.qsettings()
        self.dt_DateTime = QDateTimeEdit(MainWindow)
        locale = Locale[qsettings.value("User/language", type=str)].value
        tformat = TimeFormat[qsettings.value("User/time_format", type=str)].value
        qlocale = QLocale(locale.language, locale.region)
        self.dt_DateTime.setLocale(qlocale)
        self.dt_DateTime.setDisplayFormat(
            f"{qlocale.dateFormat(QLocale.FormatType.ShortFormat)} {tformat}"
        )
        self.dt_DateTime.setMinimumWidth(155)
        self.dt_DateTime.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.dt_DateTime.setProperty("showGroupSeparator", False)
        self.dt_DateTime.setCalendarPopup(True)
        self.dt_DateTime.setObjectName("DT_DateTime")
        self.dt_DateTime.setDateTime(QDateTime.currentDateTime())
        self.tb_lesson.addWidget(self.dt_DateTime)

        self.tb_lesson.addAction(self.ac_schedule)

        self.tb_lesson.addSeparator()

        self.lb_duration = QLabel("", MainWindow)
        self.tb_lesson.addWidget(self.lb_duration)

        self.sb_duration = QSpinBox(MainWindow)
        self.sb_duration.setObjectName("sb_duration")
        self.sb_duration.setMaximum(255)
        self.tb_lesson.addWidget(self.sb_duration)

        spa = QWidget(self.tb_lesson)
        spa.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.tb_lesson.addWidget(spa)

        self.tb_lesson.addAction(self.ac_pres_mode)
        self.tb_lesson.addAction(self.ac_show_notes)

        # Construct Table Tool Bar

        self.tb_table.addAction(self.ac_cell_finish_editing)
        self.tb_table.addSeparator()
        self.tb_table.addAction(self.ac_add_to_cell)
        widget: QToolButton = self.tb_table.widgetForAction(self.ac_add_to_cell)
        widget.setMenu(self.menu_elements)
        widget.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.tb_table.addAction(self.ac_add_row)
        self.tb_table.addAction(self.ac_add_column)
        self.tb_table.addSeparator()
        self.tb_table.addAction(self.ac_rmv_row)
        self.tb_table.addAction(self.ac_rmv_column)
        self.tb_table.addSeparator()
        self.tb_table.addAction(self.ac_clear_cell)

        self.tb_cell.addAction(self.ac_elem_finish_editing)
        self.tb_cell.addAction(self.ac_elem_discard_changes)
        self.tb_cell.addSeparator()
        self.tb_cell.addAction(self.ac_mov_up)
        self.tb_cell.addAction(self.ac_mov_dwn)
        self.tb_cell.addAction(self.ac_del_element)
        self.tb_cell.hide()

        self.retranslateUi(MainWindow)
        self.ac_show_notes.toggled["bool"].connect(self.dw_comment.setVisible)  # type: ignore
        self.dw_presenter.visibilityChanged["bool"].connect(self.ac_pres_mode.setChecked)
        self.dw_comment.visibilityChanged["bool"].connect(self.ac_show_notes.setChecked)  # type: ignore
        QMetaObject.connectSlotsByName(MainWindow)

        self.tb_view_mode_group = QButtonGroup()
        self.tb_view_mode_group.setObjectName("tb_view_mode_group")

        self.tb_vmode_table = QToolButton(self.statusbar)
        self.tb_vmode_table.setObjectName("tb_vmode_table")
        self.tb_vmode_table.setDefaultAction(self.ac_vmode_table)
        self.tb_vmode_table.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.statusbar.addPermanentWidget(self.tb_vmode_table)

        self.tb_vmode_row = QToolButton(self.statusbar)
        self.tb_vmode_row.setObjectName("tb_vmode_row")
        self.tb_vmode_row.setDefaultAction(self.ac_vmode_row)
        self.tb_vmode_row.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.statusbar.addPermanentWidget(self.tb_vmode_row)

    def retranslateUi(self, MainWindow: QMainWindow):
        _translate = QCoreApplication.translate
        MainWindow.setWindowTitle(MainWindow.tr("MainWindow"))
        self.menu_file.setTitle(MainWindow.tr("File"))
        self.menu_edit.setTitle(MainWindow.tr("Edit"))
        self.menu_elements.setTitle(MainWindow.tr("Add To Cell"))
        self.menu_view.setTitle(MainWindow.tr("View"))
        self.menu_opt.setTitle(MainWindow.tr("Options"))
        self.menu_debug.setTitle(MainWindow.tr("Debugging"))
        self.menuHelp.setTitle(MainWindow.tr("Help"))
        self.dw_presenter.setWindowTitle(MainWindow.tr("Presentation View"))
        self.dw_comment.setWindowTitle(MainWindow.tr("Notes"))
        self.tb_lesson.setWindowTitle(MainWindow.tr("Lesson Details"))
        self.tb_table.setWindowTitle(MainWindow.tr("Table Tools"))
        self.tb_cell.setWindowTitle(MainWindow.tr("Cell Tools"))
        self.ac_cell_finish_editing.setToolTip(MainWindow.tr("Finish editing cell"))
        self.ac_append_row.setText(MainWindow.tr("Append row"))
        self.ac_append_row.setToolTip(MainWindow.tr("Inserts a row after the last one"))
        self.ac_append_column.setText(MainWindow.tr("Append column"))
        self.ac_append_column.setToolTip(MainWindow.tr("Inserts column after the last one"))
        self.ac_add_to_cell.setText(MainWindow.tr("Add to Cell"))
        self.ac_from_clipboard.setText(MainWindow.tr("From Clipboard"))
        self.ac_add_row.setText(MainWindow.tr("Insert Row"))
        self.ac_add_column.setText(MainWindow.tr("Insert Column"))
        self.ac_new_doc.setText(MainWindow.tr("New"))
        self.ac_open_doc.setText(MainWindow.tr("Open"))
        self.ac_recent.setText(MainWindow.tr("Recent Files"))
        self.ac_save.setText(MainWindow.tr("Save"))
        self.ac_save_as.setText(MainWindow.tr("Save as"))
        self.ac_close.setText(MainWindow.tr("Close"))

        self.ac_pres_mode.setText(MainWindow.tr("Presentation Mode"))
        self.ac_vmode_table.setText(MainWindow.tr("Show entire table"))
        self.ac_vmode_row.setText(MainWindow.tr("Show single row"))
        self.ac_goto_active.setText(MainWindow.tr("Go to selected cell"))
        transl1 = _translate(
            "MainWindow",
            "Freeze row",
        )
        self.ac_freeze_row.define_text(
            "freeze",
            transl1,
        )
        transl2 = _translate(
            "MainWindow",
            "Unfreeze row",
        )
        self.ac_freeze_row.define_text(
            "unfreeze",
            transl2,
        )
        self.ac_freeze_row.set_text("freeze")
        self.ac_settings.setText(MainWindow.tr("Settings"))
        self.ac_course_exp.setText(MainWindow.tr("Course Explorer"))
        self.ac_course_rec.setText(MainWindow.tr("View Course Record"))
        self.ac_file_insp.setText(MainWindow.tr("File Inspector"))
        self.ac_about.setText(MainWindow.tr("About Teachart"))
        self.ac_res_view.setText(MainWindow.tr("Resource View"))
        self.ac_table_insp.setText(MainWindow.tr("Table Inspector"))
        self.ac_xml_insp.setText(MainWindow.tr("XML Inspector"))
        self.ac_schedule.setText(MainWindow.tr("Schedule"))
        self.ac_copy.setText(MainWindow.tr("Copy "))
        self.ac_paste.setText(MainWindow.tr("Paste"))
        self.ac_show_notes.setText(MainWindow.tr("Show Notes"))
        self.ac_show_ttbar.setText(MainWindow.tr("Show Table Tool Bar"))
        self.ac_add_course.setText(MainWindow.tr("New Course"))
        self.ac_rmv_row.setText(MainWindow.tr("Remove Row"))
        self.ac_rmv_column.setText(MainWindow.tr("Remove Column"))
        self.ac_scheduledf.setText(MainWindow.tr("Today's Scheduled Files"))
        self.ac_elem_finish_editing.setToolTip(MainWindow.tr("Finish editing and save changes"))
        self.ac_elem_discard_changes.setToolTip(MainWindow.tr("Discard changes"))
        self.ac_mov_up.setText(MainWindow.tr("Move Up"))
        self.ac_mov_dwn.setText(MainWindow.tr("Move Down"))
        self.ac_mov_dwn.setToolTip(MainWindow.tr("Move Down"))
        self.ac_del_element.setText(MainWindow.tr("Delete Element"))
        self.ac_clear_cell.setText(MainWindow.tr("Clear Cell"))

        self.tb_arrow.setToolTip(
            _translate(
                "MainWindow",
                "Draw Arrow - Drag the cursor while holding the mouse button and release for the arrow tip",
            )
        )
        self.tb_rubber.setToolTip(MainWindow.tr("Rubber"))
        self.tb_pen.setToolTip(MainWindow.tr("Pen"))
        self.tb_red.setToolTip(MainWindow.tr("Red"))
        self.tb_blue.setToolTip(MainWindow.tr("Blue"))
        self.tb_yellow.setToolTip(MainWindow.tr("Dark yellow"))

        self.lb_course.setText(MainWindow.tr("Course"))
        self.lb_date_time.setText(MainWindow.tr("Date/Time"))
        self.lb_duration.setText(MainWindow.tr("Duration"))
        self.lb_row.setText(MainWindow.tr("Top row"))
        self.lb_counts.setToolTip(MainWindow.tr("Number of rows | Number of columns"))

        self.sb_duration.setSuffix(MainWindow.tr(" min"))

    def add_element_actions(self, edefinitions: dict[str, BaseElementDefinitions]) -> None:
        StandardLogger.debug(f"Available menu actions {edefinitions.keys()}")
        for key in edefinitions:  # noqa: PLC0206
            action = edefinitions[key].action(self.menu_elements)
            self.menu_elements.addAction(action)

    def add_toolsets(
        self, window: QMainWindow, edefinitions: dict[str, BaseElementDefinitions]
    ) -> dict[str, BaseElementToolset]:
        d = {}
        for key in edefinitions:  # noqa: PLC0206
            toolset = edefinitions[key].toolset(window)
            window.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolset)
            toolset.setVisible(False)
            toolset.visibilityChanged.connect(self.on_element_toolbar_visibilty_changed)
            d[key] = toolset
        self.table.set_toolset_reference(d)
        return d

    def on_element_toolbar_visibilty_changed(self, open: bool) -> None:
        self.tb_cell.setVisible(open)
        self.tb_table.setVisible(not open)
