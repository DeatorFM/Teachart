from PyQt6 import QtWidgets, QtGui, QtCore
from ui.UI_Commons import *
from ui.StyledWidget import *
from enum import Enum

class CellActions(Enum):
    Remove_Element = 0
    Move_Up = 1
    Move_Down = 2

class ElementOptions(QtWidgets.QMenu):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("ElementOptions")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("resources/icons/ic_trash.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self._ac_remove = self.addAction(icon1, "")
        self._ac_remove.setData(CellActions.Remove_Element)

        self.addSeparator()

        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("resources/icons/ic_move_up.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self._ac_moveup = self.addAction(icon2, "")
        self._ac_moveup.setData(CellActions.Move_Up)

        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap("resources/icons/ic_move_down.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self._ac_movedown = self.addAction(icon3, "")
        self._ac_movedown.setData(CellActions.Move_Down)      

        self.retranslateUi()

    def retranslateUi(self) -> None:
        _translate = QtCore.QCoreApplication.translate
        self._ac_remove.setText(_translate("ElementOptions", "Remove element"))
        self._ac_moveup.setText(_translate("ElementOptions", "Move element up"))
        self._ac_movedown.setText(_translate("ElementOptions", "Move element down"))

class TableToolbox:

    def setUI(self, agent: QtWidgets.QToolBar) -> None:
        agent.setObjectName("TableToolset")
        self.cell_editor_actions = QtGui.QActionGroup(agent)

        self.ac_add_element = agent.addAction("")
        self.cell_editor_actions.addAction(self.ac_add_element)

        sep = agent.addSeparator()    
        self.cell_editor_actions.addAction(sep)
        
        self.menu_element = QtWidgets.QMenu(agent)
        self.ac_FromClipboard = self.menu_element.addAction("")
        self.ac_FromClipboard.setEnabled(False)
        self.ac_FromClipboard.setData("Clipboard")

        self.menu_element.addSeparator()

        agent.widgetForAction(self.ac_add_element).setMenu(self.menu_element)
        agent.widgetForAction(self.ac_add_element).setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)

        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("resources/icons/ic_insertRowBottom.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_new_row = agent.addAction(icon1, None)
        self.cell_editor_actions.addAction(self.ac_new_row)

        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("resources/icons/ic_insertColumnRight.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_new_column = agent.addAction(icon2, None)
        self.cell_editor_actions.addAction(self.ac_new_column)

        agent.addSeparator()

        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap("resources/icons/ic_deleterow.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_delete_row = agent.addAction(icon3, None)
        self.cell_editor_actions.addAction(self.ac_delete_row)

        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap("resources/icons/ic_deletecolumn.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_delete_column = agent.addAction(icon4, None)
        self.cell_editor_actions.addAction(self.ac_delete_column)

        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap("resources/icons/ic_notpinned.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap("resources/icons/ic_pinned.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_lock_size = SwitchAction(icon5, icon6, agent)
        agent.addAction(self.ac_lock_size)
        self.cell_editor_actions.addAction(self.ac_lock_size)
    
        self.retranslateUi()
  

    def retranslateUi(self) -> None:
        _translate = QtCore.QCoreApplication.translate
        self.ac_add_element.setText(_translate("TableToolset", "Add to cell"))
        self.ac_FromClipboard.setText(_translate("TableToolset", "From Clipboard"))
        

class TextToolbox:

    def setUI(self, agent: QtWidgets.QToolBar) -> None:
        agent.setObjectName("TextToolset")

        self.ac_element_options = agent.addAction("")
        self.element_options_menu = ElementOptions(agent)
        widget = agent.widgetForAction(self.ac_element_options)
        widget.setMenu(self.element_options_menu)
        widget.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)

        self.cb_Font = QtWidgets.QFontComboBox(agent)
        self.cb_Font.setMaximumSize(QtCore.QSize(120, 25))
        self.cb_Font.setObjectName("CB_Font")
        
        agent.addWidget(self.cb_Font)

        self.cb_FontSize = FontSizeBox(agent)
        self.cb_FontSize.setMinimumSize(QtCore.QSize(55, 25))
        self.cb_FontSize.setEditable(True)
        self.cb_FontSize.setObjectName("CB_FontSize")
        self.cb_FontSize.setContentsMargins(5, 0, 5, 0)
        agent.addWidget(self.cb_FontSize)

        agent.addSeparator()

        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("resources/icons/ic_bold.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_bold = agent.addAction(icon1, None)
        self.ac_bold.setCheckable(True)

        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("resources/icons/ic_italic.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_italic = agent.addAction(icon2, None)
        self.ac_italic.setCheckable(True)

        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap("resources/icons/ic_underline.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_underline = agent.addAction(icon3, None)
        self.ac_underline.setCheckable(True)

        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap("resources/icons/ic_textcolor.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_textcolor = agent.addAction(icon4, None)
        self.ac_textcolor.setObjectName("TextColor")
        self.ac_textcolor.setProperty("color", QtGui.QColor("#000000"))
       
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
        self.color_menu = ColorMenu(convertColors(textcolors), agent)
        action_widget = agent.widgetForAction(self.ac_textcolor)
        action_widget.setMenu(self.color_menu)
        action_widget.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        action_widget.setStyleSheet(fromStyle("TB_textcolor"))
        
        agent.addSeparator()
        
        self.veralign_group = QtGui.QActionGroup(agent)
        self.veralign_group.setExclusive(False)

        icon7 = QtGui.QIcon()
        icon7.addPixmap(QtGui.QPixmap("resources/icons/ic_subscript.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_subscript = agent.addAction(icon7, None)
        self.ac_subscript.setCheckable(True)
        self.veralign_group.addAction(self.ac_subscript)
        
        icon8 = QtGui.QIcon()
        icon8.addPixmap(QtGui.QPixmap("resources/icons/ic_superscript.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_superscript = agent.addAction(icon8, None)
        self.ac_superscript.setCheckable(True)
        self.veralign_group.addAction(self.ac_superscript)

        agent.addSeparator()

        self.align_group = QtGui.QActionGroup(agent)
        self.align_group.setExclusive(True)

        icon9 = QtGui.QIcon()
        icon9.addPixmap(QtGui.QPixmap("resources/icons/ic_alignleft.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_align_left = agent.addAction(icon9, None)
        self.ac_align_left.setCheckable(True)
        self.ac_align_left.setChecked(True)
        self.align_group.addAction(self.ac_align_left)

        icon10 = QtGui.QIcon()
        icon10.addPixmap(QtGui.QPixmap("resources/icons/ic_aligncenter.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_align_center = agent.addAction(icon10, None)
        self.ac_align_center.setCheckable(True)
        self.align_group.addAction(self.ac_align_center)

        icon11 = QtGui.QIcon()
        icon11.addPixmap(QtGui.QPixmap("resources/icons/ic_alignright.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_align_right = agent.addAction(icon11, None)
        self.ac_align_right.setCheckable(True)
        self.align_group.addAction(self.ac_align_right)

        icon12 = QtGui.QIcon()
        icon12.addPixmap(QtGui.QPixmap("resources/icons/ic_alignjustify.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_align_justify = agent.addAction(icon12, None)
        self.ac_align_justify.setCheckable(True)
        self.align_group.addAction(self.ac_align_justify)

        agent.addSeparator()

        icon13 = QtGui.QIcon()
        icon13.addPixmap(QtGui.QPixmap("resources/icons/ic_list.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_list = agent.addAction(icon13, None)

        icon14 = QtGui.QIcon()
        icon14.addPixmap(QtGui.QPixmap("resources/icons/ic_numlist.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_numlist = agent.addAction(icon14, None)

        icon15 = QtGui.QIcon()
        icon15.addPixmap(QtGui.QPixmap("resources/icons/ic_dedent.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_dedent = agent.addAction(icon15, None)

        icon16 = QtGui.QIcon()
        icon16.addPixmap(QtGui.QPixmap("resources/icons/ic_indent.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_indent = agent.addAction(icon16, None)

        agent.addSeparator()

        icon17 = QtGui.QIcon()
        icon17.addPixmap(paintIcon("resources/icons/ic_table.svg", QColor("#a0a0a0")), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_table = agent.addAction(icon17, None)
        self.menu_table = TableMenu(self)
        agent.widgetForAction(self.ac_table).setMenu(self.menu_table)
        agent.widgetForAction(self.ac_table).setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)

        icon18 = QtGui.QIcon()
        icon18.addPixmap(paintIcon("resources/icons/ic_symbol.svg", QColor("#a0a0a0")), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_symbol = agent.addAction(icon18, None)

        icon19 = QtGui.QIcon()
        icon19.addPixmap(paintIcon("resources/icons/ic_hyperlink.svg", QColor("#a0a0a0")), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_hyperlink = agent.addAction(icon19, None)

        self.tabletools_group = QtGui.QActionGroup(self)

        seperator1 = agent.addSeparator()
        self.tabletools_group.addAction(seperator1)
        
        icon20 = QtGui.QIcon()
        icon20.addPixmap(QtGui.QPixmap("resources/icons/ic_insertRowBottom.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_row_bottom = agent.addAction(icon20, None)
        self.tabletools_group.addAction(self.ac_row_bottom)

        icon21 = QtGui.QIcon()
        icon21.addPixmap(QtGui.QPixmap("resources/icons/ic_insertRowTop.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_row_top = agent.addAction(icon21, None)
        self.tabletools_group.addAction(self.ac_row_top)

        icon22 = QtGui.QIcon()
        icon22.addPixmap(QtGui.QPixmap("resources/icons/ic_insertColumnRight.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_column_right = agent.addAction(icon22, None)
        self.tabletools_group.addAction(self.ac_column_right)

        icon23 = QtGui.QIcon()
        icon23.addPixmap(QtGui.QPixmap("resources/icons/ic_insertColumnLeft.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_column_left = agent.addAction(icon23, None)
        self.tabletools_group.addAction(self.ac_column_left)

        seperator2 = agent.addSeparator()
        self.tabletools_group.addAction(seperator2)

        icon24 = QtGui.QIcon()
        icon24.addPixmap(QtGui.QPixmap("resources/icons/ic_deleterow.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_delete_row = agent.addAction(icon24, None)
        self.tabletools_group.addAction(self.ac_delete_row)

        icon25 = QtGui.QIcon()
        icon25.addPixmap(QtGui.QPixmap("resources/icons/ic_deletecolumn.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_delete_column = agent.addAction(icon25, None)
        self.tabletools_group.addAction(self.ac_delete_column)

        icon26 = QtGui.QIcon()
        icon26.addPixmap(QtGui.QPixmap("resources/icons/ic_deletetable.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_delete_table = agent.addAction(icon26, None)
        self.tabletools_group.addAction(self.ac_delete_table)

        self.tabletools_group.setVisible(False)

        self.retranslateUi()


    def retranslateUi(self) -> None:
        _translate = QtCore.QCoreApplication.translate
        self.ac_element_options.setText(_translate("TextToolbox", "Text"))
        self.ac_bold.setToolTip(_translate("TextToolbox", "Bold"))
        self.ac_italic.setToolTip(_translate("TextToolbox", "Italic"))
        self.ac_underline.setToolTip(_translate("TextToolbox", "Underline"))
        self.ac_textcolor.setToolTip(_translate("TextToolbox", "Choose text colour"))
        self.ac_align_left.setToolTip(_translate("TextToolbox", "Align left"))
        self.ac_align_center.setToolTip(_translate("TextToolbox", "Centre"))
        self.ac_align_right.setToolTip(_translate("TextToolbox", "Align right"))
        self.ac_align_justify.setToolTip(_translate("TextToolbox", "Justify"))
        self.ac_subscript.setToolTip(_translate("TextToolbox", "Subscript"))
        self.ac_superscript.setToolTip(_translate("TextToolbox", "Superscript"))
        self.ac_list.setToolTip(_translate("TextToolbox", "Create bulleted list"))
        self.ac_numlist.setToolTip(_translate("TextToolbox", "Create a numbered list"))
        self.ac_dedent.setToolTip(_translate("TextToolbox", "Decrease indent"))
        self.ac_indent.setToolTip(_translate("TextToolbox", "Increase indent"))
        self.ac_table.setToolTip(_translate("TextToolbox", "Insert table"))
        self.ac_symbol.setToolTip(_translate("TextToolbox", "Insert symbol"))
        self.ac_hyperlink.setToolTip(_translate("TextToolset", "Insert hyperlink"))
        self.ac_row_bottom.setToolTip(_translate("TextToolbox", "Insert row below"))
        self.ac_row_top.setToolTip(_translate("TextToolbox", "Insert row above"))
        self.ac_column_right.setToolTip(_translate("TextToolbox", "Insert column right"))
        self.ac_column_left.setToolTip(_translate("TextToolbox", "Insert column left"))
        self.ac_delete_row.setToolTip(_translate("TextToolbox", "Delete selected row"))
        self.ac_delete_column.setToolTip(_translate("TextToolbox", "Delete selected column"))
        self.ac_delete_table.setToolTip(_translate("TextToolbox", "Delete Table"))

class PictureToolbox:

    def setUi(self, agent: QtWidgets.QToolBar):
        agent.setObjectName("PictureToolset")

        self.ac_element_options = agent.addAction("")
        self.element_options_menu = ElementOptions(agent)
        widget = agent.widgetForAction(self.ac_element_options)
        widget.setMenu(self.element_options_menu)
        widget.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)

        self.ac_width_label = agent.addAction("")
        self.ac_width_label.setDisabled(True)

        self.sb_ImageWidth = QtWidgets.QSpinBox(agent)
        self.sb_ImageWidth.setMaximum(16000)
        self.sb_ImageWidth.setObjectName("SB_ImageWidth")
        self.sb_ImageWidth.setMinimumWidth(50)
        agent.addWidget(self.sb_ImageWidth)

        self.ac_height_label = agent.addAction("")
        self.ac_height_label.setDisabled(True)

        self.sb_ImageHeight = QtWidgets.QSpinBox(agent)
        self.sb_ImageHeight.setMaximum(16000)
        self.sb_ImageHeight.setObjectName("SB_ImageHeight")
        agent.addWidget(self.sb_ImageHeight)

        agent.addSeparator()

        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("resources/icons/ic_link.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_keep_aspect_ratio = agent.addAction(icon1, None)
        self.ac_keep_aspect_ratio.setCheckable(True)
        self.ac_keep_aspect_ratio.setChecked(True)


        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("resources/icons/ic_rotateRight.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_rotate_right = agent.addAction(icon2, None)

        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap("resources/icons/ic_rotateLeft.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)  
        self.ac_rotate_left = agent.addAction(icon3, None)   

        self.retranslateUi()

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.ac_element_options.setText(_translate("PictureToolset", "Picture"))
        self.ac_width_label.setText(_translate("PictureToolset", "Width"))
        self.ac_height_label.setText(_translate("PictureToolset", "Height"))
        self.ac_keep_aspect_ratio.setToolTip(_translate("PictureToolset", "Keep aspect ratio when changing values"))
        self.ac_rotate_right.setToolTip(_translate("PictureToolset", "Rotate right 90°"))
        self.ac_rotate_left.setToolTip(_translate("PictureToolset", "Rotate left 90°"))

class AudioToolbox:

    def setUi(self, agent: QtWidgets.QToolBar):
        agent.setObjectName("AudioToolset")

        self.ac_element_options = agent.addAction("")
        self.element_options_menu = ElementOptions(agent)
        widget = agent.widgetForAction(self.ac_element_options)
        widget.setMenu(self.element_options_menu)
        widget.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)

        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("resources/icons/ic_play.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("resources/icons/ic_pause.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_play_pause = SwitchAction(icon1, icon2, agent)
        agent.addAction(self.ac_play_pause)

        self.hs_PlayTime = QtWidgets.QSlider(agent) 
        self.hs_PlayTime.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.hs_PlayTime.setObjectName("hs_PlayTime")
        agent.addWidget(self.hs_PlayTime)

        self.te_PlayTime = QtWidgets.QTimeEdit(agent)
        self.te_PlayTime.setObjectName("sb_PlayTime")
        self.te_PlayTime.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.te_PlayTime.setDisplayFormat("h:mm:ss")
        agent.addWidget(self.te_PlayTime)

        self.pb_rew = DoubleClickButton(agent)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap("resources/icons/ic_rew.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_rew.setIcon(icon3)
        # self.pb_rew.setIconSize(QtCore.QSize(20, 20))
        self.pb_rew.setAutoRepeat(True)
        self.pb_rew.setObjectName("pb_Rew")
        agent.addWidget(self.pb_rew)

        self.pb_fwd = QtWidgets.QPushButton(agent)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap("resources/icons/ic_fwd.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pb_fwd.setIcon(icon4)
        # self.pb_fwd.setIconSize(QtCore.QSize(20, 20))
        self.pb_fwd.setAutoRepeat(True)
        self.pb_fwd.setObjectName("pb_Fwd")
        agent.addWidget(self.pb_fwd)

        agent.addSeparator()

        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap("resources/icons/ic_rew5.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_rew5 = agent.addAction(icon5, None)

        # self.pb_rew10 = QtWidgets.QPushButton(self.audio_frame)
        # self.pb_rew10.setMaximumSize(QtCore.QSize(22, 22))
        # self.pb_rew10.setText("")
        # icon3 = QtGui.QIcon()
        # icon3.addPixmap(QtGui.QPixmap("resources/icons/ic_rew10.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        # self.pb_rew10.setIcon(icon3)
        # self.pb_rew10.setIconSize(QtCore.QSize(20, 20))
        # self.pb_rew10.setObjectName("pb_Rew10")
        # self.row2.addWidget(self.pb_rew10)

        # self.pb_rew30 = QtWidgets.QPushButton(self.audio_frame)
        # self.pb_rew30.setMaximumSize(QtCore.QSize(22, 22))
        # self.pb_rew30.setText("")
        # icon4 = QtGui.QIcon()
        # icon4.addPixmap(QtGui.QPixmap("resources/icons/ic_rew30.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        # self.pb_rew30.setIcon(icon4)
        # self.pb_rew30.setIconSize(QtCore.QSize(20, 20))
        # self.pb_rew30.setObjectName("pb_Rew30")
        # self.row2.addWidget(self.pb_rew30)

        # self.pb_fwd30 = QtWidgets.QPushButton(self.audio_frame)
        # self.pb_fwd30.setMaximumSize(QtCore.QSize(22, 22))
        # self.pb_fwd30.setText("")
        # icon5 = QtGui.QIcon()
        # icon5.addPixmap(QtGui.QPixmap("resources/icons/ic_fwd30.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        # self.pb_fwd30.setIcon(icon5)
        # self.pb_fwd30.setIconSize(QtCore.QSize(20, 20))
        # self.pb_fwd30.setObjectName("pb_Fwd30")
        # self.row2.addWidget(self.pb_fwd30)

        # self.pb_fwd10 = QtWidgets.QPushButton(self.audio_frame)
        # self.pb_fwd10.setMaximumSize(QtCore.QSize(22, 22))
        # self.pb_fwd10.setText("")
        # icon6 = QtGui.QIcon()
        # icon6.addPixmap(QtGui.QPixmap("resources/icons/ic_fwd10.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        # self.pb_fwd10.setIcon(icon6)
        # self.pb_fwd10.setIconSize(QtCore.QSize(20, 20))
        # self.pb_fwd10.setObjectName("pb_Fwd10")
        # self.row2.addWidget(self.pb_fwd10)

        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap("resources/icons/ic_fwd5.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_fwd5 = agent.addAction(icon6, None)

        agent.addSeparator()

        icon7 = QtGui.QIcon()
        icon7.addPixmap(QtGui.QPixmap("resources/icons/ic_repeat.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ac_repeat = agent.addAction(icon7, None)
        self.ac_repeat.setCheckable(True)

        self.sb_RepeatTimes = QtWidgets.QSpinBox(agent)
        self.sb_RepeatTimes.setObjectName("sb_RepeatTimes")
        self.sb_RepeatTimes.setMinimum(1)
        self.sb_RepeatTimes.setDisabled(True)
        agent.addWidget(self.sb_RepeatTimes)

        self.ac_pause_length_label = agent.addAction("")
        self.ac_pause_length_label.setDisabled(True)

        self.sb_PauseLength = QtWidgets.QSpinBox(agent)
        self.sb_PauseLength.setObjectName("sb_PauseLength")
        self.sb_PauseLength.setMinimum(0)
        self.sb_PauseLength.setDisabled(True)
        agent.addWidget(self.sb_PauseLength)

        agent.addSeparator()

        self.ac_start_label = agent.addAction("")
        self.ac_start_label.setDisabled(True)

        self.te_StartTime = QtWidgets.QTimeEdit(agent)
        self.te_StartTime.setObjectName("te_StartTime")
        self.te_StartTime.setDisplayFormat("h:mm:ss")
        agent.addWidget(self.te_StartTime)

        self.ac_end_label = agent.addAction("")
        self.ac_end_label.setDisabled(True)

        self.te_EndTime = QtWidgets.QTimeEdit(agent)
        self.te_EndTime.setObjectName("te_StartTime")
        self.te_EndTime.setDisplayFormat("h:mm:ss")
        agent.addWidget(self.te_EndTime)

        self.retranslateUi()
 
    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.ac_element_options.setText(_translate("AudioToolset", "Audio"))
        self.ac_play_pause.setToolTip(_translate("AudioToolset", "Play/Pause track."))
        self.pb_rew.setToolTip(_translate("AudioToolset", "Hold to rewind or double click reset playback."))
        self.ac_rew5.setToolTip(_translate("AudioToolset", "Rewind 5 seconds."))
        self.ac_fwd5.setToolTip(_translate("AudioToolset", "Forward 5 seconds."))
        self.pb_fwd.setToolTip(_translate("AudioToolset", "Hold to move fast forward."))
        self.sb_RepeatTimes.setSuffix(_translate("AudioToolset", "times"))
        self.ac_pause_length_label.setText(_translate("AudioToolset", "Pause Length"))
        self.sb_PauseLength.setSuffix(_translate("AudioToolset", "s"))
        self.sb_PauseLength.setToolTip(_translate("AudioToolset", "Sets the pause length between repeats"))
        self.ac_start_label.setText(_translate("AudioToolset", "Start"))
        self.ac_end_label.setText(_translate("AudioToolset", "Stop"))


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