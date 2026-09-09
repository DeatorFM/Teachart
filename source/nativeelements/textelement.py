from __future__ import annotations

import json
import unicodedata
import webbrowser

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
from PyQt6 import uic
from PyQt6.QtCore import QT_TR_NOOP as tr
from PyQt6.QtCore import (
    QBuffer,
    QByteArray,
    QDataStream,
    QEvent,
    QIODevice,
    QModelIndex,
    QObject,
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
    QKeySequence,
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
    QInputDialog,
    QMenu,
    QMessageBox,
    QStyleOptionViewItem,
    QTableWidgetItem,
    QWidget,
)
from styling.utils import Svg, SvgIconEngine
from tcha.consts import ResourceFlag
from tcha.error import StandardLogger
from tcha.resmanager import FileResourceObject, ResourceContainer
from tcha.settings import Locale, Settings
from ui.element_toolsets import TextToolsetView

# fmt: off
UNICODECHART = {
  "Standard Character Set": [
    33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61,
    62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90,
    91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115,
    116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172,
    174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196,
    197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219,
    220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242,
    243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255
  ],
  "Currency Symbols": [
    36, 162, 163, 164, 165, 8352, 8353, 8354, 8355, 8356, 8357, 8358, 8359, 8360, 8361, 8362, 8363, 8364, 8365, 8366,
    8367, 8368, 8369, 8370, 8371, 8372, 8373, 8374, 8375, 8376, 8377, 8378, 8379, 8380, 8381, 8382, 8383, 8384
  ],
  "Greek Characters": [
    913, 914, 915, 916, 917, 918, 919, 920, 921, 922, 923, 924, 925, 926, 927, 928, 929, 931, 932, 933, 934, 935, 936,
    937, 938, 939, 940, 941, 942, 943, 944, 945, 946, 947, 948, 949, 950, 951, 952, 953, 954, 955, 956, 957, 958, 959,
    960, 961, 962, 963, 964, 965, 966, 967, 968, 969
  ],
  "Arrows": [
    8592, 8593, 8594, 8595, 8596, 8597, 8598, 8599, 8600, 8601, 8602, 8603, 8604, 8605, 8606, 8607, 8608, 8609, 8610,
    8611, 8612, 8613, 8614, 8615, 8616, 8617, 8618, 8619, 8620, 8621, 8622, 8623, 8624, 8625, 8626, 8627, 8628, 8629,
    8630, 8631, 8632, 8633, 8634, 8635, 8636, 8637, 8638, 8639, 8640, 8641, 8642, 8643, 8644, 8645, 8646, 8647, 8648,
    8649, 8650, 8651, 8652, 8653, 8654, 8655, 8656, 8657, 8658, 8659, 8660, 8661, 8662, 8663, 8664, 8665, 8666, 8667,
    8668, 8669, 8670, 8671, 8672, 8673, 8674, 8675, 8676, 8677, 8678, 8679, 8680, 8681, 8682, 8683, 8684, 8685, 8686,
    8687, 8688, 8689, 8690, 8691, 8692, 8693, 8694, 8695, 8696, 8697, 8698, 8699, 8700, 8701, 8702, 8703
  ],
  "Mathematical Operators": [
    8704, 8705, 8706, 8707, 8708, 8709, 8710, 8711, 8712, 8713, 8714, 8715, 8716, 8717, 8718, 8719, 8720, 8721, 8722,
    8723, 8724, 8725, 8726, 8727, 8728, 8729, 8730, 8731, 8732, 8733, 8734, 8735, 8736, 8737, 8738, 8739, 8740, 8741,
    8742, 8743, 8744, 8745, 8746, 8747, 8748, 8749, 8750, 8751, 8752, 8753, 8754, 8755, 8756, 8757, 8758, 8759, 8760,
    8761, 8762, 8763, 8764, 8765, 8766, 8767, 8768, 8769, 8770, 8771, 8772, 8773, 8774, 8775, 8776, 8777, 8778, 8779,
    8780, 8781, 8782, 8783, 8784, 8785, 8786, 8787, 8788, 8789, 8790, 8791, 8792, 8793, 8794, 8795, 8796, 8797, 8798,
    8799, 8800, 8801, 8802, 8803, 8804, 8805, 8806, 8807, 8808, 8809, 8810, 8811, 8812, 8813, 8814, 8815, 8816, 8817,
    8818, 8819, 8820, 8821, 8822, 8823, 8824, 8825, 8826, 8827, 8828, 8829, 8830, 8831, 8832, 8833, 8834, 8835, 8836,
    8837, 8838, 8839, 8840, 8841, 8842, 8843, 8844, 8845, 8846, 8847, 8848, 8849, 8850, 8851, 8852, 8853, 8854, 8855,
    8856, 8857, 8858, 8859, 8860, 8861, 8862, 8863, 8864, 8865, 8866, 8867, 8868, 8869, 8870, 8871, 8872, 8873, 8874,
    8875, 8876, 8877, 8878, 8879, 8880, 8881, 8882, 8883, 8884, 8885, 8886, 8887, 8888, 8889, 8890, 8891, 8892, 8893,
    8894, 8895, 8896, 8897, 8898, 8899, 8900, 8901, 8902, 8903, 8904, 8905, 8906, 8907, 8908, 8909, 8910, 8911, 8912,
    8913, 8914, 8915, 8916, 8917, 8918, 8919, 8920, 8921, 8922, 8923, 8924, 8925, 8926, 8927, 8928, 8929, 8930, 8931,
    8932, 8933, 8934, 8935, 8936, 8937, 8938, 8939, 8940, 8941, 8942, 8943, 8944, 8945, 8946, 8947, 8948, 8949, 8950,
    8951, 8952, 8953, 8954, 8955, 8956, 8957, 8958, 8959
  ],
  "Enclosed Alphanumerics": [
    9312, 9313, 9314, 9315, 9316, 9317, 9318, 9319, 9320, 9321, 9322, 9323, 9324, 9325, 9326, 9327, 9328, 9329, 9330,
    9331, 9332, 9333, 9334, 9335, 9336, 9337, 9338, 9339, 9340, 9341, 9342, 9343, 9344, 9345, 9346, 9347, 9348, 9349,
    9350, 9351, 9352, 9353, 9354, 9355, 9356, 9357, 9358, 9359, 9360, 9361, 9362, 9363, 9364, 9365, 9366, 9367, 9368,
    9369, 9370, 9371, 9372, 9373, 9374, 9375, 9376, 9377, 9378, 9379, 9380, 9381, 9382, 9383, 9384, 9385, 9386, 9387,
    9388, 9389, 9390, 9391, 9392, 9393, 9394, 9395, 9396, 9397, 9398, 9399, 9400, 9401, 9402, 9403, 9404, 9405, 9406,
    9407, 9408, 9409, 9410, 9411, 9412, 9413, 9414, 9415, 9416, 9417, 9418, 9419, 9420, 9421, 9422, 9423, 9424, 9425,
    9426, 9427, 9428, 9429, 9430, 9431, 9432, 9433, 9434, 9435, 9436, 9437, 9438, 9439, 9440, 9441, 9442, 9443, 9444,
    9445, 9446, 9447, 9448, 9449, 9450, 9451, 9452, 9453, 9454, 9455, 9456, 9457, 9458, 9459, 9460, 9461, 9462, 9463,
    9464, 9465, 9466, 9467, 9468, 9469, 9470
  ],
  "Miscellaneous": [
    9728, 9729, 9730, 9731, 9732, 9733, 9734, 9735, 9736, 9737, 9738, 9739, 9740, 9741, 9742, 9743, 9744, 9745, 9746,
    9747, 9748, 9749, 9750, 9751, 9752, 9753, 9754, 9755, 9756, 9757, 9758, 9759, 9760, 9761, 9762, 9763, 9764, 9765,
    9766, 9767, 9768, 9769, 9770, 9771, 9772, 9773, 9774, 9775, 9776, 9777, 9778, 9779, 9780, 9781, 9782, 9783, 9784,
    9785, 9786, 9787, 9788, 9789, 9790, 9791, 9792, 9793, 9794, 9795, 9796, 9797, 9798, 9799, 9800, 9801, 9802, 9803,
    9804, 9805, 9806, 9807, 9808, 9809, 9810, 9811, 9812, 9813, 9814, 9815, 9816, 9817, 9818, 9819, 9820, 9821, 9822,
    9823, 9824, 9825, 9826, 9827, 9828, 9829, 9830, 9831, 9832, 9833, 9834, 9835, 9836, 9837, 9838, 9839, 9840, 9841,
    9842, 9843, 9844, 9845, 9846, 9847, 9848, 9849, 9850, 9851, 9852, 9853, 9854, 9855, 9856, 9857, 9858, 9859, 9860,
    9861, 9862, 9863, 9864, 9865, 9866, 9867, 9868, 9869, 9870, 9871, 9872, 9873, 9874, 9875, 9876, 9877, 9878, 9879,
    9880, 9881, 9882, 9883, 9884, 9885, 9886, 9887, 9888, 9889, 9890, 9891, 9892, 9893, 9894, 9895, 9896, 9897, 9898,
    9899, 9900, 9901, 9902, 9903, 9904, 9905, 9906, 9907, 9908, 9909, 9910, 9911, 9912, 9913, 9914, 9915, 9916, 9917,
    9918, 9919, 9920, 9921, 9922, 9923, 9924, 9925, 9926, 9927, 9928, 9929, 9930, 9931, 9932, 9933, 9934, 9935, 9936,
    9937, 9938, 9939, 9940, 9941, 9942, 9943, 9944, 9945, 9946, 9947, 9948, 9949, 9950, 9951, 9952, 9953, 9954, 9955,
    9956, 9957, 9958, 9959, 9960, 9961, 9962, 9963, 9964, 9965, 9966, 9967, 9968, 9969, 9970, 9971, 9972, 9973, 9974,
    9975, 9976, 9977, 9978, 9979, 9980, 9981, 9982
  ],
  "Braille Patterns": [
    10241, 10242, 10243, 10244, 10245, 10246, 10247, 10248, 10249, 10250, 10251, 10252, 10253, 10254, 10255, 10256,
    10257, 10258, 10259, 10260, 10261, 10262, 10263, 10264, 10265, 10266, 10267, 10268, 10269, 10270, 10271, 10272,
    10273, 10274, 10275, 10276, 10277, 10278, 10279, 10280, 10281, 10282, 10283, 10284, 10285, 10286, 10287, 10288,
    10289, 10290, 10291, 10292, 10293, 10294, 10295, 10296, 10297, 10298, 10299, 10300, 10301, 10302, 10303, 10304,
    10305, 10306, 10307, 10308, 10309, 10310, 10311, 10312, 10313, 10314, 10315, 10316, 10317, 10318, 10319, 10320,
    10321, 10322, 10323, 10324, 10325, 10326, 10327, 10328, 10329, 10330, 10331, 10332, 10333, 10334, 10335, 10336,
    10337, 10338, 10339, 10340, 10341, 10342, 10343, 10344, 10345, 10346, 10347, 10348, 10349, 10350, 10351, 10352,
    10353, 10354, 10355, 10356, 10357, 10358, 10359, 10360, 10361, 10362, 10363, 10364, 10365, 10366, 10367, 10368,
    10369, 10370, 10371, 10372, 10373, 10374, 10375, 10376, 10377, 10378, 10379, 10380, 10381, 10382, 10383, 10384,
    10385, 10386, 10387, 10388, 10389, 10390, 10391, 10392, 10393, 10394, 10395, 10396, 10397, 10398, 10399, 10400,
    10401, 10402, 10403, 10404, 10405, 10406, 10407, 10408, 10409, 10410, 10411, 10412, 10413, 10414, 10415, 10416,
    10417, 10418, 10419, 10420, 10421, 10422, 10423, 10424, 10425, 10426, 10427, 10428, 10429, 10430, 10431, 10432,
    10433, 10434, 10435, 10436, 10437, 10438, 10439, 10440, 10441, 10442, 10443, 10444, 10445, 10446, 10447, 10448,
    10449, 10450, 10451, 10452, 10453, 10454, 10455, 10456, 10457, 10458, 10459, 10460, 10461, 10462, 10463, 10464,
    10465, 10466, 10467, 10468, 10469, 10470, 10471, 10472, 10473, 10474, 10475, 10476, 10477, 10478, 10479, 10480,
    10481, 10482, 10483, 10484, 10485, 10486, 10487, 10488, 10489, 10490, 10491, 10492, 10493, 10494, 10495
  ],
  "Emoticons": [
    128512, 128513, 128514, 128515, 128516, 128517, 128518, 128519, 128520, 128521, 128522, 128523, 128524, 128525,
    128526, 128527, 128528, 128529, 128530, 128531, 128532, 128533, 128534, 128535, 128536, 128537, 128538, 128539,
    128540, 128541, 128542, 128543, 128544, 128545, 128546, 128547, 128548, 128549, 128550, 128551, 128552, 128553,
    128554, 128555, 128556, 128557, 128558, 128559, 128560, 128561, 128562, 128563, 128564, 128565, 128566, 128567,
    128568, 128569, 128570, 128571, 128572, 128573, 128574, 128575, 128576, 128577, 128578, 128579, 128580, 128581,
    128582, 128583, 128584, 128585, 128586, 128587, 128588, 128589, 128590, 128591
  ]
}
# fmt: on


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

    def presentable_item(self) -> QGraphicsSvgItem:
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

    def shcopy(self) -> TextModel:
        model = TextModel(self.resource)
        model.setHtml(self.toHtml())
        return model

    def to_byte_array(self) -> QByteArray:
        data = QByteArray()
        stream = QDataStream(data, QIODevice.OpenModeFlag.WriteOnly)

        stream.writeQString(TextElementDefinitions.name())  # Element name
        stream.writeQString("")  # No resource because every TextElement is unique
        stream.writeQString(self.toHtml())  # HTML content

        return data

    def attrs(self) -> tuple[str]:
        return ("resource",)

    def close(self) -> None:
        self._resource.delete_member()
        self._resource = None


class TextEditor(BaseTextElementEditor):
    currentPropsChanged = pyqtSignal(dict)
    tableEntered = pyqtSignal(bool)
    sizeChanged = pyqtSignal(int, int)

    def __init__(self, target_width: float, model: TextModel, parent=None) -> None:
        super().__init__(parent)
        StandardLogger.debug(
            f"Open TextEditor with target width: {target_width}", extra={"sender", "TEXTEDITOR"}
        )
        self.setDocument(model)

        # Attributes
        self.type_lang = Locale[Settings.qsettings().value("User/language", "EnglishUK", str)]
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

    def can_copy(self) -> bool:
        return False if self.textCursor().hasSelection() else True

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
            self.setFixedHeight(int(new_height) + 10)  # Add 10px buffer to prevent scrolling
            document.set_item_size(
                QSize(int(self._target_width) + 8, document.size().toSize().height() + 10)
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

        if self.textCursor().currentList():
            if e.key() == Qt.Key.Key_Tab:
                self.change_indentation()
                e.accept()
                return
            elif e.key() == Qt.Key.Key_Backtab:
                self.change_indentation(-1)
                e.accept()
                return
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
                block = self.document().findBlockByNumber(cursor.blockNumber() - tlist.count())
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
            props["color"] = self.textColor()

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
        self.ui.cb_FontSize.sizeChanged.connect(self.on_font_size_set)
        self.ui.tb_Bold.toggled.connect(self.on_bold_set)
        self.ui.tb_Italic.toggled.connect(self.on_italic_set)
        self.ui.tb_Underline.toggled.connect(self.on_underlined_set)
        self.ui.align_group.buttonToggled.connect(self.on_alignment_set)
        self.ui.tb_TextColor.clicked.connect(lambda: self.on_font_color_set(self.text_color()))
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
                    self.ui.cb_FontSize.display_size(value)  # QComboBox with point sizes
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
        ic_engine = SvgIconEngine(Svg.from_file("icons:ic_textColor.svg"))
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

    def on_font_size_set(self, size: float) -> None:
        props = {}
        props["size"] = size
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
            document.setTextWidth(float(sub_rect.width() - 8))  # Consistent with sizeHint

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
        data: TextModel = index.data(Qt.ItemDataRole.EditRole)
        editor = TextEditor(option.rect.width() - 8.0, data, parent)
        editor.sizeChanged.connect(lambda: self.sizeHintChanged.emit(index))
        editor.installEventFilter(parent)
        editor.installEventFilter(self)
        editor.setFocus()
        editor.enable_presenter_mode(self.pres_mode)
        return editor

    def setEditorData(self, editor: TextEditor | None, index: QModelIndex) -> None:
        self._toolset.connect_editor(editor)
        self._toolset.enable_presenter_mode(self.pres_mode)

    def updateEditorGeometry(
        self,
        editor: TextEditor | None,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> None:
        editor.setGeometry(option.rect.adjusted(2, 2, -5, -2))

    def eventFilter(self, object: QObject, event: QEvent):
        if isinstance(object, TextEditor) and isinstance(event, QKeyEvent):
            if event.type() == QEvent.Type.KeyPress:
                if (
                    event.matches(QKeySequence.StandardKey.Copy)
                    and object.textCursor().hasSelection()
                ):
                    object.copy()

                if (
                    event.keyCombination().keyboardModifiers() & Qt.KeyboardModifier.ControlModifier
                    and event.key() == Qt.Key.Key_Return
                ):
                    self.commitData.emit(object)
                    self.closeEditor.emit(object)
                    event.accept()
                    return True

        return super().eventFilter(object, event)

    def setModelData(self, editor: TextEditor | None, model, index: QModelIndex) -> None:
        model.setData(index, editor.model, Qt.ItemDataRole.EditRole)

    def destroyEditor(self, editor: TextEditor, index: QModelIndex):
        editor.sizeChanged.disconnect()
        self._toolset.close_()
        super().destroyEditor(editor, index)

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        if index.isValid():
            return index.data(Qt.ItemDataRole.SizeHintRole)
        return QSize(0, 0)


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
            StandardLogger.error(
                "Disconnection error with TextToolset", extra={"sender", "TEXTTOOLSET"}
            )

        self._fontProperties.clear()

        super().close_()

    def connect_signals(self):
        self.ui.cb_Font.currentFontChanged.connect(self.on_font_family_changed)
        self.ui.cb_FontSize.sizeChanged.connect(self.on_font_size_changed)
        self.ui.ac_bold.toggled.connect(self.on_bold_set)
        self.ui.ac_italic.toggled.connect(self.on_italic_set)
        self.ui.ac_underline.toggled.connect(self.on_underlined_set)
        self.ui.align_group.triggered.connect(self.on_alignment_set)
        self.ui.veralign_group.triggered.connect(self.on_vertical_alignment_set)
        self.ui.ac_textcolor.triggered.connect(lambda: self.on_color_set(self.current_color()))
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
                    self.ui.cb_FontSize.display_size(value)  # QComboBox with point sizes
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
        self._fontProperties["size"] = float(self.ui.cb_FontSize.current_font_size())
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

    def on_font_size_changed(self, value: float) -> None:
        props = {}
        props["size"] = value
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
            svg = Svg.from_file("icons:ic_textColor.svg")
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

    def show_vertical_alignment(self, alignment: QTextCharFormat.VerticalAlignment) -> None:
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

    def __init__(self, fontfamily: str, parent=None, flags=Qt.WindowType.SubWindow) -> None:
        super().__init__(parent, flags)
        self.ui = uic.loadUi("ui/UI_Symbols.ui", self)
        self.fontfamily = fontfamily

        self.connect_signals()
        self.import_character_sets()

    def connect_signals(self) -> None:
        self.ui.cb_category.currentTextChanged.connect(self.set_table)
        self.ui.TW_Symbols.itemClicked.connect(self.set_hex_code)
        self.ui.TW_Symbols.itemDoubleClicked.connect(self.emit_character)
        self.ui.PB_Paste.clicked.connect(self.emit_character)

    def import_character_sets(self) -> None:
        for key in UNICODECHART:
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
    def model() -> type[TextModel]:
        return TextModel

    @staticmethod
    def action(parent) -> QAction:
        action = QAction(QIcon("icons:ic_text.svg"), tr("Text"), parent)
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
    def model_from_xml(xml: QXmlStreamAttributes, resobj: FileResourceObject) -> TextModel:
        model = TextModel(resobj)
        html = resobj.qfile().readAll().data().decode()
        model.setHtml(html)
        return model

    @staticmethod
    def model_from_mime_data(rescont: ResourceContainer, mime_data: QMimeData) -> TextModel | None:
        resobj = rescont.create(TextElementDefinitions.type())
        model = TextModel(resobj)
        common_types = set(TextElementDefinitions.mime_types()) & set(mime_data.formats())
        if "text/html" in common_types:
            html = mime_data.html()

            # Remove fragments markers
            html = html.replace("<!--StartFragment-->", "").replace("<!--EndFragment-->", "")

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

            model.setHtml(html)
        elif "text/plain" in common_types:
            model.setPlainText(mime_data.text())
        return model

    @staticmethod
    def model_from_bytes(
        resobj: ResourceObject, stream: QByteArray | QDataStream
    ) -> TextModel | None:
        reader = (
            QDataStream(stream, QIODevice.OpenModeFlag.ReadOnly)
            if isinstance(stream, QByteArray)
            else stream
        )
        html = reader.readQString()

        if reader.status() == QDataStream.Status.Ok:
            model = TextModel(resobj)
            model.setHtml(html)
            return model

        return None
