from __future__ import annotations

import os.path
from copy import deepcopy
from functools import cache
from pathlib import Path
from typing import Self, Type

from nativeelements.baseelement import (
    BaseElementDefinitions,
    BaseElementDelegate,
    BaseElementEditor,
    BaseElementModel,
    BaseElementToolset,
    QAction,
)
from nativeelements.views import AudioEditorView
from PyQt6.QtCore import QT_TR_NOOP as tr
from PyQt6.QtCore import (
    QByteArray,
    QDataStream,
    QIODevice,
    QMimeData,
    QModelIndex,
    QObject,
    QRect,
    QSize,
    Qt,
    QTime,
    QTimer,
    QXmlStreamAttributes,
    QXmlStreamWriter,
    pyqtSignal,
)
from PyQt6.QtGui import QCursor, QPainter, QPen
from PyQt6.QtMultimedia import QAudioOutput, QMediaFormat, QMediaPlayer
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QStyle,
    QStyleOptionButton,
    QStyleOptionViewItem,
    QWidget,
)
from styling.utils import SvgIcon
from tcha.consts import ResourceFlag
from tcha.error import StandardLogger
from tcha.resmanager import (
    FileResourceObject,
    ResourceObject,
    ResourceType,
)
from ui.ui_etoolsets import AudioToolsetView

FILE_EXTENSIONS = {
    QMediaFormat.FileFormat.WMA: ".wma",
    QMediaFormat.FileFormat.AAC: ".aac",
    QMediaFormat.FileFormat.MP3: ".mp3",
    QMediaFormat.FileFormat.Wave: ".wav",
    QMediaFormat.FileFormat.FLAC: ".flac",
    QMediaFormat.FileFormat.Mpeg4Audio: ".m4a",
}


def supported_audio_extensions() -> tuple[str]:
    supported = QMediaFormat().supportedFileFormats(QMediaFormat.ConversionMode.Decode)
    return tuple([FILE_EXTENSIONS[fformat] for fformat in supported if fformat in FILE_EXTENSIONS])


class AudioModel(BaseElementModel):
    nameChanged = pyqtSignal(str)
    repeatToggled = pyqtSignal(bool)
    repeatTimesChanged = pyqtSignal(int)
    pauseLengthChanged = pyqtSignal(int)
    startTimeChanged = pyqtSignal(int)
    endTimeChanged = pyqtSignal(int)

    def __init__(
        self,
        resource: ResourceObject,
        is_repeating: bool = False,
        repeats: int = 1,
        pause_length: int = 0,
        start_time: int = 0,
        end_time: int = 0,
        chapters: list | None = None,
        current_time: int = 0,
        parent=None,
    ):
        super().__init__(parent)
        self._resource = resource
        self._resource.add_member()

        self._is_repeating = is_repeating
        self._repeats = repeats  # Times repeating
        self._pause_length = pause_length  # Secs between repeat cycles
        self._start_time = start_time  # Msecs from start of track
        self._end_time = end_time  #  Msecs from end of track
        self._chapters = chapters if chapters is not None else []
        self._current_time = current_time
        self._text = self._resource.path.name

        self._item_size = QSize(100, 54)

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

    def set_item_size(self, size: QSize):
        self._item_size = QSize(size.width(), 54)

    @property
    def resource(self) -> ResourceObject:
        return self._resource

    @property
    def text(self) -> str:
        return self._text

    def recalculate_size(self, width):
        self._item_size.setWidth(width)

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

    def close(self) -> None:
        self._resource.delete_member()
        self._resource = None

    def presentable_item(self) -> None:
        return None

    def shcopy(self) -> AudioModel:
        model = AudioModel(
            self.resource,
            self.is_repeating,
            self.repeats,
            self.pause_length,
            self.start_time,
            self.end_time,
        )
        model.set_text(self.text)
        model.resource.delete_member()
        return model

    def to_byte_array(self) -> QByteArray:
        data = QByteArray()
        stream = QDataStream(data, QIODevice.OpenModeFlag.WriteOnly)

        stream.writeQString(AudioElementDefinitions.name())  # Element name
        stream.writeQString(self.resource.path.as_posix())  # Resource path
        stream.writeBool(self.is_repeating)  # Is repeating flag
        stream.writeUInt16(self.repeats)  # Repeat number
        stream.writeUInt64(self.pause_length)  # Pause length val
        stream.writeUInt64(self.start_time)  # Start time val
        stream.writeUInt64(self.end_time)  #  End time val
        stream.writeQString(self.text)  #  Text label

        return data

    def attrs(self) -> tuple[str]:
        return (
            "resource",
            "is_repeating",
            "repeats",
            "pause_length",
            "start_time",
            "end_time",
            "current_time",
            "text",
        )

    def __str__(self):
        return f"""AudioModel: resource={self.resource} name={self._text} repeating={self._is_repeating} repeats={self._repeats} 
        pause_length={self._pause_length}s start_time={self._start_time}ms end_time={self._end_time} current={self._current_time}"""

    def __deepcopy__(self, memo: dict | None = None) -> AudioModel:
        return AudioModel(
            deepcopy(self._resource),
            self._is_repeating,
            self._repeats,
            self._pause_length,
            self._start_time,
            self._end_time,
            [],
            0,
        )


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
        self.ui.le_name.returnPressed.connect(self.setFocus)
        self.ui.swi_PlayPause.setFocusPolicy(Qt.FocusPolicy.NoFocus)

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

    def enable_presenter_mode(self, enabled):
        return None

    def setup_player(self, model: AudioModel) -> QMediaPlayer:
        self.player.setAudioOutput(self.aoutput)
        self.player.setSourceDevice(model.resource.qfile())

    def on_media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.MediaStatus.LoadedMedia and not self._loaded:
            self.player.setPosition(self._model.current_time)
            self.ui.swi_PlayPause.setEnabled(True)
            self._loaded = True

    def set_playback_state(self, state: QMediaPlayer.PlaybackState) -> None:
        StandardLogger.info(f"Playback state set to {state}", extra={"sender": "AUDIOEDITOR"})
        if state == QMediaPlayer.PlaybackState.StoppedState:
            self.player.stop()
            self.ui.swi_PlayPause.changeState(1)
        elif state == QMediaPlayer.PlaybackState.PlayingState:
            if self.player.hasAudio():
                self.player.play()
                self.ui.swi_PlayPause.changeState(2)
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.player.pause()
            self.ui.swi_PlayPause.changeState(1)
        StandardLogger.error(
            f"Error on playback: {self.player.errorString()}", extra={"sender": "AUDIOEDITOR"}
        )

    def on_playback_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        """When the player's playback state has changed."""
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
                StandardLogger.debug(
                    f"Repeating. Remaining repeats: {self._repeats}",
                    extra={"sender": "AUDIOEDITOR"},
                )
                self._repeats -= 1
                QTimer.singleShot(
                    self._model.pause_length * 1000,
                    lambda: self.set_playback_state(QMediaPlayer.PlaybackState.PlayingState),
                )
            else:
                self._repeats = self._model.repeats

    def on_reset(self) -> None:
        """When the rewind button of the toolset has been double clicked."""
        self._repeats = self._model.repeats
        self.set_playback_state(QMediaPlayer.PlaybackState.StoppedState)

    def set_repeating(self, repeating: bool) -> None:
        self._model.set_repeating(repeating)
        if (
            self.player.playbackState() != QMediaPlayer.PlaybackState.PlayingState
            or self.player.playbackState() != QMediaPlayer.PlaybackState.PausedState
        ):
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
        width = event.size().width()
        self.ui.main_frame.setGeometry(0, 0, width, event.size().height())
        self.ui.le_name.setFixedWidth(width - 40)


class AudioDelegate(BaseElementDelegate):
    def __init__(self, toolset: AudioToolset, parent=None):
        super().__init__(toolset, parent)
        self._play_icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
        self._cached_editor: AudioEditor

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex,
        single_item=True,
    ):
        if single_item:
            painter.save()
            super().paint(painter, option, QModelIndex())
            painter.restore()

        # Apply 2px padding for element content
        sub_rect = option.rect.adjusted(2, 2, -2, -2)
        # Center button and text vertically within sub_rect (45px height - 4px padding = 41px available)
        vertical_center = sub_rect.top() + (sub_rect.height() - 23) // 2
        button_rect = QRect(sub_rect.left() + 5, vertical_center, 23, 23)
        text_rect = QRect(
            sub_rect.left() + 35,
            sub_rect.top() + (sub_rect.height() - 20) // 2,
            sub_rect.width() - 40,
            20,
        )

        painter.save()

        style = QApplication.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, option, painter, option.widget)

        mouse_pos = option.widget.viewport().mapFromGlobal(QCursor.pos())

        button_option = QStyleOptionButton()
        button_option.rect = button_rect
        button_option.icon = self._play_icon
        button_option.iconSize = QSize(20, 20)
        button_option.state = QStyle.StateFlag.State_Enabled
        if button_rect.contains(mouse_pos):
            button_option.state |= QStyle.StateFlag.State_MouseOver
        button_option.palette = option.palette
        button_option.features = QStyleOptionButton.ButtonFeature.Flat

        QApplication.style().drawControl(
            QStyle.ControlElement.CE_PushButton, button_option, painter, option.widget
        )

        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft, index.data().text)

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

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index):
        editor = AudioEditor(index.data(Qt.ItemDataRole.EditRole), parent)
        self._cached_editor = editor
        editor.player.mediaStatusChanged.connect(self.on_media_status_changed)
        self.installEventFilter(editor)
        editor.setFocus()
        return editor

    def on_media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            StandardLogger.debug(f"Media status:  {status}", extra={"sender": "AUDIOEDITOR"})
            self._toolset.connect_editor(self._cached_editor)
            self._toolset.enable_presenter_mode(self.pres_mode)
            self._cached_editor.player.mediaStatusChanged.disconnect(self.on_media_status_changed)

    def updateEditorGeometry(self, editor, option, index):
        sub_rect = option.rect.adjusted(2, 2, -2, -2)
        editor.setGeometry(sub_rect)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.model, Qt.ItemDataRole.EditRole)

    def destroyEditor(self, editor: AudioEditor, index: QModelIndex) -> None:
        """Disconnects signals and destroys the editor."""
        editor.set_playback_state(QMediaPlayer.PlaybackState.StoppedState)
        editor.player.setSourceDevice(None)
        self._toolset.close_()

        super().destroyEditor(editor, index)

    def sizeHint(self, option, index):
        if index.isValid():
            return QSize(option.rect.width(), 49)
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

    @property
    def name(self) -> str:
        return "AudioToolset"

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
            self.resetRequested,
        )
        for signal in signals:
            try:
                signal.disconnect()
            except (RuntimeError, TypeError):
                pass
        self.ui.hs_PlayTime.setSliderPosition(0)
        super().close_()

    def enable_presenter_mode(self, enabled: bool):
        self.ui.sb_RepeatTimes.setEnabled(not enabled)
        self.ui.sb_PauseLength.setEnabled(not enabled)
        self.ui.te_StartTime.setEnabled(not enabled)
        self.ui.te_EndTime.setEnabled(not enabled)

    def set_attributes(self, model: AudioModel) -> None:
        self.ui.ac_repeat.setChecked(model.is_repeating)
        self.ui.sb_RepeatTimes.setValue(model.repeats)
        self.ui.sb_PauseLength.setValue(model.pause_length)
        self.set_start_end_time(model.start_time, model.end_time)

    def set_track_length(self, duration: int) -> None:
        StandardLogger.debug(f"Duration is {duration}", extra={"sender": "AUDIOTOOLSET"})
        self.ui.hs_PlayTime.setMaximum(duration)
        self.ui.hs_PlayTime.setTickInterval(duration // 100)

        self.ui.te_StartTime.setMinimumTime(QTime.fromMSecsSinceStartOfDay(0))
        self.ui.te_StartTime.setMaximumTime(QTime.fromMSecsSinceStartOfDay(duration - 1000))
        self.ui.te_EndTime.setMinimumTime(QTime.fromMSecsSinceStartOfDay(1000))
        self.ui.te_EndTime.setMaximumTime(QTime.fromMSecsSinceStartOfDay(duration))
        self._duration = duration

    def set_start_end_time(self, start: int, end: int) -> None:
        if self._duration > 0:
            self.ui.te_StartTime.setTime(QTime.fromMSecsSinceStartOfDay(start))
            self.ui.te_StartTime.setMaximumTime(
                QTime.fromMSecsSinceStartOfDay(self._duration - end - 1000)
            )
            self.ui.te_EndTime.setMinimumTime(QTime.fromMSecsSinceStartOfDay(start + 1000))
            self.ui.te_EndTime.setTime(QTime.fromMSecsSinceStartOfDay(self._duration - end))

    def on_start_end_time_changed(self) -> int:
        """When the start or end time has been changed by user."""
        if self._duration > 0:
            start = self.ui.te_StartTime.time().msecsSinceStartOfDay()
            end = self._duration - self.ui.te_EndTime.time().msecsSinceStartOfDay()
            self.ui.te_StartTime.setMaximumTime(
                QTime.fromMSecsSinceStartOfDay(self._duration - end - 1000)
            )
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


class AudioElementDefinitions(BaseElementDefinitions):
    @staticmethod
    def create_model(resource: ResourceObject) -> AudioModel:
        if resource.path:
            return AudioModel(resource)
        raise ValueError("ResourceObject is missing an external resource.")

    @staticmethod
    def get_file(parent=None) -> str | None:
        ext = "".join(f"*{ext} " for ext in supported_audio_extensions())
        path, _ = QFileDialog.getOpenFileName(
            parent,
            directory=str(Path.home()),
            filter=tr("{} {}".format(tr("Audio files "), ext)),
        )
        return path if path else None

    @staticmethod
    def model() -> type[AudioModel]:
        return AudioModel

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.AUDIO

    @staticmethod
    def name() -> str:
        return "AudioElement"

    @staticmethod
    def id() -> int:
        return 3

    @staticmethod
    def action(parent) -> QAction:
        action = QAction(SvgIcon(":/common/file_audio"), tr("Audio File"), parent)
        action.setData(AudioElementDefinitions)
        action.setProperty("is_element_action", True)
        return action

    @staticmethod
    def toolset(parent) -> AudioToolset:
        return AudioToolset(parent)

    @staticmethod
    def editor(model: AudioModel) -> AudioEditor:
        return AudioEditor(model)

    @staticmethod
    def delegate(toolset: AudioToolset | None = None, parent=None):
        return AudioDelegate(toolset, parent)

    @staticmethod
    def resource_flag():
        return ResourceFlag.HasResource

    @staticmethod
    def mime_types() -> list[str]:
        return []

    @staticmethod
    def supports_mime_data(mime_data: QMimeData) -> bool:
        if mime_data.hasUrls():
            urls = mime_data.urls()
            filtered = tuple(
                filter(
                    lambda x: x.fileName().endswith(supported_audio_extensions()),
                    urls,
                )
            )
            return len(filtered) > 0
        return False

    @staticmethod
    def model_from_xml(xml: QXmlStreamAttributes, resobj: FileResourceObject) -> AudioModel:
        try:
            model = AudioModel(
                resobj,
                bool(int(xml.value("repeating"))),
                int(xml.value("repeats")),
                int(xml.value("pause_length")),
                int(xml.value("start_time")),
                int(xml.value("end_time")),
            )
            model.set_text(str(xml.value("name")))
            return model

        except (ValueError, TypeError):
            return None

    @staticmethod
    def model_from_mime_data(rescont, mime_data):
        urls = mime_data.urls()
        url = tuple(  # noqa: RUF015
            filter(
                lambda x: x.fileName().endswith(supported_audio_extensions()),
                urls,
            )
        )[0].toLocalFile()
        resobj = rescont.save(AudioElementDefinitions.type(), Path(url))
        return AudioModel(resobj)

    @staticmethod
    def model_from_bytes(resobj: ResourceObject, stream: QByteArray | QDataStream):
        if resobj.path:
            reader = (
                QDataStream(stream, QIODevice.OpenModeFlag.ReadOnly)
                if isinstance(stream, QByteArray)
                else stream
            )
            is_repeating = reader.readBool()
            repeats = reader.readUInt16()
            pause_length = reader.readUInt64()
            start_time = reader.readUInt64()
            end_time = reader.readUInt64()
            text = reader.readQString()

            if reader.status() == QDataStream.Status.Ok:
                model = AudioModel(
                    resobj, is_repeating, repeats, pause_length, start_time, end_time
                )
                model.set_text(text)
                return model
        return None
