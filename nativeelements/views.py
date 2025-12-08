from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFontComboBox, QSpacerItem, QSizePolicy,
                             QPushButton, QFrame, QWidgetAction, QButtonGroup, QLineEdit, QMenu)
from PyQt6.QtCore import QSize, QCoreApplication, Qt
from PyQt6.QtGui import QIcon, QPixmap, QActionGroup
from ui.StyledWidget import fromStyle, convertColors
from ui.element_toolsets import FontSizeBox
from ui.element_toolsets import ColorSplitButton, ColorMenu
from ui.commons import SwitchButton

class TextEditorMenuView:
    
    def setUi(self, agent: QMenu):
        agent.setObjectName("TextEditorMenu")

        self.wac_textTools = QWidgetAction(agent)

        self.tools_widget = QWidget(agent)
        self.tools_widget.setStyleSheet(fromStyle("Toolbar"))
        self.text_tools_layout = QVBoxLayout(self.tools_widget)
        self.tools_widget.setLayout(self.text_tools_layout)

        self.wac_textTools.setDefaultWidget(self.tools_widget)

        self.row1 = QHBoxLayout()
        self.row1.setContentsMargins(0, 0, 0, 0)
        self.row1.setObjectName("Row1")

        self.cb_Font = QFontComboBox(self.tools_widget)
        self.cb_Font.setMaximumSize(QSize(120, 25))
        self.cb_Font.setObjectName("CB_Font")
        self.row1.addWidget(self.cb_Font)

        self.cb_FontSize = FontSizeBox(self.tools_widget)
        self.cb_FontSize.setMinimumSize(QSize(40, 25))
        self.cb_FontSize.setEditable(True)
        self.cb_FontSize.setObjectName("CB_FontSize")
        self.cb_FontSize.setContentsMargins(5, 0, 5, 0)
        self.row1.addWidget(self.cb_FontSize)

        self.text_tools_layout.addLayout(self.row1)

        self.row2 = QHBoxLayout()
        self.row2.setContentsMargins(-1, -1, -1, 0)
        self.row2.setSpacing(2)
        self.row2.setObjectName("Row2")

        spa1 = QSpacerItem(15, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.row2.addItem(spa1)

        self.pb_Bold = QPushButton(self.tools_widget)
        self.pb_Bold.setMaximumSize(QSize(22, 22))
        self.pb_Bold.setText("")
        icon2 = QIcon()
        icon2.addPixmap(QPixmap("resources/icons/ic_bold.svg"), QIcon.Mode.Normal, QIcon.State.Off)
        self.pb_Bold.setIcon(icon2)
        self.pb_Bold.setIconSize(QSize(20, 20))
        self.pb_Bold.setCheckable(True)
        self.pb_Bold.setObjectName("PB_Bold")
        self.row2.addWidget(self.pb_Bold)

        self.pb_Italic = QPushButton(self.tools_widget)
        self.pb_Italic.setFixedSize(QSize(22, 22))
        self.pb_Italic.setText("")
        icon3 = QIcon()
        icon3.addPixmap(QPixmap("resources/icons/ic_italic.svg"), QIcon.Mode.Normal, QIcon.State.Off)
        self.pb_Italic.setIcon(icon3)
        self.pb_Italic.setIconSize(QSize(20, 20))
        self.pb_Italic.setCheckable(True)
        self.pb_Italic.setObjectName("PB_Italic")
        self.row2.addWidget(self.pb_Italic)

        self.pb_Underline = QPushButton(self.tools_widget)
        self.pb_Underline.setFixedSize(QSize(22, 22))
        self.pb_Underline.setText("")
        icon4 = QIcon()
        icon4.addPixmap(QPixmap("resources/icons/ic_underline.svg"), QIcon.Mode.Normal, QIcon.State.Off)
        self.pb_Underline.setIcon(icon4)
        self.pb_Underline.setIconSize(QSize(20, 20))
        self.pb_Underline.setCheckable(True)
        self.pb_Underline.setObjectName("PB_Underline")
        self.row2.addWidget(self.pb_Underline)

        self.csb_TextColor = ColorSplitButton(agent)
        self.csb_TextColor.lbutton.setFixedSize(QSize(22, 22))
        icon5 = QIcon()
        icon5.addPixmap(QPixmap("resources/icons/ic_textcolor.svg"), QIcon.Mode.Normal, QIcon.State.Off)
        self.csb_TextColor.lbutton.setIcon(icon5)
        self.csb_TextColor.lbutton.setIconSize(QSize(20, 20))
        self.csb_TextColor.lbutton.setFlat(False)
        self.csb_TextColor.lbutton.setStyleSheet(fromStyle("PB_textcolor"))
        self.csb_TextColor.lbutton.setObjectName("PB_ApplyColur")

        self.csb_TextColor.rbutton.setFixedSize(QSize(12, 22))
        self.csb_TextColor.rbutton.setStyleSheet("border-radius: 4px;")
        textcolors = [
            "#000000", "#434343", "#666666", "#999999", "#b7b7b7", "#cccccc", "#d9d9d9", "#efefef", "#f3f3f3", "#ffffff",
            "#980000", "#ff0000", "#ff9900", "#ffff00", "#00ff00", "#00ffff", "#4a86e8", "#0000ff", "#9900ff", "#ff00ff", 
            "#e6b8af", "#f4cccc", "#fce5cd", "#fff2cc", "#d9ead3", "#d0e0e3", "#c9daf8", "#cfe2f3", "#d9d2e9", "#ead1dc", 
            "#dd7e6b", "#ea9999", "#f9cb9c", "#ffe599", "#b6d7a8", "#a2c4c9", "#a4c2f4", "#9fc5e8", "#b4a7d6", "#d5a6bd", 
            "#cc4125", "#e06666", "#f6b26b", "#ffd966", "#93c47d", "#76a5af", "#6d9eeb", "#6fa8dc", "#8e7cc3", "#c27ba0", 
            "#a61c00", "#cc0000", "#e69138", "#f1c232", "#6aa84f", "#45818e", "#3c78d8", "#3d85c6", "#674ea7", "#a64d79", 
            "#85200c", "#990000", "#b45f06", "#bf9000", "#38761d", "#134f5c", "#1155cc", "#0b5394", "#351c75", "#741b47", 
            "#5b0f00", "#660000", "#783f04", "#7f6000", "#274e13", "#0c343d", "#1c4587", "#073763", "#20124d", "#4c1130"
                    ]
        self.color_menu = ColorMenu(convertColors(textcolors), self.csb_TextColor.rbutton)
        self.csb_TextColor.rbutton.setMenu(self.color_menu)
        self.csb_TextColor.rbutton.setObjectName("TextColor")
        self.row2.addWidget(self.csb_TextColor)

        l1 = QFrame(self.tools_widget)
        l1.setStyleSheet("background: none")
        l1.setFrameShape(QFrame.Shape.VLine)
        l1.setFrameShadow(QFrame.Shadow.Sunken)
        l1.setObjectName("l1")
        self.row2.addWidget(l1)

        self.align_group = QButtonGroup()
        self.align_group.setExclusive(True)

        self.pb_AlignLeft = QPushButton(self.tools_widget)
        self.pb_AlignLeft.setFixedSize(QSize(22, 22))
        self.pb_AlignLeft.setText("")
        icon6 = QIcon()
        icon6.addPixmap(QPixmap("resources/icons/ic_alignleft.svg"), QIcon.Mode.Normal, QIcon.State.Off)
        self.pb_AlignLeft.setIcon(icon6)
        self.pb_AlignLeft.setIconSize(QSize(20, 20))
        self.pb_AlignLeft.setCheckable(True)
        self.pb_AlignLeft.setObjectName("PB_AlignLeft")
        self.pb_AlignLeft.setChecked(True)
        self.align_group.addButton(self.pb_AlignLeft)
        self.row2.addWidget(self.pb_AlignLeft)

        self.pb_AlignCenter = QPushButton(self.tools_widget)
        self.pb_AlignCenter.setFixedSize(QSize(22, 22))
        self.pb_AlignCenter.setText("")
        icon7 = QIcon()
        icon7.addPixmap(QPixmap("resources/icons/ic_aligncenter.svg"), QIcon.Mode.Normal, QIcon.State.Off)
        self.pb_AlignCenter.setIcon(icon7)
        self.pb_AlignCenter.setIconSize(QSize(20, 20))
        self.pb_AlignCenter.setCheckable(True)
        self.pb_AlignCenter.setObjectName("PB_AlignCenter")
        self.align_group.addButton(self.pb_AlignCenter)
        self.row2.addWidget(self.pb_AlignCenter)

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

        self.ac_RowBottom = agent.addAction(QIcon("resources/icons/ic_insertRowBottom.svg"), "")
        self.table_group.addAction(self.ac_RowBottom)
        self.ac_RowTop = agent.addAction(QIcon("resources/icons/ic_insertRowTop.svg"), "")
        self.table_group.addAction(self.ac_RowTop)
        self.ac_ColumnRight = agent.addAction(QIcon("resources/icons/ic_insertColumnRight.svg"), "")
        self.table_group.addAction(self.ac_ColumnRight)
        self.ac_ColumnLeft = agent.addAction(QIcon("resources/icons/ic_insertColumnLeft.svg"), "")
        self.table_group.addAction(self.ac_ColumnLeft)

        sep3 = agent.addSeparator()
        self.table_group.addAction(sep3)

        self.ac_DeleteRow = agent.addAction(QIcon("resources/icons/ic_deleterow.svg"), "")
        self.table_group.addAction(self.ac_DeleteRow)
        self.ac_DeleteColumn = agent.addAction(QIcon("resources/icons/ic_deletecolumn.svg"), "")
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
        self.ac_DeleteColumn.setText(_translate("TextEditorMenu", "Delete selected column"))
        self.ac_DeleteHyperlink.setText(_translate("TextEditorMenu", "Delete hyperlink"))

class AudioEditorView:

    def setUi(self, agent: QWidget) -> None:
        agent.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)        
        # agent.setMinimumWidth(90)
        agent.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        agent.setStyleSheet(fromStyle("AudioElement"))
        agent.setAutoFillBackground(True)
        print("Audio size", agent.width(), agent.height())

        self.main_layout = QVBoxLayout(agent)
        self.main_layout.setContentsMargins(0, 0, 0, -5)
        agent.setLayout(self.main_layout)

        self.main_frame = QFrame(agent)
        self.main_frame.setFrameShape(QFrame.Shape.Box)

        self.frame_layout = QHBoxLayout(self.main_frame)

        self.frame_layout.setContentsMargins(3, 3, 7, 3)

        self.main_frame.setLayout(self.frame_layout)

        self.swi_PlayPause = SwitchButton("resources/icons/ic_play.svg", "resources/icons/ic_pause.svg", self.main_frame)
        self.swi_PlayPause.setMaximumSize(QSize(23, 23))
        self.swi_PlayPause.setObjectName("swi_PlayPause")
        self.frame_layout.addWidget(self.swi_PlayPause)

        self.le_name = QLineEdit(self.main_frame)
        self.le_name.setObjectName("self.le_name")
        # self.le_name.setMinimumWidth(90)
        self.le_name.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # self.le_name.setMaximumWidth(300)
        self.frame_layout.addWidget(self.le_name)

class PictureEditorView:

    def setUi(self, agent: QWidget):
        agent.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        agent.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        agent.setObjectName("PictureElement")
        self.main_layout = QVBoxLayout(agent)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.setContentsMargins(3,3,3,3)
        self.main_layout.setSpacing(0)

        # self.piclabel = PictureLabel(self)
        # self.piclabel.resized.connect(self.fitToPicture)
        # self.main_layout.addWidget(self.piclabel)

        agent.setLayout(self.main_layout)

    def fitToPicture(self) -> None:
        self.setFixedSize(self.piclabel.width()+6, self.piclabel.height()+6)