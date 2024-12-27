from PyQt6 import QtWidgets, QtGui, QtCore
from ui.UI_Commons import *
from ui.StyledWidget import *

class TextToolbox:

    def setUI(self, agent: QtWidgets.QWidget) -> None:
        agent.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Minimum)
        agent.setStyleSheet(fromStyle("Toolset"))
        agent.setObjectName("TextToolset")
        self.text_toolset_layout = QtWidgets.QVBoxLayout(agent)
        self.text_toolset_layout.setContentsMargins(0, 0, 0, 10)
        self.text_toolset_layout.setObjectName("TextToolsetLayout")
        agent.setLayout(self.text_toolset_layout)

        self.text_frame = QtWidgets.QFrame(agent)
        self.text_frame.setFrameShape(QtWidgets.QFrame.Shape.Panel)
        self.text_frame.setFixedHeight(165)
        self.text_frame.setObjectName("StandardFrame")

        self.text_frame_layout = QtWidgets.QVBoxLayout(self.text_frame)
        self.text_frame_layout.setSpacing(8)
        self.text_frame_layout.setObjectName("TextFrameLayout")

        self.lb_TextTools = QtWidgets.QLabel(self.text_frame)
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(10)
        font.setBold(True)
        font.setStyleStrategy(QtGui.QFont.StyleStrategy.PreferAntialias)
        self.lb_TextTools.setFont(font)
        self.lb_TextTools.setObjectName("LB_TextTools")
        self.text_frame_layout.addWidget(self.lb_TextTools)

        self.row1 = QtWidgets.QHBoxLayout()
        self.row1.setContentsMargins(0, 0, 0, 0)
        self.row1.setObjectName("Row1")

        self.cb_Font = QtWidgets.QFontComboBox(self.text_frame)
        self.cb_Font.setMaximumSize(QtCore.QSize(120, 25))
        self.cb_Font.setObjectName("CB_Font")
        self.row1.addWidget(self.cb_Font)

        self.cb_FontSize = FontSizeBox(self.text_frame)
        self.cb_FontSize.setMinimumSize(QtCore.QSize(40, 25))
        self.cb_FontSize.setEditable(True)
        self.cb_FontSize.setObjectName("CB_FontSize")
        self.cb_FontSize.setContentsMargins(5, 0, 5, 0)
        self.row1.addWidget(self.cb_FontSize)

        self.text_frame_layout.addLayout(self.row1)

        self.row2 = QtWidgets.QHBoxLayout()
        self.row2.setContentsMargins(-1, -1, -1, 0)
        self.row2.setSpacing(2)
        self.row2.setObjectName("Row2")

        spa1 = QtWidgets.QSpacerItem(15, 5, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.row2.addItem(spa1)

        self.pb_Bold = QtWidgets.QPushButton(self.text_frame)
        self.pb_Bold.setMaximumSize(QtCore.QSize(22, 22))
        self.pb_Bold.setText("")
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("resources/icons/ic_bold.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_Bold.setIcon(icon2)
        self.pb_Bold.setIconSize(QtCore.QSize(20, 20))
        self.pb_Bold.setCheckable(True)
        self.pb_Bold.setObjectName("PB_Bold")
        self.row2.addWidget(self.pb_Bold)

        self.pb_Italic = QtWidgets.QPushButton(self.text_frame)
        self.pb_Italic.setFixedSize(QtCore.QSize(22, 22))
        self.pb_Italic.setText("")
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap("resources/icons/ic_italic.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_Italic.setIcon(icon3)
        self.pb_Italic.setIconSize(QtCore.QSize(20, 20))
        self.pb_Italic.setCheckable(True)
        self.pb_Italic.setObjectName("PB_Italic")
        self.row2.addWidget(self.pb_Italic)

        self.pb_Underline = QtWidgets.QPushButton(self.text_frame)
        self.pb_Underline.setFixedSize(QtCore.QSize(22, 22))
        self.pb_Underline.setText("")
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap("resources/icons/ic_underline.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_Underline.setIcon(icon4)
        self.pb_Underline.setIconSize(QtCore.QSize(20, 20))
        self.pb_Underline.setCheckable(True)
        self.pb_Underline.setObjectName("PB_Underline")
        self.row2.addWidget(self.pb_Underline)

        self.csb_TextColor = ColorSplitButton(self.text_frame)
        self.csb_TextColor.lbutton.setFixedSize(QtCore.QSize(22, 22))
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap("resources/icons/ic_textcolor.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.csb_TextColor.lbutton.setIcon(icon5)
        self.csb_TextColor.lbutton.setIconSize(QtCore.QSize(20, 20))
        self.csb_TextColor.lbutton.setFlat(False)
        self.csb_TextColor.lbutton.setStyleSheet(fromStyle("PB_textcolor"))
        self.csb_TextColor.lbutton.setObjectName("PB_ApplyColour")

        self.csb_TextColor.rbutton.setFixedSize(QtCore.QSize(12, 22))
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

        # self.csb_BackgroundColor = ColorSplitButton(self.text_frame)
        # self.csb_BackgroundColor.setFixedWidth(35)
        # self.csb_BackgroundColor.lbutton.setFixedSize(QtCore.QSize(22, 22))
        # icon6 = QtGui.QIcon()
        # icon6.addPixmap(QtGui.QPixmap("resources/icons/ic_backgroundColor.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        # self.csb_BackgroundColor.lbutton.setIcon(icon6)
        # self.csb_BackgroundColor.lbutton.setIconSize(QtCore.QSize(20, 20))
        # self.csb_BackgroundColor.lbutton.setFlat(False)
        # stylesheet = fromStyle("PB_textcolor")
        # stylesheet = stylesheet.replace("#000000", "#ffffff")
        # self.csb_BackgroundColor.lbutton.setStyleSheet(stylesheet)
        # self.csb_BackgroundColor.lbutton.setObjectName("csb_backgroundColorL")

        # self.csb_BackgroundColor.rbutton.setFixedSize(QtCore.QSize(12, 22))
        # self.csb_BackgroundColor.rbutton.setStyleSheet("border-radius: 4px;")
        # self.color_menu2 = ColorMenu(convertColors(textcolors), self.csb_BackgroundColor.rbutton)
        # self.csb_BackgroundColor.rbutton.setMenu(self.color_menu2)
        # self.csb_BackgroundColor.rbutton.setObjectName("csb_backgroundColorR")
        # self.csb_BackgroundColor.setColor(QtGui.QColor("#ffffff"))
        # self.row2.addWidget(self.csb_BackgroundColor)

        l1 = QtWidgets.QFrame(self.text_frame)
        l1.setStyleSheet("background: none")
        l1.setFrameShape(QtWidgets.QFrame.Shape.VLine)
        l1.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        l1.setObjectName("l1")
        self.row2.addWidget(l1)
        
        self.veralign_group = QtWidgets.QButtonGroup(self)
        self.veralign_group.setExclusive(False)

        self.pb_Subscript = QtWidgets.QPushButton(self.text_frame)
        self.pb_Subscript.setFixedSize(QtCore.QSize(22, 22))
        self.pb_Subscript.setText("")
        icon10 = QtGui.QIcon()
        icon10.addPixmap(QtGui.QPixmap("resources/icons/ic_subscript.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_Subscript.setIcon(icon10)
        self.pb_Subscript.setIconSize(QtCore.QSize(20, 20))
        self.pb_Subscript.setCheckable(True)
        self.pb_Subscript.setObjectName("PB_Subscript")
        self.veralign_group.addButton(self.pb_Subscript)
        self.row2.addWidget(self.pb_Subscript)
        
        self.pb_Superscript = QtWidgets.QPushButton(self.text_frame)
        self.pb_Superscript.setFixedSize(QtCore.QSize(22, 22))
        self.pb_Superscript.setText("")
        icon11 = QtGui.QIcon()
        icon11.addPixmap(QtGui.QPixmap("resources/icons/ic_superscript.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_Superscript.setIcon(icon11)
        self.pb_Superscript.setIconSize(QtCore.QSize(20, 20))
        self.pb_Superscript.setCheckable(True)
        self.pb_Superscript.setObjectName("PB_Superscript")
        self.veralign_group.addButton(self.pb_Superscript)
        self.row2.addWidget(self.pb_Superscript)

        spa2 = QtWidgets.QSpacerItem(15, 5, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.row2.addItem(spa2)

        self.text_frame_layout.addLayout(self.row2)

        self.row3 = QtWidgets.QHBoxLayout()
        self.row3.setContentsMargins(0, 0, 0, 0)
        self.row3.setSpacing(3)
        self.row3.setObjectName("Row3")

        self.align_group = QtWidgets.QButtonGroup()
        self.align_group.setExclusive(True)

        self.pb_AlignLeft = QtWidgets.QPushButton(self.text_frame)
        self.pb_AlignLeft.setFixedSize(QtCore.QSize(22, 22))
        self.pb_AlignLeft.setText("")
        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap("resources/icons/ic_alignleft.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_AlignLeft.setIcon(icon6)
        self.pb_AlignLeft.setIconSize(QtCore.QSize(20, 20))
        self.pb_AlignLeft.setCheckable(True)
        self.pb_AlignLeft.setObjectName("PB_AlignLeft")
        self.pb_AlignLeft.setChecked(True)
        self.align_group.addButton(self.pb_AlignLeft)
        self.row3.addWidget(self.pb_AlignLeft)

        self.pb_AlignCenter = QtWidgets.QPushButton(self.text_frame)
        self.pb_AlignCenter.setFixedSize(QtCore.QSize(22, 22))
        self.pb_AlignCenter.setText("")
        icon7 = QtGui.QIcon()
        icon7.addPixmap(QtGui.QPixmap("resources/icons/ic_aligncenter.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_AlignCenter.setIcon(icon7)
        self.pb_AlignCenter.setIconSize(QtCore.QSize(20, 20))
        self.pb_AlignCenter.setCheckable(True)
        self.pb_AlignCenter.setObjectName("PB_AlignCenter")
        self.align_group.addButton(self.pb_AlignCenter)
        self.row3.addWidget(self.pb_AlignCenter)

        self.pb_AlignRight = QtWidgets.QPushButton(self.text_frame)
        self.pb_AlignRight.setFixedSize(QtCore.QSize(22, 22))
        self.pb_AlignRight.setText("")
        icon8 = QtGui.QIcon()
        icon8.addPixmap(QtGui.QPixmap("resources/icons/ic_alignrigeduc.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_AlignRight.setIcon(icon8)
        self.pb_AlignRight.setIconSize(QtCore.QSize(20, 20))
        self.pb_AlignRight.setCheckable(True)
        self.pb_AlignRight.setObjectName("PB_AlignRight")
        self.align_group.addButton(self.pb_AlignRight)
        self.row3.addWidget(self.pb_AlignRight)

        self.pb_AlignJustify = QtWidgets.QPushButton(self.text_frame)
        self.pb_AlignJustify.setFixedSize(QtCore.QSize(22, 22))
        self.pb_AlignJustify.setText("")
        icon9 = QtGui.QIcon()
        icon9.addPixmap(QtGui.QPixmap("resources/icons/ic_alignjustify.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_AlignJustify.setIcon(icon9)
        self.pb_AlignJustify.setIconSize(QtCore.QSize(20, 20))
        self.pb_AlignJustify.setCheckable(True)
        self.pb_AlignJustify.setObjectName("PB_AlignJustify")
        self.align_group.addButton(self.pb_AlignJustify)
        self.row3.addWidget(self.pb_AlignJustify)

        l2 = QtWidgets.QFrame(self.text_frame)
        l2.setStyleSheet("background: none")
        l2.setFrameShape(QtWidgets.QFrame.Shape.VLine)
        l2.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        l2.setObjectName("l2")
        self.row3.addWidget(l2)

        self.pb_List = QtWidgets.QPushButton(self.text_frame)
        self.pb_List.setFixedSize(QtCore.QSize(22, 22))
        self.pb_List.setText("")
        icon12 = QtGui.QIcon()
        icon12.addPixmap(QtGui.QPixmap("resources/icons/ic_list.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_List.setIcon(icon12)
        self.pb_List.setIconSize(QtCore.QSize(20, 20))
        self.pb_List.setObjectName("PB_List")
        self.row3.addWidget(self.pb_List)

        self.pb_NumList = QtWidgets.QPushButton(self.text_frame)
        self.pb_NumList.setFixedSize(QtCore.QSize(22, 22))
        self.pb_NumList.setText("")
        icon13 = QtGui.QIcon()
        icon13.addPixmap(QtGui.QPixmap("resources/icons/ic_numlist.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_NumList.setIcon(icon13)
        self.pb_NumList.setIconSize(QtCore.QSize(20, 20))
        self.pb_NumList.setObjectName("PB_NumList")
        self.row3.addWidget(self.pb_NumList)

        l3 = QtWidgets.QFrame(self.text_frame)
        l3.setStyleSheet("background: none")
        l3.setFrameShape(QtWidgets.QFrame.Shape.VLine)
        l3.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        l3.setObjectName("l3")
        self.row3.addWidget(l3)

        self.pb_Dedent = QtWidgets.QPushButton(self.text_frame)
        self.pb_Dedent.setFixedSize(QtCore.QSize(22, 22))
        self.pb_Dedent.setText("")
        icon14 = QtGui.QIcon()
        icon14.addPixmap(QtGui.QPixmap("resources/icons/ic_dedent.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_Dedent.setIcon(icon14)
        self.pb_Dedent.setIconSize(QtCore.QSize(20, 20))
        self.pb_Dedent.setObjectName("PB_Dedent")
        self.row3.addWidget(self.pb_Dedent)

        self.pb_Indent = QtWidgets.QPushButton(self.text_frame)
        self.pb_Indent.setFixedSize(QtCore.QSize(22, 22))
        self.pb_Indent.setText("")
        icon15 = QtGui.QIcon()
        icon15.addPixmap(QtGui.QPixmap("resources/icons/ic_indent.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_Indent.setIcon(icon15)
        self.pb_Indent.setIconSize(QtCore.QSize(20, 20))
        self.pb_Indent.setObjectName("PB_Indent")
        self.row3.addWidget(self.pb_Indent)

        self.text_frame_layout.addLayout(self.row3)

        self.insert_row = QtWidgets.QWidget(self.text_frame)
        self.insert_row.setMaximumSize(QtCore.QSize(16777215, 26))
        self.insert_row.setStyleSheet(fromStyle("SpecialRow"))
        self.insert_row.setObjectName("InsertRow")

        self.row4 = QtWidgets.QHBoxLayout(self.insert_row)
        self.row4.setContentsMargins(6, 3, 0, 3)
        self.row4.setObjectName("Row4")

        self.lb_TextInsert = QtWidgets.QLabel(self.insert_row)
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(9)
        font.setBold(True)
        self.lb_TextInsert.setFont(font)
        self.lb_TextInsert.setObjectName("LB_TextInsert")
        self.row4.addWidget(self.lb_TextInsert)

        self.pb_Table = QtWidgets.QPushButton(self.insert_row)
        self.pb_Table.setFixedSize(QtCore.QSize(22, 22))
        self.pb_Table.setText("")
        icon16 = QtGui.QIcon()
        icon16.addPixmap(paintIcon("resources/icons/ic_table.svg", QColor("#ffffff")), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_Table.setIcon(icon16)
        self.pb_Table.setIconSize(QtCore.QSize(20, 20))
        self.pb_Table.setObjectName("PB_Table")
        self.menu_table = TableMenu(self)
        self.pb_Table.setMenu(self.menu_table)
        self.row4.addWidget(self.pb_Table)

        self.pb_Symbol = QtWidgets.QPushButton(self.insert_row)
        self.pb_Symbol.setFixedSize(QtCore.QSize(22, 22))
        self.pb_Symbol.setText("")
        icon17 = QtGui.QIcon()
        icon17.addPixmap(paintIcon("resources/icons/ic_symbol.svg", QColor("#ffffff")), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_Symbol.setIcon(icon17)
        self.pb_Symbol.setIconSize(QtCore.QSize(20, 20))
        self.pb_Symbol.setObjectName("PB_Symbol")
        self.row4.addWidget(self.pb_Symbol)

        self.pb_Hyperlink = QtWidgets.QPushButton(self.insert_row)
        self.pb_Hyperlink.setFixedSize(QtCore.QSize(22, 22))
        self.pb_Hyperlink.setText("")
        icon18 = QtGui.QIcon()
        icon18.addPixmap(paintIcon("resources/icons/ic_hyperlink.svg", QColor("#ffffff")), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_Hyperlink.setIcon(icon18)
        self.pb_Hyperlink.setIconSize(QtCore.QSize(20, 20))
        self.pb_Hyperlink.setObjectName("PB_Symbol")
        self.row4.addWidget(self.pb_Hyperlink)

        spa4 = QtWidgets.QSpacerItem(15, 5, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.row4.addItem(spa4)

        self.text_frame_layout.addWidget(self.insert_row)

        self.text_toolset_layout.addWidget(self.text_frame)

        self.table_frame = QtWidgets.QFrame(agent)
        self.table_frame.setFixedHeight(60)
        self.table_frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.table_frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.table_frame.setObjectName("TableFrame")
        self.table_frame.hide()

        self.table_frame_layout = QtWidgets.QVBoxLayout(self.table_frame)
        self.table_frame_layout.setObjectName("TableFrameLayout")
        
        self.lb_TableTools = QtWidgets.QLabel(self.table_frame)
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(10)
        font.setBold(True)
        self.lb_TableTools.setFont(font)
        self.lb_TableTools.setObjectName("LB_TableTools")
        self.table_frame_layout.addWidget(self.lb_TableTools)

        self.row5 = QtWidgets.QHBoxLayout()
        self.row5.setContentsMargins(0, 0, 0, 0)
        self.row5.setObjectName("Row5")

        self.pb_RowBottom = QtWidgets.QPushButton(self.table_frame)
        self.pb_RowBottom.setFixedSize(QtCore.QSize(22, 22))
        self.pb_RowBottom.setText("")
        icon19 = QtGui.QIcon()
        icon19.addPixmap(QtGui.QPixmap("resources/icons/ic_insertRowBottom.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_RowBottom.setIcon(icon19)
        self.pb_RowBottom.setIconSize(QtCore.QSize(20, 20))
        self.pb_RowBottom.setObjectName("PB_RowBottom")
        self.row5.addWidget(self.pb_RowBottom)

        self.pb_RowTop = QtWidgets.QPushButton(self.table_frame)
        self.pb_RowTop.setFixedSize(QtCore.QSize(22, 22))
        self.pb_RowTop.setText("")
        icon20 = QtGui.QIcon()
        icon20.addPixmap(QtGui.QPixmap("resources/icons/ic_insertRowTop.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_RowTop.setIcon(icon20)
        self.pb_RowTop.setIconSize(QtCore.QSize(20, 20))
        self.pb_RowTop.setObjectName("PB_RowTop")
        self.row5.addWidget(self.pb_RowTop)

        self.l5 = QtWidgets.QFrame(self.table_frame)
        self.l5.setStyleSheet("background: none;")
        self.l5.setFrameShape(QtWidgets.QFrame.Shape.VLine)
        self.l5.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.l5.setObjectName("l5")
        self.row5.addWidget(self.l5)

        self.pb_ColumnRight = QtWidgets.QPushButton(self.table_frame)
        self.pb_ColumnRight.setFixedSize(QtCore.QSize(22, 22))
        self.pb_ColumnRight.setText("")
        icon21 = QtGui.QIcon()
        icon21.addPixmap(QtGui.QPixmap("resources/icons/ic_insertColumnRight.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_ColumnRight.setIcon(icon21)
        self.pb_ColumnRight.setIconSize(QtCore.QSize(20, 20))
        self.pb_ColumnRight.setObjectName("PB_ColumnRight")
        self.row5.addWidget(self.pb_ColumnRight)

        self.pb_ColumnLeft = QtWidgets.QPushButton(self.table_frame)
        self.pb_ColumnLeft.setFixedSize(QtCore.QSize(22, 22))
        self.pb_ColumnLeft.setText("")
        icon22 = QtGui.QIcon()
        icon22.addPixmap(QtGui.QPixmap("resources/icons/ic_insertColumnLeft.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_ColumnLeft.setIcon(icon22)
        self.pb_ColumnLeft.setIconSize(QtCore.QSize(20, 20))
        self.pb_ColumnLeft.setObjectName("PB_ColumnLeft")
        self.row5.addWidget(self.pb_ColumnLeft)

        l6 = QtWidgets.QFrame(self.table_frame)
        l6.setStyleSheet("background: none;")
        l6.setFrameShape(QtWidgets.QFrame.Shape.VLine)
        l6.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        l6.setObjectName("l6")
        self.row5.addWidget(l6)

        self.pb_DeleteRow = QtWidgets.QPushButton(self.table_frame)
        self.pb_DeleteRow.setFixedSize(QtCore.QSize(22, 22))
        self.pb_DeleteRow.setText("")
        icon23 = QtGui.QIcon()
        icon23.addPixmap(QtGui.QPixmap("resources/icons/ic_deleterow.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_DeleteRow.setIcon(icon23)
        self.pb_DeleteRow.setIconSize(QtCore.QSize(20, 20))
        self.pb_DeleteRow.setObjectName("PB_DeleteRow")
        self.row5.addWidget(self.pb_DeleteRow)

        self.pb_DeleteColumn = QtWidgets.QPushButton(self.table_frame)
        self.pb_DeleteColumn.setFixedSize(QtCore.QSize(22, 22))
        self.pb_DeleteColumn.setText("")
        icon24 = QtGui.QIcon()
        icon24.addPixmap(QtGui.QPixmap("resources/icons/ic_deletecolumn.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_DeleteColumn.setIcon(icon24)
        self.pb_DeleteColumn.setIconSize(QtCore.QSize(20, 20))
        self.pb_DeleteColumn.setObjectName("PB_DeleteColumn")
        self.row5.addWidget(self.pb_DeleteColumn)

        l7 = QtWidgets.QFrame(self.table_frame)
        l7.setStyleSheet("background: none;")
        l7.setFrameShape(QtWidgets.QFrame.Shape.VLine)
        l7.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        l7.setObjectName("l7")
        self.row5.addWidget(l7)

        self.pb_DeleteTable = QtWidgets.QPushButton(self.table_frame)
        self.pb_DeleteTable.setFixedSize(QtCore.QSize(22, 22))
        self.pb_DeleteTable.setText("")
        icon25 = QtGui.QIcon()
        icon25.addPixmap(QtGui.QPixmap("resources/icons/ic_deletetable.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_DeleteTable.setIcon(icon25)
        self.pb_DeleteTable.setIconSize(QtCore.QSize(20, 20))
        self.pb_DeleteTable.setObjectName("PB_DeleteTable")
        self.row5.addWidget(self.pb_DeleteTable)

        # spa5 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        # self.row5.addItem(spa5)

        self.table_frame_layout.addLayout(self.row5)

        self.text_toolset_layout.addWidget(self.table_frame)

        self.retranslateUi()


    def retranslateUi(self) -> None:
        _translate = QtCore.QCoreApplication.translate
        self.lb_TextTools.setText(_translate("TextToolbox", "Text Tools"))
        self.pb_Bold.setToolTip(_translate("TextToolbox", "Bold"))
        self.pb_Italic.setToolTip(_translate("TextToolbox", "Italic"))
        self.pb_Underline.setToolTip(_translate("TextToolbox", "Underline"))
        self.csb_TextColor.lbutton.setToolTip(_translate("TextToolbox", "Set font colour"))
        self.csb_TextColor.rbutton.setToolTip(_translate("TextToolbox", "Choose text colour"))
        self.pb_AlignLeft.setToolTip(_translate("TextToolbox", "Align left"))
        self.pb_AlignCenter.setToolTip(_translate("TextToolbox", "Centre"))
        self.pb_AlignRight.setToolTip(_translate("TextToolbox", "Align right"))
        self.pb_AlignJustify.setToolTip(_translate("TextToolbox", "Justify"))
        self.pb_Subscript.setToolTip(_translate("TextToolbox", "Subscript"))
        self.pb_Superscript.setToolTip(_translate("TextToolbox", "Superscript"))
        self.pb_List.setToolTip(_translate("TextToolbox", "Create bulleted list"))
        self.pb_NumList.setToolTip(_translate("TextToolbox", "Create a numbered list"))
        self.pb_Dedent.setToolTip(_translate("TextToolbox", "Decrease indent"))
        self.pb_Indent.setToolTip(_translate("TextToolbox", "Increase indent"))
        self.lb_TextInsert.setText(_translate("TextToolbox", "Insert"))
        self.pb_Table.setToolTip(_translate("TextToolbox", "Insert table"))
        self.pb_Symbol.setToolTip(_translate("TextToolbox", "Insert symbol"))
        self.pb_Hyperlink.setToolTip(_translate("TextToolset", "Insert hyperlink"))
        self.lb_TableTools.setText(_translate("TextToolbox", "Table Tools"))
        self.pb_RowBottom.setToolTip(_translate("TextToolbox", "Insert row below"))
        self.pb_RowTop.setToolTip(_translate("TextToolbox", "Insert row above"))
        self.pb_ColumnRight.setToolTip(_translate("TextToolbox", "Insert column right"))
        self.pb_ColumnLeft.setToolTip(_translate("TextToolbox", "Insert column left"))
        self.pb_DeleteRow.setToolTip(_translate("TextToolbox", "Delete selected row"))
        self.pb_DeleteColumn.setToolTip(_translate("TextToolbox", "Delete selected column"))
        self.pb_DeleteTable.setToolTip(_translate("TextToolbox", "Delete Table"))

class PictureToolbox:

    def setUi(self, agent: QtWidgets.QWidget):
        agent.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Minimum)
        agent.setStyleSheet(fromStyle("Toolset"))
        agent.setObjectName("PictureToolset")
        self.picture_toolset_layout = QtWidgets.QVBoxLayout(agent)
        self.picture_toolset_layout.setContentsMargins(0, 0, 0, 10)
        agent.setLayout(self.picture_toolset_layout)

        self.picture_frame = QtWidgets.QFrame(agent)
        self.picture_frame.setFrameShape(QtWidgets.QFrame.Shape.Panel)
        self.picture_frame.setObjectName("StandardFrame")

        self.picture_frame_layout = QtWidgets.QVBoxLayout(self.picture_frame)
        self.picture_frame_layout.setSpacing(8)
        self.picture_frame_layout.setObjectName("PictureFrameLayout")
        self.picture_frame.setLayout(self.picture_frame_layout)

        self.picture_toolset_layout.addWidget(self.picture_frame)

        self.lb_PictureTools = QtWidgets.QLabel(self.picture_frame)
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(10)
        font.setBold(True)
        font.setStyleStrategy(QtGui.QFont.StyleStrategy.PreferAntialias)
        self.lb_PictureTools.setFont(font)
        self.lb_PictureTools.setObjectName("Grey")
        self.picture_frame_layout.addWidget(self.lb_PictureTools)

        self.row1 = QtWidgets.QHBoxLayout()
        self.row1.setContentsMargins(0, 0, 0, 0)
        self.row1.setSpacing(3)
        self.row1.setObjectName("Row1")

        self.lb_ImageWidth = QtWidgets.QLabel(self.picture_frame)
        self.lb_ImageWidth.setMinimumWidth(10)
        self.lb_ImageWidth.setObjectName("LB_ImageWidth")
        self.row1.addWidget(self.lb_ImageWidth)

        self.sb_ImageWidth = QtWidgets.QSpinBox(self.picture_frame)
        self.sb_ImageWidth.setMaximum(16000)
        self.sb_ImageWidth.setObjectName("SB_ImageWidth")
        self.sb_ImageWidth.setMinimumWidth(50)
        self.row1.addWidget(self.sb_ImageWidth)

        spalb = QtWidgets.QLabel(" ")
        self.row1.addWidget(spalb)

        self.lb_ImageHeight = QtWidgets.QLabel(self.picture_frame)
        self.lb_ImageHeight.setObjectName("LB_ImageHeight")
        self.lb_ImageHeight.setMinimumWidth(10)
        self.row1.addWidget(self.lb_ImageHeight)

        self.sb_ImageHeight = QtWidgets.QSpinBox(self.picture_frame)
        self.sb_ImageHeight.setMaximum(16000)
        self.sb_ImageHeight.setObjectName("SB_ImageHeight")
        self.row1.addWidget(self.sb_ImageHeight)

        self.picture_frame_layout.addLayout(self.row1)

        self.row2 = QtWidgets.QHBoxLayout()
        self.row2.setContentsMargins(0, 0, 0, 0)
        self.row2.setSpacing(3)
        self.row2.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.row2.setObjectName("Row2")

        self.pb_KeepAspectRatio = QtWidgets.QPushButton(self.picture_frame)
        self.pb_KeepAspectRatio.setMaximumSize(QtCore.QSize(22, 22))
        self.pb_KeepAspectRatio.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("resources/icons/ic_link.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_KeepAspectRatio.setIcon(icon1)
        self.pb_KeepAspectRatio.setIconSize(QtCore.QSize(20, 20))
        self.pb_KeepAspectRatio.setCheckable(True)
        self.pb_KeepAspectRatio.setObjectName("pb_KeepAspectRatio")
        self.pb_KeepAspectRatio.setChecked(True)
        self.row2.addWidget(self.pb_KeepAspectRatio)

        l1 = QtWidgets.QFrame(self.picture_frame)
        l1.setStyleSheet("background: none")
        l1.setFrameShape(QtWidgets.QFrame.Shape.VLine)
        l1.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        l1.setObjectName("l1")
        self.row2.addWidget(l1)

        self.pb_RotateRight = QtWidgets.QPushButton(self.picture_frame)
        self.pb_RotateRight.setMaximumSize(QtCore.QSize(22, 22))
        self.pb_RotateRight.setText("")
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("resources/icons/ic_rotateRight.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_RotateRight.setIcon(icon2)
        self.pb_RotateRight.setIconSize(QtCore.QSize(20, 20))
        self.pb_RotateRight.setObjectName("pb_RotateRight")
        self.row2.addWidget(self.pb_RotateRight)

        self.pb_RotateLeft = QtWidgets.QPushButton(self.picture_frame)
        self.pb_RotateLeft.setMaximumSize(QtCore.QSize(22, 22))
        self.pb_RotateLeft.setText("")
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap("resources/icons/ic_rotateLeft.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_RotateLeft.setIcon(icon3)
        self.pb_RotateLeft.setIconSize(QtCore.QSize(20, 20))
        self.pb_RotateLeft.setObjectName("pb_RotateLeft")
        self.row2.addWidget(self.pb_RotateLeft)      

        self.picture_frame_layout.addLayout(self.row2)

        self.retranslateUi()

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.lb_PictureTools.setText(_translate("PictureToolset", "Picture Tools"))
        self.lb_ImageWidth.setText(_translate("PictureToolset", "Width"))
        self.lb_ImageHeight.setText(_translate("PictureToolset", "Height"))
        self.pb_KeepAspectRatio.setToolTip(_translate("PictureToolset", "Keep aspect ratio when changing values"))
        self.pb_RotateRight.setToolTip(_translate("PictureToolset", "Rotate right 90°"))
        self.pb_RotateLeft.setToolTip(_translate("PictureToolset", "Rotate left 90°"))

class AudioToolbox:

    def setUi(self, agent: QtWidgets.QWidget):
        agent.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Minimum)
        agent.setStyleSheet(fromStyle("Toolset"))
        agent.setObjectName("AudioToolset")
        self.audio_toolset_layout = QtWidgets.QVBoxLayout(agent)
        self.audio_toolset_layout.setContentsMargins(0, 0, 0, 10)
        self.audio_toolset_layout.setObjectName("audio_toolset_layout")
        agent.setLayout(self.audio_toolset_layout)

        self.audio_frame = QtWidgets.QFrame(agent)
        self.audio_frame.setFrameShape(QtWidgets.QFrame.Shape.Panel)
        self.audio_frame.setObjectName("StandardFrame")

        self.audio_frame_layout = QtWidgets.QVBoxLayout(self.audio_frame)
        self.audio_frame_layout.setSpacing(8)
        self.audio_frame_layout.setObjectName("AudioFrameLayout")
        self.audio_frame.setLayout(self.audio_frame_layout)

        self.audio_toolset_layout.addWidget(self.audio_frame)

        self.lb_AudioTools = QtWidgets.QLabel(self.audio_frame)
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(10)
        font.setBold(True)
        font.setStyleStrategy(QtGui.QFont.StyleStrategy.PreferAntialias)
        self.lb_AudioTools.setFont(font)
        self.lb_AudioTools.setObjectName("Grey")
        self.audio_frame_layout.addWidget(self.lb_AudioTools)

        self.row1 = QtWidgets.QHBoxLayout()
        self.row1.setContentsMargins(0, 0, 0, 0)
        self.row1.setSpacing(3)
        self.row1.setObjectName("Row1")

        self.swi_PlayPause = SwitchButton("resources/icons/ic_play.svg", "resources/icons/ic_pause.svg", self.audio_frame)
        self.swi_PlayPause.setMaximumSize(QtCore.QSize(22, 22))
        self.swi_PlayPause.setText("")
        self.swi_PlayPause.setObjectName("swi_PlayPause")
        self.row1.addWidget(self.swi_PlayPause)

        self.hs_PlayTime = QtWidgets.QSlider(self.audio_frame) 
        self.hs_PlayTime.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.hs_PlayTime.setObjectName("hs_PlayTime")
        self.row1.addWidget(self.hs_PlayTime)

        self.te_PlayTime = QtWidgets.QTimeEdit(self.audio_frame)
        self.te_PlayTime.setObjectName("sb_PlayTime")
        self.te_PlayTime.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.te_PlayTime.setDisplayFormat("h:mm:ss")
        self.row1.addWidget(self.te_PlayTime)

        self.audio_frame_layout.addLayout(self.row1)

        self.row2 = QtWidgets.QHBoxLayout()
        self.row2.setContentsMargins(0, 0, 0, 0)
        self.row2.setSpacing(3)
        self.row2.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.row2.setObjectName("Row2")      

        self.pb_rew = DoubleClickButton(self.audio_frame)
        self.pb_rew.setMaximumSize(QtCore.QSize(22, 22))
        self.pb_rew.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("resources/icons/ic_rew.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_rew.setIcon(icon1)
        self.pb_rew.setIconSize(QtCore.QSize(20, 20))
        self.pb_rew.setAutoRepeat(True)
        self.pb_rew.setObjectName("pb_Rew")
        self.row2.addWidget(self.pb_rew)

        self.pb_rew5 = QtWidgets.QPushButton(self.audio_frame)
        self.pb_rew5.setMaximumSize(QtCore.QSize(22, 22))
        self.pb_rew5.setText("")
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("resources/icons/ic_rew5.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_rew5.setIcon(icon2)
        self.pb_rew5.setIconSize(QtCore.QSize(20, 20))
        self.pb_rew5.setObjectName("pb_Rew5")
        self.row2.addWidget(self.pb_rew5)

        self.pb_rew10 = QtWidgets.QPushButton(self.audio_frame)
        self.pb_rew10.setMaximumSize(QtCore.QSize(22, 22))
        self.pb_rew10.setText("")
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap("resources/icons/ic_rew10.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_rew10.setIcon(icon3)
        self.pb_rew10.setIconSize(QtCore.QSize(20, 20))
        self.pb_rew10.setObjectName("pb_Rew10")
        self.row2.addWidget(self.pb_rew10)

        self.pb_rew30 = QtWidgets.QPushButton(self.audio_frame)
        self.pb_rew30.setMaximumSize(QtCore.QSize(22, 22))
        self.pb_rew30.setText("")
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap("resources/icons/ic_rew30.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_rew30.setIcon(icon4)
        self.pb_rew30.setIconSize(QtCore.QSize(20, 20))
        self.pb_rew30.setObjectName("pb_Rew30")
        self.row2.addWidget(self.pb_rew30)

        self.pb_fwd30 = QtWidgets.QPushButton(self.audio_frame)
        self.pb_fwd30.setMaximumSize(QtCore.QSize(22, 22))
        self.pb_fwd30.setText("")
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap("resources/icons/ic_fwd30.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_fwd30.setIcon(icon5)
        self.pb_fwd30.setIconSize(QtCore.QSize(20, 20))
        self.pb_fwd30.setObjectName("pb_Fwd30")
        self.row2.addWidget(self.pb_fwd30)

        self.pb_fwd10 = QtWidgets.QPushButton(self.audio_frame)
        self.pb_fwd10.setMaximumSize(QtCore.QSize(22, 22))
        self.pb_fwd10.setText("")
        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap("resources/icons/ic_fwd10.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_fwd10.setIcon(icon6)
        self.pb_fwd10.setIconSize(QtCore.QSize(20, 20))
        self.pb_fwd10.setObjectName("pb_Fwd10")
        self.row2.addWidget(self.pb_fwd10)

        self.pb_fwd5 = QtWidgets.QPushButton(self.audio_frame)
        self.pb_fwd5.setMaximumSize(QtCore.QSize(22, 22))
        self.pb_fwd5.setText("")
        icon7 = QtGui.QIcon()
        icon7.addPixmap(QtGui.QPixmap("resources/icons/ic_fwd5.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_fwd5.setIcon(icon7)
        self.pb_fwd5.setIconSize(QtCore.QSize(20, 20))
        self.pb_fwd5.setObjectName("pb_Fwd5")
        self.row2.addWidget(self.pb_fwd5)

        self.pb_fwd = QtWidgets.QPushButton(self.audio_frame)
        self.pb_fwd.setMaximumSize(QtCore.QSize(22, 22))
        self.pb_fwd.setText("")
        icon8 = QtGui.QIcon()
        icon8.addPixmap(QtGui.QPixmap("resources/icons/ic_fwd.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_fwd.setIcon(icon8)
        self.pb_fwd.setIconSize(QtCore.QSize(20, 20))
        self.pb_fwd.setAutoRepeat(True)
        self.pb_fwd.setObjectName("pb_Fwd")
        self.row2.addWidget(self.pb_fwd)

        self.audio_frame_layout.addLayout(self.row2)

        self.row3 = QtWidgets.QHBoxLayout()
        self.row3.setContentsMargins(0, 0, 0, 0)
        self.row3.setSpacing(3)
        self.row3.setObjectName("Row3")  

        self.pb_repeat = QtWidgets.QPushButton(self.audio_frame)
        self.pb_repeat.setMaximumSize(QtCore.QSize(22, 22))
        self.pb_repeat.setText("")
        icon9 = QtGui.QIcon()
        icon9.addPixmap(QtGui.QPixmap("resources/icons/ic_repeat.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_repeat.setIcon(icon9)
        self.pb_repeat.setIconSize(QtCore.QSize(20, 20))
        self.pb_repeat.setCheckable(True)
        self.pb_repeat.setObjectName("pb_repeat")
        self.row3.addWidget(self.pb_repeat)

        self.sb_RepeatTimes = QtWidgets.QSpinBox(self.audio_frame)
        self.sb_RepeatTimes.setObjectName("sb_RepeatTimes")
        self.sb_RepeatTimes.setMinimum(1)
        self.sb_RepeatTimes.setDisabled(True)
        self.row3.addWidget(self.sb_RepeatTimes)

        spa1 = PointSpacer(3, self.audio_frame)
        self.row3.addWidget(spa1)

        self.lb_PauseLength = QtWidgets.QLabel(self.audio_frame)
        self.lb_PauseLength.setText("")
        self.lb_PauseLength.setObjectName("Grey")
        self.lb_PauseLength.setMinimumWidth(10)
        self.row3.addWidget(self.lb_PauseLength)

        self.sb_PauseLength = QtWidgets.QSpinBox(self.audio_frame)
        self.sb_PauseLength.setObjectName("sb_PauseLength")
        self.sb_PauseLength.setMinimum(0)
        self.sb_PauseLength.setDisabled(True)
        self.row3.addWidget(self.sb_PauseLength)

        self.audio_frame_layout.addLayout(self.row3)

        self.row4 = QtWidgets.QHBoxLayout()
        self.row4.setContentsMargins(0, 0, 0, 0)
        self.row4.setSpacing(3)
        self.row4.setObjectName("Row4")

        self.lb_StartTime = QtWidgets.QLabel(self.audio_frame)
        self.lb_StartTime.setObjectName("Grey")
        self.lb_StartTime.setText("")
        self.lb_StartTime.setMinimumWidth(10)
        self.row4.addWidget(self.lb_StartTime)

        self.te_StartTime = QtWidgets.QTimeEdit(self.audio_frame)
        self.te_StartTime.setObjectName("te_StartTime")
        self.te_StartTime.setDisplayFormat("h:mm:ss")
        self.row4.addWidget(self.te_StartTime)

        spa2 = PointSpacer(3, self.audio_frame)
        self.row4.addWidget(spa2)

        self.lb_EndTime = QtWidgets.QLabel(self.audio_frame)
        self.lb_EndTime.setObjectName("Grey")
        self.lb_EndTime.setMinimumWidth(10)
        self.lb_EndTime.setText("")
        self.row4.addWidget(self.lb_EndTime)

        self.te_EndTime = QtWidgets.QTimeEdit(self.audio_frame)
        self.te_EndTime.setObjectName("te_StartTime")
        self.te_EndTime.setDisplayFormat("h:mm:ss")
        self.row4.addWidget(self.te_EndTime)

        self.audio_frame_layout.addLayout(self.row4)

        self.retranslateUi()
 
    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.lb_AudioTools.setText(_translate("AudioToolset", "Audio Tools"))
        self.swi_PlayPause.setToolTip(_translate("AudioToolset", "Play/Pause track."))
        self.pb_rew.setToolTip(_translate("AudioToolset", "Hold to rewind or double click reset playback."))
        self.pb_rew5.setToolTip(_translate("AudioToolset", "Rewind 5 seconds."))
        self.pb_rew10.setToolTip(_translate("AudioToolset", "Rewind 10 seconds."))
        self.pb_rew30.setToolTip(_translate("AudioToolset", "Rewind 30 seconds."))
        self.pb_fwd30.setToolTip(_translate("AudioToolset", "Forward 30 seconds."))
        self.pb_fwd10.setToolTip(_translate("AudioToolset", "Forward 10 seconds."))
        self.pb_fwd10.setToolTip(_translate("AudioToolset", "Forward 5 seconds."))
        self.pb_fwd.setToolTip(_translate("AudioToolset", "Hold to move fast forward."))
        self.lb_PauseLength.setText(_translate("AudioToolset", "Pause Length"))
        self.sb_PauseLength.setSuffix(_translate("AudioToolset", "sec"))
        self.sb_PauseLength.setToolTip(_translate("AudioToolset", "Sets the pause length between repeats"))
        self.lb_StartTime.setText(_translate("AudioToolset", "Start"))
        self.lb_EndTime.setText(_translate("AudioToolset", "Stop"))


class FontSizeBox(QtWidgets.QComboBox):
    textEntered = QtCore.pyqtSignal()

    def __init__(self, parent: None) -> None:
        super().__init__(parent)
        self.setInsertPolicy(QtWidgets.QComboBox.InsertPolicy.NoInsert)
        self.addItems(["8", "9", "10.5", "11", "12", "14", "16", "18", "20", "22", "24", "26", "28", "36", "48", "72"])
        self.setLineEdit(QtWidgets.QLineEdit())
        self.lineEdit().editingFinished.connect(self.checkEnteredSize)
        self._setValidator()

    def _setValidator(self) -> None:
        validator = QtGui.QRegularExpressionValidator()
        re = QtCore.QRegularExpression("(\\d+,\\d+)|(\\d+\\.\\d+)|\\d+")
        validator.setRegularExpression(re)
        self.setValidator(validator)

    def currentFontSize(self) -> int|float:
        fontsize = self.currentText()
        fontsize = fontsize.replace(",", ".")
        return float(fontsize)
    
    def setCurrentFontSize(self, fontsize: int|float):
        if fontsize % 1 == 0:
            self.setCurrentText(str(int(fontsize)))
        else:
            self.setCurrentText(str(fontsize))

    def checkEnteredSize(self) -> None:
        print("Accepted!")
        fontsize = self.currentText().replace(",", ".")
        if fontsize.startswith("0"):
            self.setCurrentText("1")
        elif float(fontsize) > 100:
            self.setCurrentText(str(100))
        self.textEntered.emit()

class TableMenu(QtWidgets.QMenu):
    tableSize = QtCore.pyqtSignal(int, int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setUI()

    def setUI(self) -> None:
        self.tableGrid = TableGrid(self)
        self.tableGrid.tableSize.connect(self.emitTableSize)
        self.ac_TableGrid = QtWidgets.QWidgetAction(self)
        self.ac_TableGrid.setDefaultWidget(self.tableGrid)
        self.addAction(self.ac_TableGrid)

    @QtCore.pyqtSlot(int, int)
    def emitTableSize(self, line: int, column: int) -> None:
        print(line, column)
        self.tableSize.emit(line, column)

class TableGrid(QtWidgets.QWidget):
    tableSize = QtCore.pyqtSignal(int, int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setUI()

    def setUI(self) -> None:
        self.setStyleSheet(fromStyle("GridButton"))
        self.button_layout = QtWidgets.QGridLayout(self)
        self.button_layout.setHorizontalSpacing(0)
        self.button_layout.setVerticalSpacing(0)

        for iline in range(8):
            for icolumn in range(10):
                button = GridButton(self)
                button.line = iline+1
                button.column = icolumn+1
                button.entered.connect(self.setMarkedButtons)
                button.sizeSet.connect(self.getTableSize)
                button.left.connect(self.clearMarkings)
                self.button_layout.addWidget(button, iline, icolumn)

        self.lb_TableSize = QtWidgets.QLabel("0 x 0")
        self.lb_TableSize.setStyleSheet("background: none;")
        self.button_layout.addWidget(self.lb_TableSize, 9, 1, 1, 10)

        self.setLayout(self.button_layout)

    @QtCore.pyqtSlot(int, int)
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

    @QtCore.pyqtSlot(int, int)
    def getTableSize(self, line: int, column: int) -> None:
        self.tableSize.emit(line, column)

    def showTableSize(self, line: int, column: int) -> None:
        self.lb_TableSize.setText(f"{column} x {line}") 

class GridButton(QtWidgets.QFrame):
    entered = QtCore.pyqtSignal(int, int)
    sizeSet = QtCore.pyqtSignal(int, int)
    left = QtCore.pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setProperty("hovered", False)
        self.setFixedSize(15, 15)
        self.line: int
        self.column: int

    def enterEvent(self, event: QtGui.QEnterEvent) -> None:
        self.entered.emit(self.line, self.column)
        super().enterEvent(event)

    def leaveEvent(self, a0: QtCore.QEvent) -> None:
        self.setProperty("hovered", False)
        self.style().polish(self)
        self.left.emit()
        super().leaveEvent(a0)        

    def mouseReleaseEvent(self, e: QtGui.QMouseEvent) -> None:
        self.sizeSet.emit(self.line, self.column)
        super().mouseReleaseEvent(e)

class ColorSplitButton(SplitButton):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self._color = QtGui.QColor("#000000")

    def setColor(self, color: QtGui.QColor) -> None:
        self._color = color

    def color(self) -> QtGui.QColor:
        return self._color