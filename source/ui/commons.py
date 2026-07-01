from pathlib import Path

from PyQt6.QtCore import QT_TR_NOOP as tr
from PyQt6.QtCore import QEvent, QMimeData, QObject, QPoint, QSize, Qt, QUrl, pyqtSignal
from PyQt6.QtGui import (
    QAction,
    QColor,
    QCursor,
    QDesktopServices,
    QFont,
    QIcon,
    QMouseEvent,
    QPixmap,
    QTextCharFormat,
)
from PyQt6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListView,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QToolButton,
    QWidget,
    QWidgetAction,
)

from tcha.dbmodels import FilteredCourseModel, FilteredStudentModel
from ui.StyledWidget import *


class IconButton(QPushButton):
    def __init__(self, icon: QIcon, parent=None, width=20, height=20):
        super().__init__(parent)
        ic = icon
        self.setIcon(ic)
        self.setIconSize(QSize(width, height))
        self.setProperty("borderless", True)


class SplitButton(QFrame):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.button_layout = QHBoxLayout(self)
        self.button_layout.setSpacing(0)
        self.button_layout.setContentsMargins(2, 0, 2, 0)
        self.lbutton = QPushButton()
        self.lbutton.setObjectName("lbutton")
        self.button_layout.addWidget(self.lbutton)
        self.rbutton = QPushButton()
        self.rbutton.setObjectName("rbutton")
        self.button_layout.addWidget(self.rbutton)


class PrettyButton(QPushButton):
    def __init__(self, title, iconpath: str, iconpathhover: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName(title)
        self.default_icon = QIcon()
        self.default_icon.addPixmap(QPixmap(f"{iconpath}"))
        self.hover_icon = QIcon()
        self.hover_icon.addPixmap(QPixmap(f"{iconpathhover}"))
        self.setIcon(self.default_icon)
        self.setIconSize(QSize(20, 20))
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.installEventFilter(self)

    def eventFilter(self, a0: "QObject", event: "QEvent") -> bool:
        if event.type() == QEvent.Type.HoverEnter:
            self.setIcon(self.hover_icon)
            self.setIconSize(QSize(20, 20))
        elif event.type() == QEvent.Type.HoverLeave:
            self.setIcon(self.default_icon)
        super().eventFilter(a0, event)


class SwitchButton(QPushButton):
    stateChanged = pyqtSignal(int)

    def __init__(self, icon1: QIcon, icon2: QIcon, parent=None) -> None:
        super().__init__(parent)
        self.icon1 = icon1
        self.icon2 = icon2
        self.setIcon(self.icon1)
        self.setIconSize(QSize(20, 20))
        self._state = 1
        self.clicked.connect(self.switchState)

    def switchState(self) -> None:
        if self._state == 1:
            self.setIcon(self.icon2)
            self.style().polish(self)
            self._state = 2
        else:
            self.setIcon(self.icon1)
            self.style().polish(self)
            self._state = 1
        self.stateChanged.emit(self.state())

    def changeState(self, state: int) -> None:
        if state == 1:
            self.setIcon(self.icon1)
            self.style().polish(self)
            self._state = 1
        elif state == 2:
            self.setIcon(self.icon2)
            self.style().polish(self)
            self._state = 2

    def state(self) -> int:
        return self._state


class SwitchAction(QAction):
    stateChanged = pyqtSignal(int)

    def __init__(self, icon1: QIcon, icon2: QIcon, parent=None) -> None:
        super().__init__(icon1, None, parent)
        self.icon1 = icon1
        self.icon2 = icon2
        self._state = 1
        self.triggered.connect(self.switch_state)

    def switch_state(self) -> None:
        if self._state == 1:
            self.setIcon(self.icon2)
            self._state = 2
        else:
            self.setIcon(self.icon1)
            self._state = 1
        self.stateChanged.emit(self.state())

    def changeState(self, state: int) -> None:
        if state == 1:
            self.setIcon(self.icon1)
            self._state = 1
        elif state == 2:
            self.setIcon(self.icon2)
            self._state = 2

    def state(self) -> int:
        return self._state


class MultiLabelAction(QAction):
    """A QAction whose label text can be changed by binding it to key words."""

    def __init__(
        self,
        parent=...,
        **texts: dict[str, str],
    ):

        super().__init__(parent)
        self._texts = texts

    def define_text(self, key: str, text: str) -> None:
        self._texts[key] = text

    def set_text(self, key: str) -> None:
        self.setText(self._texts.get(key))

    def set_tool_tip(self, key: str) -> None:
        self.setToolTip(self._texts.get(key))


class DoubleClickButton(QPushButton):
    doubleClicked = pyqtSignal()

    def mouseDoubleClickEvent(self, a0: QMouseEvent) -> None:
        self.doubleClicked.emit()


class ColorAction(QWidgetAction):
    colorSelected = pyqtSignal(QColor)

    def __init__(self, colors: list[QColor], parent=None) -> None:
        super().__init__(parent)
        widget = QWidget(parent)
        layout = QGridLayout(widget)
        layout.setSpacing(0)
        layout.setContentsMargins(2, 2, 2, 2)
        palette = colors
        count = len(palette)
        rows = count // round(count**0.5)
        for row in range(rows):
            for column in range(count // rows):
                color = palette.pop(0)
                # print(color.name(QColor.NameFormat.HexRgb))
                button = QToolButton(widget)
                button.setAutoRaise(True)
                button.clicked.connect(
                    lambda state, color=color: self.handleButton(color)
                )
                pixmap = QPixmap(16, 16)
                pixmap.fill(color)
                button.setIcon(QIcon(pixmap))
                layout.addWidget(button, row, column)
        self.setDefaultWidget(widget)

    def handleButton(self, color: QColor):
        self.parent().hide()
        self.colorSelected.emit(color)
        # print(color.name(QColor.NameFormat.HexRgb))


class ColorMenu(QMenu):
    colorChanged = pyqtSignal(QColor)

    def __init__(self, colors: list[QColor], parent=None) -> None:
        QMenu.__init__(self, parent)
        self.ac_color = ColorAction(colors, self)
        self.ac_color.colorSelected.connect(self.changeColor)
        self.addAction(self.ac_color)
        self.addSeparator()
        self.ac_CustomColor = self.addAction("Custom Color")
        self.ac_CustomColor.triggered.connect(self.from_color_dialog)

    def changeColor(self, color: QColor) -> None:
        self.colorChanged.emit(color)

    def from_color_dialog(self) -> None:
        color = QColorDialog.getColor()
        self.changeColor(color)


class PointSpacer(QLabel):
    def __init__(self, spaces: int, parent=None) -> None:
        super().__init__(parent)
        self.setText("" * spaces)


class ComboBoxListView(QListView):
    keyPress = pyqtSignal(QEvent)

    def event(self, event: QEvent) -> bool:
        # Only handle mouse and special keys, pass other events up
        if event.type() == QEvent.Type.KeyPress:
            print("Key press in view")
            key = event.key()
            if key not in (
                Qt.Key.Key_Up,
                Qt.Key.Key_Down,
                Qt.Key.Key_Enter,
                Qt.Key.Key_Escape,
            ):
                self.keyPress.emit(event)
        return super().event(event)

    def showEvent(self, a0):
        if self.model().rowCount() > 0:
            super().showEvent(a0)


class LabeledWidget(QWidget):
    def __init__(self, label: str, widget: QWidget, parent=None):
        super().__init__(parent, Qt.WindowType.Widget)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.label = QLabel(label)
        layout.addWidget(self.label)
        layout.addWidget(widget)
        self.setMaximumHeight(33)

    def set_label_text(self, text: str) -> None:
        self.label.setText(text)


class StrongLineEdit(QLineEdit):
    def keyPressEvent(self, a0):
        self.setFocus()
        return super().keyPressEvent(a0)

    def focusOutEvent(self, e: QEvent):
        if e.reason() == Qt.FocusReason.PopupFocusReason:
            self.setFocus()
            e.ignore()
            return
        print("Other focus out reason: ", e.reason())
        return super().focusOutEvent(e)


class SearchableComboBox(QComboBox):
    def __init__(self, parent=...):
        """A QComboBox that also functions as a search field for its items and supports filtered dbmodels."""
        super().__init__(parent)
        self.setLineEdit(StrongLineEdit(self))
        self.setView(ComboBoxListView(self))
        self.view().keyPress.connect(self.lineEdit().keyPressEvent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.setCompleter(None)
        self.lineEdit().textEdited.connect(self.filter_items)

    def filter_items(self, text: str):
        print("Text searched ", text)
        if isinstance(self.model(), FilteredCourseModel) or isinstance(
            self.model(), FilteredStudentModel
        ):
            self.model().set_search_filter(text)
            if self.model().rowCount() > 0:
                self.showPopup()
            else:
                self.hidePopup()
            self.setEditText(text)

    def showPopup(self):
        super().showPopup()
        cursor_pos = self.lineEdit().cursorPosition()
        self.lineEdit().setFocus()
        self.lineEdit().setCursorPosition(cursor_pos)

    def focusOutEvent(self, event):
        if self.view().isVisible():
            self.lineEdit().setFocus()
        else:
            super().focusOutEvent(event)


class PasteConfirmation(QMessageBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PasteMessageBox")
        self.setWindowTitle(tr("Select paste method"))
        self.setIcon(QMessageBox.Icon.Question)
        self.setText("This cell already has content. How would you like to paste?")

        self.pb_replace = self.addButton(
            tr("Replace"), QMessageBox.ButtonRole.ActionRole
        )
        self.pb_replace.setToolTip(
            tr("Replaces the selected cell with the copied cell.")
        )
        self.pb_replace.clicked.connect(self.accept)

        self.pb_append = self.addButton(tr("Append"), QMessageBox.ButtonRole.ActionRole)
        self.pb_append.setToolTip(
            tr(
                "Appends the copied cell's contents after the last element of the selected cell."
            )
        )
        self.pb_append.clicked.connect(self.accept)
        self.pb_cancel = self.addButton(QMessageBox.StandardButton.Cancel)
        self.setDefaultButton(QMessageBox.StandardButton.Cancel)

    def selected_paste_method(self) -> int:
        if self.clickedButton() == self.pb_replace:
            return 1
        if self.clickedButton() == self.pb_append:
            return 2
        return 0


class NoteEdit(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self._default_font = QFont()
        self._default_font.setPointSize(10)

        self.setFont(self._default_font)

    def canInsertFromMimeData(self, source: QMimeData):
        if source.hasUrls():
            return True
        return super().canInsertFromMimeData(source)

    def insertFromMimeData(self, source: QMimeData):
        print("Pasting Data")
        if source.hasUrls():
            old_fmt = self.currentCharFormat()
            print("Pasting Urls")
            cur = self.textCursor()
            urls = source.urls()
            cur.insertBlock()
            for url in urls:
                fmt = QTextCharFormat()
                fmt.setForeground(QColor("#4673ee"))
                fmt.setFontUnderline(True)
                fmt.setAnchor(True)
                if url.isLocalFile():
                    fmt.setAnchorHref(url.toString())
                    cur.insertText(url.fileName(), fmt)
                    cur.insertBlock()
                    cur.setCharFormat(old_fmt)
            self.setFont(self._default_font)
            return

        if source.hasText() and source.text().startswith(
            ("https://", "http://", "www.")
        ):
            old_fmt = self.currentCharFormat()
            link = source.text()
            if link.startswith("www."):
                link = "http://" + link
            fmt = QTextCharFormat()
            fmt.setForeground(QColor("#4673ee"))
            fmt.setFontUnderline(True)
            fmt.setAnchor(True)
            fmt.setAnchorHref(link)
            cur = self.textCursor()
            url_text, ok = QInputDialog.getText(
                self.parent(),
                tr("Insert URL"),
                tr("Type in link text:"),
                QLineEdit.EchoMode.Normal,
                link,
            )
            if ok:
                cur.insertBlock()
                if url_text:
                    cur.insertText(url_text, fmt)
                else:
                    cur.insertText(link, fmt)
            else:
                return
            cur.insertBlock()
            cur.setCharFormat(old_fmt)
            self.setFont(self._default_font)
            return

        super().insertFromMimeData(source)

    def mousePressEvent(self, e: QMouseEvent) -> None:
        if e.button() == Qt.MouseButton.LeftButton:
            self.open_hyperlink(e.pos())
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        self.has_hyperlink(e.pos())
        super().mouseMoveEvent(e)

    def open_hyperlink(self, pos: QPoint) -> None:
        anchor = self.anchorAt(pos)
        url = QUrl(anchor)
        print(f"Clicked on link: {anchor}")
        if anchor:
            result = QDesktopServices.openUrl(url)
            if not result:
                QMessageBox.critical(
                    self,
                    tr("File not found"),
                    "{} '{}' {}".format(
                        tr("The file at"),
                        url.toLocalFile(),
                        tr("could not be found."),
                    ),
                )

    def has_hyperlink(self, pos: QPoint) -> bool:
        anchor = self.anchorAt(pos)
        if anchor:
            self.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
            return True
        else:
            self.viewport().setCursor(Qt.CursorShape.IBeamCursor)
            return False
