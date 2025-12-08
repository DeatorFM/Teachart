from PyQt6.QtWidgets import QWidget, QStyleOptionViewItem, QStyleOptionButton, QStyle, QApplication, QSizePolicy, QFileDialog
from PyQt6.QtGui import QIcon, QPen, QCursor, QColor, QPainter, QPainterPath, QMouseEvent
from PyQt6.QtCore import QObject, QTimer, QTime, pyqtSignal, Qt, QXmlStreamWriter, QSize, QRect, QMargins, QModelIndex, QXmlStreamAttributes, QT_TR_NOOP as tr
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

from nativeelements.baseelement import BaseElementDefinitions, BaseElementEditor, BaseElementModel, BaseElementDelegate, BaseElementToolset, QAction
from tcha.error import LFExceptions
from nativeelements.views import AudioEditorView
from tcha.resmanager import ResourceType, ResourceObject
from typing import Self, Type
from pathlib import Path
import os.path
import asyncio

from ui.element_toolsets import AudioToolsetView, ElementOptions

class AudioModel(BaseElementModel):
    nameChanged = pyqtSignal(str)
    repeatToggled = pyqtSignal(bool)
    repeatTimesChanged = pyqtSignal(int)
    pauseLengthChanged = pyqtSignal(int)
    startTimeChanged = pyqtSignal(int)
    endTimeChanged = pyqtSignal(int)

    def __init__(self, 
                 resource: ResourceObject, 
                 is_repeating: bool = False, 
                 repeats: int = 1, 
                 pause_length: int = 0, 
                 start_time: int = 0, 
                 end_time: int = 0, 
                 chapters: list = [], 
                 current_time: int = 0, 
                 parent = None):
        super().__init__(parent)
        self._resource = resource
        self._resource.add_member()

        self._is_repeating = is_repeating
        self._repeats = repeats # Times repeating
        self._pause_length = pause_length # Secs between repeat cycles
        self._start_time = start_time # Msecs from start of track
        self._end_time = end_time #  Msecs from end of track
        self._chapters = chapters
        self._current_time = current_time
        self._text = os.path.basename(self.resource.path)
        
    @staticmethod
    def restype() -> ResourceType:
        return ResourceType.AUDIO
    
    @property
    def name(self) -> str:
        return "AudioElement"
    
    def xml(self, writer: QXmlStreamWriter) -> QXmlStreamWriter:
        writer.writeEmptyElement("element")
        writer.writeAttribute("type", "AudioElement")
        writer.writeAttribute("file", self.resource.filename())
        writer.writeAttribute("name", self.text)
        writer.writeAttribute("repeating", str(int(self.is_repeating)))
        writer.writeAttribute("repeats", str(self.repeats))
        writer.writeAttribute("pause_length", str(self.pause_length))
        writer.writeAttribute("start_time", str(self.start_time))
        writer.writeAttribute("end_time", str(self.end_time))
        return writer
    
    @classmethod
    def read(cls: Self, xml: QXmlStreamAttributes, resobj: ResourceObject) -> Self:
        try:
            model = cls(resobj, 
                        bool(int(xml.value("repeating"))), 
                        int(xml.value("repeats")), 
                        int(xml.value("pause_length")),
                        int(xml.value("start_time")),
                        int(xml.value("end_time")))
            model.set_text(str(xml.value("name")))
            return model
        
        except (ValueError, TypeError):
            raise LFExceptions.ModelReadError(False, "Attribute for AudioModel could not be read.")
        
    @property
    def resource(self) -> ResourceObject:
        return self._resource
    
    @property
    def text(self) -> str:
        return self._text
    
    def delegate(self, toolset: BaseElementToolset, parent: QObject) -> BaseElementDelegate:
        return AudioDelegate(toolset, parent)
    
    @property
    def is_repeating(self) -> bool:
        return self._is_repeating
    
    @property
    def repeats(self) -> int:
        return self._repeats
    
    @property
    def pause_length(self) -> int:
        return self._pause_length
    
    @property
    def start_time(self) -> int:
        return self._start_time
    
    @property
    def end_time(self) -> int:
        return self._end_time
    
    @property
    def current_time(self) -> int:
        return self._current_time

    def set_resource(self, resource: ResourceObject) -> None:
        self._resource = resource
        self._resource.add_member()

    def set_text(self, text: str) -> None:
        self._text = text

    def set_repeating(self, on: bool) -> None:
        self._is_repeating = on

    def set_repeats(self, times: int) -> None:
        self._repeats = times

    def set_pause_length(self, sec: int) -> None:
        self._pause_length = sec

    def set_start_time(self, msec: int) -> None:
        self._start_time = msec

    def set_end_time(self, msec: int) -> None:
        self._end_time = msec

    def set_current_time(self, msec: int) -> None:
        self._current_time = msec
    
    def change_on_mouse_hover(self) -> bool:
        return True
    
    def expected_size(self, width) -> QSize:
        return QSize(width, 45)
    
    def __str__(self):
        return f"""AudioModel: resource={self.resource} name={self._text} repeating={self._is_repeating} repeats={self._repeats} 
        pause_length={self._pause_length}s start_time={self._start_time}ms end_time={self._end_time} current={self._current_time}"""
    
    def __del__(self) -> None:
        print("Audio model to be deleted")
        if self._resource:
            try:
                self._resource.delete_member()
            except RuntimeError:
                pass
        self._resource = None
        self.disconnect() 

class ChapterObject:
    def __init__(self, start: QTime, end: QTime, name="") -> None:
        self.start = start
        self.end = end
        self.name = name

class AudioEditor(BaseElementEditor):
    playbackStateChanged = pyqtSignal(QMediaPlayer.PlaybackState)
    positionChanged = pyqtSignal(int)

    def __init__(self, model: AudioModel, parent=None) -> None:
        super().__init__(parent)
        self.ui = AudioEditorView()
        self.ui.setUi(self)
        self.ui.swi_PlayPause.setEnabled(False)

        # Models
        self._model = model

        # Attributes
        self.aoutput = QAudioOutput()
        self.player = QMediaPlayer()
        self._repeats = self._model.repeats
        self._loaded = False

        self.connect_signals()
        self.setup_player(self._model)
        self.ui.le_name.setText(self._model.text)
        self.ui.le_name.setCursorPosition(0)
        self.setAttribute(Qt.WidgetAttribute.WA_NoMousePropagation, True)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

    @property
    def model(self) -> AudioModel:
        return self._model
    
    @property
    def toolset(self) -> str:
        return "AudioToolset"
    
    @property
    def duration(self) -> int:
        if self.player.hasAudio():
            return self.player.duration()
        return 0

    def connect_signals(self) -> None:
        self.ui.swi_PlayPause.stateChanged.connect(self.on_playpause_pressed)
        self.ui.le_name.textChanged.connect(self._model.set_text) 

        self.player.positionChanged.connect(self.on_position_changed)
        self.player.playbackStateChanged.connect(self.on_playback_state_changed)
        self.player.mediaStatusChanged.connect(self.on_media_status_changed)

    def setup_player(self, model: AudioModel) -> QMediaPlayer:
        self.player.setAudioOutput(self.aoutput)
        self.player.setSourceDevice(model.resource.qfile())
        print(f"Media status {self.player.mediaStatus()}")

    def on_media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.MediaStatus.LoadedMedia and not self._loaded:
            self.player.setPosition(self._model.current_time)
            self.ui.swi_PlayPause.setEnabled(True)
            self._loaded = True

    def set_playback_state(self, state: QMediaPlayer.PlaybackState) -> None:
        print(f"Playback state set to {state}")
        print(f"Audio Connected {self.player.hasAudio()}")
        if state == QMediaPlayer.PlaybackState.StoppedState:
            self.player.stop()
            self.ui.swi_PlayPause.changeState(1)
        elif state == QMediaPlayer.PlaybackState.PlayingState:
            self.player.play()
            self.ui.swi_PlayPause.changeState(2)
            print("Let's play")
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.player.pause()
            self.ui.swi_PlayPause.changeState(1)
        print("Error on playback: ", self.player.errorString())
        
    def on_playback_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        """When the player's playback state has changed."""
        print(f"Changed to PlayBackState {self.player.playbackState()}")
        self.playbackStateChanged.emit(state)
        if state is QMediaPlayer.PlaybackState.StoppedState:
            self.on_stop()
        elif state is QMediaPlayer.PlaybackState.PlayingState:
            self.on_play()

    def on_playpause_pressed(self, state: int) -> None:
        """When editor's Play/Pause button has been pressed by the user."""
        playback_state = QMediaPlayer.PlaybackState.StoppedState
        if state == 1:
            playback_state = QMediaPlayer.PlaybackState.PausedState
        elif state == 2:
            playback_state = QMediaPlayer.PlaybackState.PlayingState
        self.set_playback_state(playback_state)
        

    def set_player_position(self, position: int) -> None:
        """When user has changed the position by e.g. dragging the toolset's slider."""
        self.player.setPosition(position)
        self.set_playback_state(QMediaPlayer.PlaybackState.PlayingState)
        
    def on_position_changed(self, position: int) -> None:
        """When playback time has changed."""
        self.positionChanged.emit(position)
        self._model.set_current_time(position)
        if self.player.position() >= self.duration - self._model.end_time:
            self.set_playback_state(QMediaPlayer.PlaybackState.StoppedState)


    def on_play(self) -> None:
        """When the playback state is switched to 'play'"""
        if self.player.position() < self._model.start_time:
            self.player.setPosition(self._model.start_time)
            self.set_playback_state(QMediaPlayer.PlaybackState.PlayingState)

    def on_stop(self) -> None:
        """When the playback state is switched to 'stop'"""
        if self._model and self._model.is_repeating:
            if self._repeats > 0:
                print("Repeating")
                self._repeats -= 1
                QTimer.singleShot(
                self._model.pause_length * 1000,  
                lambda: self.set_playback_state(QMediaPlayer.PlaybackState.PlayingState)
            )
            else:
                self._repeats = self._model.repeats

    def on_reset(self) -> None:
        """When the rewind button of the toolset has been double clicked."""
        print("Reset playback.")
        self._repeats = self._model.repeats
        self.set_playback_state(QMediaPlayer.PlaybackState.StoppedState)


    def set_repeating(self, repeating: bool) -> None:
        self._model.set_repeating(repeating)
        if self.player.playbackState() != QMediaPlayer.PlaybackState.PlayingState or self.player.playbackState() != QMediaPlayer.PlaybackState.PausedState:
            self._repeats = self._model.repeats

    def set_repeats(self, times: int) -> None:
        self._model.set_repeats(times)

    def set_pause_length(self, sec: int) -> None:
        self._model.set_pause_length(sec)

    def set_start_end_time(self, start: int, end: int) -> None:
        self._model.set_start_time(start)
        self._model.set_end_time(end)



    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = min(event.size().width(), 180) 
        self.ui.main_frame.setGeometry(0, 0, width, event.size().height())
        self.ui.le_name.setFixedWidth(width - 40) 
        print(f"AudioElement resized to: {event.size()}")
        
class AudioDelegate(BaseElementDelegate):
    def __init__(self, toolset: 'AudioToolset', parent = None):
        super().__init__(toolset, parent)
        self._play_icon = QIcon("resources/icons/ic_play.svg")
        self._cached_editor: AudioEditor

    
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

        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft, index.data().text)

        painter.restore()

        if index.row() < index.model().rowCount() - 1:
            painter.save()
            pen = QPen(Qt.GlobalColor.lightGray, 1)
            painter.setPen(pen)
            painter.drawLine(option.rect.bottomLeft().x() + 5, option.rect.bottomLeft().y(), option.rect.bottomRight().x() - 5, option.rect.bottomRight().y())
            painter.restore()
    
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index):
        editor = AudioEditor(index.data(), parent)
        self._cached_editor = editor
        editor.player.mediaStatusChanged.connect(self.on_media_status_changed)
        editor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        return editor
    
    def on_media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            print("Media status: ", status)
            self._toolset.connect_editor(self._cached_editor)
            self._cached_editor.player.mediaStatusChanged.disconnect(self.on_media_status_changed)
            
    
    def updateEditorGeometry(self, editor, option, index):
        sub_rect = option.rect.marginsAdded(QMargins(-6, -8, -5, -5))
        print("Audio rect", sub_rect.width(), sub_rect.height())
        editor.setGeometry(sub_rect)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.model)

    def destroyEditor(self, editor: AudioEditor, index: QModelIndex) -> None:
        """Disconnects signals and destroys the editor."""
        print("Destroying AudioElement")
        editor.player.stop()
        editor.player.setSourceDevice(None)
        self._toolset.close_()

        super().destroyEditor(editor, index)

    def passthru(self) -> bool:
        return True
    
    def sizeHint(self, option, index):
        if index.data():
            return QSize(option.rect.width(), 45)
        else:
            return QSize(option.rect.width(), 0)
        
class AudioToolset(BaseElementToolset):
    playbackStateSet = pyqtSignal(QMediaPlayer.PlaybackState)
    startEndTimeChanged = pyqtSignal(int, int)
    positionSet = pyqtSignal(int)
    repeatToggled = pyqtSignal(bool)
    repeatsChanged = pyqtSignal(int)
    repeatPauseChanged = pyqtSignal(int)
    resetRequested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.ui = AudioToolsetView()
        self.ui.setUi(self)

        # Attributes
        self._duration = 0

        # Initial routines
        self.connect_signals()
        self.setAttribute(Qt.WidgetAttribute.WA_NoMousePropagation, True)

    @property
    def name(self) -> str:
        return "AudioToolset"
    
    @property
    def element_menu(self) -> ElementOptions:
        return self.ui.element_options_menu

    def connect_editor(self, editor: AudioEditor) -> None:
        self.set_track_length(editor.duration)
        self.set_attributes(editor.model)

        editor.playbackStateChanged.connect(self.on_playback_state_changed)
        editor.positionChanged.connect(self.on_position_changed)

        self.playbackStateSet.connect(editor.set_playback_state)
        self.positionSet.connect(editor.set_player_position)
        self.repeatToggled.connect(editor.set_repeating)
        self.repeatsChanged.connect(editor.set_repeats)
        self.repeatPauseChanged.connect(editor.set_pause_length)
        self.startEndTimeChanged.connect(editor.set_start_end_time)
        self.resetRequested.connect(editor.on_reset)

        self.setVisible(True)

    def connect_signals(self) -> None:
        self.ui.ac_close.triggered.connect(self.closed.emit)

        self.ui.ac_play_pause.stateChanged.connect(self.on_playpause_pressed)
        self.ui.hs_PlayTime.sliderReleased.connect(self.set_current_position)
        self.ui.hs_PlayTime.valueChanged.connect(self.on_slider_value_changed)

        # self.ui.ac_reset.triggered.connect(self.reset)
        self.ui.tb_rew.pressed.connect(self.rewind)
        self.ui.ac_rew5.triggered.connect(lambda: self.change_position_by(-5000))
        self.ui.tb_fwd.pressed.connect(self.fast_forward)
        self.ui.ac_fwd5.triggered.connect(lambda: self.change_position_by(5000))

        self.ui.ac_repeat.toggled.connect(self.on_repeat_toggled)
        self.ui.sb_RepeatTimes.valueChanged.connect(self.on_repeat_times_changed)
        self.ui.sb_PauseLength.valueChanged.connect(self.on_pause_length_changed)
        
        self.ui.te_StartTime.timeChanged.connect(self.on_start_end_time_changed)
        self.ui.te_EndTime.timeChanged.connect(self.on_start_end_time_changed)

    def close_(self):
        signals = (
            self.playbackStateSet,
            self.positionSet,
            self.repeatToggled,
            self.repeatsChanged,
            self.repeatPauseChanged,
            self.startEndTimeChanged,
            self.resetRequested
        )
        for signal in signals:
            try:
                signal.disconnect()
            except (RuntimeError, TypeError):
                pass
        self.ui.hs_PlayTime.setSliderPosition(0)
        super().close_()


    def set_attributes(self, model: AudioModel) -> None:
        self.ui.ac_repeat.setChecked(model.is_repeating)
        self.ui.sb_RepeatTimes.setValue(model.repeats)
        self.ui.sb_PauseLength.setValue(model.pause_length)
        self.set_start_end_time(model.start_time, model.end_time)

    def set_track_length(self, duration: int) -> None:
        print(f"Duration is {duration}")
        self.ui.hs_PlayTime.setMaximum(duration)
        self.ui.hs_PlayTime.setTickInterval(duration//100)

        self.ui.te_StartTime.setMinimumTime(QTime.fromMSecsSinceStartOfDay(0))
        self.ui.te_StartTime.setMaximumTime(QTime.fromMSecsSinceStartOfDay(duration - 1000))
        self.ui.te_EndTime.setMinimumTime(QTime.fromMSecsSinceStartOfDay(1000))
        self.ui.te_EndTime.setMaximumTime(QTime.fromMSecsSinceStartOfDay(duration))
        self._duration = duration


    def set_start_end_time(self, start: int, end: int) -> None:
        print("Duration / start / end", self._duration, start, end)
        if self._duration > 0:
            self.ui.te_StartTime.setTime(QTime.fromMSecsSinceStartOfDay(start))
            self.ui.te_StartTime.setMaximumTime(QTime.fromMSecsSinceStartOfDay(self._duration - end - 1000))
            self.ui.te_EndTime.setMinimumTime(QTime.fromMSecsSinceStartOfDay(start + 1000))
            self.ui.te_EndTime.setTime(QTime.fromMSecsSinceStartOfDay(self._duration - end))

    def on_start_end_time_changed(self) -> int:
        """When the start or end time has been changed by user."""
        if self._duration > 0:
            start = self.ui.te_StartTime.time().msecsSinceStartOfDay()
            end = self._duration - self.ui.te_EndTime.time().msecsSinceStartOfDay()
            self.ui.te_StartTime.setMaximumTime(QTime.fromMSecsSinceStartOfDay(self._duration - end - 1000))
            self.ui.te_EndTime.setMinimumTime(QTime.fromMSecsSinceStartOfDay(start + 1000))
            self.startEndTimeChanged.emit(start, end)                            

    
    def set_current_position(self) -> None:
        """When user has changed the playback time by using buttons or moving the slider."""
        self.positionSet.emit(self.ui.hs_PlayTime.sliderPosition())

    def rewind(self) -> None:
        QTimer.singleShot(100, lambda: self.change_position_by(-1000))

    def fast_forward(self) -> None:
        QTimer.singleShot(100, lambda: self.change_position_by(1000))

    def change_position_by(self, msec: int) -> None:
        self.positionSet.emit(self.ui.hs_PlayTime.sliderPosition() + msec)

    def on_position_changed(self, position: int) -> None:
        """When the playback time has changed."""
        if not self.ui.hs_PlayTime.isSliderDown():
            self.ui.hs_PlayTime.setSliderPosition(position)

    def on_slider_value_changed(self, value: int) -> None:
        self.ui.te_PlayTime.setTime(QTime.fromMSecsSinceStartOfDay(value))

        
    def set_playback_state(self, state: QMediaPlayer.PlaybackState) -> None:
        """When the user has clicked the playpause button."""
        print(f"Got PlayBackState {state}")
        self.playbackStateSet.emit(state)

    def reset(self) -> None:
        self.resetRequested.emit()

    def on_playpause_pressed(self) -> None:
        """When the Play/Pause button is pressed."""
        if self.ui.ac_play_pause.state() == 2:
            self.set_playback_state(QMediaPlayer.PlaybackState.PlayingState)
        elif self.ui.ac_play_pause.state() == 1:
            self.set_playback_state(QMediaPlayer.PlaybackState.PausedState)

    def on_playback_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        """When the playback state has been changed by the editor."""
        if state is QMediaPlayer.PlaybackState.StoppedState:
            self.ui.ac_play_pause.changeState(1)
        elif state is QMediaPlayer.PlaybackState.PlayingState:
            self.ui.ac_play_pause.changeState(2)
        elif state is QMediaPlayer.PlaybackState.PausedState:
            self.ui.ac_play_pause.changeState(1)


    def on_repeat_toggled(self, state: bool) -> None:
        self.repeatToggled.emit(state)
        self.ui.sb_RepeatTimes.setEnabled(state)
        self.ui.sb_PauseLength.setEnabled(state)

    def on_repeat_times_changed(self, times: int) -> None:
        self.repeatsChanged.emit(times)

    def on_pause_length_changed(self, length: int) -> None:
        self.repeatPauseChanged.emit(length)


    def sizeHint(self) -> QSize:
        return QSize(240, 160)
    
class AudioElementDefinitions(BaseElementDefinitions):

    @staticmethod
    def create_model(resource: ResourceObject) -> AudioModel:
        if resource.path:
            return AudioModel(resource)
        raise ValueError("ResourceObject is missing an external resource.")
    
    @staticmethod
    def get_file(parent=None) -> str | None:
        path, _ = QFileDialog.getOpenFileName(parent, directory=str(Path.home()), filter=tr("Audio files (*.mp3 *.aac *.wav *.m4a *.flac *.wma)"))
        return path if path else None

    @staticmethod
    def model() -> Type[AudioModel]:
        return AudioModel
    
    @staticmethod
    def type() -> ResourceType:
        return ResourceType.AUDIO
    
    @staticmethod
    def name() -> str:
        return "AudioElement"
    
    @staticmethod
    def action(parent) -> QAction:
        action = QAction(QIcon("resources/icons/ic_audiofile.svg"), tr("Audio File"), parent)
        action.setData("AudioElement")
        return action
    
    @staticmethod
    def toolset() -> AudioToolset:
        return AudioToolset()
    
    @staticmethod
    def editor(model: AudioModel) -> AudioEditor:
        return AudioEditor(model)