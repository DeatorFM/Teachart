from __future__ import annotations

from pathlib import Path

from nativeelements.audioelement import AudioElementDefinitions
from nativeelements.baseelement import (
    BaseElementDefinitions,
    BaseElementDelegate,
    BaseElementEditor,
    BaseElementModel,
    BaseElementToolset,
    QAction,
)
from nativeelements.views import PictureEditorView
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
    QXmlStreamAttributes,
    QXmlStreamWriter,
    pyqtSignal,
    pyqtSlot,
)
from PyQt6.QtGui import (
    QImage,
    QImageReader,
    QImageWriter,
    QPainter,
    QPen,
    QPixmap,
    QTransform,
)
from PyQt6.QtWidgets import (
    QFileDialog,
    QGraphicsPixmapItem,
    QStyle,
    QStyleOptionViewItem,
)
from styling.utils import SvgIcon
from tcha.consts import ResourceFlag
from tcha.error import StandardLogger
from tcha.resmanager import (
    FileResourceObject,
    ResourceContainer,
    ResourceObject,
    ResourceType,
)
from tcha.settings import Settings
from ui.ui_etoolsets import PictureToolsetView


class PictureModel(BaseElementModel):
    def __init__(
        self,
        resource: FileResourceObject,
        width: int = 1,
        height: int = 1,
        rotation: int = 0,
        adjusted: bool = False,
        cache_pxm: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self._resource = resource
        self._resource.add_member()

        reader = QImageReader()
        reader.setDevice(self.resource.qfile())
        size = reader.size()

        self._width = width if width > 1 else size.width()  # Last width
        self._height = height if height > 1 else size.height()  # Last height
        self._rotation = rotation
        self._adjusted = adjusted  # If sizes have been adjusted by the user

        self._pixmap = QPixmap.fromImageReader(reader) if cache_pxm else None

        self._item_size = QSize(size.width(), self._height)

        self._original_aspect_ratio: float = (
            size.height() / size.width() if not size.isNull() else 1.0
        )

    def xml(self, writer: QXmlStreamWriter) -> QXmlStreamWriter:
        writer.writeEmptyElement("element")
        writer.writeAttribute("type", "PictureElement")
        writer.writeAttribute("file", self.resource.filename())
        writer.writeAttribute("width", str(self.width))
        writer.writeAttribute("height", str(self.height))
        writer.writeAttribute("rotation", str(self.rotation))
        writer.writeAttribute("adjusted", str(int(self.adjusted)))
        return writer

    @property
    def name(self) -> str:
        return "PictureElement"

    def delegate(self, toolset: BaseElementToolset, parent: QObject) -> PictureDelegate:
        return PictureDelegate(toolset, parent)

    @property
    def resource(self) -> ResourceObject:
        return self._resource

    @property
    def path(self) -> str:
        return self.resource.path

    def recalculate_size(self, width: int):
        if self._adjusted and width >= self._width:
            self._item_size = QSize(width, self._item_size.height() + 4)
            return
        else:
            h = round(self.height * (width / self._width))
            self.set_size(width, h)
            self._item_size = QSize(width, h + 4)
            self.set_adjusted(False)

    @property
    def pixmap(self) -> QPixmap:
        return self._pixmap

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def size(self) -> QSize:
        return QSize(self.width, self.height)

    @property
    def rotation(self) -> int:
        return self._rotation

    @property
    def adjusted(self) -> bool:
        return self._adjusted

    @property
    def original_aspect_ratio(self) -> float:
        """Aspect ratio of the image file."""
        return self._original_aspect_ratio

    @property
    def current_aspect_ratio(self) -> float:
        """Aspect ratio based on current width and height values"""
        return self.height / self.width

    def cache_pixmap(self) -> None:
        """Caches the pixmap from the resource."""
        reader = QImageReader()
        reader.setDevice(self.resource.qfile())
        self._pixmap = QPixmap.fromImageReader(reader)

    def clear_cache(self) -> None:
        self._pixmap = None

    def editable(self) -> bool:
        return False

    def set_resource(self, obj: ResourceObject) -> None:
        self._resource.delete_member()
        self._resource = obj

    def set_adjusted(self, user_adjusted: bool) -> None:
        self._adjusted = user_adjusted

    def set_width(self, width: int) -> None:
        self._width = width

    def set_height(self, height: int) -> None:
        self._height = height

    def set_size(self, width: int, height: int) -> None:
        self.set_width(width)
        self.set_height(height)

    def set_rotation(self, rotation: int) -> bool:
        if rotation % 90 == 0:
            self._rotation = rotation
            return True
        return False

    def rotate_by(self, incr: int) -> bool:
        if incr % 90 == 0:
            self._rotation = self.rotation + incr
            return True
        return False

    def close(self) -> None:
        self._resource.delete_member()
        self._resource = None

    def presentable_item(self) -> QGraphicsPixmapItem:
        pixmap = QPixmap(self.resource.path.as_posix())
        if self.rotation > 0:
            transformation = QTransform()
            transformation.rotate(float(self.rotation))
            pixmap = pixmap.transformed(transformation)
        if self.adjusted:
            pixmap = pixmap.scaled(self.width, self.height)
        item = QGraphicsPixmapItem(pixmap)
        item.setCacheMode(QGraphicsPixmapItem.CacheMode.DeviceCoordinateCache)
        return item

    def shcopy(self) -> PictureModel:
        model = PictureModel(self.resource, self.width, self.height, self.rotation, self.adjusted)
        model.resource.delete_member()
        return model

    def to_byte_array(self) -> QByteArray:
        data = QByteArray()
        stream = QDataStream(data, QIODevice.OpenModeFlag.WriteOnly)

        stream.writeQString(PictureElementDefinitions.name())  # Element name
        stream.writeQString(self.resource.path)  # Resource path
        stream.writeInt32(self.width)  # Width val
        stream.writeInt32(self.height)  # Height val
        stream.writeInt16(self.rotation)  # Rotation val
        stream.writeBool(self.adjusted)  # Is Adjusted flag

        return data

    def attrs(self) -> tuple[str]:
        return (
            "resource",
            "width",
            "height",
            "rotation",
            "adjusted",
            "original_aspect_ratio",
        )

    def __str__(self) -> str:
        return f"Picture element: width={self._width} height={self._height} rotation={self._rotation} user_adjusted={self._adjusted}"

    # def __del__(self) -> None:
    #     self._resource.delete_member()
    #     self._resource = None


class PictureEditor(BaseElementEditor):
    sizeChanged = pyqtSignal(int, int)

    def __init__(self, model: PictureModel, max_width: int, parent=None) -> None:
        super().__init__(parent)
        self.ui = PictureEditorView()
        self.ui.setUi(self)
        self.ui.piclabel.resized.connect(lambda qsize: self.set_size(qsize.width(), qsize.height()))

        # Attributes
        self._model = model
        self._max_width = max_width
        StandardLogger.debug(
            f"Opened PictureEditr with max width: {self._max_width}",
            extra={"sender": "PICTUREEDITOR"},
        )

        self.ui.piclabel.set_max_width(max_width)
        self.ui.piclabel.setMaximumWidth(max_width)
        self.set_pixmap(self._model.width, self._model.height, self._model.rotation)

        self.setAttribute(Qt.WidgetAttribute.WA_NoMousePropagation, True)

    @property
    def model(self) -> PictureModel:
        return self._model

    @property
    def max_width(self) -> int:
        return self._max_width

    def enable_presenter_mode(self, enabled):
        return None

    def set_width(self, width: int, keep_aspect_ratio: bool = False) -> None:
        if keep_aspect_ratio:
            height = round(
                self._model.height * (width / self._model.width)
            )  # Current height * (new width / current width)
            self._model.set_size(width, height)
            self._model.set_item_size(QSize(self._max_width, height))
            self.ui.piclabel.setFixedSize(width, height)
        else:
            self._model.set_width(width)
            self.ui.piclabel.setFixedSize(width, self.ui.piclabel.height())
        self._model.set_adjusted(True)
        self.sizeChanged.emit(self.model.width, self.model.height)

    def set_height(self, height: int, keep_aspect_ratio: bool = False) -> None:
        if keep_aspect_ratio:
            width = round(
                self._model.width * (height / self._model.height)
            )  # Current width * (new height  / current height)
            if width <= self._max_width:
                self._model.set_size(width, height)
                self.ui.piclabel.setFixedSize(width, height)
        else:
            self._model.set_height(self.ui.piclabel.width(), height)
            self.ui.piclabel.setFixedSize(self.ui.piclabel.width(), height)
        self._model.set_item_size(QSize(self._max_width, height))
        self._model.set_adjusted(True)
        self.sizeChanged.emit(self._model.width, self._model.height)

    def set_size(self, width: int, height: int) -> None:
        self.setFocus()
        self._model.set_size(width, height)
        self._model.set_adjusted(True)
        self._model.set_item_size(QSize(self._max_width, height))
        self.sizeChanged.emit(self.model.width, self.model.height)

    def adjust_label_size(self) -> None:
        if self._model.adjusted and self._model.width > 0 and self._model.height > 0:
            self.ui.piclabel.setFixedSize(self._model.size)

    def rotate_right(self) -> None:
        self._model.rotate_by(90)
        if self._model.height > self._max_width:
            height = round(self._model.width / self.model._height * self._max_width)
            self._model.set_size(self._max_width, height)
            self._model.set_item_size(QSize(self._max_width, height))
        else:
            self._model.set_size(self.model.height, self.model.width)
            self._model.set_item_size(QSize(self._max_width, self.model.height))
        self.set_pixmap(self._model.width, self._model.height, self._model.rotation)
        self.sizeChanged.emit(self._model.width, self._model.height)

    def rotate_left(self) -> None:
        self._model.rotate_by(-90)
        if self._model.height > self._max_width:
            height = round(self._model.width / self.model._height * self._max_width)
            self._model.set_size(self._max_width, height)
            self._model.set_item_size(QSize(self._max_width, height))
        else:
            self._model.set_size(self.model.height, self.model.width)
            self._model.set_item_size(QSize(self._max_width, self.model.height))
        self.sizeChanged.emit(self._model.width, self._model.height)
        self.set_pixmap(self._model.width, self._model.height, self._model.rotation)

    def restore_image(self) -> None:
        """Restore picture's original aspect ratio."""
        self._model.set_size(
            self.max_width, round(self._model.original_aspect_ratio * self.max_width)
        )
        self._model.set_item_size(self.max_width, self._model.height)
        self._model.set_rotation(0)
        self.sizeChanged.emit(self.model.width, self.model.height)
        self.set_pixmap(self._model.width, self._model.height, self._model.rotation)

    def set_pixmap(self, width: int, height: int, rotation: int) -> None:
        """Sets the label with a pixmap of given specifications"""
        pixmap = self._model.pixmap.transformed(QTransform().rotate(rotation))
        if self._model.adjusted:
            self.ui.piclabel.setPixmap(pixmap)
            self.ui.piclabel.setFixedSize(width, height)
        else:
            self.ui.piclabel.setPixmap(pixmap)


class PictureDelegate(BaseElementDelegate):
    def __init__(self, toolset, parent=None):
        super().__init__(toolset, parent)

    def paint(
        self,
        painter: QPainter | None,
        option: QStyleOptionViewItem,
        index: QModelIndex,
        single_item=True,
    ) -> None:
        if single_item:
            painter.save()
            super().paint(painter, option, QModelIndex())
            painter.restore()

            sub_rect = option.rect.adjusted(2, 2, -2, -2)

        painter.save()

        sub_rect = option.rect.adjusted(2, 2, -2, -2)

        style = option.widget.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, option, painter, option.widget)

        model: PictureModel = index.data()
        pixmap = model.pixmap

        if model.rotation % 360 > 0:
            pixmap = pixmap.transformed(QTransform().rotate(model.rotation))

        if model.adjusted and sub_rect.width() >= model.width:
            new_rect = QRect(sub_rect.topLeft(), model.size)
            painter.drawPixmap(new_rect, pixmap)
        else:
            model.set_adjusted(False)
            painter.drawPixmap(sub_rect, pixmap)

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

    def createEditor(self, parent, option, index) -> PictureEditor:
        editor = PictureEditor(
            index.data(Qt.ItemDataRole.EditRole),
            option.rect.width(),
            parent,
        )
        editor.sizeChanged.connect(lambda: self.sizeHintChanged.emit(index))
        self.installEventFilter(editor)
        editor.setFocus()
        return editor

    def setEditorData(self, editor, index):
        self._toolset.connect_editor(editor)
        self._toolset.enable_presenter_mode(self.pres_mode)

    def updateEditorGeometry(self, editor: PictureEditor, option, index):
        adjusted_rect = option.rect
        editor.setGeometry(adjusted_rect)
        editor.adjust_label_size()

    def setModelData(self, editor: PictureEditor, model: PictureModel, index: QModelIndex):
        model.setData(index, editor.model, Qt.ItemDataRole.EditRole)

    def destroyEditor(self, editor, index):
        self._toolset.close_()
        return super().destroyEditor(editor, index)

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        if index.isValid():
            return index.data(Qt.ItemDataRole.SizeHintRole)
        return QSize(0, 0)


class PictureToolset(BaseElementToolset):
    widthSet = pyqtSignal(int, bool)  # Width value, keep aspect ratio (True/False)
    heightSet = pyqtSignal(int, bool)  # Height value, keep aspect ratio (True/False)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.ui = PictureToolsetView()
        self.ui.setUi(self)

        self._max_height = 0

        self.connect_signals()

    @property
    def name(self) -> str:
        return "PictureToolset"

    def connect_editor(self, editor: PictureEditor) -> None:
        if editor:
            self.widthSet.connect(editor.set_width)
            self.heightSet.connect(editor.set_height)
            self.ui.ac_rotate_right.triggered.connect(editor.rotate_right)
            self.ui.ac_rotate_left.triggered.connect(editor.rotate_left)
            self.ui.ac_reset_image.triggered.connect(editor.restore_image)

            editor.sizeChanged.connect(self.on_size_changed)

            self.set_max_width(editor.max_width)
            self.set_attributes(editor.model)

            self.on_keep_aspect_ratio_toggled(self.ui.ac_keep_aspect_ratio.isChecked())
            self.setVisible(True)

    def connect_signals(self) -> None:
        self.ui.sb_ImageWidth.valueChanged.connect(self.on_width_set)
        self.ui.sb_ImageHeight.valueChanged.connect(self.on_height_set)
        self.ui.ac_keep_aspect_ratio.toggled.connect(self.on_keep_aspect_ratio_toggled)

    def enable_presenter_mode(self, enabled: bool):
        self.setVisible(not enabled)

    def close_(self):
        signals = (
            self.widthSet,
            self.heightSet,
            self.ui.ac_rotate_right.triggered,
            self.ui.ac_rotate_left,
            self.ui.ac_reset_image.triggered,
        )
        for signal in signals:
            try:
                signal.disconnect()
            except (RuntimeError, TypeError):
                pass

        super().close_()

    def set_max_width(self, width: int) -> None:
        self.ui.sb_ImageWidth.setMaximum(width)

    def set_attributes(self, model: PictureModel) -> None:
        self.ui.sb_ImageWidth.valueChanged.disconnect()
        self.ui.sb_ImageHeight.valueChanged.disconnect()
        self.ui.sb_ImageWidth.setValue(model.width)
        self.ui.sb_ImageHeight.setValue(model.height)
        self.ui.sb_ImageWidth.valueChanged.connect(self.on_width_set)
        self.ui.sb_ImageHeight.valueChanged.connect(self.on_height_set)
        self._max_height = round(model.height * (self.ui.sb_ImageWidth.maximum() / model.width))
        self.ui.sb_ImageHeight.setMaximum(self._max_height)

    @pyqtSlot(int, int)
    def on_size_changed(self, width: int, height: int) -> None:
        self.ui.sb_ImageWidth.valueChanged.disconnect()
        self.ui.sb_ImageHeight.valueChanged.disconnect()
        self.ui.sb_ImageWidth.setValue(width)
        self.ui.sb_ImageHeight.setValue(height)
        self.ui.sb_ImageWidth.valueChanged.connect(self.on_width_set)
        self.ui.sb_ImageHeight.valueChanged.connect(self.on_height_set)
        if self.ui.ac_keep_aspect_ratio.isChecked():
            self._max_height = round(height * (self.ui.sb_ImageWidth.maximum() / width))
            self.ui.sb_ImageHeight.setMaximum(self._max_height)
        else:
            self.ui.sb_ImageHeight.setMaximum(999)

    def on_width_set(self) -> None:
        self.widthSet.emit(self.ui.sb_ImageWidth.value(), self.ui.ac_keep_aspect_ratio.isChecked())

    def on_height_set(self) -> None:
        self.heightSet.emit(
            self.ui.sb_ImageHeight.value(), self.ui.ac_keep_aspect_ratio.isChecked()
        )

    def on_keep_aspect_ratio_toggled(self, checked: bool) -> None:
        if checked:
            self._max_height = round(
                self.ui.sb_ImageHeight.value()
                * (self.ui.sb_ImageWidth.maximum() / self.ui.sb_ImageWidth.value())
            )
            self.ui.sb_ImageHeight.setMaximum(self._max_height)
        else:
            self.ui.sb_ImageHeight.setMaximum(999)


class PictureElementDefinitions(BaseElementDefinitions):
    @staticmethod
    def name() -> str:
        return "PictureElement"

    @staticmethod
    def id() -> int:
        return 2

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.IMAGE

    @staticmethod
    def create_model(resource: ResourceObject) -> PictureModel:
        return PictureModel(resource)

    @staticmethod
    def get_file(parent=None) -> str | None:
        path, _ = QFileDialog.getOpenFileName(
            parent, directory=str(Path.home()), filter=tr("Image files *.png, *.bmp *.jpeg *.jpg")
        )
        if path and Settings.value("User/editor.compress_image"):
            return PictureElementDefinitions.compress_resource(path)
        return path if path else None

    @staticmethod
    def compress_resource(original_file: str) -> str:
        """Compresses image and returns path to file"""
        path = Path(original_file)
        if path.exists():
            image = QImage(path.as_posix())
            compressed_file = Path(ResourceContainer.tempdir.name) / (
                path.stem + ".compressed" + path.suffix
            )
            writer = QImageWriter(compressed_file.as_posix())
            if path.suffix.lower() in (".jpg", "jpeg", ".webp"):
                writer.setQuality(75)
            elif path.suffix.lower() == ".png":
                writer.setQuality(100)
            if writer.write(image):
                StandardLogger.info(
                    f"Compressed media '{original_file}' successfully to {compressed_file.as_posix()}",
                    extra={"sender", "PICTUREELEMENTDEFINITION"},
                )
                return compressed_file.as_posix()

        return original_file

    @staticmethod
    def model() -> type[PictureModel]:
        return PictureModel

    @staticmethod
    def action(parent) -> QAction:
        action = QAction(SvgIcon(":/common/file_image"), tr("Picture"), parent)
        action.setData(PictureElementDefinitions)
        action.setProperty("is_element_action", True)
        return action

    @staticmethod
    def toolset(parent) -> PictureToolset:
        return PictureToolset(parent)

    @staticmethod
    def editor(model: PictureModel):
        return PictureEditor(model)

    @staticmethod
    def resource_flag():
        return ResourceFlag.HasResource

    @staticmethod
    def mime_types():
        return ["application/x-qt-image"]

    @staticmethod
    def supports_mime_data(mime_data: QMimeData) -> bool:
        # TODO: USE QIMAGEWRITER
        if "application/x-qt-image" in mime_data.formats():
            return True
        if "text/uri-list" in mime_data.formats():
            urls = mime_data.urls()
            return (
                len(urls) == 1
                and urls[0].isLocalFile()
                and QImageReader(urls[0].toLocalFile()).canRead()
            )
        return False

    @staticmethod
    def model_from_xml(
        xml: QXmlStreamAttributes, resobj: FileResourceObject
    ) -> PictureModel | None:
        try:
            width, height, adjusted, rotation = (
                int(xml.value("width")),
                int(xml.value("height")),
                bool(int(xml.value("adjusted"))),
                int(xml.value("rotation")),
            )
            if (
                width > 0 and height > 0 and rotation % 90 == 0
            ):  # Width and height values must be at least 1
                model = PictureModel(resobj, width, height, rotation, adjusted)
                return model
            return None

        except (ValueError, TypeError):
            return None

    @staticmethod
    def model_from_mime_data(
        rescont: ResourceContainer, mime_data: QMimeData
    ) -> PictureModel | None:
        # TODO: USE QIMAGEWRITER
        if "application/x-qt-image" in mime_data.formats():
            path = rescont.make_path("png")
            image = QImage(mime_data.imageData())
            if image.save(path):
                resobj = rescont.save(PictureElementDefinitions.type(), Path(path))
                return PictureModel(resobj)
        elif mime_data.hasUrls():
            url = mime_data.urls()[0]
            resobj = rescont.save(AudioElementDefinitions.type(), url.toLocalFile())
            return PictureModel(resobj)
        return None

    @staticmethod
    def model_from_bytes(
        resobj: ResourceObject, stream: QByteArray | QDataStream
    ) -> PictureModel | None:
        if resobj.path:
            reader = (
                QDataStream(stream, QIODevice.OpenModeFlag.ReadOnly)
                if isinstance(stream, QByteArray)
                else stream
            )

            width = reader.readInt32()
            height = reader.readInt32()
            rotation = reader.readInt16()
            adjusted = reader.readBool()

            if reader.status() == QDataStream.Status.Ok:
                return PictureModel(resobj, width, height, rotation, adjusted)

        return None
