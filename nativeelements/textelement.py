from typing import Protocol, Self, Type
import webbrowser
import json
import unicodedata

from PyQt6.QtWidgets import QSizePolicy, QInputDialog, QMessageBox, QMenu, QApplication, QWidget, QDialog, QStyleOptionViewItem, QStyle, QTableWidgetItem, QAbstractItemDelegate
from PyQt6.QtGui import (QKeyEvent, QColor, QFont, QTextListFormat, QTextCursor,  QMouseEvent, QTextLength, QTextCharFormat, 
                         QContextMenuEvent, QTextDocument, QPainter, QPen, QAction, QIcon, QTextTableFormat)
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt, QSize, QPoint, QMimeData, QXmlStreamWriter, QXmlStreamAttributes, QModelIndex, QRect, QT_TR_NOOP as tr
from PyQt6 import uic

from ui.element_toolsets import ElementOptions, TextToolsetView
from nativeelements.baseelement import BaseElementDelegate, BaseElementToolset, BaseTextElementEditor, BaseElementModel, BaseElementDefinitions, ResourceObject, ResourceType
from nativeelements.views import TextEditorMenuView
from tcha.settings import Settings, Locale


class TextElement(Protocol):
    ...

class TextDelegate(Protocol):
    ...

class TextModel(QTextDocument, BaseElementModel):

    def __init__(self, resource: ResourceObject, parent=None) -> None:
        super().__init__(parent)
        self._resource = resource
        self._resource.add_member()
        self._resource.set_extension("html")
        self._resource.set_datalink(lambda: self.toHtml().encode())
        self.setDefaultStyleSheet("p {background-color: white;}")

    def xml(self, writer: QXmlStreamWriter) -> QXmlStreamWriter:
        writer.writeEmptyElement("element")
        writer.writeAttribute("type", "TextElement")
        writer.writeAttribute("file", self._resource.filename())
        return writer
    
    @classmethod
    def read(cls: Self, xml: QXmlStreamAttributes, resobj: ResourceObject) -> Self:
        model = cls(resobj)
        html = resobj.get_data().decode("utf-8")
        model.setHtml(html)
        return model
    
    @staticmethod
    def restype() -> ResourceType:
        return ResourceType.TEXT
    
    @property
    def name(self) -> str:
        return "TextElement"
    
    def expected_size(self, width: int) -> QSize:
        self.setTextWidth(float(width))
        self.setDocumentMargin(3.0)
        size = self.size().toSize()
        return size
    
    def editable(self) -> bool:
        return True
    
    def delegate(self, toolset: BaseElementToolset, parent=None) -> TextDelegate:
        return TextDelegate(toolset, parent)
    
    def change_on_mouse_hover(self) -> bool:
        return False

    def close(self) -> None:
        self._resource.delete_member()
        self._resource = None

class TextEditor(BaseTextElementEditor):
    requestTextProps = pyqtSignal()
    elementFontChanged = pyqtSignal(dict)
    showTableTools = pyqtSignal(bool)

    def __init__(self, model: TextModel, parent=None) -> None:
        super().__init__(parent)
        self.setDocument(model)

        # Attributes
        self.type_lang = Locale[Settings.qsettings().value("User/language")]
        self.last_char: str
        self.last_format: dict = {
            "family": ["Calibri"], 
            "size": 10.0, 
            "bold": False, 
            "italic": False, 
            "underlined": False, 
            "color": QColor("#000000"),
            }
        

        # Initial routines
        self.set_text_format(self.last_format)
        self.requestTextProps.emit()
        self.default_format = self.last_format
        self.menu = TextEditorMenu(self)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoMousePropagation, True)
        self.setMouseTracking(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)
        self.set_default_cursor()
        self.connect_signals()

    @property
    def toolset(self) -> str:
        return "TextToolset"
    
    @property
    def model(self) -> TextModel:
        return self.document()

    def connect_signals(self) -> None:
        self.cursorPositionChanged.connect(self.on_cursor_position_changed)

        self.menu.fontChanged.connect(self.set_text_format)
        self.menu.fontChanged.connect(self.to_toolset)

        self.menu.ui.ac_RowTop.triggered.connect(self.insert_row)
        self.menu.ui.ac_RowBottom.triggered.connect(lambda: self.insert_row(1))
        self.menu.ui.ac_ColumnLeft.triggered.connect(self.insert_column)
        self.menu.ui.ac_ColumnRight.triggered.connect(lambda: self.insert_column(1))
        self.menu.ui.ac_DeleteRow.triggered.connect(self.delete_row)
        self.menu.ui.ac_DeleteColumn.triggered.connect(self.delete_column)
        self.menu.ui.ac_DeleteHyperlink.triggered.connect(self.delete_hyperlink)
        self.menu.ui.ac_Copy.triggered.connect(self.copy)
        self.menu.ui.ac_Cut.triggered.connect(self.cut)
        self.menu.ui.ac_Paste.triggered.connect(self.paste)

        # self.document().contentsChanged.connect(self.fit_to_text)
        self.document().blockCountChanged.connect(self.on_new_block)

    def set_default_cursor(self) -> None:
        """Sets initial cursor settings"""
        self.setTextColor(QColor().fromString("#000000"))
        self.setTextBackgroundColor(QColor("#ffffff"))
    
    @pyqtSlot(dict)
    def set_text_format(self, props: dict) -> None:
        """Gets signal from the editor when the font properties are changed by the user"""
        self.setFocus()

        cformat = QTextCharFormat()
        for key, value in props.items():
            self.last_format[key] = value
            
            match key:
                case "family":
                    cformat.setFontFamilies(value)
                case "size":
                    cformat.setFontPointSize(self.allowed_font_size(value))
                case "bold":
                    cformat.setFontWeight(self.bool_to_weight(value))
                case "italic":
                    cformat.setFontItalic(value)
                case "underlined":
                    cformat.setFontUnderline(value)
                case "alignment":
                    self.setAlignment(value)
                case "veralign":
                    cformat.setVerticalAlignment(value)
                case "color":
                    cformat.setForeground(value)
                # case "bcolor":
                #     cformat.setBackground(value)

        self.mergeCurrentCharFormat(cformat)
        # self.fit_to_text()

    def bool_to_weight(self, bold: bool) -> QFont.Weight:
        if bold:
            return QFont.Weight.Bold
        else:
            return QFont.Weight.Normal

    def allowed_font_size(self, point: float) -> float:
        """Prevents that font size is larger than width"""
        if point*(4/3) > self.width():
            return round(self.width()*0.75 - 5, 1)
        else:
            if self.width() >= 100:
                self.setMinimumWidth(int(point*(4/3))+5)
            return point

    def to_toolset(self, props: dict) -> None:
        self.elementFontChanged.emit(props)

    def keyPressEvent(self, e: QKeyEvent) -> None:        
        self.last_char = e.text()
        # print("Last Character: ", repr(self.last_char))

        if self.textCursor().currentList():
            if e.key() == Qt.Key.Key_Tab:
                self.change_indentation()
                return None
            elif e.key() == Qt.Key.Key_Backtab:
                self.change_indentation(-1)
                return None
        super().keyPressEvent(e)

    def mousePressEvent(self, e: QMouseEvent) -> None:
        if e.button() == Qt.MouseButton.LeftButton:
            self.send_current_text_format()
            self.open_hyperlink(e.pos())
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        self.has_hyperlink(e.pos())
        super().mouseMoveEvent(e)

    def on_cursor_position_changed(self) -> None:
        self.in_table()
        self.send_current_text_format()
        self.on_empty_document()

    def on_empty_document(self) -> None:
        if self.document().characterCount() == 1:
            self.requestTextProps.emit()

    def on_new_block(self) -> None:
        cformat = QTextCharFormat()
        cformat.setFontFamilies(self.last_format["family"])
        cformat.setFontPointSize(self.last_format["size"])#
        cformat.setFontWeight(self.bool_to_weight(self.last_format["bold"]))
        cformat.setFontItalic(self.last_format["italic"])
        cformat.setFontUnderline(self.last_format["underlined"])
        self.setCurrentCharFormat(cformat)
        self.send_current_text_format()


    def insert_list(self, lformat: QTextListFormat.Style) -> None:
        self.setFocus()
        cursor = self.textCursor()
        textList = cursor.currentList()
        if textList:
            start = cursor.selectionStart()
            end = cursor.selectionEnd()
            removed = 0
            for i in range(textList.count()):
                item = textList.item(i - removed)
                if (item.position() <= end and item.position() + item.length() > start):
                    textList.remove(item)
                    blockCursor = QTextCursor(item)
                    blockFormat = blockCursor.blockFormat()
                    blockFormat.setIndent(0)
                    blockCursor.mergeBlockFormat(blockFormat)
                    removed += 1
        else:
            listFormat = QTextListFormat()
            listFormat.setStyle(lformat)
            cursor.createList(listFormat)
    

    def change_indentation(self, incr=1) -> None:
        self.setFocus()
        cursor = self.textCursor()
        tlist = cursor.currentList()
        if tlist:
            lformat = tlist.format()
            lstyle = tlist.format().style()
            bformat = cursor.blockFormat()
            newindent = bformat.indent() + incr
            bformat.setIndent(newindent)
            cursor.mergeBlockFormat(bformat)

            if incr < 0:
                block = self.document().findBlockByNumber(cursor.blockNumber() - tlist.count())
                lowerlist = block.textList()
                if lowerlist:
                    lowerlist.add(cursor.block()) 
            else:
                # Bullet list
                if lstyle == QTextListFormat.Style.ListDisc or lstyle == QTextListFormat.Style.ListCircle or lstyle == QTextListFormat.Style.ListSquare:
                    if bformat.indent() == 0: lformat.setStyle(QTextListFormat.Style.ListDisc)
                    elif bformat.indent() == 1: lformat.setStyle(QTextListFormat.Style.ListCircle)
                    elif bformat.indent() >= 2: lformat.setStyle(QTextListFormat.Style.ListSquare)

                # Numbered list
                elif lstyle == QTextListFormat.Style.ListDecimal or lstyle == QTextListFormat.Style.ListLowerAlpha or lstyle == QTextListFormat.Style.ListLowerRoman:
                    if bformat.indent() == 0: lformat.setStyle(QTextListFormat.Style.ListDecimal)
                    elif bformat.indent() == 1: lformat.setStyle(QTextListFormat.Style.ListLowerAlpha)
                    elif bformat.indent() >= 2: lformat.setStyle(QTextListFormat.Style.ListLowerRoman)
                cursor.createList(lformat)

        else:
            bformat = cursor.blockFormat()
            if incr == 1:
                bformat.setIndent(bformat.indent() + 1)
            elif bformat.indent() == 0:
                bformat.setIndent(0)
            else:
                bformat.setIndent(bformat.indent() - 1)   
            cursor.setBlockFormat(bformat)

    @pyqtSlot(int, int)
    def insert_table(self, line: int, column: int) -> None:
        cursor = self.textCursor()

        fmt = QTextTableFormat()

        fmt.setBorder(1.0)
        fmt.setBorderStyle(QTextTableFormat.BorderStyle.BorderStyle_Solid)
        fmt.setBorderCollapse(False)

        brsh = fmt.borderBrush()
        brsh.setColor(Qt.GlobalColor.black)
        fmt.setBorderBrush(brsh)

        fmt.setWidth(QTextLength(QTextLength.Type.PercentageLength, 100))
        fmt.setCellPadding(5.0)
        fmt.setCellSpacing(0.0)

        cursor.insertTable(line, column, fmt)

    def insert_row(self, pos=0) -> None:
        cursor = self.textCursor()
        table = cursor.currentTable()
        if table:
            table.insertRows(table.cellAt(cursor).row()+pos, 1)

    def insert_column(self, pos=0) -> None:
        cursor = self.textCursor()
        table = cursor.currentTable()
        if table:
            table.insertColumns(table.cellAt(cursor).column()+pos, 1)

    def delete_row(self) -> None:
        cursor = self.textCursor()
        table = cursor.currentTable()
        if table:
            table.removeRows(table.cellAt(cursor).row(), 1)

    def delete_column(self) -> None:
        cursor = self.textCursor()
        table = cursor.currentTable()
        if table:
            table.removeColumns(table.cellAt(cursor).column(), 1)

    def delete_table(self) -> None:
        cursor = self.textCursor()
        table = cursor.currentTable()
        if table:
            table.removeColumns(0, table.columns())

    def in_table(self) -> bool:
        cursor = self.textCursor()
        if cursor.currentTable():
            self.showTableTools.emit(True)
            return True
        else:
            self.showTableTools.emit(False)
            return False

    def insert_symbol(self, symbol: str) -> None:
        self.insertPlainText(symbol)

    def insert_hyperlink(self) -> None:
        link, ok = QInputDialog.getText(None, tr("Insert Hyperlink"), tr("Hyperlink:"))
        if ok:
            if link.startswith(("https://", "http://", "www.")):
                if link.startswith("www."):
                    link = "http://" + link
                fmt = QTextCharFormat()
                fmt.setFontUnderline(True)
                fmt.setAnchor(True)
                fmt.setAnchorHref(link)
                cur = self.textCursor()
                cur.insertText(link, fmt)
            else:
                dialog = QMessageBox.warning(None, tr("Unvalid link"), tr("The link is not valid. Check the address and try again."), QMessageBox.StandardButton.Ok)
                self.insert_hyperlink()

    def delete_hyperlink(self) -> None:
        fmt = self.textCursor().charFormat()
        fmt.setAnchor(False)
        self.textCursor().setBlockCharFormat(fmt)

    def open_hyperlink(self, pos: QPoint) -> None:
        anchor = self.anchorAt(pos)
        if anchor:
            webbrowser.open(anchor)

    def has_hyperlink(self, pos: QPoint) -> bool:
        anchor = self.anchorAt(pos)
        if anchor:
            self.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
            return True
        else:
            self.viewport().setCursor(Qt.CursorShape.IBeamCursor)
            return False

    def localeTextControl(self) -> None:
        pass

    def insertFromMimeData(self, source: QMimeData):
        if source.hasText():
            # self.insertPlainText(source.text())
            # self.selectAll()
            cformat = QTextCharFormat()
            cformat.setBackground(QColor("#ffffff"))
            cformat_ = self.textCursor().charFormat()
            cformat_.merge(cformat)
            self.textCursor().insertText(source.text(), cformat_)
            # self.mergeCurrentCharFormat(cformat)

    def accurate_background_color(self) -> QColor:
        """Necessary because Qt does not return the background color accurately when the p-element has no 'background-color' attribute."""
        html = self.toHtml()
        start = html.rfind("<p")
        if html.find("; background-color:", start) != -1:
            return self.textBackgroundColor()
        else:
            return self.default_format["bcolor"]


    def send_current_text_format(self) -> None:
        cursor = self.textCursor()
        cformat = cursor.charFormat()
        props = {}

        if cursor.hasSelection() == False and self.document().characterCount() > 1:
            if cformat.fontWeight() == 700: 
                props["bold"] = True
            else:
                props["bold"] = False
            props["italic"] = cformat.fontItalic()
            props["underlined"] = cformat.fontUnderline()
            props["family"] = self.has_format(cformat.fontFamilies(), self.last_format["family"])

            props["veralign"] = cformat.verticalAlignment()
            props["alignment"] = self.alignment()

            if cformat.fontPointSize() > 0:
                if cformat.fontPointSize() % 1 == 0:
                    props["size"] = int(cformat.fontPointSize())
                else:
                    props["size"] = cformat.fontPointSize()
            else:
                if self.fontPointSize() % 1 == 0:
                    props["size"] = int(self.last_format["size"])
                else:
                    props["size"] = self.last_format["size"]
            # print(props["size"])
            props["color"] = self.textColor()
            # props["bcolor"] = self.accurate_background_color()

            self.last_format = props
            # print(props)
            # print("BG_Colour accurate", props["bcolor"].name())
           
            self.elementFontChanged.emit(props)
            self.menu.set_font_props(props)

    def has_format(self, fmt, default):
        if fmt:
            return fmt
        else: 
            return default 

    def sizeHint(self) -> QSize:
        return QSize(100, 50)

    def contextMenuEvent(self, e: QContextMenuEvent):
        self.send_current_text_format()
        self.menu.open_(e.globalPos(), self.textCursor().hasSelection(), bool(QApplication.clipboard().text()), self.in_table(), self.has_hyperlink(e.pos()))

class TextEditorMenu(QMenu):
    fontChanged = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = TextEditorMenuView()
        self.ui.setUi(self)

        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        self._fontProperties = {}

        self.connect_signals()
        self.get_all()

    def open_(self, globalPos: QPoint, copy: bool, paste: bool, table: bool, hyperlink: bool) -> None:
        print(f"copy: {copy}, paste: {paste}, table: {table}, hyperlink: {hyperlink}")
        self.ui.ac_Copy.setEnabled(copy)
        self.ui.ac_Cut.setEnabled(copy)
        self.ui.ac_Paste.setEnabled(paste)
        self.enable_table_tools(table)
        self.enable_hyperlink_tools(hyperlink)
        self.exec(globalPos)

    def connect_signals(self) -> None:
        self.ui.cb_Font.currentFontChanged.connect(self.get_font_family)
        self.ui.cb_FontSize.currentIndexChanged.connect(self.get_font_size)
        self.ui.cb_FontSize.textEntered.connect(self.get_font_size)
        self.ui.pb_Bold.toggled.connect(self.is_bold)
        self.ui.pb_Italic.toggled.connect(self.is_italic)
        self.ui.pb_Underline.toggled.connect(self.is_underlined)
        self.ui.align_group.buttonToggled.connect(self.alignment)
        self.ui.csb_TextColor.lbutton.clicked.connect(lambda: self.get_font_color(self.text_color()))
        self.ui.color_menu.colorChanged.connect(self.get_font_color)

    def get_all(self):
        self._fontProperties["family"] = self.ui.cb_Font.currentFont().families()
        self._fontProperties["size"] = float(self.ui.cb_FontSize.currentFontSize())
        self._fontProperties["bold"] = self.ui.pb_Bold.isChecked()
        self._fontProperties["italic"] = self.ui.pb_Italic.isChecked()
        self._fontProperties["underlined"] = self.ui.pb_Underline.isChecked()
        self._fontProperties["alignment"] = self.alignment(True)
        self._fontProperties["color"] = self.ui.csb_TextColor.color()
        self.send_text_properties(self._fontProperties)

    @pyqtSlot(dict)
    def set_font_props(self, props: dict) -> None:
        for key, value in props.items():
            match key:
                case "family":
                    font = QFont()
                    font.setFamilies(value)
                    self.ui.cb_Font.setCurrentFont(font) # QFontComboBox
                case "size":
                    self.ui.cb_FontSize.setEditText(str(value)) #QComboBox with point sizes
                case "bold":
                    self.ui.pb_Bold.setChecked(value) # Checkable QPushButton
                case "italic":
                    self.ui.pb_Italic.setChecked(value) # Checkable QPushButton
                case "underlined":
                    self.ui.pb_Underline.setChecked(value) # Checkable QPushButton
                case "alignment":
                    self.set_alignment(value)
                case "color":
                    self.set_button_color(self._fontProperties["color"], value)
            self._fontProperties[key] = value

    def set_button_color(self, old: QColor, color: QColor) -> None:
        self.ui.csb_TextColor.setColor(color)
        stylesheet = self.ui.csb_TextColor.lbutton.styleSheet()
        stylesheet = stylesheet.replace(f"border-bottom: 5px solid {old.name()};", f"border-bottom: 5px solid {color.name()};")
        self.ui.csb_TextColor.lbutton.setStyleSheet(stylesheet)

    def text_color(self) -> QColor:
        return self.csb_TextColor.color()

    def set_alignment(self, alignment: Qt.AlignmentFlag) -> None:
        if alignment == Qt.AlignmentFlag.AlignLeft:
            self.ui.pb_AlignLeft.setChecked(True)
        elif alignment == Qt.AlignmentFlag.AlignCenter:
            self.ui.pb_AlignCenter.setChecked(True)
        else:
            self.ui.align_group.setExclusive(False)
            self.ui.pb_AlignCenter.setChecked(False)
            self.ui.pb_AlignLeft.setChecked(False)
            self.ui.align_group.setExclusive(True)

    def send_text_properties(self, props: dict) -> dict:
        self.fontChanged.emit(props)
        return self._fontProperties

    def get_font_family(self) -> None:
        props = {}
        props["family"] = self.ui.cb_Font.currentFont().families()
        self.send_text_properties(props)

    def get_font_size(self) -> None:
        props = {}
        props["size"] = float(self.ui.cb_FontSize.currentFontSize())
        self.send_text_properties(props)

    def get_font_color(self, color: QColor) -> None:
        props = {}
        self.set_button_color(self._fontProperties["color"], color)
        props["color"] = color
        self.send_text_properties(props)

    def is_bold(self) -> None:
        props = {}
        props["bold"] = self.ui.pb_Bold.isChecked()
        self.send_text_properties(props)

    def is_italic(self) -> None:
        props = {}
        props["italic"] = self.ui.pb_Italic.isChecked()
        self.send_text_properties(props)

    def is_underlined(self) -> None:
        props = {}
        props["underlined"] = self.ui.pb_Underline.isChecked()
        self.send_text_properties(props)

    def alignment(self, get=False) -> None|Qt.AlignmentFlag:
        props = {}
        if self.ui.pb_AlignLeft.isChecked():
            props["alignment"] = Qt.AlignmentFlag.AlignLeft
        elif self.ui.pb_AlignCenter.isChecked():
            props["alignment"] = Qt.AlignmentFlag.AlignCenter
        if get == True:
            return props["alignment"]
        self.send_text_properties(props)

    def enable_table_tools(self, enable: bool) -> None:
        self.ui.table_group.setVisible(enable)

    def enable_hyperlink_tools(self, enable: bool) -> None:
        self.ui.hyperlink_group.setVisible(enable)

class TextDelegate(BaseElementDelegate):
 

    def paint(self, painter: QPainter | None, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        # print("Text painting started")
        data: QTextDocument = index.data()
        data.setDocumentMargin(3.0)

        sub_rect = QRect(option.rect.x() + 5, option.rect.y() + 5, option.rect.width() - 10, option.rect.height() + 10)
        data.setTextWidth(sub_rect.width())
        sub_rect.setHeight(int(data.size().height() + 10))

        painter.save()
        style = option.widget.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, option, painter, option.widget)

        # print("Text width", sub_rect.width())
        painter.translate(sub_rect.topLeft())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        data.drawContents(painter)
        painter.restore()

        if index.row() < index.model().rowCount() - 1:
            painter.save()
            pen = QPen(Qt.GlobalColor.lightGray, 1)
            painter.setPen(pen)
            painter.drawLine(option.rect.bottomLeft().x() + 5, option.rect.bottomLeft().y(), option.rect.bottomRight().x() - 5, option.rect.bottomRight().y())
            painter.restore()

        
    def createEditor(self, parent: QWidget | None, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget | None:
        print("Trying to create a TextEditor")
        editor = TextEditor(index.data(Qt.ItemDataRole.EditRole), parent)
        editor.setStyleSheet("background: none; border: 1px solid LightGray")
        editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        editor.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        editor.textChanged.connect(lambda: self.fit_to_text(editor, option, index))
        editor.setContentsMargins(3, 3, 3, 3)
        editor.setFocus()
        
        print("TextEditor created")
        return editor
    
    def setEditorData(self, editor: TextEditor | None, index: QModelIndex) -> None:
        self._toolset.connect_editor(editor)
        print("Connected TextEditor")

    def updateEditorGeometry(self, editor: TextEditor| None, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        print("Rect width", option.rect.width())
        editor.setGeometry(option.rect.adjusted(5, 5, -5, -5))

    def fit_to_text(self, editor: TextEditor, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        document = editor.document()
        docHeight = document.size().height()
        if 0 <= docHeight:
            editor.setFixedHeight(int(docHeight) + editor.currentFont().pixelSize() + 5)
        self.sizeHintChanged.emit(index)
        # index.model().dataChanged.emit(index, index)

    def setModelData(self, editor: TextEditor | None, model, index: QModelIndex) -> None:
        model.setData(index, editor.document())

    def destroyEditor(self, editor: TextEditor, index: QModelIndex):
        self._toolset.close_()
        print("TextEditor destroyed")
        return super().destroyEditor(editor, index)

    def passthru(self) -> bool:
        return False

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        if index.data():
            size = index.data().expected_size(option.rect.width() - 10)
            return QSize(option.rect.width(), size.height() + 10)
        else:
            return QSize(option.rect.width(), 0)

class TextToolset(BaseElementToolset):
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
        self.ui = TextToolsetView()
        self.ui.setUI(self)

        # Attributes
        self._fontProperties = {}
        
        self.setAttribute(Qt.WidgetAttribute.WA_NoMousePropagation, True)
        self.connect_signals()
        self.get_all()

    @property
    def name(self) -> str:
        return "TextElement"
    
    @property
    def element_menu(self) -> ElementOptions:
        return self.ui.element_options_menu

    def connect_editor(self, editor: TextEditor) -> None:
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
        self.called.emit(self.name)

        self.setVisible(True)

    def close_(self):
        signals = (
            self.fontChanged,
            self.blist,
            self.numlist,
            self.indent,
            self.dedent,
            self.insert_table,
            self.insertSymbol,
            self.insertHyperlink,
            self.addRowT,
            self.addRowB,
            self.addColumnL,
            self.addColumnR,
            self.deleteRow,
            self.deleteColumn,
            self.deleteTable,
            )
        for signal in signals:
            try:
                signal.disconnect()
            except (RuntimeError, TypeError):
                print("Couldn't disconnect")
                pass

        super().close_()
    
    def connect_signals(self):
        self.ui.ac_close.triggered.connect(self.closed.emit)

        self.ui.cb_Font.currentFontChanged.connect(self.get_font_family)
        self.ui.cb_FontSize.currentIndexChanged.connect(self.get_font_size)
        self.ui.cb_FontSize.textEntered.connect(self.get_font_size)
        self.ui.ac_bold.toggled.connect(self.is_bold)
        self.ui.ac_italic.toggled.connect(self.is_italic)
        self.ui.ac_underline.toggled.connect(self.is_underlined)
        self.ui.align_group.triggered.connect(self.alignment)
        self.ui.veralign_group.triggered.connect(self.vertical_alignment)
        self.ui.ac_textcolor.triggered.connect(lambda: self.get_color(self.textColor()))
        self.ui.color_menu.colorChanged.connect(self.get_color)
        # self.color_menu2.colorChanged.connect(self.get_background_color)
        self.ui.ac_list.triggered.connect(self.request_bullet_list)
        self.ui.ac_numlist.triggered.connect(self.request_num_list)
        self.ui.ac_indent.triggered.connect(self.request_indent)
        self.ui.ac_dedent.triggered.connect(self.request_dedent)
        self.ui.menu_table.tableSize.connect(self.request_table_insert)
        self.ui.ac_symbol.triggered.connect(self.open_symbol_dialog)
        self.ui.ac_hyperlink.triggered.connect(self.request_hyperlink_insert)

        self.ui.ac_row_top.triggered.connect(self.request_add_row_top)
        self.ui.ac_row_bottom.triggered.connect(self.request_add_row_bottom)
        self.ui.ac_column_left.triggered.connect(self.request_add_column_left)
        self.ui.ac_column_right.triggered.connect(self.request_add_column_right)
        self.ui.ac_delete_row.triggered.connect(self.request_delete_row)
        self.ui.ac_delete_column.triggered.connect(self.request_delete_column)
        self.ui.ac_delete_table.triggered.connect(self.request_delete_table)

    def send_text_properties(self, props: dict) -> dict:
        self.fontChanged.emit(props)
        return self._fontProperties
    
    @pyqtSlot(bool)
    def set_table_tools_visible(self, visible: bool):
        self.ui.tabletools_group.setVisible(visible)

    @pyqtSlot(dict)
    def set_font_props(self, props: dict) -> None:
        for key, value in props.items():
            match key:
                case "family":
                    font = QFont()
                    font.setFamilies(value)
                    self.ui.cb_Font.setCurrentFont(font) # QFontComboBox
                case "size":
                    self.ui.cb_FontSize.setEditText(str(value)) #QComboBox with point sizes
                case "bold":
                    self.ui.ac_bold.setChecked(value) # Checkable QPushButton
                case "italic":
                    self.ui.ac_italic.setChecked(value) # Checkable QPushButton
                case "underlined":
                    self.ui.ac_underline.setChecked(value) # Checkable QPushButton
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
        self._fontProperties["family"] = self.ui.cb_Font.currentFont().families()
        self._fontProperties["size"] = float(self.ui.cb_FontSize.currentFontSize())
        self._fontProperties["bold"] = self.ui.ac_bold.isChecked()
        self._fontProperties["italic"] = self.ui.ac_italic.isChecked()
        self._fontProperties["underlined"] = self.ui.ac_underline.isChecked()
        self._fontProperties["alignment"] = self.alignment(True)
        self._fontProperties["veralign"] = self.vertical_alignment(True)
        self._fontProperties["color"] = self.ui.ac_textcolor.property("color")
        # self._fontProperties["bcolor"] = self.csb_BackgroundColor.color()
        self.send_text_properties(self._fontProperties)

    def get_font_family(self) -> None:
        props = {}
        props["family"] = self.ui.cb_Font.currentFont().families()
        self.send_text_properties(props)

    def get_font_size(self) -> None:
        props = {}
        props["size"] = float(self.ui.cb_FontSize.currentFontSize())
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
            self.ui.ac_textcolor.setProperty("color", color)
            widget = self.widgetForAction(self.ui.ac_textcolor)
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
        return self.ui.ac_textcolor.property("color")
    
    # def bg_color(self) -> QColor:
    #     return self.csb_BackgroundColor.color()

    def is_bold(self) -> None:
        props = {}
        props["bold"] = self.ui.ac_bold.isChecked()
        self.send_text_properties(props)

    def is_italic(self) -> None: 
        props = {}
        props["italic"] = self.ui.ac_italic.isChecked()
        self.send_text_properties(props)

    def is_underlined(self) -> None:
        props = {}
        props["underlined"] = self.ui.ac_underline.isChecked()
        self.send_text_properties(props)

    def set_alignment(self, alignment: Qt.AlignmentFlag) -> None:
        if alignment == Qt.AlignmentFlag.AlignLeft:
            self.ui.ac_align_left.setChecked(True)
        elif alignment == Qt.AlignmentFlag.AlignCenter:
            self.ui.ac_align_center.setChecked(True)
        elif alignment == Qt.AlignmentFlag.AlignRight:
            self.ui.ac_align_right.setChecked(True)
        elif alignment == Qt.AlignmentFlag.AlignJustify:
            self.ui.ac_align_justify.setChecked(True)

    def set_vertical_alignment(self, alignment: QTextCharFormat.VerticalAlignment) -> None:
        if alignment == QTextCharFormat.VerticalAlignment.AlignSubScript:
            self.ui.ac_subscript.setChecked(True)
        elif alignment == QTextCharFormat.VerticalAlignment.AlignSuperScript:
            self.ui.ac_superscript.setChecked(True)
        else:
            self.ui.ac_subscript.setChecked(False)
            self.ui.ac_superscript.setChecked(False)

    def alignment(self, get=False) -> None | Qt.AlignmentFlag:
        props = {}
        if self.ui.ac_align_left.isChecked():
            props["alignment"] = Qt.AlignmentFlag.AlignLeft
        elif self.ui.ac_align_center.isChecked():
            props["alignment"] = Qt.AlignmentFlag.AlignCenter
        elif self.ui.ac_align_right.isChecked():
            props["alignment"] = Qt.AlignmentFlag.AlignRight
        elif self.ui.ac_align_justify.isChecked():
            props["alignment"] = Qt.AlignmentFlag.AlignJustify
        if get == True:
            return props["alignment"]
        self.send_text_properties(props)

    def vertical_alignment(self, get=False):
        props = {}
        if self.ui.ac_superscript.isChecked():
            props["veralign"] = QTextCharFormat.VerticalAlignment.AlignSuperScript
            self.ui.ac_subscript.setChecked(False)
        elif self.ui.ac_subscript.isChecked():
            props["veralign"] = QTextCharFormat.VerticalAlignment.AlignSubScript
            self.ui.ac_superscript.setChecked(False)
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

class TextElementDefinitions(BaseElementDefinitions):

    @staticmethod
    def name() -> str:
        return "TextElement"
    
    @staticmethod
    def type() -> ResourceType:
        return ResourceType.TEXT

    @staticmethod
    def create_model(resource: ResourceObject) -> TextModel:
        return TextModel(resource)
    
    @staticmethod
    def get_file() -> None:
        return None
    
    @staticmethod
    def model() -> Type[TextModel]:
        return TextModel
    
    @staticmethod
    def action(parent) -> QAction:
        action = QAction(QIcon("resources/icons/ic_text.svg"), tr("Text"), parent)
        action.setData("TextElement")
        return action

    @staticmethod
    def toolset() -> TextToolset:
        return TextToolset()
    
    @staticmethod
    def editor(model: TextModel):
        return TextEditor(model)