from PyQt6.QtWidgets import QSizePolicy, QInputDialog, QMessageBox, QMenu, QApplication, QWidget, QStyledItemDelegate, QStyleOptionViewItem, QStyle
from PyQt6.QtGui import QKeyEvent, QColor, QFont, QTextListFormat, QTextCursor,  QMouseEvent, QTextLength, QTextCharFormat, QContextMenuEvent, QTextDocument, QPainter, QPen, QTextOption
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt, QSize, QPoint, QMimeData, QXmlStreamWriter, QXmlStreamAttributes, QModelIndex, QRect, QT_TR_NOOP as tr
from PyQt6.QtXml import QDomElement
from tcha.elements.baseelement import BaseEditor, BaseModel
from tcha.resmanager import ResourceType, ResourceObject
from ui.ui_TextElement import TextMenu
from tcha.settings import get
from dataclasses import dataclass
from typing import Protocol, Self
import webbrowser

class TextElement(Protocol):
    ...

class TextDelegate(Protocol):
    ...

@dataclass
class TextModel(QTextDocument, BaseModel):
    resource: ResourceObject

    def __post_init__(self, parent=None) -> None:
        super().__init__(parent)
        # option = QTextOption()
        self.setDefaultStyleSheet("p {background-color: white;}")

    def xml(self, writer: QXmlStreamWriter) -> QXmlStreamWriter:
        writer.writeEmptyElement("element")
        writer.writeAttribute("type", "TextElement")
        writer.writeAttribute("file", self.resource.make_serialised_name("text", ".html"))
        self.resource.set_data(bytes(self.toHtml(), "utf-8"))
        return writer
    
    @classmethod
    def read(cls: Self, xml: QXmlStreamAttributes, resobj: ResourceObject) -> "TextModel":
        model = cls(resobj)
        html = resobj.get_data().decode("utf-8")
        model.setHtml(html)
        return model
    
    @staticmethod
    def restype() -> ResourceType:
        return ResourceType.TEXT
    
    def editor(self) -> TextElement:
        return TextElement()
    
    def expected_size(self, width: int) -> QSize:
        self.setTextWidth(float(width))
        self.setDocumentMargin(3.0)
        size = self.size().toSize()
        return size
    
    def editable(self) -> bool:
        return True
    
    def delegate(self, parent: QWidget) -> TextDelegate:
        return TextDelegate(parent)

    def change_on_mouse_hover(self) -> bool:
        return False

    def __del__(self) -> None:
        self.resource.delete_member()

def return_model() -> TextModel:
    return TextModel
    
class TextElement(BaseEditor):
    requestTextProps = pyqtSignal()
    elementFontChanged = pyqtSignal(dict)
    showTableTools = pyqtSignal(bool)

    def __init__(self, model: TextModel, parent=None) -> None:
        super().__init__(parent)
        self.setDocument(model)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        self.setStyleSheet("background-color: white;")

        self.type_lang = get("General", "Language")
        self.last_char: str
        self.last_format: dict = {
            "family": ["Segoe UI"], 
            "size": 8.0, 
            "bold": False, 
            "italic": False, 
            "underlined": False, 
            "color": QColor("#000000"),
            }
        
        self.set_text_format(self.last_format)
        self.requestTextProps.emit()
        self.default_format = self.last_format
        self.menu = TextElementMenu(self)

        self.setAttribute(Qt.WidgetAttribute.WA_NoMousePropagation, True)
        self.setMouseTracking(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)
        self.set_default_cursor()
        self.connect_signals()

    @property
    def toolset(self) -> str:
        return "TextToolset"
    
    def model(self) -> TextModel:
        return self.document()

    def connect_signals(self) -> None:
        self.cursorPositionChanged.connect(self.on_cursor_position_changed)

        self.menu.fontChanged.connect(self.set_text_format)
        self.menu.fontChanged.connect(self.to_toolset)

        self.menu.ac_RowTop.triggered.connect(self.insert_row)
        self.menu.ac_RowBottom.triggered.connect(lambda: self.insert_row(1))
        self.menu.ac_ColumnLeft.triggered.connect(self.insert_column)
        self.menu.ac_ColumnRight.triggered.connect(lambda: self.insert_column(1))
        self.menu.ac_DeleteRow.triggered.connect(self.delete_row)
        self.menu.ac_DeleteColumn.triggered.connect(self.delete_column)
        self.menu.ac_DeleteHyperlink.triggered.connect(self.delete_hyperlink)
        self.menu.ac_Copy.triggered.connect(self.copy)
        self.menu.ac_Cut.triggered.connect(self.cut)
        self.menu.ac_Paste.triggered.connect(self.paste)

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

    def focusOutEvent(self, e):
        return 

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
            self.requestToolset.emit()
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
        table = cursor.insertTable(line, column)
        fmt = table.format()
        fmt.setWidth(QTextLength(QTextLength.Type.PercentageLength, 100))
        table.setFormat(fmt)

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


class TextElementMenu(QMenu, TextMenu):
    fontChanged = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setUi(self)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        self._fontProperties = {}

        self.connect_signals()
        self.get_all()

    def open_(self, globalPos: QPoint, copy: bool, paste: bool, table: bool, hyperlink: bool) -> None:
        print(f"copy: {copy}, paste: {paste}, table: {table}, hyperlink: {hyperlink}")
        self.ac_Copy.setEnabled(copy)
        self.ac_Cut.setEnabled(copy)
        self.ac_Paste.setEnabled(paste)
        self.enable_table_tools(table)
        self.enable_hyperlink_tools(hyperlink)
        self.exec(globalPos)

    def connect_signals(self) -> None:
        self.cb_Font.currentFontChanged.connect(self.get_font_family)
        self.cb_FontSize.currentIndexChanged.connect(self.get_font_size)
        self.cb_FontSize.textEntered.connect(self.get_font_size)
        self.pb_Bold.toggled.connect(self.is_bold)
        self.pb_Italic.toggled.connect(self.is_italic)
        self.pb_Underline.toggled.connect(self.is_underlined)
        self.align_group.buttonToggled.connect(self.alignment)
        self.csb_TextColor.lbutton.clicked.connect(lambda: self.get_font_color(self.text_color()))
        self.color_menu.colorChanged.connect(self.get_font_color)

    def get_all(self):
        self._fontProperties["family"] = self.cb_Font.currentFont().families()
        self._fontProperties["size"] = float(self.cb_FontSize.currentFontSize())
        self._fontProperties["bold"] = self.pb_Bold.isChecked()
        self._fontProperties["italic"] = self.pb_Italic.isChecked()
        self._fontProperties["underlined"] = self.pb_Underline.isChecked()
        self._fontProperties["alignment"] = self.alignment(True)
        self._fontProperties["color"] = self.csb_TextColor.color()
        self.send_text_properties(self._fontProperties)

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
                    self.pb_Bold.setChecked(value) # Checkable QPushButton
                case "italic":
                    self.pb_Italic.setChecked(value) # Checkable QPushButton
                case "underlined":
                    self.pb_Underline.setChecked(value) # Checkable QPushButton
                case "alignment":
                    self.set_alignment(value)
                case "color":
                    self.set_button_color(self._fontProperties["color"], value)
            self._fontProperties[key] = value

    def set_button_color(self, old: QColor, color: QColor) -> None:
        self.csb_TextColor.setColor(color)
        stylesheet = self.csb_TextColor.lbutton.styleSheet()
        stylesheet = stylesheet.replace(f"border-bottom: 5px solid {old.name()};", f"border-bottom: 5px solid {color.name()};")
        self.csb_TextColor.lbutton.setStyleSheet(stylesheet)

    def text_color(self) -> QColor:
        return self.csb_TextColor.color()

    def set_alignment(self, alignment: Qt.AlignmentFlag) -> None:
        if alignment == Qt.AlignmentFlag.AlignLeft:
            self.pb_AlignLeft.setChecked(True)
        elif alignment == Qt.AlignmentFlag.AlignCenter:
            self.pb_AlignCenter.setChecked(True)
        else:
            self.align_group.setExclusive(False)
            self.pb_AlignCenter.setChecked(False)
            self.pb_AlignLeft.setChecked(False)
            self.align_group.setExclusive(True)

    def send_text_properties(self, props: dict) -> dict:
        self.fontChanged.emit(props)
        return self._fontProperties

    def get_font_family(self) -> None:
        props = {}
        props["family"] = self.cb_Font.currentFont().families()
        self.send_text_properties(props)

    def get_font_size(self) -> None:
        props = {}
        props["size"] = float(self.cb_FontSize.currentFontSize())
        self.send_text_properties(props)

    def get_font_color(self, color: QColor) -> None:
        props = {}
        self.set_button_color(self._fontProperties["color"], color)
        props["color"] = color
        self.send_text_properties(props)

    def is_bold(self) -> None:
        props = {}
        props["bold"] = self.pb_Bold.isChecked()
        self.send_text_properties(props)

    def is_italic(self) -> None:
        props = {}
        props["italic"] = self.pb_Italic.isChecked()
        self.send_text_properties(props)

    def is_underlined(self) -> None:
        props = {}
        props["underlined"] = self.pb_Underline.isChecked()
        self.send_text_properties(props)

    def alignment(self, get=False) -> None|Qt.AlignmentFlag:
        props = {}
        if self.pb_AlignLeft.isChecked():
            props["alignment"] = Qt.AlignmentFlag.AlignLeft
        elif self.pb_AlignCenter.isChecked():
            props["alignment"] = Qt.AlignmentFlag.AlignCenter
        if get == True:
            return props["alignment"]
        self.send_text_properties(props)

    def enable_table_tools(self, enable: bool) -> None:
        self.table_group.setVisible(enable)

    def enable_hyperlink_tools(self, enable: bool) -> None:
        self.hyperlink_group.setVisible(enable)

class TextDelegate(QStyledItemDelegate):
    editorOpened = pyqtSignal(QWidget)

    def paint(self, painter: QPainter | None, option: QStyleOptionViewItem, index: QModelIndex) -> None:
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
        editor = TextElement(QTextDocument(), parent)
        editor.setStyleSheet("background: none; border: 1px solid LightGray")
        editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        editor.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        editor.textChanged.connect(lambda: self.fit_to_text(editor, option, index))
        editor.setContentsMargins(3, 3, 3, 3)
        editor.setFocus()
        self.editorOpened.emit(editor)
        return editor
    
    def setEditorData(self, editor: TextElement | None, index: QModelIndex) -> None:
        editor.setDocument(index.data(Qt.ItemDataRole.EditRole))

    def setModelData(self, editor: TextElement | None, model, index: QModelIndex) -> None:
        model.setData(index, editor.document())

    def updateEditorGeometry(self, editor: TextElement | None, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        print("Rect width", option.rect.width())
        editor.setGeometry(option.rect.adjusted(5, 5, -5, -5))

    def fit_to_text(self, editor: TextElement, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        document = editor.document()
        docHeight = document.size().height()
        if 0 <= docHeight:
            editor.setFixedHeight(int(docHeight) + editor.currentFont().pixelSize() + 5)
        self.sizeHintChanged.emit(index)
        index.model().dataChanged.emit(index, index)

    def passthru(self) -> bool:
        return False

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        if index.data():
            size = index.data().expected_size(option.rect.width() - 10)
            return QSize(option.rect.width(), size.height() + 10)
        else:
            return QSize(option.rect.width(), 0)
