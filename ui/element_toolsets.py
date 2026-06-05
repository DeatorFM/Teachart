from typing import Any

from PyQt6.QtCore import (
    QAbstractListModel,
    QCoreApplication,
    QEvent,
    QLocale,
    QModelIndex,
    QRegularExpression,
    Qt,
    pyqtSignal,
    pyqtSlot,
)
from PyQt6.QtGui import (
    QActionGroup,
    QColor,
    QEnterEvent,
    QKeySequence,
    QMouseEvent,
    QRegularExpressionValidator,
)
from PyQt6.QtWidgets import (
    QComboBox,
    QFontComboBox,
    QFrame,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QSlider,
    QSpinBox,
    QStyle,
    QStyledItemDelegate,
    QTimeEdit,
    QToolBar,
    QToolButton,
    QWidget,
    QWidgetAction,
)

from tcha.settings import Settings
from tcha.styling import SvgIcon
from tcha.utils import evened
from ui.commons import ColorMenu, LabeledWidget, SplitButton, SwitchAction
from ui.StyledWidget import convertColors


class TextToolsetView:
    def setUI(self, agent: QToolBar) -> None:
        agent.setObjectName("TextToolset")

        self.cb_Font = QFontComboBox(agent)
        self.cb_Font.setMaximumHeight(28)
        self.cb_Font.setObjectName("CB_Font")

        agent.addWidget(self.cb_Font)

        self.cb_FontSize = FontSizeBox(agent)
        self.cb_FontSize.setMinimumWidth(65)
        self.cb_FontSize.setMaximumHeight(28)
        self.cb_FontSize.setObjectName("CB_FontSize")
        self.cb_FontSize.setContentsMargins(5, 0, 5, 0)
        agent.addWidget(self.cb_FontSize)

        agent.addSeparator()

        icon1 = SvgIcon("resources/icons/ic_bold.svg")
        self.ac_bold = agent.addAction(icon1, None)
        self.ac_bold.setCheckable(True)
        self.ac_bold.setShortcut(QKeySequence.StandardKey.Bold)

        icon2 = SvgIcon("resources/icons/ic_italic.svg")
        self.ac_italic = agent.addAction(icon2, None)
        self.ac_italic.setCheckable(True)
        self.ac_italic.setShortcut(QKeySequence.StandardKey.Italic)

        icon3 = SvgIcon("resources/icons/ic_underline.svg")
        self.ac_underline = agent.addAction(icon3, None)
        self.ac_underline.setCheckable(True)
        self.ac_underline.setShortcut(QKeySequence.StandardKey.Underline)

        icon4 = SvgIcon("resources/icons/ic_textColor.svg")
        self.ac_textcolor = agent.addAction(icon4, None)
        self.ac_textcolor.setObjectName("TextColor")
        self.ac_textcolor.setProperty("color", QColor())

        textcolors = [
            "#000000",
            "#434343",
            "#666666",
            "#999999",
            "#b7b7b7",
            "#cccccc",
            "#d9d9d9",
            "#efefef",
            "#f3f3f3",
            "#ffffff",
            "#980000",
            "#ff0000",
            "#ff9900",
            "#ffff00",
            "#00ff00",
            "#00ffff",
            "#4a86e8",
            "#0000ff",
            "#9900ff",
            "#ff00ff",
            "#e6b8af",
            "#f4cccc",
            "#fce5cd",
            "#fff2cc",
            "#d9ead3",
            "#d0e0e3",
            "#c9daf8",
            "#cfe2f3",
            "#d9d2e9",
            "#ead1dc",
            "#dd7e6b",
            "#ea9999",
            "#f9cb9c",
            "#ffe599",
            "#b6d7a8",
            "#a2c4c9",
            "#a4c2f4",
            "#9fc5e8",
            "#b4a7d6",
            "#d5a6bd",
            "#cc4125",
            "#e06666",
            "#f6b26b",
            "#ffd966",
            "#93c47d",
            "#76a5af",
            "#6d9eeb",
            "#6fa8dc",
            "#8e7cc3",
            "#c27ba0",
            "#a61c00",
            "#cc0000",
            "#e69138",
            "#f1c232",
            "#6aa84f",
            "#45818e",
            "#3c78d8",
            "#3d85c6",
            "#674ea7",
            "#a64d79",
            "#85200c",
            "#990000",
            "#b45f06",
            "#bf9000",
            "#38761d",
            "#134f5c",
            "#1155cc",
            "#0b5394",
            "#351c75",
            "#741b47",
            "#5b0f00",
            "#660000",
            "#783f04",
            "#7f6000",
            "#274e13",
            "#0c343d",
            "#1c4587",
            "#073763",
            "#20124d",
            "#4c1130",
        ]
        self.color_menu = ColorMenu(convertColors(textcolors), agent)
        action_widget = agent.widgetForAction(self.ac_textcolor)
        action_widget.setMenu(self.color_menu)
        action_widget.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)

        agent.addSeparator()

        self.veralign_group = QActionGroup(agent)
        self.veralign_group.setExclusive(False)

        icon7 = SvgIcon("resources/icons/ic_subscript.svg")
        self.ac_subscript = agent.addAction(icon7, None)
        self.ac_subscript.setCheckable(True)
        self.veralign_group.addAction(self.ac_subscript)

        icon8 = SvgIcon("resources/icons/ic_superscript.svg")
        self.ac_superscript = agent.addAction(icon8, None)
        self.ac_superscript.setCheckable(True)
        self.veralign_group.addAction(self.ac_superscript)

        agent.addSeparator()

        self.align_group = QActionGroup(agent)
        self.align_group.setExclusive(True)

        icon9 = SvgIcon("resources/icons/ic_alignleft.svg")
        self.ac_align_left = agent.addAction(icon9, None)
        self.ac_align_left.setCheckable(True)
        self.ac_align_left.setChecked(True)
        self.align_group.addAction(self.ac_align_left)

        icon10 = SvgIcon("resources/icons/ic_aligncenter.svg")
        self.ac_align_center = agent.addAction(icon10, None)
        self.ac_align_center.setCheckable(True)
        self.align_group.addAction(self.ac_align_center)

        icon11 = SvgIcon("resources/icons/ic_alignright.svg")
        self.ac_align_right = agent.addAction(icon11, None)
        self.ac_align_right.setCheckable(True)
        self.align_group.addAction(self.ac_align_right)

        icon12 = SvgIcon("resources/icons/ic_alignjustify.svg")
        self.ac_align_justify = agent.addAction(icon12, None)
        self.ac_align_justify.setCheckable(True)
        self.align_group.addAction(self.ac_align_justify)

        agent.addSeparator()

        icon13 = SvgIcon("resources/icons/ic_list.svg")
        self.ac_list = agent.addAction(icon13, None)

        icon14 = SvgIcon("resources/icons/ic_numlist.svg")
        self.ac_numlist = agent.addAction(icon14, None)

        icon15 = SvgIcon("resources/icons/ic_dedent.svg")
        self.ac_dedent = agent.addAction(icon15, None)

        icon16 = SvgIcon("resources/icons/ic_indent.svg")
        self.ac_indent = agent.addAction(icon16, None)

        agent.addSeparator()

        icon17 = SvgIcon("resources/icons/ic_table.svg")
        self.ac_table = agent.addAction(icon17, None)
        self.menu_table = TableMenu(agent)
        agent.widgetForAction(self.ac_table).setMenu(self.menu_table)
        agent.widgetForAction(self.ac_table).setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup
        )

        icon18 = SvgIcon("resources/icons/ic_symbol.svg")
        self.ac_symbol = agent.addAction(icon18, None)

        icon19 = SvgIcon("resources/icons/ic_hyperlink.svg")
        self.ac_hyperlink = agent.addAction(icon19, None)

        self.tabletools_group = QActionGroup(agent)

        seperator1 = agent.addSeparator()
        self.tabletools_group.addAction(seperator1)

        icon20 = SvgIcon("resources/icons/ic_insertRowBottom.svg")
        self.ac_row_bottom = agent.addAction(icon20, None)
        self.tabletools_group.addAction(self.ac_row_bottom)

        icon21 = SvgIcon("resources/icons/ic_insertRowTop.svg")
        self.ac_row_top = agent.addAction(icon21, None)
        self.tabletools_group.addAction(self.ac_row_top)

        icon22 = SvgIcon("resources/icons/ic_insertColumnRight.svg")
        self.ac_column_right = agent.addAction(icon22, None)
        self.tabletools_group.addAction(self.ac_column_right)

        icon23 = SvgIcon("resources/icons/ic_insertColumnLeft.svg")
        self.ac_column_left = agent.addAction(icon23, None)
        self.tabletools_group.addAction(self.ac_column_left)

        seperator2 = agent.addSeparator()
        self.tabletools_group.addAction(seperator2)

        icon24 = SvgIcon("resources/icons/ic_deleteRow.svg")
        self.ac_delete_row = agent.addAction(icon24, None)
        self.tabletools_group.addAction(self.ac_delete_row)

        icon25 = SvgIcon("resources/icons/ic_deleteColumn.svg")
        self.ac_delete_column = agent.addAction(icon25, None)
        self.tabletools_group.addAction(self.ac_delete_column)

        icon26 = SvgIcon("resources/icons/ic_deleteTable.svg")
        self.ac_delete_table = agent.addAction(icon26, None)
        self.tabletools_group.addAction(self.ac_delete_table)

        self.tabletools_group.setVisible(False)

        self.retranslateUi()

    def retranslateUi(self) -> None:
        _translate = QCoreApplication.translate
        self.ac_bold.setToolTip(_translate("TextToolset", "Bold"))
        self.ac_italic.setToolTip(_translate("TextToolset", "Italic"))
        self.ac_underline.setToolTip(_translate("TextToolset", "Underline"))
        self.ac_textcolor.setToolTip(_translate("TextToolset", "Choose text colour"))
        self.ac_align_left.setToolTip(_translate("TextToolset", "Align left"))
        self.ac_align_center.setToolTip(_translate("TextToolset", "Centre"))
        self.ac_align_right.setToolTip(_translate("TextToolset", "Align right"))
        self.ac_align_justify.setToolTip(_translate("TextToolset", "Justify"))
        self.ac_subscript.setToolTip(_translate("TextToolset", "Subscript"))
        self.ac_superscript.setToolTip(_translate("TextToolset", "Superscript"))
        self.ac_list.setToolTip(_translate("TextToolset", "Create bulleted list"))
        self.ac_numlist.setToolTip(_translate("TextToolset", "Create a numbered list"))
        self.ac_dedent.setToolTip(_translate("TextToolset", "Decrease indent"))
        self.ac_indent.setToolTip(_translate("TextToolset", "Increase indent"))
        self.ac_table.setToolTip(_translate("TextToolset", "Insert table"))
        self.ac_symbol.setToolTip(_translate("TextToolset", "Insert symbol"))
        self.ac_hyperlink.setToolTip(_translate("TextToolset", "Insert hyperlink"))
        self.ac_row_bottom.setToolTip(_translate("TextToolset", "Insert row below"))
        self.ac_row_top.setToolTip(_translate("TextToolset", "Insert row above"))
        self.ac_column_right.setToolTip(
            _translate("TextToolset", "Insert column right")
        )
        self.ac_column_left.setToolTip(_translate("TextToolset", "Insert column left"))
        self.ac_delete_row.setToolTip(_translate("TextToolset", "Delete selected row"))
        self.ac_delete_column.setToolTip(
            _translate("TextToolset", "Delete selected column")
        )
        self.ac_delete_table.setToolTip(_translate("TextToolset", "Delete Table"))


class PictureToolsetView:
    def setUi(self, agent: QToolBar):
        agent.setObjectName("PictureToolset")

        self.sb_ImageWidth = QSpinBox(agent)
        self.sb_ImageWidth.setMaximum(16000)
        self.sb_ImageWidth.setMaximumHeight(28)
        self.sb_ImageWidth.setObjectName("SB_ImageWidth")
        self.sb_ImageWidth.setMinimumWidth(65)
        self.pair1 = LabeledWidget("", self.sb_ImageWidth)
        agent.addWidget(self.pair1)

        self.sb_ImageHeight = QSpinBox(agent)
        self.sb_ImageHeight.setMaximum(16000)
        self.sb_ImageHeight.setMaximumHeight(28)
        self.sb_ImageHeight.setMinimumWidth(65)
        self.sb_ImageHeight.setObjectName("SB_ImageHeight")
        self.sb_ImageHeight.setSingleStep(1)
        self.pair2 = LabeledWidget("", self.sb_ImageHeight)
        agent.addWidget(self.pair2)

        agent.addSeparator()

        icon1 = SvgIcon("resources/icons/ic_link.svg")
        self.ac_keep_aspect_ratio = agent.addAction(icon1, None)
        self.ac_keep_aspect_ratio.setCheckable(True)
        self.ac_keep_aspect_ratio.setChecked(True)

        icon2 = SvgIcon("resources/icons/ic_rotateRight.svg")
        self.ac_rotate_right = agent.addAction(icon2, None)

        icon3 = SvgIcon("resources/icons/ic_rotateLeft.svg")
        self.ac_rotate_left = agent.addAction(icon3, None)

        agent.addSeparator()

        icon4 = SvgIcon("resources/icons/ic_reset.svg")
        self.ac_reset_image = agent.addAction(icon4, None)

        self.retranslateUi()

    def retranslateUi(self):
        _translate = QCoreApplication.translate
        self.pair1.set_label_text(_translate("PictureToolset", "Width"))
        self.pair2.set_label_text(_translate("PictureToolset", "Height"))
        self.ac_keep_aspect_ratio.setToolTip(
            _translate("PictureToolset", "Keep aspect ratio when changing values")
        )
        self.ac_rotate_right.setToolTip(
            _translate("PictureToolset", "Rotate right 90°")
        )
        self.ac_rotate_left.setToolTip(_translate("PictureToolset", "Rotate left 90°"))
        self.ac_reset_image.setToolTip(
            _translate("PictureToolset", "Restore the picture's original size")
        )


class AudioToolsetView:
    def setUi(self, agent: QToolBar):
        agent.setObjectName("AudioToolset")

        self.icon1 = agent.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
        self.icon2 = agent.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause)
        self.ac_play_pause = SwitchAction(self.icon1, self.icon2, agent)
        agent.addAction(self.ac_play_pause)

        self.hs_PlayTime = QSlider(agent)
        self.hs_PlayTime.setOrientation(Qt.Orientation.Horizontal)
        self.hs_PlayTime.setObjectName("hs_PlayTime")
        self.hs_PlayTime.setMinimumWidth(100)
        self.hs_PlayTime.setMaximumWidth(200)
        agent.addWidget(self.hs_PlayTime)

        self.te_PlayTime = QTimeEdit(agent)
        self.te_PlayTime.setObjectName("sb_PlayTime")
        self.te_PlayTime.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.te_PlayTime.setDisplayFormat("h:mm:ss")
        self.te_PlayTime.setMaximumWidth(60)
        self.te_PlayTime.setMaximumHeight(28)
        agent.addWidget(self.te_PlayTime)

        icon3 = agent.style().standardIcon(QStyle.StandardPixmap.SP_MediaSeekBackward)
        ac_rew = agent.addAction(icon3, "")
        self.tb_rew = agent.widgetForAction(ac_rew)
        # self.pb_rew.setIconSize(QSize(20, 20))
        self.tb_rew.setAutoRepeat(True)

        icon4 = agent.style().standardIcon(QStyle.StandardPixmap.SP_MediaSeekForward)
        ac_fwd = agent.addAction(icon4, "")
        self.tb_fwd = agent.widgetForAction(ac_fwd)
        self.tb_fwd.setAutoRepeat(True)

        agent.addSeparator()

        icon5 = SvgIcon("resources/icons/ic_rew5.svg")
        self.ac_rew5 = agent.addAction(icon5, None)

        icon6 = SvgIcon("resources/icons/ic_fwd5.svg")
        self.ac_fwd5 = agent.addAction(icon6, None)

        agent.addSeparator()

        icon7 = SvgIcon("resources/icons/ic_repeat.svg")
        self.ac_repeat = agent.addAction(icon7, None)
        self.ac_repeat.setCheckable(True)

        self.sb_RepeatTimes = QSpinBox(agent)
        self.sb_RepeatTimes.setObjectName("sb_RepeatTimes")
        self.sb_RepeatTimes.setMinimum(1)
        self.sb_RepeatTimes.setMaximumHeight(28)
        self.sb_RepeatTimes.setDisabled(True)
        agent.addWidget(self.sb_RepeatTimes)

        self.sb_PauseLength = QSpinBox(agent)
        self.sb_PauseLength.setObjectName("sb_PauseLength")
        self.sb_PauseLength.setMinimum(0)
        self.sb_PauseLength.setMaximumHeight(28)
        self.sb_PauseLength.setDisabled(True)
        self.pair3 = LabeledWidget("", self.sb_PauseLength)
        agent.addWidget(self.pair3)

        agent.addSeparator()

        self.te_StartTime = QTimeEdit(agent)
        self.te_StartTime.setObjectName("te_StartTime")
        self.te_StartTime.setDisplayFormat("h:mm:ss")  # ANPASSEN
        self.te_StartTime.setMaximumHeight(28)
        self.pair1 = LabeledWidget("", self.te_StartTime)
        agent.addWidget(self.pair1)

        self.te_EndTime = QTimeEdit(agent)
        self.te_EndTime.setObjectName("te_StartTime")
        self.te_EndTime.setDisplayFormat("h:mm:ss")
        self.te_EndTime.setMaximumHeight(28)
        self.pair2 = LabeledWidget("", self.te_EndTime)
        agent.addWidget(self.pair2)

        self.retranslateUi()

    def retranslateUi(self):
        _translate = QCoreApplication.translate
        self.ac_play_pause.setToolTip(_translate("AudioToolset", "Play/Pause track."))
        self.tb_rew.setToolTip(
            _translate(
                "AudioToolset", "Hold to rewind or double click to reset playback."
            )
        )
        self.ac_rew5.setToolTip(_translate("AudioToolset", "Rewind 5 seconds."))
        self.ac_fwd5.setToolTip(_translate("AudioToolset", "Forward 5 seconds."))
        self.tb_fwd.setToolTip(_translate("AudioToolset", "Hold to move fast forward."))
        self.sb_RepeatTimes.setSuffix(_translate("AudioToolset", " times"))
        self.pair3.set_label_text(_translate("AudioToolset", "Pause Length"))
        self.sb_PauseLength.setSuffix(_translate("AudioToolset", "s"))
        self.sb_PauseLength.setToolTip(
            _translate("AudioToolset", "Sets the pause length between repeats")
        )
        self.pair1.set_label_text(_translate("AudioToolset", "Start"))
        self.pair2.set_label_text(_translate("AudioToolset", "Stop"))


class FontSizeValidator(QRegularExpressionValidator):
    def __init__(self, parent=None):
        super().__init__(
            QRegularExpression(r"^([1-9]\d?([.,]\d+)?|100([.,]0+)?)$"), parent
        )


class FontSizeModel(QAbstractListModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._sizes = (
            8.0,
            9.0,
            10.5,
            11.0,
            12.0,
            14.0,
            16.0,
            18.0,
            20.0,
            22.0,
            24.0,
            26.0,
            28.0,
            36.0,
            48.0,
            72.0,
        )
        self._locale: QLocale = Settings.value("User/language").to_qlocale()
        print("Locale is ", self._locale)

    def rowCount(self, parent=None):
        return len(self._sizes)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            evened_num = evened(self._sizes[index.row()])
            return self._locale.toString(evened_num)
        elif role == Qt.ItemDataRole.UserRole:
            return self._sizes[index.row()]
        else:
            return None


class FontSizeBox(QComboBox):
    sizeChanged = pyqtSignal(float)

    def __init__(self, parent: None) -> None:
        super().__init__(parent)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        model = FontSizeModel(self)
        self.setModel(model)

        self.setEditable(True)
        self.setValidator(FontSizeValidator())

        self.currentIndexChanged.connect(self._on_index_changed)
        self.lineEdit().editingFinished.connect(self.checkEnteredSize)

    def current_font_size(self) -> float:
        if self.currentIndex() > -1:
            return self.currentData()
        text = self.currentText().replace(",", ".")
        return float(text)

    def display_size(self, size: float) -> None:
        evened_num = evened(size)
        self.setEditText(self.locale().toString(evened_num))

    def set_current_font_size(self, size: float) -> None:
        evened_num = evened(size)
        self.setCurrentText(self.locale().toString(evened_num))

    def _on_index_changed(self, index: int) -> None:
        if index > -1:
            print("Emit value of index ", index)
            self.sizeChanged.emit(self.itemData(index))

    def checkEnteredSize(self) -> None:
        fontsize = self.currentText().replace(",", ".")
        print(f"Current font size {fontsize}")
        self.sizeChanged.emit(float(fontsize))


class TableMenu(QMenu):
    tableSize = pyqtSignal(int, int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setUI()

    def setUI(self) -> None:
        self.tableGrid = TableGrid(self)
        self.tableGrid.tableSize.connect(self.emitTableSize)
        self.ac_TableGrid = QWidgetAction(self)
        self.ac_TableGrid.setDefaultWidget(self.tableGrid)
        self.addAction(self.ac_TableGrid)

    @pyqtSlot(int, int)
    def emitTableSize(self, line: int, column: int) -> None:
        print(line, column)
        self.tableSize.emit(line, column)


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
            for icolumn in range(10):
                button = GridButton(self)
                button.line = iline + 1
                button.column = icolumn + 1
                button.entered.connect(self.setMarkedButtons)
                button.sizeSet.connect(self.getTableSize)
                button.left.connect(self.clearMarkings)
                self.button_layout.addWidget(button, iline, icolumn)

        self.lb_TableSize = QLabel("0 x 0")
        self.button_layout.addWidget(self.lb_TableSize, 9, 1, 1, 10)

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
        self.lb_TableSize.setText(f"{column} x {line}")


class GridButton(QFrame):
    entered = pyqtSignal(int, int)
    sizeSet = pyqtSignal(int, int)
    left = pyqtSignal()

    extra_stylesheet = """
    QFrame[hovered=true] {
        background: #4183e3
        }
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(self.extra_stylesheet)
        self.setFrameShape(QFrame.Shape.Box)
        self.setProperty("hovered", False)
        self.setFixedSize(20, 20)
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


class ColorSplitButton(SplitButton):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self._color = QColor("#000000")

    def setColor(self, color: QColor) -> None:
        self._color = color

    def color(self) -> QColor:
        return self._color
