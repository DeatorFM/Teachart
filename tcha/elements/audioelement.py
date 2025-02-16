from PyQt6.QtWidgets import QStyledItemDelegate, QStyleOptionButton, QStyle, QApplication, QSizePolicy, QWidget
from PyQt6.QtGui import QFocusEvent, QIcon, QPen, QCursor, QColor, QPainter, QPainterPath
from PyQt6.QtCore import QTime, pyqtSignal, Qt, QXmlStreamWriter, QSize, QRect, QMargins, QModelIndex
from PyQt6.QtXml import QDomElement
from PyQt6.QtMultimedia import QMediaPlayer
from tcha.elements.baseelement import BaseElement, BaseModel
from ui.ui_AudioElement import AudioView
from dataclasses import field, dataclass
from tcha.resmanager import ResourceType

@dataclass(frozen=True)
class AudioModel(BaseModel):
    nameChanged = pyqtSignal(str)
    repeatToggled = pyqtSignal(bool)
    repeatTimesChanged = pyqtSignal(int)
    pauseLengthChanged = pyqtSignal(int)
    startTimeChanged = pyqtSignal(int)
    endTimeChanged = pyqtSignal(int)

    resource: str
    name: str
    is_repeating: bool = field(default=False)
    repeats: int = field(default=1)
    pause_length: int = field(default=0) # in secs
    start_time: int = field(default=0) # in msecs from the start of the track
    end_time: int = field(default= 0) # in msecs from the end of the track
    chapters: list = field(default_factory=list)

    def __post_init__(self, parent=None) -> None:
        super().__init__(parent)
        
    @staticmethod
    def restype() -> ResourceType:
        return ResourceType.AUDIO
    
    def xml(self, stream: QXmlStreamWriter, path: str) -> QXmlStreamWriter:
        stream.writeEmptyElement("h", "element")
        stream.writeAttribute("h", "type", "AudioElement")
        stream.writeAttribute("h", "resource", path)
        stream.writeAttribute("h", "name", self.name)
        stream.writeAttribute("h", "repeating", str(int(self.is_repeating)))
        stream.writeAttribute("h", "repeats", str(self.repeats))
        stream.writeAttribute("h", "pause_length", str(self.pause_length))
        stream.writeAttribute("h", "start_time", str(self.start_time))
        stream.writeAttribute("h", "end_time", str(self.end_time))
        return stream
    
    @classmethod
    def read(cls, domelement: QDomElement) -> "AudioModel":
        if domelement.attribute("type") == "AudioElement":
            resource = domelement.attribute("resource")
            name = domelement.attribute("name")
            is_repeating = bool(int(domelement.attribute("repeating")))
            repeats = int(domelement.attribute("repeats"))
            pause_length = int(domelement.attribute("pause-length"))
            start_time = int(domelement.attribute("start-time"))
            end_time = int(domelement.attribute("end-time"))
            return cls(resource, name, is_repeating, repeats, pause_length, start_time, end_time)
        else:
            raise TypeError("DOM-Element has not attribute type=AudioElement.")

    def set_resource(self, res: str) -> None:
        object.__setattr__(self, "resource", res)

    def set_name(self, name: str) -> None:
        object.__setattr__(self, "name", name)
    
    def set_repeating(self, on: bool) -> None:
        object.__setattr__(self, "is_repeating", on)

    def set_repeats(self, times: int) -> None:
        object.__setattr__(self, "repeats", times)

    def set_pause_length(self, sec: int) -> None:
        object.__setattr__(self, "pause_length", sec)

    def set_start_time(self, msec: int) -> None:
        object.__setattr__(self, "start_time", msec)

    def set_end_time(self, msec: int) -> None:
        object.__setattr__(self, "end_time", msec)

    def delegate(self, parent) -> QStyledItemDelegate:
        return AudioDelegate(parent)
    
    def change_on_mouse_hover(self) -> bool:
        return True
    
    def expected_size(self, width) -> QSize:
        return QSize(width, 45)

class ChapterObject:
    def __init__(self, start: QTime, end: QTime, name="") -> None:
        self.start = start
        self.end = end
        self.name = name


class AudioElement(BaseElement, AudioView):
    playbackRequested = pyqtSignal(AudioModel, bool)
    playbackStateChanged = pyqtSignal(QMediaPlayer.PlaybackState)

    def __init__(self, model: AudioModel, parent=None) -> None:
        super().__init__(parent)
        self.setUi(self)
        self.main_frame.setProperty("focussed", False)
        self.setAutoFillBackground(True)

        self._model = model
        self.is_own_model = False
        self.le_name.setText(self._model.name)
        self.le_name.setCursorPosition(0)

        self.connect_signals()
        self.setAttribute(Qt.WidgetAttribute.WA_NoMousePropagation, True)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
    
    def model(self) -> BaseModel:
        return self._model
    
    @property
    def toolset(self) -> str:
        return "AudioToolset"

    def connect_signals(self) -> None:
        self.swi_PlayPause.stateChanged.connect(self.on_playpause)
        self.le_name.textChanged.connect(self._model.set_name)    

    def on_playback_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        if state == QMediaPlayer.PlaybackState.StoppedState:
            self.swi_PlayPause.changeState(1)
        elif state == QMediaPlayer.PlaybackState.PlayingState:
            self.swi_PlayPause.changeState(2)
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.swi_PlayPause.changeState(1)

    def on_playpause(self) -> None:
        self.set_playback_state()

    def set_playback_state(self) -> None:
        if self.swi_PlayPause.state() == 1:
            self.playbackStateChanged.emit(QMediaPlayer.PlaybackState.PausedState)
        elif self.swi_PlayPause.state() == 2:
            self.playbackStateChanged.emit(QMediaPlayer.PlaybackState.PlayingState)

    def on_model_set(self, model: AudioModel):
        if model == self._model:
            self.is_own_model = True
        else:
            self.is_own_model = False

    def focusInEvent(self, a0: QFocusEvent) -> None:
        self.playbackRequested.emit(self._model, False)
        super().focusInEvent(a0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = min(event.size().width(), 180) 
        self.main_frame.setGeometry(0, 0, width, event.size().height())
        self.le_name.setFixedWidth(width - 40) 
        print(f"AudioElement resized to: {event.size()}")
        

class AudioDelegate(QStyledItemDelegate):
    editorOpened = pyqtSignal(QWidget)

    def __init__(self, parent = ...):
        super().__init__(parent)
        self._play_icon = QIcon("resources/icons/ic_play.svg")

    
    def paint(self, painter, option, index):
        sub_rect = option.rect.adjusted(5, 5, -5, -5)
        button_rect = sub_rect.adjusted(3, 5, -7, -3)
        button_rect.setWidth(23)
        button_rect.setHeight(23)
        text_rect = QRect(sub_rect.left() + 33, sub_rect.top() + 10, min(sub_rect.width() - 33, 180 - 33), 20)

        painter.save()

        style = option.widget.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, option, painter, option.widget)

        mouse_pos = option.widget.viewport().mapFromGlobal(QCursor.pos())

        if button_rect.contains(mouse_pos):
            path = QPainterPath()
            path.addRoundedRect(button_rect.toRectF(), 4, 4) 
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.fillPath(path, QColor(236, 236, 236, 160))

        button_option = QStyleOptionButton()
        button_option.rect = button_rect
        button_option.icon = self._play_icon
        button_option.iconSize = QSize(20, 20)
        button_option.state = QStyle.StateFlag.State_Enabled
        button_option.features = QStyleOptionButton.ButtonFeature.Flat
        
        QApplication.style().drawControl(QStyle.ControlElement.CE_PushButton, button_option, painter)

        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWrapAnywhere, index.data().name)

        painter.restore()

        if index.row() < index.model().rowCount() - 1:
            painter.save()
            pen = QPen(Qt.GlobalColor.lightGray, 1)
            painter.setPen(pen)
            painter.drawLine(option.rect.bottomLeft().x() + 5, option.rect.bottomLeft().y(), option.rect.bottomRight().x() - 5, option.rect.bottomRight().y())
            painter.restore()
    
    def createEditor(self, parent, option, index):
        editor = AudioElement(index.data(), parent)
        editor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.editorOpened.emit(editor)
        return editor
    
    def updateEditorGeometry(self, editor, option, index):
        sub_rect = option.rect.marginsAdded(QMargins(-6, -8, -5, -5))
        print("Audio rect", sub_rect.width(), sub_rect.height())
        editor.setGeometry(sub_rect)

    def setModelData(self, editor, model, index):
        self.destroyEditor(editor, index)

    def destroyEditor(self, editor: AudioElement, index: QModelIndex) -> None:
        """Disconnects signals and destroys the editor."""
        print("Destroying AudioElement")
        try:
            editor.playbackRequested.disconnect()
        except TypeError:
            pass
        editor.deleteLater()
        super().destroyEditor(editor, index)

    def passthru(self) -> bool:
        return True
    
    def sizeHint(self, option, index):
        if index.data():
            return QSize(option.rect.width(), 45)
        else:
            return QSize(option.rect.width(), 0)