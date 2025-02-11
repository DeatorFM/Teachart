from PyQt6 import QtWidgets, QtCore, QtGui
from ui.ui_toolsets import FontSizeBox, ColorSplitButton, ColorMenu
from ui.StyledWidget import convertColors, fromStyle

class TextMenu:
    
    def setUi(self, agent: QtWidgets.QMenu):
        agent.setObjectName("TextMenu")

        self.wac_textTools = QtWidgets.QWidgetAction(agent)

        self.tools_widget = QtWidgets.QWidget(agent)
        self.tools_widget.setStyleSheet(fromStyle("Toolbar"))
        self.text_tools_layout = QtWidgets.QVBoxLayout(self.tools_widget)
        self.tools_widget.setLayout(self.text_tools_layout)

        self.wac_textTools.setDefaultWidget(self.tools_widget)

        self.row1 = QtWidgets.QHBoxLayout()
        self.row1.setContentsMargins(0, 0, 0, 0)
        self.row1.setObjectName("Row1")

        self.cb_Font = QtWidgets.QFontComboBox(self.tools_widget)
        self.cb_Font.setMaximumSize(QtCore.QSize(120, 25))
        self.cb_Font.setObjectName("CB_Font")
        self.row1.addWidget(self.cb_Font)

        self.cb_FontSize = FontSizeBox(self.tools_widget)
        self.cb_FontSize.setMinimumSize(QtCore.QSize(40, 25))
        self.cb_FontSize.setEditable(True)
        self.cb_FontSize.setObjectName("CB_FontSize")
        self.cb_FontSize.setContentsMargins(5, 0, 5, 0)
        self.row1.addWidget(self.cb_FontSize)

        self.text_tools_layout.addLayout(self.row1)

        self.row2 = QtWidgets.QHBoxLayout()
        self.row2.setContentsMargins(-1, -1, -1, 0)
        self.row2.setSpacing(2)
        self.row2.setObjectName("Row2")

        spa1 = QtWidgets.QSpacerItem(15, 5, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.row2.addItem(spa1)

        self.pb_Bold = QtWidgets.QPushButton(self.tools_widget)
        self.pb_Bold.setMaximumSize(QtCore.QSize(22, 22))
        self.pb_Bold.setText("")
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("resources/icons/ic_bold.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_Bold.setIcon(icon2)
        self.pb_Bold.setIconSize(QtCore.QSize(20, 20))
        self.pb_Bold.setCheckable(True)
        self.pb_Bold.setObjectName("PB_Bold")
        self.row2.addWidget(self.pb_Bold)

        self.pb_Italic = QtWidgets.QPushButton(self.tools_widget)
        self.pb_Italic.setFixedSize(QtCore.QSize(22, 22))
        self.pb_Italic.setText("")
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap("resources/icons/ic_italic.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_Italic.setIcon(icon3)
        self.pb_Italic.setIconSize(QtCore.QSize(20, 20))
        self.pb_Italic.setCheckable(True)
        self.pb_Italic.setObjectName("PB_Italic")
        self.row2.addWidget(self.pb_Italic)

        self.pb_Underline = QtWidgets.QPushButton(self.tools_widget)
        self.pb_Underline.setFixedSize(QtCore.QSize(22, 22))
        self.pb_Underline.setText("")
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap("resources/icons/ic_underline.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_Underline.setIcon(icon4)
        self.pb_Underline.setIconSize(QtCore.QSize(20, 20))
        self.pb_Underline.setCheckable(True)
        self.pb_Underline.setObjectName("PB_Underline")
        self.row2.addWidget(self.pb_Underline)

        self.csb_TextColor = ColorSplitButton(self)
        self.csb_TextColor.lbutton.setFixedSize(QtCore.QSize(22, 22))
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap("resources/icons/ic_textcolor.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.csb_TextColor.lbutton.setIcon(icon5)
        self.csb_TextColor.lbutton.setIconSize(QtCore.QSize(20, 20))
        self.csb_TextColor.lbutton.setFlat(False)
        self.csb_TextColor.lbutton.setStyleSheet(fromStyle("PB_textcolor"))
        self.csb_TextColor.lbutton.setObjectName("PB_ApplyColur")

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

        l1 = QtWidgets.QFrame(self.tools_widget)
        l1.setStyleSheet("background: none")
        l1.setFrameShape(QtWidgets.QFrame.Shape.VLine)
        l1.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        l1.setObjectName("l1")
        self.row2.addWidget(l1)

        self.align_group = QtWidgets.QButtonGroup()
        self.align_group.setExclusive(True)

        self.pb_AlignLeft = QtWidgets.QPushButton(self.tools_widget)
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
        self.row2.addWidget(self.pb_AlignLeft)

        self.pb_AlignCenter = QtWidgets.QPushButton(self.tools_widget)
        self.pb_AlignCenter.setFixedSize(QtCore.QSize(22, 22))
        self.pb_AlignCenter.setText("")
        icon7 = QtGui.QIcon()
        icon7.addPixmap(QtGui.QPixmap("resources/icons/ic_aligncenter.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_AlignCenter.setIcon(icon7)
        self.pb_AlignCenter.setIconSize(QtCore.QSize(20, 20))
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

        self.table_group = QtGui.QActionGroup(agent)

        sep2 = agent.addSeparator()
        self.table_group.addAction(sep2)

        self.ac_RowBottom = agent.addAction(QtGui.QIcon("resources/icons/ic_insertRowBottom.svg"), "")
        self.table_group.addAction(self.ac_RowBottom)
        self.ac_RowTop = agent.addAction(QtGui.QIcon("resources/icons/ic_insertRowTop.svg"), "")
        self.table_group.addAction(self.ac_RowTop)
        self.ac_ColumnRight = agent.addAction(QtGui.QIcon("resources/icons/ic_insertColumnRight.svg"), "")
        self.table_group.addAction(self.ac_ColumnRight)
        self.ac_ColumnLeft = agent.addAction(QtGui.QIcon("resources/icons/ic_insertColumnLeft.svg"), "")
        self.table_group.addAction(self.ac_ColumnLeft)

        sep3 = agent.addSeparator()
        self.table_group.addAction(sep3)

        self.ac_DeleteRow = agent.addAction(QtGui.QIcon("resources/icons/ic_deleterow.svg"), "")
        self.table_group.addAction(self.ac_DeleteRow)
        self.ac_DeleteColumn = agent.addAction(QtGui.QIcon("resources/icons/ic_deletecolumn.svg"), "")
        self.table_group.addAction(self.ac_DeleteColumn)

        self.hyperlink_group = QtGui.QActionGroup(agent)

        sep4 = agent.addSeparator()
        self.hyperlink_group.addAction(sep4)

        self.ac_DeleteHyperlink = agent.addAction("")
        self.hyperlink_group.addAction(self.ac_DeleteHyperlink)

        self.retranslateUi()

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.ac_Cut.setText(_translate("TextMenu", "Cut"))
        self.ac_Copy.setText(_translate("TextMenu", "Copy"))
        self.ac_Paste.setText(_translate("TextMenu", "Paste"))
        self.ac_RowTop.setText(_translate("TextMenu", "Insert row above"))
        self.ac_RowBottom.setText(_translate("TextMenu", "Insert row below"))
        self.ac_ColumnLeft.setText(_translate("TextMenu", "Insert column left"))
        self.ac_ColumnRight.setText(_translate("TextMenu", "Insert colum right"))
        self.ac_DeleteRow.setText(_translate("TextMenu", "Delete selected row"))
        self.ac_DeleteColumn.setText(_translate("TextMenu", "Delete selected column"))
        self.ac_DeleteHyperlink.setText(_translate("TextMenu", "Delete hyperlink"))