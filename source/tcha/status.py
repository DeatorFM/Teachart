import typing

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QLabel, QPushButton, QSpinBox, QStatusBar, QWidget


class StatusLabel(QLabel):
    def __init__(self, text: str, permanent=False, parent=None) -> None:
        super().__init__(parent)
        if text:
            self.setText(text)
        self.permanent = permanent
        self.setContentsMargins(5, 0, 5, 0)


class StatusButton(QPushButton):
    def __init__(self, text: str, permanent=False, parent=None) -> None:
        super().__init__(text, parent)
        self.permanent = permanent
        self.setContentsMargins(5, 0, 5, 0)


class StatusSpinBox(QSpinBox):
    def __init__(self, minimum: int, maximum: int, permanent=False, parent=None) -> None:
        super().__init__(parent)
        self.setMinimum(minimum)
        self.setMaximum(maximum)
        self.permanent = permanent
        self.setContentsMargins(5, 0, 5, 0)


class StatusBarContainer(QObject):
    """Container to hold and manage all widgets that should be displayed in a status bar."""

    messageShown = pyqtSignal(str, int)
    elementAdded = pyqtSignal(int)

    def __init__(self, *args: QWidget) -> None:
        super().__init__()
        self._elements = list(args)

    def add_status_widget(self, widget: QWidget, pos=-1) -> None:
        if pos > -1:
            self._elements.insert(widget, pos)
        else:
            self._elements.append(widget)
        self.elementAdded(pos)

    def show_message(self, text: str, msecs: int = 0) -> None:
        self.messageShown.emit(text, msecs)

    def __iter__(self) -> typing.Iterator:
        return iter(self._elements)


class StatusBar(QStatusBar):
    """Custom QStatusBar object that can handle a StatusBarContainer object."""

    def __init__(self, parent=...):
        super().__init__(parent)
        self._container: StatusBarContainer | None = None

        self.setMinimumHeight(28)
        self.setContentsMargins(5, 2, 5, 2)

    def set_container(self, container: StatusBarContainer) -> None:
        self.clear_status_bar()
        self._container = container
        self._container.messageShown.connect(self.showMessage)
        self._container.elementAdded.connect(self.add)
        self._set_status_widgets()

    def _set_status_widgets(self) -> None:
        for widget in self._container:
            if widget.permanent:
                self.addPermanentWidget(widget)
                widget.show()
                continue
            self.addWidget(widget)
            widget.show()

    def add(self, at: int) -> None:
        self.addWidget(self._elements[at])

    def clear_status_bar(self) -> None:
        if self._container:
            for widget in self._container:
                self.removeWidget(widget)
