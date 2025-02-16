from PyQt6.QtWidgets import QDialog, QTableWidgetItem, QMessageBox, QFileDialog, QToolBar, QSizePolicy
from PyQt6.QtGui import QColor, QFont, QTextCharFormat,  QTextListFormat, QAction, QIcon
from PyQt6.QtCore import QSize, pyqtSignal, pyqtSlot, Qt, QUrl, QFile, QTime, QPoint, QT_TR_NOOP as tr
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaFormat
from PyQt6 import uic
from ui.ui_toolsets import TextToolbox, PictureToolbox, AudioToolbox, TableToolbox
from tcha.elements.baseelement import BaseElement, BaseModel
from tcha.elements.audioelement import AudioModel
from tcha.resmanager import ResourceType
from pathlib import Path
from os.path import basename
import json
import unicodedata
import importlib
import abc
import asyncio

ToolBarStyleSheet = """
QToolButton::menu-indicator {image: none;}
"""


class BaseToolset(QToolBar):
    __metaclass__ = abc.ABCMeta
    requestResource = pyqtSignal()
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(50)
        self.setFloatable(False)
        self.setMovable(False)
        self.setIconSize(QSize(23, 23))
        self.setSizePolicy(
        QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.setAllowedAreas(Qt.ToolBarArea.TopToolBarArea)
        self.setStyleSheet(ToolBarStyleSheet)

    @abc.abstractmethod
    def action(self) -> QAction:
        """Returns the Action that is shown in the element menu. The action needs to have the toolset's name as data."""
        return QAction()

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Returns the name of the toolset as an identifier."""
        return ""
    
    @property
    @abc.abstractmethod
    def restype(self) -> ResourceType:
        return ResourceType

    @abc.abstractmethod
    def createElement(self, respath="") -> BaseModel:
        """Returns an element to be inserted in a cell. The element is connected to this toolset and vice versa."""
        return 
 
    @abc.abstractmethod
    def openElement(self, model: BaseModel) -> BaseElement:
        """Returns an element set with the suitable model 'model'. The element is connected to this toolset and vice versa."""
        return
    
    @abc.abstractmethod
    def getResource(self) -> str:
        return ""

def returnToolsets(parent) -> list[BaseToolset]:
    toolsets = []
    with open("tcha/toolsets.json", "r", encoding="utf-8") as f:
        names = json.load(f)
    for name in names:
        toolset = getattr(importlib.import_module("tcha.toolset"), name)
        toolset = toolset(parent)
        toolsets.append(toolset)
    return toolsets

class TableToolset(QToolBar, TableToolbox):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setUI(self)
        self.cell_editor_actions.setEnabled(False)
        self.setFixedHeight(50)
        self.setIconSize(QSize(23, 23))
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.setAllowedAreas(Qt.ToolBarArea.TopToolBarArea)
        self.setStyleSheet(ToolBarStyleSheet)

    def mousePressEvent(self, a0):
        print("Clicked")
        super().mousePressEvent(a0)

class TextToolset(BaseToolset, TextToolbox):
    fontChanged = pyqtSignal(dict)
    blist = pyqtSignal()
    numlist = pyqtSignal()
    indent = pyqtSignal()
    dedent = pyqtSignal()
    insert_table = pyqtSignal(int, int)
    insertSymbol = pyqtSignal(str)
    insertHyperlink = pyqtSignal()

    addRowT = pyqtSignal()
    addRowB = pyqtSignal()
    addColumnL = pyqtSignal()
    addColumnR = pyqtSignal()
    deleteRow = pyqtSignal()
    deleteColumn = pyqtSignal()
    deleteTable = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setUI(self)
        self._fontProperties = {}
        
        self.setAttribute(Qt.WidgetAttribute.WA_NoMousePropagation, True)
        self.connect_signals()
        self.get_all()

    def action(self) -> QAction:
        action = QAction(QIcon("resources/icons/ic_text.svg"), tr("Text"), self)
        action.setData(self.name)
        return action

    @property
    def name(self) -> str:
        return "TextToolset"
    
    @property
    def restype(self) -> ResourceType:
        return ResourceType.TEXT
    
    def getResource(self) -> str:
        return ""
    
    def createElement(self, respath="") -> BaseModel:
        model = getattr(importlib.import_module("tcha.elements.textelement"), "TextModel")
        model = model(respath)

        return model

    def connect_editor(self, editor: BaseElement) -> None:
        editor.requestTextProps.connect(self.get_all)
        editor.elementFontChanged.connect(self.set_font_props)
        editor.showTableTools.connect(self.set_table_tools_visible)

        self.fontChanged.connect(editor.set_text_format)
        self.blist.connect(lambda: editor.insert_list(QTextListFormat.Style.ListDisc))
        self.numlist.connect(lambda: editor.insert_list(QTextListFormat.Style.ListDecimal))
        self.indent.connect(lambda: editor.change_indentation(incr=1))
        self.dedent.connect(lambda: editor.change_indentation(incr=-1))
        self.insert_table.connect(editor.insert_table)
        self.insertSymbol.connect(editor.insert_symbol)
        self.insertHyperlink.connect(editor.insert_hyperlink)

        self.addRowT.connect(editor.insert_row)
        self.addRowB.connect(lambda: editor.insert_row(1))
        self.addColumnL.connect(editor.insert_column)
        self.addColumnR.connect(lambda: editor.insert_column(1))
        self.deleteRow.connect(editor.delete_row)
        self.deleteColumn.connect(editor.delete_column)
        self.deleteTable.connect(editor.delete_table)
    
    def openElement(self, model: BaseModel) -> BaseElement:
        pass
    
    def connect_signals(self):
        self.cb_Font.currentFontChanged.connect(self.get_font_family)
        self.cb_FontSize.currentIndexChanged.connect(self.get_font_size)
        self.cb_FontSize.textEntered.connect(self.get_font_size)
        self.ac_bold.toggled.connect(self.is_bold)
        self.ac_italic.toggled.connect(self.is_italic)
        self.ac_underline.toggled.connect(self.is_underlined)
        self.align_group.triggered.connect(self.alignment)
        self.veralign_group.triggered.connect(self.vertical_alignment)
        self.ac_textcolor.triggered.connect(lambda: self.get_color(self.textColor()))
        self.color_menu.colorChanged.connect(self.get_color)
        # self.color_menu2.colorChanged.connect(self.get_background_color)
        self.ac_list.triggered.connect(self.request_bullet_list)
        self.ac_numlist.triggered.connect(self.request_num_list)
        self.ac_indent.triggered.connect(self.request_indent)
        self.ac_dedent.triggered.connect(self.request_dedent)
        self.menu_table.tableSize.connect(self.request_table_insert)
        self.ac_symbol.triggered.connect(self.open_symbol_dialog)
        self.ac_hyperlink.triggered.connect(self.request_hyperlink_insert)

        self.ac_row_top.triggered.connect(self.request_add_row_top)
        self.ac_row_bottom.triggered.connect(self.request_add_row_bottom)
        self.ac_column_left.triggered.connect(self.request_add_column_left)
        self.ac_column_right.triggered.connect(self.request_add_column_right)
        self.ac_delete_row.triggered.connect(self.request_delete_row)
        self.ac_delete_column.triggered.connect(self.request_delete_column)
        self.ac_delete_table.triggered.connect(self.request_delete_table)

    def send_text_properties(self, props: dict) -> dict:
        self.fontChanged.emit(props)
        return self._fontProperties
    
    @pyqtSlot(bool)
    def set_table_tools_visible(self, visible: bool):
        self.tabletools_group.setVisible(visible)

    @pyqtSlot(dict)
    def set_font_props(self, props: dict) -> None:
        for key, value in props.items():
            match key:
                case "family":
                    font = QFont()
                    font.setFamilies(value)
                    self.cb_Font.setCurrentFont(font) # QFontComboBox
                case "size":
                    self.cb_FontSize.setEditText(str(value)) #QComboBox with point sizes
                case "bold":
                    self.ac_bold.setChecked(value) # Checkable QPushButton
                case "italic":
                    self.ac_italic.setChecked(value) # Checkable QPushButton
                case "underlined":
                    self.ac_underline.setChecked(value) # Checkable QPushButton
                case "alignment":
                    self.set_alignment(value)
                case "veralign":
                    self.set_vertical_alignment(value)
                case "color":
                    self.set_button_color(self._fontProperties["color"], value)
                # case "bcolor":
                #     self.set_bg_button_color(self._fontProperties["bcolor"], value)
            self._fontProperties[key] = value

    def get_all(self):
        self._fontProperties["family"] = self.cb_Font.currentFont().families()
        self._fontProperties["size"] = float(self.cb_FontSize.currentFontSize())
        self._fontProperties["bold"] = self.ac_bold.isChecked()
        self._fontProperties["italic"] = self.ac_italic.isChecked()
        self._fontProperties["underlined"] = self.ac_underline.isChecked()
        self._fontProperties["alignment"] = self.alignment(True)
        self._fontProperties["veralign"] = self.vertical_alignment(True)
        self._fontProperties["color"] = self.ac_textcolor.property("color")
        # self._fontProperties["bcolor"] = self.csb_BackgroundColor.color()
        self.send_text_properties(self._fontProperties)

    def get_font_family(self) -> None:
        props = {}
        props["family"] = self.cb_Font.currentFont().families()
        self.send_text_properties(props)

    def get_font_size(self) -> None:
        props = {}
        props["size"] = float(self.cb_FontSize.currentFontSize())
        self.send_text_properties(props)

    def get_color(self, color: QColor) -> None:
        props = {}
        self.set_button_color(self._fontProperties["color"], color)
        props["color"] = color
        self.send_text_properties(props)   

    # def get_background_color(self, color: QColor) -> None:
    #     props = {}
    #     self.set_bg_button_color(self._fontProperties["bcolor"], color)
    #     props["bcolor"] = color
    #     self.send_text_properties(props)               

    def set_button_color(self, old: QColor, color: QColor) -> None:
        if color != old:
            self.ac_textcolor.setProperty("color", color)
            widget = self.widgetForAction(self.ac_textcolor)
            stylesheet = widget.styleSheet()
            stylesheet = stylesheet.replace(f"border-bottom: 5px solid {old.name()};", f"border-bottom: 5px solid {color.name()};")
            widget.setStyleSheet(stylesheet)

    # def set_bg_button_color(self, old: QColor, color: QColor) -> None:
    #     if color != old:
    #         self.csb_BackgroundColor.setColor(color)
    #         ss = self.csb_BackgroundColor.lbutton.styleSheet()
    #         ss = ss.replace(f"border-bottom: 5px solid {old.name()};", f"border-bottom: 5px solid {color.name()};")
    #         self.csb_BackgroundColor.lbutton.setStyleSheet(ss)

    def textColor(self) -> QColor:
        return self.ac_textcolor.property("color")
    
    # def bg_color(self) -> QColor:
    #     return self.csb_BackgroundColor.color()

    def is_bold(self) -> None:
        props = {}
        props["bold"] = self.ac_bold.isChecked()
        self.send_text_properties(props)

    def is_italic(self) -> None: 
        props = {}
        props["italic"] = self.ac_italic.isChecked()
        self.send_text_properties(props)

    def is_underlined(self) -> None:
        props = {}
        props["underlined"] = self.ac_underline.isChecked()
        self.send_text_properties(props)

    def set_alignment(self, alignment: Qt.AlignmentFlag) -> None:
        if alignment == Qt.AlignmentFlag.AlignLeft:
            self.ac_align_left.setChecked(True)
        elif alignment == Qt.AlignmentFlag.AlignCenter:
            self.ac_align_center.setChecked(True)
        elif alignment == Qt.AlignmentFlag.AlignRight:
            self.ac_align_right.setChecked(True)
        elif alignment == Qt.AlignmentFlag.AlignJustify:
            self.ac_align_justify.setChecked(True)

    def set_vertical_alignment(self, alignment: QTextCharFormat.VerticalAlignment) -> None:
        if alignment == QTextCharFormat.VerticalAlignment.AlignSubScript:
            self.ac_subscript.setChecked(True)
        elif alignment == QTextCharFormat.VerticalAlignment.AlignSuperScript:
            self.ac_superscript.setChecked(True)
        else:
            self.ac_subscript.setChecked(False)
            self.ac_superscript.setChecked(False)

    def alignment(self, get=False) -> None | Qt.AlignmentFlag:
        props = {}
        if self.ac_align_left.isChecked():
            props["alignment"] = Qt.AlignmentFlag.AlignLeft
        elif self.ac_align_center.isChecked():
            props["alignment"] = Qt.AlignmentFlag.AlignCenter
        elif self.ac_align_right.isChecked():
            props["alignment"] = Qt.AlignmentFlag.AlignRight
        elif self.ac_align_justify.isChecked():
            props["alignment"] = Qt.AlignmentFlag.AlignJustify
        if get == True:
            return props["alignment"]
        self.send_text_properties(props)

    def vertical_alignment(self, get=False):
        props = {}
        if self.ac_superscript.isChecked():
            props["veralign"] = QTextCharFormat.VerticalAlignment.AlignSuperScript
            self.ac_subscript.setChecked(False)
        elif self.ac_subscript.isChecked():
            props["veralign"] = QTextCharFormat.VerticalAlignment.AlignSubScript
            self.ac_superscript.setChecked(False)
        else:
            props["veralign"] = QTextCharFormat.VerticalAlignment.AlignNormal
        if get == True:
            return props["veralign"]
        self.send_text_properties(props)

    def request_bullet_list(self):
        self.blist.emit()

    def request_num_list(self) -> None:
        self.numlist.emit()

    def request_indent(self) -> None:
        self.indent.emit()

    def request_dedent(self) -> None:
        self.dedent.emit()

    @pyqtSlot(int, int)
    def request_table_insert(self, line, column) -> None:
        self.insert_table.emit(line, column)

    def request_add_row_top(self) -> None:
        self.addRowT.emit()

    def request_add_row_bottom(self) -> None:
        self.addRowB.emit()

    def request_add_column_left(self) -> None:
        self.addColumnL.emit()

    def request_add_column_right(self) -> None:
        self.addColumnR.emit()

    def request_delete_row(self) -> None:
        self.deleteRow.emit()

    def request_delete_column(self) -> None:
        self.deleteColumn.emit()
        
    def request_delete_table(self) -> None:
        ok = QMessageBox.question(None, tr("Delete Table"), tr("Are you sure you want to delete the whole table?"))
        if ok == QMessageBox.StandardButton.Yes:
            self.deleteTable.emit()

    def open_symbol_dialog(self) -> None:
        dialog = SymbolDialog(self.cb_Font.currentFont().family())
        dialog.characterClicked.connect(self.send_symbol)
        dialog.show()

    def send_symbol(self, symbol: str) -> None:
        self.insertSymbol.emit(symbol)

    def request_hyperlink_insert(self) -> None:
        self.insertHyperlink.emit()

    # def hideEvent(self, e: QHideEvent) -> None:
    #     self.table_frame.hide()
    #     super().hideEvent(e)

    def sizeHint(self) -> QSize:
        return QSize(230, 180)

class SymbolDialog(QDialog):
    characterClicked = pyqtSignal(str)

    def __init__(self, fontfamily: str, parent=None, flags=Qt.WindowType.SubWindow) -> None:
        super().__init__(parent, flags)
        self.ui = uic.loadUi("ui/UI_Symbols.ui", self)
        self.chars = self.load_character_set()
        self.fontfamily = fontfamily

        self.connect_signals()
        self.import_character_sets()

    def connect_signals(self) -> None:
        self.ui.cb_category.currentTextChanged.connect(self.set_table)
        self.ui.TW_Symbols.itemClicked.connect(self.set_hex_code)
        self.ui.TW_Symbols.itemDoubleClicked.connect(self.emit_character)
        self.ui.PB_Paste.clicked.connect(self.emit_character)

    def load_character_set(self) -> dict[str, list[int]]:
        with open("tcha/unicodechart.json", "r", encoding="utf-8") as f:
            return json.load(f)
    
    def import_character_sets(self) -> None:
        for key in self.chars.keys():
            self.ui.cb_category.addItem(key)
        self.ui.cb_category.setCurrentText("Standard Character Set")

    def set_table(self, charset: str) -> None:
        self.ui.TW_Symbols.clear()
        self.ui.LB_UnicodeName.setText("")

        rows = len(self.chars[charset]) // 16
        self.ui.TW_Symbols.setColumnCount(16)
        self.ui.TW_Symbols.setRowCount(rows)

        for irow in range(self.ui.TW_Symbols.rowCount()):
            for icolumn in range(self.ui.TW_Symbols.columnCount()):
                try:
                    item = QTableWidgetItem(chr(self.chars[charset][irow * 16 + icolumn]))
                    font = QFont()
                    font.setPointSize(12)
                    font.setFamily(self.fontfamily)
                    item.setFont(font)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.ui.TW_Symbols.setItem(irow, icolumn, item)
                except IndexError:
                    break

    def set_hex_code(self, item: QTableWidgetItem) -> None:
        text = item.text()
        self.ui.LE_HexCode.setText(format(ord(text), "x").upper())
        try:
            self.ui.LB_UnicodeName.setText(unicodedata.name(text))
        except ValueError:
            self.ui.LB_UnicodeName.setText("Unknown")

    def emit_character(self) -> None:
        if self.ui.TW_Symbols.selectedItems():
            item = self.ui.TW_Symbols.selectedItems()[0]
            text = item.text()
            self.characterClicked.emit(text)

class PictureToolset(BaseToolset, PictureToolbox):
    
    sizeChanged = pyqtSignal(int, int)
    keepAspectRatio = pyqtSignal(bool)
    rotateRight = pyqtSignal()
    rotateLeft = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setUi(self)
        self._current_size = QSize(0, 0)

        self.connect_signals()
        self.setAttribute(Qt.WidgetAttribute.WA_NoMousePropagation, True)

    def action(self) -> QAction:
        action = QAction(QIcon("resources/icons/ic_newpic.svg"), tr("Picture"), self)
        action.setData(self.name)
        return action
    
    @property
    def name(self) -> str:
        return "PictureToolset"

    @property
    def restype(self) -> ResourceType:
        return ResourceType.IMAGE

    def getResource(self) -> str|None:
        path = QFileDialog.getOpenFileName(self, directory=str(Path.home()), filter=tr("Image files *.png, *.bmp *.jpeg *.jpg"))
        if path[0]:
            return path[0]
        else: 
            return None

    def createElement(self, respath="") -> BaseElement:
        model = getattr(importlib.import_module("tcha.elements.pictureelement"), "PictureModel")
        model = model(respath, 100, 100)
        return model

    def connect_editor(self, editor: BaseElement) -> None:#
        if editor:
            self.sizeChanged.connect(editor.set_size)
            self.rotateRight.connect(editor.rotate_right)
            self.rotateLeft.connect(editor.rotate_left)

            editor.imageChanged.connect(self.on_size_changed)
            editor.refresh()
    
    def openElement(self, model: BaseModel) -> BaseElement:
        return super().openElement(model)

    def connect_signals(self) -> None:
        self.sb_ImageWidth.valueChanged.connect(self.on_values_set)
        self.sb_ImageWidth.valueChanged.connect(self.on_width_set)
        self.sb_ImageHeight.valueChanged.connect(self.on_values_set)
        self.sb_ImageHeight.valueChanged.connect(self.on_height_set)
        self.ac_rotate_right.triggered.connect(self.request_rotate_right)
        self.ac_rotate_left.triggered.connect(self.request_rotate_left)

    @pyqtSlot(int, int)
    def on_size_changed(self, width: int, height: int) -> None:
        self.sb_ImageWidth.valueChanged.disconnect()
        self.sb_ImageHeight.valueChanged.disconnect()
        self.sb_ImageWidth.setValue(width)
        self.sb_ImageHeight.setValue(height)
        self._current_size = QSize(width, height)
        self.sb_ImageWidth.valueChanged.connect(self.on_values_set)
        self.sb_ImageWidth.valueChanged.connect(self.on_width_set)
        self.sb_ImageHeight.valueChanged.connect(self.on_values_set)
        self.sb_ImageHeight.valueChanged.connect(self.on_height_set)

    def on_values_set(self) -> None:
        if not self.ac_keep_aspect_ratio.isChecked():
            self.sizeChanged.emit(self.sb_ImageWidth.value(), self.sb_ImageHeight.value())
            self._current_size = QSize(self.sb_ImageWidth.value(), self.sb_ImageHeight.value())

    def on_width_set(self) -> None:
        if self.ac_keep_aspect_ratio.isChecked():
            newHeight = (self.current_size.height() / self.current_size.width()) * self.sb_ImageWidth.value()
            self.sb_ImageHeight.valueChanged.disconnect()
            self.sb_ImageHeight.setValue(int(newHeight))
            self.sb_ImageHeight.valueChanged.connect(self.on_values_set)
            self.sb_ImageHeight.valueChanged.connect(self.on_height_set)
            self.sizeChanged.emit(self.sb_ImageWidth.value(), self.sb_ImageHeight.value())
            self._current_size = QSize(self.sb_ImageWidth.value(), self.sb_ImageHeight.value())

    def on_height_set(self) -> None:
        if self.ac_keep_aspect_ratio.isChecked():
            newWidth = (self.current_size.width() / self.current_size.height()) * self.sb_ImageHeight.value()
            self.sb_ImageWidth.valueChanged.disconnect()
            self.sb_ImageWidth.setValue(int(newWidth))
            self.sb_ImageWidth.valueChanged.connect(self.on_values_set)
            self.sb_ImageWidth.valueChanged.connect(self.on_width_set)
            self.sizeChanged.emit(self.sb_ImageWidth.value(), self.sb_ImageHeight.value())
            self._current_size = QSize(self.sb_ImageWidth.value(), self.sb_ImageHeight.value())

    def request_rotate_right(self) -> None:
        self.rotateRight.emit()

    def request_rotate_left(self) -> None:
        self.rotateLeft.emit()

    @property
    def current_size(self) -> QSize:
        return self._current_size

    def sizeHint(self) -> QSize:
        return QSize(220, 100)
    
class AudioToolset(BaseToolset, AudioToolbox):
    playbackStateSet = pyqtSignal(QMediaPlayer.PlaybackState)
    modelSet = pyqtSignal(AudioModel)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setUi(self)

        self.player = QMediaPlayer()
        self.aoutput = QAudioOutput()
        self.player.setAudioOutput(self.aoutput)
        self._model = AudioModel("", "")
        self._model.repeatToggled.connect(self.ac_repeat.setChecked)
        self._model.repeatTimesChanged.connect(self.update_repeat_times)
        self.repeats = 0
        self.winding = False

        self.connect_signals()
        self.setAttribute(Qt.WidgetAttribute.WA_NoMousePropagation, True)

    def action(self) -> QAction:
        action = QAction(QIcon("resources/icons/ic_audiofile.svg"), tr("Audio File"), self)
        action.setData(self.name)
        return action

    @property
    def name(self) -> str:
        return "AudioToolset"
    
    @property
    def restype(self) -> ResourceType:
        return ResourceType.AUDIO
    
    def getResource(self) -> str | None:
        path = QFileDialog.getOpenFileName(self, directory=str(Path.home()), filter=tr("Audio files (*.mp3 *.aac *.wav *.m4a *.flac *.wma)"))
        if path[0]:
            return path[0]
        else: 
            return None
    
    def createElement(self, respath="") -> BaseModel:
        model = getattr(importlib.import_module("tcha.elements.audioelement"), "AudioModel")
        model = model(respath, basename(respath))
        return model

    def connect_editor(self, editor: BaseElement) -> None:
        print("Connect Editor to Audio Toolset")
        editor.playbackStateChanged.connect(self.set_playback_state)
        editor.playbackRequested.connect(self.set_player)

        self.playbackStateSet.connect(editor.on_playback_state_changed)
        # self.modelSet.connect(editor.on_model_set)
        self.set_player(editor.model(), False)


    def openElement(self, model: BaseModel) -> BaseElement:
        return BaseElement()

    def connect_signals(self) -> None:
        self.ac_play_pause.stateChanged.connect(self.playpause)
        self.pb_rew.doubleClicked.connect(self.reset)
        self.pb_rew.pressed.connect(lambda: asyncio.run(self.rewind()))
        self.ac_rew5.triggered.connect(lambda: self.change_position_by(-5000))
        self.pb_fwd.pressed.connect(lambda: asyncio.run(self.fast_forward()))
        self.ac_fwd5.triggered.connect(lambda: self.change_position_by(5000))
        self.ac_repeat.toggled.connect(self.on_repeat_toggled)
        self.sb_RepeatTimes.valueChanged.connect(lambda: self._model.set_repeats(self.sb_RepeatTimes.value()))
        self.sb_PauseLength.valueChanged.connect(lambda: self._model.set_pause_length(self.sb_PauseLength.value()))
        self.te_StartTime.timeChanged.connect(lambda: self._model.set_start_time(self.on_start_time_changed()))
        self.te_EndTime.timeChanged.connect(lambda: self._model.set_end_time(self.on_end_time_changed()))
        self.hs_PlayTime.sliderMoved.connect(self.on_slider_moved)
        self.player.durationChanged.connect(self.set_track_length)
        self.player.positionChanged.connect(self.set_current_position)
        self.player.playbackStateChanged.connect(self.on_playback_state_changed)
        self.player.mediaStatusChanged.connect(self.print_player_notifications)
        self.player.errorChanged.connect(self.print_player_notifications)

    def print_player_notifications(self) -> None:
        print("Notification: ", self.player.mediaStatus(), "with", self.player.source())
        print("Error: ", self.player.error(), self.player.errorString())

    def set_player(self, model: AudioModel, play: bool) -> None:
        if model == self._model:
            return
        else:
            self.set_playback_state(QMediaPlayer.PlaybackState.StoppedState)
            self._model.disconnect()
            self._model = model
            print("Audio Toolset has new model:", self._model)
            self.modelSet.emit(model)
            self.on_model_set()
            if play:
                self.set_playback_state(QMediaPlayer.PlaybackState.PlayingState)

    def on_model_set(self) -> None:
        print("Applying model's properties")
        self._verify_audio_file(self._model.resource)
        self._model.repeatToggled.connect(self.ac_repeat.setChecked)
        self._model.repeatTimesChanged.connect(self.update_repeat_times)
        self.player.setSource(QUrl.fromLocalFile(self._model.resource))
        self.repeats = self._model.repeats
        self.ac_repeat.setChecked(self._model.is_repeating)
        self.sb_RepeatTimes.disconnect()
        self.sb_RepeatTimes.setValue(self._model.repeats)
        self.sb_RepeatTimes.valueChanged.connect(lambda: self._model.set_repeats(self.sb_RepeatTimes.value()))
        self.sb_PauseLength.disconnect()
        self.sb_PauseLength.setValue(self._model.pause_length)
        self.sb_PauseLength.valueChanged.connect(lambda: self._model.set_pause_length(self.sb_PauseLength.value()))
        print("Properties", self.player.duration(), self._model)
        print("Notification: ", self.player.mediaStatus(), "with", self.player.source())
        print("Error: ", self.player.error(), self.player.errorString())

    def _verify_audio_file(self, path):
        print("=== File Verification ===")
        file = QFile(path)
        print(f"Path: {path}")
        print(f"Exists: {file.exists()}")
        if file.open(QFile.OpenModeFlag.ReadOnly):
            print(f"Size: {file.size()} bytes")
            print(f"Readable: True")
            file.close()
        
    def set_track_length(self) -> None:
        print("Duration: ", self.player.duration())
        self.hs_PlayTime.setMaximum(self.player.duration())
        self.hs_PlayTime.setTickInterval(self.player.duration()//100)
        self.te_PlayTime.setMaximumTime(QTime().fromMSecsSinceStartOfDay(self.player.duration()))
        self.set_start_end_time(self._model.start_time, self.player.duration() - self._model.end_time)

    def set_start_end_time(self, start: int, end: int) -> None:
        print(start, end)
        self.te_StartTime.setMinimumTime(QTime(0, 0, 0))
        self.te_EndTime.setMaximumTime(self.te_PlayTime.maximumTime())
        self.te_StartTime.setTime(QTime.fromMSecsSinceStartOfDay(start))
        self.te_EndTime.setTime(QTime.fromMSecsSinceStartOfDay(end))

    def set_current_position(self, duration: int) -> None:
        if not self.hs_PlayTime.isSliderDown():
            self.hs_PlayTime.setSliderPosition(duration)
            self.te_PlayTime.setTime(QTime(0, 0, 0).addMSecs(duration))
            if self._model.end_time > 0 and self.player.position() // 100 == (self.player.duration() - self._model.end_time) // 100:
                print("Stopping now!")
                self.set_playback_state(QMediaPlayer.PlaybackState.StoppedState)

    def on_playback_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        print(f"Changed to PlayBackState {state}")
        if state is QMediaPlayer.PlaybackState.StoppedState:
            self.ac_play_pause.changeState(1)
            self.player.setPosition(0)
            asyncio.run(self.on_stop())
        elif state is QMediaPlayer.PlaybackState.PlayingState:
            self.ac_play_pause.changeState(2)
            self.on_play()
        elif state is QMediaPlayer.PlaybackState.PausedState:
            self.ac_play_pause.changeState(1)
        self.playbackStateSet.emit(state) 

    def set_playback_state(self, state: QMediaPlayer.PlaybackState) -> None:
        """Sets player's 'PlayerbackState'"""
        print(f"Got PlayBackState {state}")
        if state is QMediaPlayer.PlaybackState.StoppedState:
            self.player.stop()
        elif state is QMediaPlayer.PlaybackState.PlayingState:
            self.player.play()
        elif state is QMediaPlayer.PlaybackState.PausedState:
            self.player.pause() 

    def play_(self) -> None:
        if self.player.bufferProgress() == 1.0:
            self.player.play()
        else: 
            self.play_()

    def on_slider_moved(self) -> None:
        self.player.setPosition(self.hs_PlayTime.sliderPosition())

    async def on_stop(self) -> None:
        if self._model.is_repeating:
            if self.repeats > 0:
                print("Repeating")
                self.repeats -= 1
                await asyncio.sleep(float(self._model.pause_length))
                self.set_playback_state(QMediaPlayer.PlaybackState.PlayingState)
            else:
                self.repeats = self._model.repeats

    def on_play(self) -> None:
        if self.player.position() < self._model.start_time:
            self.player.setPosition(self._model.start_time)

    def on_repeat_toggled(self, state: bool) -> None:
        self._model.set_repeating(state)
        self.sb_RepeatTimes.setEnabled(state)
        self.sb_PauseLength.setEnabled(state)

    def update_repeat_times(self, times: int) -> None:
        print(f"Set repeat for {times} times")
        self.repeats = times

    def on_start_time_changed(self) -> int:
        return self.te_StartTime.time().msecsSinceStartOfDay()
    
    def on_end_time_changed(self) -> int:
        print("Ending at ", self.player.duration() - (self.player.duration() - self.te_EndTime.time().msecsSinceStartOfDay()))
        return self.player.duration() - self.te_EndTime.time().msecsSinceStartOfDay()

    def resetStartEndTime(self) -> None:
        self.te_StartTime.setTime(QTime(0, 0, 0))
        self.te_EndTime.setTime(QTime.fromMSecsSinceStartOfDay(self.te_PlayTime.maximumTime().msecsSinceStartOfDay()))

    def playpause(self) -> None:
        if self.ac_play_pause.state() == 2:
            self.set_playback_state(QMediaPlayer.PlaybackState.PlayingState)
        elif self.ac_play_pause.state() == 1:
            self.set_playback_state(QMediaPlayer.PlaybackState.PausedState)

    def change_position_by(self, msec: int) -> None:
        self.player.setPosition(self.player.position() + msec)

    async def rewind(self) -> None:
        self.player.setPosition(self.player.position()-1000)
        await asyncio.sleep(0.1)

    async def fast_forward(self) -> None:
        self.player.setPosition(self.player.position()+1000)
        await asyncio.sleep(0.1)

    def reset(self) -> None:
        self.repeats = 0
        self.set_playback_state(QMediaPlayer.PlaybackState.StoppedState)
        self.repeats = self._model.repeats

    def hideEvent(self, a0):
        self.player.pause()
        super().hideEvent(a0)

    def sizeHint(self) -> QSize:
        return QSize(240, 160)