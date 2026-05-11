from __future__ import annotations

import json
import unicodedata
import webbrowser
from typing import Self, Type

from PyQt6 import uic
from PyQt6.QtCore import QT_TR_NOOP as tr
from PyQt6.QtCore import (
    QBuffer,
    QByteArray,
    QDataStream,
    QIODevice,
    QModelIndex,
    QPoint,
    QPointF,
    QRectF,
    QSize,
    Qt,
    QXmlStreamAttributes,
    QXmlStreamWriter,
    pyqtSignal,
    pyqtSlot,
)
from PyQt6.QtGui import (
    QAction,
    QColor,
    QContextMenuEvent,
    QFont,
    QIcon,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPen,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
    QTextLength,
    QTextListFormat,
    QTextOption,
    QTextTableFormat,
)
from PyQt6.QtSvg import QSvgGenerator, QSvgRenderer
from PyQt6.QtSvgWidgets import QGraphicsSvgItem
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QGraphicsTextItem,
    QInputDialog,
    QMenu,
    QMessageBox,
    QStyleOptionViewItem,
    QTableWidgetItem,
    QWidget,
)

from nativeelements.baseelement import (
    BaseElementDefinitions,
    BaseElementDelegate,
    BaseElementModel,
    BaseElementToolset,
    BaseTextElementEditor,
    QMimeData,
    ResourceObject,
    ResourceType,
)
from nativeelements.views import TextEditorMenuView
from tcha.consts import ResourceFlag
from tcha.resmanager import ResourceContainer
from tcha.settings import Locale, Settings
from tcha.styling import Svg, SvgIconEngine
from ui.element_toolsets import TextToolsetView


class TextModel(QTextDocument, BaseElementModel):
    def __init__(self, resource: ResourceObject, parent=None) -> None:
        super().__init__(parent)
        self._resource = resource
        self._resource.add_member()
        self._resource.set_extension("html")
        self._resource.set_datalink(lambda: self.toHtml().encode())

        option = self.defaultTextOption()
        option.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        self.setDefaultTextOption(option)
        self.setDocumentMargin(8.0)

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

    @classmethod
    def from_mime_data(cls, resobj: ResourceObject, mime_data: QMimeData) -> TextModel:
        model = TextModel(resobj)
        if mime_data.hasHtml():
            model.setHtml(mime_data.html())
        elif mime_data.hasText():
            model.setPlainText(mime_data.text())
        return model

    @staticmethod
    def restype() -> ResourceType:
        return ResourceType.TEXT

    @property
    def name(self) -> str:
        return "TextElement"

    @property
    def resource(self) -> ResourceObject:
        return self._resource

    def recalculate_size(self, width: int):
        self.setTextWidth(width - 8)
        self.set_item_size(QSize(width, self.size().toSize().height() + 14))

    def editable(self) -> bool:
        return True

    def delegate(self, toolset: BaseElementToolset, parent=None) -> TextDelegate:
        return TextDelegate(toolset, parent)

    def presentable_item(self) -> QGraphicsTextItem:
        # item = QGraphicsTextItem()
        bytearr = QByteArray()
        buffer = QBuffer()
        buffer.setBuffer(bytearr)
        svg_gen = QSvgGenerator()
        svg_gen.setOutputDevice(buffer)
        painter = QPainter(svg_gen)
        # item.setDocument(self.clone())
        # item.setCacheMode(QGraphicsTextItem.CacheMode.DeviceCoordinateCache)
        self.drawContents(painter, QRectF(QPointF(0, 0), self.size()))
        painter.end()
        renderer = QSvgRenderer(bytearr)
        item = QGraphicsSvgItem()
        item.setSharedRenderer(renderer)
        item.setZValue(0.0)
        return item

    def copy(self, rescont: ResourceContainer) -> TextModel:
        resobj = rescont.create(self.restype())
        model = TextModel(resobj)
        model.setHtml(self.toHtml())
        return model

    def to_byte_array() -> QByteArray:
        data = QByteArray()
        stream = QDataStream(data, QIODevice.OpenModeFlag.WriteOnly)

        stream.writeQString(TextElementDefinitions.name())  # Element name
        stream.writeQString(self.resource.path)  # Path to resource
        stream.writeQString(self.toHtml())  # HTML content

        return data

    def attrs(self) -> tuple[str]:
        return tuple(["resource"])

    def close(self) -> None:
        self._resource.delete_member()
        self._resource = None

    def __del__(self) -> None:
        if self._resource:
            self._resource.delete_member()
            self._resource = None


class TextEditor(BaseTextElementEditor):
    currentPropsChanged = pyqtSignal(dict)
    tableEntered = pyqtSignal(bool)
    sizeChanged = pyqtSignal(int, int)

    def __init__(self, target_width: float, model: TextModel, parent=None) -> None:
        super().__init__(parent)
        print(f"Open editor with target width: {target_width}")
        self.setDocument(model)

        # Attributes
        self.type_lang = Locale[
            Settings.qsettings().value("User/language", "EnglishUK", str)
        ]
        self.last_char: str
        self.last_format: dict = {
            "family": ["Calibri"],
            "size": 10.0,
            "bold": False,
            "italic": False,
            "underlined": False,
        }
        self._target_width = target_width

        # Initial routines
        self.default_format = self.last_format
        self.menu = TextEditorMenu(self)

        if not self.is_empty():
            self.currentPropsChanged.emit(self.current_text_props())

        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setMouseTracking(True)  # When a hyperlink is under the mouse
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.setLineWrapMode(TextEditor.LineWrapMode.FixedPixelWidth)
        self.setLineWrapColumnOrWidth(3)
        self.textCursor().movePosition(QTextCursor.MoveOperation.End)
        self.connect_signals()

    @property
    def toolset(self) -> str:
        return "TextToolset"

    @property
    def model(self) -> TextModel:
        return self.document()

    def connect_signals(self) -> None:
        self.currentCharFormatChanged.connect(self.on_char_format_changed)
        self.cursorPositionChanged.connect(self.on_cursor_position_changed)

        self.menu.fontSet.connect(self.set_text_format)

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

        self.document().blockCountChanged.connect(self.on_new_block)
        self.document().contentsChanged.connect(self.fit_to_text)
        self.fit_to_text()

    def disconnect_signals(self) -> None:
        """Disconnect all signals to prevent memory leaks."""
        try:
            self.currentCharFormatChanged.disconnect(self.on_cursor_position_changed)
            self.menu.fontSet.disconnect(self.set_text_format)
            self.menu.ui.ac_RowTop.triggered.disconnect()
            self.menu.ui.ac_RowBottom.triggered.disconnect()
            self.menu.ui.ac_ColumnLeft.triggered.disconnect()
            self.menu.ui.ac_ColumnRight.triggered.disconnect()
            self.menu.ui.ac_DeleteRow.triggered.disconnect()
            self.menu.ui.ac_DeleteColumn.triggered.disconnect()
            self.menu.ui.ac_DeleteHyperlink.triggered.disconnect()
            self.menu.ui.ac_Copy.triggered.disconnect()
            self.menu.ui.ac_Cut.triggered.disconnect()
            self.menu.ui.ac_Paste.triggered.disconnect()
            self.document().blockCountChanged.disconnect(self.on_new_block)
        except (RuntimeError, TypeError):
            # Signals may already be disconnected
            pass

    def closeEvent(self, event) -> None:
        """Clean up resources when editor is closed."""
        self.disconnect_signals()
        if self.menu:
            self.menu.deleteLater()
            self.menu = None
        super().closeEvent(event)

    def fit_to_text(self) -> None:
        document: TextModel = self.document()
        old_height = document.size().toSize().height()
        document.setTextWidth(self._target_width)
        new_height = document.size().height()
        if 0 <= new_height:
            self.setFixedHeight(
                int(new_height) + 10
            )  # Add 10px buffer to prevent scrolling
            document.set_item_size(
                QSize(
                    int(self._target_width) + 8, document.size().toSize().height() + 10
                )
            )
            self.sizeChanged.emit(old_height, new_height)

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
                    if value.isValid():
                        cformat.setForeground(value)
                    else:
                        cformat.clearForeground()
            self.last_format[key] = value

        self.mergeCurrentCharFormat(cformat)

    def bool_to_weight(self, bold: bool) -> QFont.Weight:
        if bold:
            return QFont.Weight.Bold
        else:
            return QFont.Weight.Normal

    def allowed_font_size(self, point: float) -> float:
        """Prevents that font size is larger than width"""
        if point * (4 / 3) > self.width():
            return round(self.width() * 0.75 - 5, 1)
        else:
            if self.width() >= 100:
                self.setMinimumWidth(int(point * (4 / 3)) + 5)
            return point

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
            self.currentPropsChanged.emit(self.current_text_props())
            self.open_hyperlink(e.pos())
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        self.has_hyperlink(e.pos())
        super().mouseMoveEvent(e)

    def wheelEvent(self, e):
        return

    def on_cursor_position_changed(self) -> None:
        table = self.in_table()
        self.tableEntered.emit(table)
        self.document().setTextWidth(self._target_width)

    def on_char_format_changed(self) -> None:
        self.currentPropsChanged.emit(self.current_text_props())

    def is_empty(self) -> bool:
        if self.document().characterCount() <= 1:
            return True
        return False

    def on_new_block(self) -> None:
        self.set_text_format(self.last_format)
        self.currentPropsChanged.emit(self.last_format)

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
                if item.position() <= end and item.position() + item.length() > start:
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
                block = self.document().findBlockByNumber(
                    cursor.blockNumber() - tlist.count()
                )
                lowerlist = block.textList()
                if lowerlist:
                    lowerlist.add(cursor.block())
            else:
                # Bullet list
                if (
                    lstyle == QTextListFormat.Style.ListDisc
                    or lstyle == QTextListFormat.Style.ListCircle
                    or lstyle == QTextListFormat.Style.ListSquare
                ):
                    if bformat.indent() == 0:
                        lformat.setStyle(QTextListFormat.Style.ListDisc)
                    elif bformat.indent() == 1:
                        lformat.setStyle(QTextListFormat.Style.ListCircle)
                    elif bformat.indent() >= 2:
                        lformat.setStyle(QTextListFormat.Style.ListSquare)

                # Numbered list
                elif (
                    lstyle == QTextListFormat.Style.ListDecimal
                    or lstyle == QTextListFormat.Style.ListLowerAlpha
                    or lstyle == QTextListFormat.Style.ListLowerRoman
                ):
                    if bformat.indent() == 0:
                        lformat.setStyle(QTextListFormat.Style.ListDecimal)
                    elif bformat.indent() == 1:
                        lformat.setStyle(QTextListFormat.Style.ListLowerAlpha)
                    elif bformat.indent() >= 2:
                        lformat.setStyle(QTextListFormat.Style.ListLowerRoman)
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
            table.insertRows(table.cellAt(cursor).row() + pos, 1)

    def insert_column(self, pos=0) -> None:
        cursor = self.textCursor()
        table = cursor.currentTable()
        if table:
            table.insertColumns(table.cellAt(cursor).column() + pos, 1)

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
            return True
        return False

    def open_symbol_dialog(self) -> None:
        dialog = SymbolDialog(self.currentFont().family())
        dialog.characterClicked.connect(self.insert_symbol)
        dialog.show()

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
                _ = QMessageBox.warning(
                    self,
                    tr("Unvalid link"),
                    tr("The link is not valid. Check the address and try again."),
                    QMessageBox.StandardButton.Ok,
                )
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

    def current_text_props(self) -> dict:
        cursor = self.textCursor()
        cformat = cursor.charFormat()
        props = {}

        if not cursor.hasSelection():
            if cformat.fontWeight() == 700:
                props["bold"] = True
            else:
                props["bold"] = False
            props["italic"] = cformat.fontItalic()
            props["underlined"] = cformat.fontUnderline()
            props["family"] = self.has_format(
                cformat.fontFamilies(), self.last_format["family"]
            )

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
            props["color"] = self.textColor()
            # props["bcolor"] = self.accurate_background_color()

            # print(props)
            # print("BG_Colour accurate", props["bcolor"].name())

        return props

    def has_format(self, fmt, default):
        if fmt:
            return fmt
        else:
            return default

    def contextMenuEvent(self, e: QContextMenuEvent):
        self.menu.open_(
            e.globalPos(),
            self.current_text_props(),
            self.textCursor().hasSelection(),
            bool(QApplication.clipboard().text()),
            self.in_table(),
            self.has_hyperlink(e.pos()),
        )


class TextEditorMenu(QMenu):
    fontSet = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = TextEditorMenuView()
        self.ui.setUi(self)

        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        self._fontProperties = {}

        self.connect_signals()

    def open_(
        self,
        globalPos: QPoint,
        props: dict,
        copy: bool,
        paste: bool,
        table: bool,
        hyperlink: bool,
    ) -> None:
        self.show_font_props(props)
        self.ui.ac_Copy.setEnabled(copy)
        self.ui.ac_Cut.setEnabled(copy)
        self.ui.ac_Paste.setEnabled(paste)
        self.enable_table_tools(table)
        self.enable_hyperlink_tools(hyperlink)
        self.exec(globalPos)

    def connect_signals(self) -> None:
        self.ui.cb_Font.currentFontChanged.connect(self.on_font_family_set)
        self.ui.cb_FontSize.currentIndexChanged.connect(self.on_font_size_set)
        self.ui.cb_FontSize.textEntered.connect(self.on_font_size_set)
        self.ui.tb_Bold.toggled.connect(self.on_bold_set)
        self.ui.tb_Italic.toggled.connect(self.on_italic_set)
        self.ui.tb_Underline.toggled.connect(self.on_underlined_set)
        self.ui.align_group.buttonToggled.connect(self.on_alignment_set)
        self.ui.tb_TextColor.clicked.connect(
            lambda: self.on_font_color_set(self.text_color())
        )
        self.ui.color_menu.colorChanged.connect(self.on_font_color_set)

    @pyqtSlot(dict)
    def show_font_props(self, props: dict) -> None:
        for key, value in props.items():
            match key:
                case "family":
                    font = QFont()
                    font.setFamilies(value)
                    self.ui.cb_Font.setCurrentFont(font)  # QFontComboBox
                case "size":
                    self.ui.cb_FontSize.setEditText(
                        str(value)
                    )  # QComboBox with point sizes
                case "bold":
                    self.ui.pb_Bold.setChecked(value)  # Checkable QPushButton
                case "italic":
                    self.ui.pb_Italic.setChecked(value)  # Checkable QPushButton
                case "underlined":
                    self.ui.pb_Underline.setChecked(value)  # Checkable QPushButton
                case "alignment":
                    self.show_alignment(value)
                # case "color":
                #     self.set_button_color(self._fontProperties["color"], value)
            self._fontProperties[key] = value

    def set_button_color(self, old: QColor, color: QColor) -> None:
        self.ui.tb_TextColor.setProperty("color", color)
        ic_engine = SvgIconEngine(Svg.from_file("resources/icons/ic_textColor.svg"))
        ic_engine.set_path_color("lineBottom", color)
        self.ui.tb_TextColor.setIcon(QIcon(ic_engine))

    def text_color(self) -> QColor:
        return self.ui.tb_TextColor.property("color")

    def show_alignment(self, alignment: Qt.AlignmentFlag) -> None:
        if alignment == Qt.AlignmentFlag.AlignLeft:
            self.ui.pb_AlignLeft.setChecked(True)
        elif alignment == Qt.AlignmentFlag.AlignCenter:
            self.ui.pb_AlignCenter.setChecked(True)
        else:
            self.ui.align_group.setExclusive(False)
            self.ui.pb_AlignCenter.setChecked(False)
            self.ui.pb_AlignLeft.setChecked(False)
            self.ui.align_group.setExclusive(True)

    def on_font_family_set(self) -> None:
        props = {}
        props["family"] = self.ui.cb_Font.currentFont().families()
        self.fontSet.emit(props)

    def on_font_size_set(self) -> None:
        props = {}
        props["size"] = float(self.ui.cb_FontSize.currentFontSize())
        self.fontSet.emit(props)

    def on_font_color_set(self, color: QColor) -> None:
        props = {}
        self.set_button_color(self._fontProperties["color"], color)
        props["color"] = color
        self.fontSet.emit(props)

    def on_bold_set(self) -> None:
        props = {}
        props["bold"] = self.ui.pb_Bold.isChecked()
        self.fontSet.emit(props)

    def on_italic_set(self) -> None:
        props = {}
        props["italic"] = self.ui.pb_Italic.isChecked()
        self.fontSet.emit(props)

    def on_underlined_set(self) -> None:
        props = {}
        props["underlined"] = self.ui.pb_Underline.isChecked()
        self.fontSet.emit(props)

    def on_alignment_set(self) -> None:
        props = {}
        if self.ui.pb_AlignLeft.isChecked():
            props["alignment"] = Qt.AlignmentFlag.AlignLeft
        elif self.ui.pb_AlignCenter.isChecked():
            props["alignment"] = Qt.AlignmentFlag.AlignCenter
        self.fontSet.emit(props)

    def get_alignment(self) -> Qt.AlignmentFlag | None:
        if self.ui.pb_AlignLeft.isChecked():
            return Qt.AlignmentFlag.AlignLeft
        elif self.ui.pb_AlignCenter.isChecked():
            return Qt.AlignmentFlag.AlignCenter

    def enable_table_tools(self, enable: bool) -> None:
        self.ui.table_group.setVisible(enable)

    def enable_hyperlink_tools(self, enable: bool) -> None:
        self.ui.hyperlink_group.setVisible(enable)


class TextDelegate(BaseElementDelegate):
    def paint(
        self,
        painter: QPainter | None,
        option: QStyleOptionViewItem,
        index: QModelIndex,
        single_item=True,  # False when whole cell is painted
    ) -> None:
        if single_item:
            painter.save()
            option.rect = option.rect.adjusted(-2, -2, 2, 2)
            super().paint(painter, option, QModelIndex())
            painter.restore()

        data: TextModel = index.data()

        # Apply 2px padding for element content
        sub_rect = option.rect.adjusted(2, 2, -2, -2)

        document = QTextDocument()
        document.setHtml(data.toHtml())
        document.setDocumentMargin(8.0)  # Match TextModel's document margin
        if document.characterCount() > 0:
            document.setTextWidth(
                float(sub_rect.width() - 8)
            )  # Consistent with sizeHint

        painter.save()
        painter.translate(sub_rect.topLeft())

        document.drawContents(painter)
        painter.restore()

        if index.row() < index.model().rowCount() - 1:
            painter.save()
            pen = QPen(Qt.GlobalColor.lightGray, 1)
            painter.setPen(pen)
            painter.drawLine(
                option.rect.bottomLeft().x() + 2,
                option.rect.bottomLeft().y(),
                option.rect.bottomRight().x() - 2,
                option.rect.bottomRight().y(),
            )
            painter.restore()

    def createEditor(
        self, parent: QWidget | None, option: QStyleOptionViewItem, index: QModelIndex
    ) -> QWidget | None:
        print("Trying to create a TextEditor")
        data: TextModel = index.data(Qt.ItemDataRole.EditRole)
        editor = TextEditor(option.rect.width() - 8.0, data, parent)
        editor.sizeChanged.connect(lambda: self.sizeHintChanged.emit(index))
        editor.installEventFilter(parent)
        editor.setFocus()
        editor.enable_presenter_mode(self.pres_mode)
        return editor

    def setEditorData(self, editor: TextEditor | None, index: QModelIndex) -> None:
        self._toolset.connect_editor(editor)
        self._toolset.enable_presenter_mode(self.pres_mode)
        print("Connected TextEditor")

    def updateEditorGeometry(
        self,
        editor: TextEditor | None,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> None:
        print(f"Geometry with width: {option.rect.width() - 7}")
        editor.setGeometry(option.rect.adjusted(2, 2, -5, -2))

    def setModelData(
        self, editor: TextEditor | None, model, index: QModelIndex
    ) -> None:
        model.setData(index, editor.document())

    def destroyEditor(self, editor: TextEditor, index: QModelIndex):
        editor.sizeChanged.disconnect()
        self._toolset.close_()
        super().destroyEditor(editor, index)

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        model: TextModel | None = index.data()
        if model:
            return model.item_size
        else:
            return QSize(option.rect.width(), 30)


class TextToolset(BaseElementToolset):
    fontSet = pyqtSignal(dict)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.ui = TextToolsetView()
        self.ui.setUI(self)

        # Attributes
        self._fontProperties = {}

        self.connect_signals()
        self.set_button_color(QColor())

    @property
    def name(self) -> str:
        return "TextElement"

    def connect_editor(self, editor: TextEditor) -> None:
        self.set_font_props(editor.current_text_props())
        editor.currentPropsChanged.connect(self.set_font_props)
        editor.tableEntered.connect(self.set_table_tools_visible)

        if editor.is_empty():
            self.set_font_props(editor.current_text_props())

        self.fontSet.connect(editor.set_text_format)

        self.ui.ac_list.triggered.connect(
            lambda: editor.insert_list(QTextListFormat.Style.ListDisc)
        )
        self.ui.ac_numlist.triggered.connect(
            lambda: editor.insert_list(QTextListFormat.Style.ListDecimal)
        )
        self.ui.ac_indent.triggered.connect(lambda: editor.change_indentation(incr=1))
        self.ui.ac_dedent.triggered.connect(lambda: editor.change_indentation(incr=-1))
        self.ui.menu_table.tableSize.connect(editor.insert_table)
        self.ui.ac_symbol.triggered.connect(editor.open_symbol_dialog)
        self.ui.ac_hyperlink.triggered.connect(editor.insert_hyperlink)

        self.ui.ac_row_top.triggered.connect(editor.insert_row)
        self.ui.ac_row_bottom.triggered.connect(lambda: editor.insert_row(1))
        self.ui.ac_column_left.triggered.connect(editor.insert_column)
        self.ui.ac_column_right.triggered.connect(lambda: editor.insert_column(1))
        self.ui.ac_delete_row.triggered.connect(editor.delete_row)
        self.ui.ac_delete_column.triggered.connect(editor.delete_column)
        self.ui.ac_delete_table.triggered.connect(editor.delete_table)
        self.called.emit(self.name)

        self.setVisible(True)

    def close_(self):
        try:
            self.fontSet.disconnect()
            self.ui.ac_list.disconnect()
            self.ui.ac_numlist.disconnect()
            self.ui.ac_indent.disconnect()
            self.ui.ac_dedent.disconnect()
            self.ui.ac_table.disconnect()
            self.ui.ac_symbol.disconnect()
            self.ui.ac_hyperlink.disconnect()
            self.ui.ac_row_top.disconnect()
            self.ui.ac_row_bottom.disconnect()
            self.ui.ac_column_left.disconnect()
            self.ui.ac_column_right.disconnect()
            self.ui.ac_delete_row.disconnect()
            self.ui.ac_delete_column.disconnect()
            self.ui.ac_delete_table.disconnect()
        except (RuntimeError, TypeError):
            print("Couldn't disconnect")
            pass

        self._fontProperties.clear()

        super().close_()

    def connect_signals(self):
        self.ui.cb_Font.currentFontChanged.connect(self.on_font_family_changed)
        self.ui.cb_FontSize.currentIndexChanged.connect(self.on_font_size_changed)
        self.ui.cb_FontSize.textEntered.connect(self.on_font_size_changed)
        self.ui.ac_bold.toggled.connect(self.on_bold_set)
        self.ui.ac_italic.toggled.connect(self.on_italic_set)
        self.ui.ac_underline.toggled.connect(self.on_underlined_set)
        self.ui.align_group.triggered.connect(self.on_alignment_set)
        self.ui.veralign_group.triggered.connect(self.on_vertical_alignment_set)
        self.ui.ac_textcolor.triggered.connect(
            lambda: self.on_color_set(self.current_color())
        )
        self.ui.color_menu.colorChanged.connect(self.on_color_set)

    def enable_presenter_mode(self, enabled: bool):
        self.setVisible(not enabled)

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
                    self.ui.cb_Font.setCurrentFont(font)  # QFontComboBox
                case "size":
                    self.ui.cb_FontSize.setEditText(
                        str(value)
                    )  # QComboBox with point sizes
                case "bold":
                    self.ui.ac_bold.setChecked(value)  # Checkable QPushButton
                case "italic":
                    self.ui.ac_italic.setChecked(value)  # Checkable QPushButton
                case "underlined":
                    self.ui.ac_underline.setChecked(value)  # Checkable QPushButton
                case "alignment":
                    self.show_alignment(value)
                case "veralign":
                    self.show_vertical_alignment(value)
                # case "color":
                #     self.set_button_color(self._fontProperties["color"], value)
                # case "bcolor":
                #     self.set_bg_button_color(self._fontProperties["bcolor"], value)
            self._fontProperties[key] = value

    def get_all(self):
        self._fontProperties["family"] = self.ui.cb_Font.currentFont().families()
        self._fontProperties["size"] = float(self.ui.cb_FontSize.currentFontSize())
        self._fontProperties["bold"] = self.ui.ac_bold.isChecked()
        self._fontProperties["italic"] = self.ui.ac_italic.isChecked()
        self._fontProperties["underlined"] = self.ui.ac_underline.isChecked()
        self._fontProperties["alignment"] = self.get_alignment()
        self._fontProperties["veralign"] = self.get_vertical_alignment()
        self._fontProperties["color"] = self.ui.ac_textcolor.property("color")
        # self._fontProperties["bcolor"] = self.csb_BackgroundColor.color()
        return self._fontProperties

    def on_font_family_changed(self) -> None:
        props = {}
        props["family"] = self.ui.cb_Font.currentFont().families()
        self.fontSet.emit(props)

    def on_font_size_changed(self) -> None:
        props = {}
        props["size"] = float(self.ui.cb_FontSize.currentFontSize())
        self.fontSet.emit(props)

    def on_color_set(self, color: QColor) -> None:
        props = {}
        if color.name() == "#ffffff" or color.name() == "#000000":
            props["color"] = QColor()
        else:
            props["color"] = color
        self.set_button_color(props["color"])
        self.fontSet.emit(props)

    def set_button_color(self, color: QColor) -> None:
        if color:
            svg = Svg.from_file("resources/icons/ic_textColor.svg")
            if color.isValid():
                ic_engine = SvgIconEngine(svg)
                ic_engine.set_path_color("lineBottom", color)
            else:
                theme_val = Settings.qsettings().value("User/appearance", "light", str)
                ic_engine = SvgIconEngine(svg)
                if theme_val == "light":
                    ic_engine.set_path_color("lineBottom", QColor(Qt.GlobalColor.black))
                else:
                    ic_engine.set_path_color("lineBottom", QColor(Qt.GlobalColor.white))
            self.ui.ac_textcolor.setProperty("color", color)
            self.ui.ac_textcolor.setIcon(QIcon(ic_engine))

    def current_color(self) -> QColor:
        return self.ui.ac_textcolor.property("color")

    # def bg_color(self) -> QColor:
    #     return self.csb_BackgroundColor.color()

    def on_bold_set(self) -> None:
        props = {}
        props["bold"] = self.ui.ac_bold.isChecked()
        self.fontSet.emit(props)

    def on_italic_set(self) -> None:
        props = {}
        props["italic"] = self.ui.ac_italic.isChecked()
        self.fontSet.emit(props)

    def on_underlined_set(self) -> None:
        props = {}
        props["underlined"] = self.ui.ac_underline.isChecked()
        self.fontSet.emit(props)

    def show_alignment(self, alignment: Qt.AlignmentFlag) -> None:
        if alignment == Qt.AlignmentFlag.AlignLeft:
            self.ui.ac_align_left.setChecked(True)
        elif alignment == Qt.AlignmentFlag.AlignCenter:
            self.ui.ac_align_center.setChecked(True)
        elif alignment == Qt.AlignmentFlag.AlignRight:
            self.ui.ac_align_right.setChecked(True)
        elif alignment == Qt.AlignmentFlag.AlignJustify:
            self.ui.ac_align_justify.setChecked(True)

    def show_vertical_alignment(
        self, alignment: QTextCharFormat.VerticalAlignment
    ) -> None:
        if alignment == QTextCharFormat.VerticalAlignment.AlignSubScript:
            self.ui.ac_subscript.setChecked(True)
        elif alignment == QTextCharFormat.VerticalAlignment.AlignSuperScript:
            self.ui.ac_superscript.setChecked(True)
        else:
            self.ui.ac_subscript.setChecked(False)
            self.ui.ac_superscript.setChecked(False)

    def on_alignment_set(self) -> None | Qt.AlignmentFlag:
        props = {}
        if self.ui.ac_align_left.isChecked():
            props["alignment"] = Qt.AlignmentFlag.AlignLeft
        elif self.ui.ac_align_center.isChecked():
            props["alignment"] = Qt.AlignmentFlag.AlignCenter
        elif self.ui.ac_align_right.isChecked():
            props["alignment"] = Qt.AlignmentFlag.AlignRight
        elif self.ui.ac_align_justify.isChecked():
            props["alignment"] = Qt.AlignmentFlag.AlignJustify
        self.fontSet.emit(props)

    def get_alignment(self) -> Qt.AlignmentFlag | None:
        if self.ui.ac_align_left.isChecked():
            return Qt.AlignmentFlag.AlignLeft
        elif self.ui.ac_align_center.isChecked():
            return Qt.AlignmentFlag.AlignCenter
        elif self.ui.ac_align_right.isChecked():
            return Qt.AlignmentFlag.AlignRight
        elif self.ui.ac_align_justify.isChecked():
            return Qt.AlignmentFlag.AlignJustify
        return None

    def on_vertical_alignment_set(self):
        props = {}
        if self.ui.ac_superscript.isChecked():
            props["veralign"] = QTextCharFormat.VerticalAlignment.AlignSuperScript
            self.ui.ac_subscript.setChecked(False)
        elif self.ui.ac_subscript.isChecked():
            props["veralign"] = QTextCharFormat.VerticalAlignment.AlignSubScript
            self.ui.ac_superscript.setChecked(False)
        else:
            props["veralign"] = QTextCharFormat.VerticalAlignment.AlignNormal
        self.fontSet.emit(props)

    def get_vertical_alignment(self) -> QTextCharFormat.VerticalAlignment:
        if self.ui.ac_superscript.isChecked():
            return QTextCharFormat.VerticalAlignment.AlignSuperScript
        elif self.ui.ac_subscript.isChecked():
            return QTextCharFormat.VerticalAlignment.AlignSubScript
        else:
            return QTextCharFormat.VerticalAlignment.AlignNormal

    def open_symbol_dialog(self) -> None:
        dialog = SymbolDialog(self.cb_Font.currentFont().family())
        dialog.characterClicked.connect(self.send_symbol)
        dialog.show()

    # def hideEvent(self, e: QHideEvent) -> None:
    #     self.table_frame.hide()
    #     super().hideEvent(e)


class SymbolDialog(QDialog):
    characterClicked = pyqtSignal(str)

    def __init__(
        self, fontfamily: str, parent=None, flags=Qt.WindowType.SubWindow
    ) -> None:
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
                    item = QTableWidgetItem(
                        chr(self.chars[charset][irow * 16 + icolumn])
                    )
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
    def id() -> int:
        return 1

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
        action.setData(TextElementDefinitions)
        action.setProperty("is_element_action", True)
        return action

    @staticmethod
    def toolset(parent) -> TextToolset:
        return TextToolset(parent)

    @staticmethod
    def editor(model: TextModel):
        return TextEditor(model)

    @staticmethod
    def resource_flag():
        return ResourceFlag.NoResource

    @staticmethod
    def mime_types() -> list[str]:
        return ["text/plain", "text/html"]

    @staticmethod
    def supports_mime_data(mime_data: QMimeData) -> bool:
        return (
            ("text/plain" in mime_data.formats() or "text/html" in mime_data.formats())
            and not mime_data.hasImage()
            and not mime_data.hasUrls()
        )

    @staticmethod
    def model_from_mime_data(
        rescont: ResourceContainer, mime_data: QMimeData
    ) -> TextModel | None:
        resobj = rescont.create(TextElementDefinitions.type())
        model = TextModel(resobj)
        common_types = set(TextElementDefinitions.mime_types()) & set(
            mime_data.formats()
        )
        if "text/html" in common_types:
            print(f"Raw html: {mime_data.html()}")
            html = mime_data.html()

            # Remove fragments markers
            html = html.replace("<!--StartFragment-->", "").replace(
                "<!--EndFragment-->", ""
            )

            # Remove problematic CSS properties that break text wrapping
            html = html.replace("white-space: pre;", "")
            html = html.replace("white-space:pre;", "")

            # Remove fixed line-height that interferes with Qt's layout
            import re

            html = re.sub(r"line-height:\s*\d+px;?", "", html)

            # Convert nested divs to spans to allow proper text wrapping
            # This prevents each line from being a non-wrapping block
            html = re.sub(r"<div><span", "<span", html)
            html = re.sub(r"</span></div>", "</span><br>", html)

            print(f"Adjusted html: {html}")
            model.setHtml(html)
        elif "text/plain" in common_types:
            model.setPlainText(mime_data.text())
        return model

    @staticmethod
    def model_from_bytes(
        resobj: ResourceObject, stream: QByteArray | QDataStream
    ) -> TextModel | None:
        if resobj.path:
            return TextModel(resobj)
        else:
            reader = (
                QDataStream(stream, QIODevice.OpenModeFlag.ReadOnly)
                if isinstance(stream, QByteArray)
                else stream
            )
            html = reader.readQString()

            if not reader.status() & QDataStream.Status.ReadPastEnd:
                model = TextModel(resobj)
                model.setHtml(html)
                return model

        return None
