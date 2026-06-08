from enum import Enum

from PyQt6.QtCore import Q, QCoreApplication, QPoint, QRect, QSize, Qt, pyqtSignal
from PyQt6.QtGui import (
    QActionGroup,
    QColor,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QResizeEvent,
)
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFontComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QSizePolicy,
    QSpacerItem,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from tcha.styling import SvgIcon
from ui.commons import SwitchButton
from ui.element_toolsets import ColorMenu, FontSizeBox
from ui.StyledWidget import convertColors


class TextEditorMenuView:
    def setUi(self, agent: QMenu):
        agent.setObjectName("TextEditorMenu")

        self.wac_textTools = QWidgetAction(agent)

        self.tools_widget = QWidget(agent)
        self.text_tools_layout = QVBoxLayout(self.tools_widget)
        self.tools_widget.setLayout(self.text_tools_layout)

        self.wac_textTools.setDefaultWidget(self.tools_widget)

        self.row1 = QHBoxLayout()
        self.row1.setContentsMargins(0, 0, 0, 0)
        self.row1.setObjectName("Row1")

        self.cb_Font = QFontComboBox(self.tools_widget)
        # self.cb_Font.setMaximumSize(QSize(120, 25))
        self.cb_Font.setObjectName("CB_Font")
        self.row1.addWidget(self.cb_Font)

        self.cb_FontSize = FontSizeBox(self.tools_widget)
        self.cb_FontSize.setMinimumSize(QSize(40, 25))
        self.cb_FontSize.setObjectName("CB_FontSize")
        self.cb_FontSize.setContentsMargins(5, 0, 5, 0)
        self.row1.addWidget(self.cb_FontSize)

        self.text_tools_layout.addLayout(self.row1)

        self.row2 = QHBoxLayout()
        self.row2.setContentsMargins(-1, -1, -1, 0)
        self.row2.setSpacing(2)
        self.row2.setObjectName("Row2")

        spa1 = QSpacerItem(
            15, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self.row2.addItem(spa1)

        self.tb_Bold = QToolButton(self.tools_widget)
        self.tb_Bold.setMaximumSize(QSize(22, 22))
        self.tb_Bold.setText("")
        icon2 = SvgIcon("resources/icons/ic_bold.svg")
        self.tb_Bold.setIcon(icon2)
        self.tb_Bold.setIconSize(QSize(20, 20))
        self.tb_Bold.setCheckable(True)
        self.tb_Bold.setObjectName("PB_Bold")
        self.row2.addWidget(self.tb_Bold)

        self.tb_Italic = QToolButton(self.tools_widget)
        self.tb_Italic.setFixedSize(QSize(22, 22))
        self.tb_Italic.setText("")
        icon3 = SvgIcon("resources/icons/ic_italic.svg")
        self.tb_Italic.setIcon(icon3)
        self.tb_Italic.setIconSize(QSize(20, 20))
        self.tb_Italic.setCheckable(True)
        self.tb_Italic.setObjectName("PB_Italic")
        self.row2.addWidget(self.tb_Italic)

        self.tb_Underline = QToolButton(self.tools_widget)
        self.tb_Underline.setFixedSize(QSize(22, 22))
        self.tb_Underline.setText("")
        icon4 = SvgIcon("resources/icons/ic_underline.svg")
        self.tb_Underline.setIcon(icon4)
        self.tb_Underline.setIconSize(QSize(20, 20))
        self.tb_Underline.setCheckable(True)
        self.tb_Underline.setObjectName("PB_Underline")
        self.row2.addWidget(self.tb_Underline)

        self.tb_TextColor = QToolButton(agent)
        self.tb_TextColor.setFixedSize(QSize(22, 22))
        icon5 = SvgIcon("resources/icons/ic_textColor.svg")
        self.tb_TextColor.setIcon(icon5)
        self.tb_TextColor.setIconSize(QSize(20, 20))
        self.tb_TextColor.setObjectName("tb_text_color")
        self.tb_TextColor.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.tb_TextColor.setProperty("color", QColor())

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
        self.color_menu = ColorMenu(convertColors(textcolors), self.tb_TextColor)
        self.tb_TextColor.setMenu(self.color_menu)
        self.row2.addWidget(self.tb_TextColor)

        l1 = QFrame(self.tools_widget)
        l1.setFrameShape(QFrame.Shape.VLine)
        l1.setFrameShadow(QFrame.Shadow.Sunken)
        l1.setObjectName("l1")
        self.row2.addWidget(l1)

        self.align_group = QButtonGroup()
        self.align_group.setExclusive(True)

        self.tb_AlignLeft = QToolButton(self.tools_widget)
        self.tb_AlignLeft.setFixedSize(QSize(22, 22))
        self.tb_AlignLeft.setText("")
        icon6 = SvgIcon("resources/icons/ic_alignleft.svg")
        self.tb_AlignLeft.setIcon(icon6)
        self.tb_AlignLeft.setIconSize(QSize(20, 20))
        self.tb_AlignLeft.setCheckable(True)
        self.tb_AlignLeft.setObjectName("PB_AlignLeft")
        self.tb_AlignLeft.setChecked(True)
        self.align_group.addButton(self.tb_AlignLeft)
        self.row2.addWidget(self.tb_AlignLeft)

        self.tb_AlignCenter = QToolButton(self.tools_widget)
        self.tb_AlignCenter.setFixedSize(QSize(22, 22))
        self.tb_AlignCenter.setText("")
        icon7 = SvgIcon("resources/icons/ic_aligncenter.svg")
        self.tb_AlignCenter.setIcon(icon7)
        self.tb_AlignCenter.setIconSize(QSize(20, 20))
        self.tb_AlignCenter.setCheckable(True)
        self.tb_AlignCenter.setObjectName("PB_AlignCenter")
        self.align_group.addButton(self.tb_AlignCenter)
        self.row2.addWidget(self.tb_AlignCenter)

        self.text_tools_layout.addLayout(self.row2)

        agent.addAction(self.wac_textTools)

        agent.addSeparator()

        self.ac_Cut = agent.addAction("")
        self.ac_Cut.setEnabled(False)
        self.ac_Copy = agent.addAction("")
        self.ac_Copy.setEnabled(False)
        self.ac_Paste = agent.addAction("")
        self.ac_Paste.setEnabled(False)

        self.table_group = QActionGroup(agent)

        sep2 = agent.addSeparator()
        self.table_group.addAction(sep2)

        self.ac_RowBottom = agent.addAction(
            SvgIcon("resources/icons/ic_insertRowBottom.svg"), ""
        )
        self.table_group.addAction(self.ac_RowBottom)
        self.ac_RowTop = agent.addAction(
            SvgIcon("resources/icons/ic_insertRowTop.svg"), ""
        )
        self.table_group.addAction(self.ac_RowTop)
        self.ac_ColumnRight = agent.addAction(
            SvgIcon("resources/icons/ic_insertColumnRight.svg"), ""
        )
        self.table_group.addAction(self.ac_ColumnRight)
        self.ac_ColumnLeft = agent.addAction(
            SvgIcon("resources/icons/ic_insertColumnLeft.svg"), ""
        )
        self.table_group.addAction(self.ac_ColumnLeft)

        sep3 = agent.addSeparator()
        self.table_group.addAction(sep3)

        self.ac_DeleteRow = agent.addAction(
            SvgIcon("resources/icons/ic_deleterow.svg"), ""
        )
        self.table_group.addAction(self.ac_DeleteRow)
        self.ac_DeleteColumn = agent.addAction(
            SvgIcon("resources/icons/ic_deletecolumn.svg"), ""
        )
        self.table_group.addAction(self.ac_DeleteColumn)

        self.hyperlink_group = QActionGroup(agent)

        sep4 = agent.addSeparator()
        self.hyperlink_group.addAction(sep4)

        self.ac_DeleteHyperlink = agent.addAction("")
        self.hyperlink_group.addAction(self.ac_DeleteHyperlink)

        self.retranslateUi()

    def retranslateUi(self):
        _translate = QCoreApplication.translate
        self.ac_Cut.setText(_translate("TextEditorMenu", "Cut"))
        self.ac_Copy.setText(_translate("TextEditorMenu", "Copy"))
        self.ac_Paste.setText(_translate("TextEditorMenu", "Paste"))
        self.ac_RowTop.setText(_translate("TextEditorMenu", "Insert row above"))
        self.ac_RowBottom.setText(_translate("TextEditorMenu", "Insert row below"))
        self.ac_ColumnLeft.setText(_translate("TextEditorMenu", "Insert column left"))
        self.ac_ColumnRight.setText(_translate("TextEditorMenu", "Insert colum right"))
        self.ac_DeleteRow.setText(_translate("TextEditorMenu", "Delete selected row"))
        self.ac_DeleteColumn.setText(
            _translate("TextEditorMenu", "Delete selected column")
        )
        self.ac_DeleteHyperlink.setText(
            _translate("TextEditorMenu", "Delete hyperlink")
        )


class AudioEditorView:
    def setUi(self, agent: QWidget) -> None:
        # agent.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # agent.setMinimumWidth(90)
        agent.setAutoFillBackground(True)

        self.main_layout = QVBoxLayout(agent)
        self.main_layout.setContentsMargins(0, 0, 0, -2)
        agent.setLayout(self.main_layout)

        self.main_frame = QFrame(agent)
        self.main_frame.setFrameShape(QFrame.Shape.Box)

        self.frame_layout = QHBoxLayout(self.main_frame)

        self.frame_layout.setContentsMargins(0, 0, 5, 0)
        self.frame_layout.setSpacing(2)

        self.main_frame.setLayout(self.frame_layout)

        self.swi_PlayPause = SwitchButton(
            agent.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay),
            agent.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause),
            self.main_frame,
        )
        self.swi_PlayPause.setMaximumSize(QSize(23, 23))
        self.swi_PlayPause.setObjectName("swi_PlayPause")
        self.swi_PlayPause.setFlat(True)
        self.frame_layout.addWidget(self.swi_PlayPause)

        self.le_name = QLineEdit(self.main_frame)
        self.le_name.setObjectName("self.le_name")
        # self.le_name.setMinimumWidth(90)
        self.le_name.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        # self.le_name.setMaximumWidth(300)
        self.frame_layout.addWidget(self.le_name)


class ResizeOverlay(QFrame):
    class State(Enum):
        Inactive = 0
        StartPosSet = 1
        Moving = 2

    class Section(Enum):
        NoSection = 0
        Bottom = 1
        BottomRight = 2
        Right = 3

    def __init__(self, init_rect: QRect, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setShape(QLabel.Shape.Box)
        self.setWindowOpacity(0.4)
        self.setGeometry(init_rect)

        self._cursor_map = {
            ResizeOverlay.Section.NoSection: Qt.CursorShape.ArrowCursor,
            ResizeOverlay.Section.Bottom: Qt.CursorShape.SizeVerCursor,
            ResizeOverlay.Section.BottomRight: Qt.CursorShape.SizeFDiagCursor,
            ResizeOverlay.Section.Right: Qt.CursorShape.SizeHorCursor,
        }
        self._control_rects: dict[ResizeOverlay.Section, QRect] = {}
        (
            self._control_rects[ResizeOverlay.Section.Bottom],
            self._control_rects[ResizeOverlay.Section.BottomRight],
            self._control_rects[ResizeOverlay.Section.Right],
        ) = self.get_control_rects()

        self._max_width = 0
        self._resizing_state = ResizeOverlay.State.Inactive
        self._current_section = ResizeOverlay.Section.NoSection
        self._start_pos = QPoint()

    def get_control_rects(self) -> tuple[QRect, QRect, QRect]:
        rect = self.rect()
        center_bottom = QPoint(rect.center().x() - 3, rect.bottom() - 3)
        bottom_right = QPoint(rect.bottomRight().x() - 3, rect.bottomRight().y() - 3)
        center_right = QPoint(rect.right() - 3, rect.center().y() - 3)

        return (
            QRect(center_bottom, QSize(6, 6)),
            QRect(bottom_right, QSize(6, 6)),
            QRect(center_right, QSize(6, 6)),
        )

    def get_current_section(self, pos: QPoint) -> Section:
        for section, rect in self._control_rects.items():
            if rect.contains(pos):
                return section
        return ResizeOverlay.Section.NoSection

    def drag_to_resize(self, new_pos: QPoint) -> None: ...

    def mousePressEvent(self, ev: QMouseEvent):
        if ev.button() == Qt.MouseButton.LeftButton and self._current_section:
            self._start_pos = ev.pos()
            self._resizing_state == ResizeOverlay.State.StartPosSet
        return super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev: QMouseEvent):
        self._current_section = self.get_current_section(ev.pos())
        self.setCursor(self._cursor_map[self._cursor_map])
        if ev.button() == Qt.MouseButton.LeftButton and self._resizing_state:
            self._resizing_state = ResizeOverlay.State.Moving
            self.drag_to_resize(ev.pos())
        return super().mouseMoveEvent(ev)

    def paintEvent(self, ev: QPaintEvent):
        painter = QPainter(self)
        painter.drawRects(self._control_rects.values())
        return super().paintEvent(ev)

    def resizeEvent(self, ev: QResizeEvent):
        (
            self._control_rects[ResizeOverlay.Section.Bottom],
            self._control_rects[ResizeOverlay.Section.BottomRight],
            self._control_rects[ResizeOverlay.Section.Right],
        ) = self.get_control_rects()
        return super().resizeEvent(ev)


class PictureLabel(QLabel):
    resized = pyqtSignal(QSize)

    def __init__(self, parent=None) -> None:
        super().__init__(parent, Qt.WindowType.Widget)
        self.setMouseTracking(True)
        self.setScaledContents(True)
        self.setShape(QLabel.Shape.Box)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self._max_width = 0
        self.control_points = {}
        self.cursor_map = {
            "cb": Qt.CursorShape.SizeVerCursor,
            "br": Qt.CursorShape.SizeFDiagCursor,
            "cr": Qt.CursorShape.SizeHorCursor,
        }
        (
            self.control_points["cb"],
            self.control_points["br"],
            self.control_points["cr"],
        ) = self.get_control_rects()
        self._current_section = PictureLabel.Section.NoSection
        self._resizing_state = PictureLabel.ResizingState.Inactive
        self._intersecting_rect: str | None = None
        self._drag_start_pos = QPoint()

    def set_max_width(self, width: int) -> None:
        self._max_width = width

    def get_control_rects(self) -> tuple[QRect, QRect, QRect]:
        rect = self.rect()
        center_bottom = QPoint(rect.center().x() - 3, rect.bottom() - 3)
        bottom_right = QPoint(rect.bottomRight().x() - 3, rect.bottomRight().y() - 3)
        center_right = QPoint(rect.right() - 3, rect.center().y() - 3)

        return (
            QRect(center_bottom, QSize(6, 6)),
            QRect(bottom_right, QSize(6, 6)),
            QRect(center_right, QSize(6, 6)),
        )

    def intersected_control_rect(
        self, point: QPoint
    ) -> tuple[str, QRect] | tuple[None, None]:
        for location, rect in self.control_point.items():
            if rect.contains(point):
                return location, rect
        return None, None

    def mousePressEvent(self, ev: QMouseEvent) -> None:
        if ev.buttons() == Qt.MouseButton.LeftButton and self._intersecting_rect:
            self._drag_start_pos = ev.pos()
            self._resizing_state = PictureLabel.ResizingState.StartPosSet
        super().mousePressEvent(ev)

    def mouseReleaseEvent(self, ev: QMouseEvent):
        if (
            ev.buttons() == Qt.MouseButton.LeftButton
            and self._resizing_state == PictureLabel.ResizingState.Moving
        ):
            self._resizing_state = PictureLabel.ResizingState.Inactive
            self.resized.emit(self.size())

        return super().mouseReleaseEvent(ev)

    def mouseMoveEvent(self, ev: QMouseEvent) -> None:
        self._intersecting_rect, control_rect = self.intersected_control_rect(ev.pos())
        if control_rect or self._user_moving:
            self.setCursor(self.cursor_map[location])
            if (
                ev.buttons() == Qt.MouseButton.LeftButton
                and PictureLabel.ResizingState.StartPosSet
            ):
                self._user_moving = True
        else:
            self.unsetCursor()

        super().mouseMoveEvent(ev)

    def paintEvent(self, ev: QPaintEvent) -> None:
        painter = QPainter(self)

        painter.drawRects([self.cb_rect, self.br_rect, self.cr_rect])

        super().paintEvent(ev)


class PictureEditorView:
    def setUi(self, agent: QWidget):
        agent.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        agent.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        agent.setObjectName("PictureElement")
        self.main_layout = QVBoxLayout(agent)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.setContentsMargins(3, 3, 3, 3)
        self.main_layout.setSpacing(0)

        # self.piclabel = PictureLabel(self)
        # self.piclabel.resized.connect(self.fitToPicture)
        # self.main_layout.addWidget(self.piclabel)

        agent.setLayout(self.main_layout)

    def fitToPicture(self) -> None:
        self.setFixedSize(self.piclabel.width() + 6, self.piclabel.height() + 6)
