from PyQt6.QtGui import QFocusEvent
from PyQt6.QtCore import QTime, pyqtSignal, Qt, QXmlStreamWriter
from PyQt6.QtXml import QDomElement
from PyQt6.QtMultimedia import QMediaPlayer
from elements.baseelement import BaseElement, BaseModel
from ui.UI_AudioElement import AudioView
from dataclasses import field, dataclass
from educ.resmanager import ResourceType

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

        self._model = model
        self.is_own_model = False
        self.le_name.setText(self._model.name)

        self.connect_signals()
        self.setAttribute(Qt.WidgetAttribute.WA_NoMousePropagation, True)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
    
    def model(self) -> BaseModel:
        return self._model
    
    @property
    def toolset(self) -> str:
        return "AudioToolset"
    
    def on_focussed(self, focussed: bool) -> None:
        self.main_frame.setProperty("focussed", focussed)
        self.main_frame.style().polish(self.main_frame)

    def connect_signals(self) -> None:
        self.swi_PlayPause.stateChanged.connect(self.on_playpause)
        self.le_name.textChanged.connect(self._model.set_name)    

    def on_playback_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        if self.is_own_model == True:
            if state == QMediaPlayer.PlaybackState.StoppedState:
                self.swi_PlayPause.changeState(1)
            elif state == QMediaPlayer.PlaybackState.PlayingState:
                self.swi_PlayPause.changeState(2)
            elif state == QMediaPlayer.PlaybackState.PausedState:
                self.swi_PlayPause.changeState(1)

    def on_playpause(self) -> None:
        if self.is_own_model == True:
            self.set_playback_state()
            self.focussed.emit(self)
        else:
            self.focussed.emit(self)
            self.playbackRequested.emit(self._model, True)      

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
        print("AudioElement focussed")
        if self.is_own_model == False:
            self.playbackRequested.emit(self._model, False)
        self.focussed.emit(self)
        super().focusInEvent(a0)