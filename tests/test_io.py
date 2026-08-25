from pathlib import Path
from pprint import pprint
from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtCore import QBuffer, QDate, QDateTime, QIODevice, Qt, QTime, QXmlStreamReader
from PyQt6.QtGui import QImage, QImageWriter, QPainter
from PyQt6.QtWidgets import QApplication


@pytest.fixture
def qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    yield app


import uuid

from nativeelements.audioelement import AudioElementDefinitions
from nativeelements.pictureelement import PictureElementDefinitions
from tcha.lesson import Lesson
from tcha.lfio import FileMetaData, XmlReader
from tcha.tablemodel import HeaderDataItem, TableModel


@pytest.fixture
def mock_settings():
    """Mock Settings class."""
    with patch("tcha.settings.Settings") as mock_settings_class:
        mock_settings_class.user_path.return_value = Path(".")
        mock_settings_class.qsettings.return_value = MagicMock()
        mock_qsettings = MagicMock()
        mock_qsettings.value.side_effect = lambda key, type=str: {
            "User/editor.compress_image": False
        }.get(key, "")
        mock_settings_class.qsettings.return_value = mock_qsettings
        yield mock_settings_class


class MockResourceObject:
    def __init__(self, data: QIODevice, filename: str = "blahblahblah.file"):
        self._data = data
        self._filename = filename

    def qfile(self) -> QIODevice:
        return self._data

    @property
    def path(self) -> str:
        return self._filename

    def set_compressed_file(self) -> None:
        pass

    def add_member(self) -> None:
        pass


class MockPath:
    def __init__(self, path: str):
        self._path = Path(path)

    def as_posix(self) -> str:
        return self._path.as_posix()

    def exists(self) -> bool:
        return True

    def is_file(self) -> bool:
        return True

    @property
    def path(self) -> Path:
        return self._path


class MockTchPath:
    def __init__(
        self,
        *,
        struct_io: QIODevice = QBuffer(),
        lesson_io: QIODevice = QBuffer(),
        metadata_io: QIODevice = QBuffer(),
    ):
        self._struct_io = struct_io
        self._lesson_io = lesson_io
        self._metadata_io = metadata_io

    def has_required_files(self) -> bool:
        return True

    @property
    def structure(self) -> QIODevice:
        return self._struct_io

    @property
    def lesson(self) -> QIODevice:
        return self._lesson_io

    @property
    def metadata(self) -> QIODevice:
        return self._metadata_io

    def resource(self, basename: str) -> MockPath:
        return MockPath(basename)


class MockIOLogger:
    def __init__(self):
        self._messages = []

    def log(self, level: int, msg: str):
        self._messages.append((level, msg))

    @property
    def messages(self) -> list:
        return self._messages


@pytest.fixture
def test_picture_factory():
    """Factory to create fresh test pictures for each test."""

    def _create_picture():
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.ReadWrite)

        image = QImage(200, 200, QImage.Format.Format_RGB32)
        image.fill(Qt.GlobalColor.white)
        painter = QPainter(image)
        painter.setPen(Qt.GlobalColor.black)
        painter.drawRect(10, 10, 180, 180)
        painter.end()

        writer = QImageWriter(buffer, b"PNG")
        writer.write(image)
        buffer.seek(0)
        return buffer

    return _create_picture


@pytest.fixture
def xml_textmodel() -> dict[str, bool]:
    return {
        '<element type="TextElement" file="essay.html"/>': True,
        '<element type="TextElement" file="notes.html"/>': True,
        '<element type="TextElement" file="chapter1.html"/>': True,
        '<element type="TextElement" file="text_with_underscores.html"/>': True,
        '<element type="TextElement" file="text-with-dashes.html"/>': True,
        '<element type="TextElement" file="123456.html"/>': True,
        '<element type="TextElement" file="very_long_filename_that_is_still_valid.html"/>': True,
        '<element type="TextElement" file="file with spaces.html"/>': True,
        '<element type="TextElement" file="файл.html"/>': True,  # Unicode filename
        '<element type="TextElement" file="a.html"/>': True,  # Single character filename
        '<element type="TextElement"/>': False,  # Missing file attribute
        "<element/>": False,  # Missing both attributes
        '<element type="TextElement" file=""/>': False,  # Empty file attribute
    }


@pytest.fixture
def xml_picturemodel() -> dict[str, bool]:
    return {
        '<element type="PictureElement" file="photo.jpg" width="800" height="600" rotation="0" adjusted="0"/>': True,
        '<element type="PictureElement" file="portrait.png" width="600" height="800" rotation="90" adjusted="1"/>': True,
        '<element type="PictureElement" file="icon.png" width="1" height="1" rotation="0" adjusted="0"/>': True,
        '<element type="PictureElement" file="banner.jpg" width="1920" height="1080" rotation="0" adjusted="1"/>': True,
        '<element type="PictureElement" file="diagram.svg" width="500" height="500" rotation="270" adjusted="0"/>': True,
        '<element type="PictureElement" file="image.webp" width="640" height="480" rotation="45" adjusted="0"/>': False,
        '<element type="PictureElement" file="empty.png" width="0" height="0" rotation="0" adjusted="0"/>': False,
        '<element type="PictureElement" file="broken.png"/>': False,
        '<element type="PictureElement" file="invalid.jpg" width="-100" height="200" rotation="0" adjusted="0"/>': False,
    }


@pytest.fixture
def xml_audiomodel() -> dict[str, bool]:
    return {
        '<element type="AudioElement" file="song.mp3" name="My Audio Track" repeating="1" repeats="3" pause_length="5" start_time="1000" end_time="2000"/>': True,
        '<element type="AudioElement" file="sound.wav" name="Sound Effect" repeating="0" repeats="1" pause_length="0" start_time="0" end_time="0"/>': True,
        '<element type="AudioElement" file="alert.aac" name="" repeating="0" repeats="1" pause_length="0" start_time="0" end_time="0"/>': True,
        '<element type="AudioElement" file="podcast.mp3" name="Long Podcast" repeating="1" repeats="100" pause_length="30" start_time="0" end_time="3600000"/>': True,
        '<element type="AudioElement" file="music.flac" name="Background Music" repeating="true" repeats="5" pause_length="10" start_time="500" end_time="1500"/>': False,
        '<element type="AudioElement" file="broken.mp3" name="Broken"/>': False,
    }


@pytest.fixture
def xml_lesson_model() -> dict[str, bool]:
    return {
        # Valid cases
        '<lesson course_name="Math 101" course_id="1" date="2460551" time="32400000" duration="45" source_id="a1b2c3">Great lesson on algebra</lesson>': True,
        '<lesson course_name="Physics" course_id="25" date="2460551" time="50400000" duration="90" source_id="ff00aa">Introduction to mechanics</lesson>': True,
        '<lesson course_name="Chemistry" course_id="100" date="2460000" time="0" duration="60" source_id="123abc"></lesson>': True,
        '<lesson course_name="Biology" course_id="5" date="2460551" time="86399000" duration="120" source_id="deadbeef">Lab session</lesson>': True,
        '<lesson course_name="History" course_id="0" date="2460551" time="0" duration="0" source_id="1">Empty values</lesson>': True,
        '<lesson course_name="Art" course_id="-10" date="2460551" time="0" duration="-30" source_id="abc123">Negative values become absolute</lesson>': True,
        '<lesson course_name="" course_id="99" date="2460551" time="0" duration="45" source_id="f1f2f3">Empty course_name sets course_id to 0</lesson>': True,
        '<lesson course_name="Music" course_id="7" date="-100" time="32400000" duration="60" source_id="cafe">Negative date accepted</lesson>': True,
        '<lesson course_name="PE" course_id="3" date="2460551" time="0" duration="45" source_id="ABCDEF">Uppercase hex</lesson>': True,
        '<lesson course_name="English" course_id="2" date="2460551" time="0" duration="45" source_id="0001">Leading zeros in hex</lesson>': True,
        '<lesson course_id="1" date="2460551" time="32400000" duration="45" source_id="abc123">Missing course_name</lesson>': True,
        # Invalid cases - missing attributes
        '<lesson course_name="Math" date="2460551" time="32400000" duration="45" source_id="abc123">Missing course_id</lesson>': False,
        '<lesson course_name="Math" course_id="1" time="32400000" duration="45" source_id="abc123">Missing date</lesson>': False,
        '<lesson course_name="Math" course_id="1" date="2460551" duration="45" source_id="abc123">Missing time</lesson>': False,
        '<lesson course_name="Math" course_id="1" date="2460551" time="32400000" source_id="abc123">Missing duration</lesson>': False,
        '<lesson course_name="Math" course_id="1" date="2460551" time="32400000" duration="45">Missing source_id</lesson>': False,
        # Invalid cases - wrong data types
        '<lesson course_name="Math" course_id="not_a_number" date="2460551" time="32400000" duration="45" source_id="abc123">Invalid course_id</lesson>': False,
        '<lesson course_name="Math" course_id="1" date="not_a_number" time="32400000" duration="45" source_id="abc123">Invalid date</lesson>': False,
        '<lesson course_name="Math" course_id="1" date="2460551" time="not_a_number" duration="45" source_id="abc123">Invalid time</lesson>': False,
        '<lesson course_name="Math" course_id="1" date="2460551" time="32400000" duration="not_a_number" source_id="abc123">Invalid duration</lesson>': False,
        '<lesson course_name="Math" course_id="1.5" date="2460551" time="32400000" duration="45" source_id="abc123">Float course_id</lesson>': False,
        '<lesson course_name="Math" course_id="1" date="2460551.5" time="32400000" duration="45" source_id="abc123">Float date</lesson>': False,
        '<lesson course_name="Math" course_id="1" date="2460551" time="32400000" duration="45.5" source_id="abc123">Float duration</lesson>': False,
        # Invalid cases - invalid hexadecimal source_id
        '<lesson course_name="Math" course_id="1" date="2460551" time="32400000" duration="45" source_id="xyz">Invalid hex source_id</lesson>': False,
        '<lesson course_name="Math" course_id="1" date="2460551" time="32400000" duration="45" source_id="abc xyz">Hex with space</lesson>': False,
        '<lesson course_name="Math" course_id="1" date="2460551" time="32400000" duration="45" source_id="12.34">Hex with dot</lesson>': False,
        '<lesson course_name="Math" course_id="1" date="2460551" time="32400000" duration="45" source_id="">Empty source_id</lesson>': False,
        '<lesson course_name="Math" course_id="1" date="2460551" time="32400000" duration="45" source_id="0">Zero hex source_id</lesson>': False,
        '<lesson course_name="Math" course_id="1" date="2460551" time="32400000" duration="45" source_id="0000">All zeros hex</lesson>': False,
        '<lesson course_name="Math" course_id="1" date="2460551" time="32400000" duration="45" source_id="g123">Invalid hex character</lesson>': False,
    }


@pytest.fixture
def xml_lesson() -> dict[bytes, tuple[bool, Lesson]]:
    return {
        # Valid lesson data - should succeed
        b'<?xml version="1.0"?><tch version="1"><lesson course_name="Math 101" course_id="1" date="2460551" time="32400000" duration="45" source_id="a1b2c3">Great lesson on algebra</lesson></tch>': (
            True,
            Lesson(
                source_id="a1b2c3",
                datetime=QDateTime(
                    QDate.fromJulianDay(2460551), QTime.fromMSecsSinceStartOfDay(32400000)
                ),
                course_name="Math 101",
                course_id=1,
                duration=45,
                comment="Great lesson on algebra",
            ),
        ),
        # Valid lesson with empty comment
        b'<?xml version="1.0"?><tch version="1"><lesson course_name="Physics" course_id="25" date="2460551" time="50400000" duration="90" source_id="ff00aa"></lesson></tch>': (
            True,
            Lesson(
                source_id="ff00aa",
                datetime=QDateTime(
                    QDate.fromJulianDay(2460551), QTime.fromMSecsSinceStartOfDay(50400000)
                ),
                course_name="Physics",
                course_id=25,
                duration=90,
                comment="",
            ),
        ),
        # Valid lesson with negative values (converted to absolute)
        b'<?xml version="1.0"?><tch version="1"><lesson course_name="Art" course_id="-10" date="2460551" time="0" duration="-30" source_id="abc123">Test</lesson></tch>': (
            True,
            Lesson(
                source_id="abc123",
                datetime=QDateTime(QDate.fromJulianDay(2460551), QTime.fromMSecsSinceStartOfDay(0)),
                course_name="Art",
                course_id=10,
                duration=30,
                comment="Test",
            ),
        ),
        # Empty course_name sets course_id to 0
        b'<?xml version="1.0"?><tch version="1"><lesson course_name="" course_id="99" date="2460551" time="0" duration="45" source_id="f1f2f3">Test</lesson></tch>': (
            True,
            Lesson(
                source_id="f1f2f3",
                datetime=QDateTime(QDate.fromJulianDay(2460551), QTime.fromMSecsSinceStartOfDay(0)),
                course_name="",
                course_id=0,
                duration=45,
                comment="Test",
            ),
        ),
        # Wrong root element - validation fails
        b'<?xml version="1.0"?><wrong version="1"><lesson course_name="Math" course_id="1" date="2460551" time="32400000" duration="45" source_id="abc123">Test</lesson></wrong>': (
            False,
            None,
        ),
        # Version too high - validation fails
        b'<?xml version="1.0"?><tch version="999"><lesson course_name="Math" course_id="1" date="2460551" time="32400000" duration="45" source_id="abc123">Test</lesson></tch>': (
            False,
            None,
        ),
        # Missing lesson element - returns default Lesson
        b'<?xml version="1.0"?><tch version="1"></tch>': (
            True,
            "DEFAULT",
        ),
        # Invalid course_id - returns default Lesson
        b'<?xml version="1.0"?><tch version="1"><lesson course_name="Math" course_id="not_a_number" date="2460551" time="32400000" duration="45" source_id="abc123">Test</lesson></tch>': (
            True,
            "DEFAULT",
        ),
        # Invalid source_id (not hex) - returns default Lesson
        b'<?xml version="1.0"?><tch version="1"><lesson course_name="Math" course_id="1" date="2460551" time="32400000" duration="45" source_id="xyz">Test</lesson></tch>': (
            True,
            "DEFAULT",
        ),
        # Missing source_id - returns default Lesson
        b'<?xml version="1.0"?><tch version="1"><lesson course_name="Math" course_id="1" date="2460551" time="32400000" duration="45">Test</lesson></tch>': (
            True,
            "DEFAULT",
        ),
        # Empty/zero source_id - returns default Lesson
        b'<?xml version="1.0"?><tch version="1"><lesson course_name="Math" course_id="1" date="2460551" time="32400000" duration="45" source_id="0">Test</lesson></tch>': (
            True,
            "DEFAULT",
        ),
    }


@pytest.fixture
def xml_header() -> dict[str, tuple[list[bool], list[HeaderDataItem]]]:
    """Test XML for header parsing in read_table().
    Values are tuples of (expected return values, expected HeaderDataItems)."""
    return {
        # Valid cases - all headers succeed
        '<?xml version="1.0"?><tch version="1"><table rows="1" columns="3"><headers><header text="Column 1" size="100"/><header text="Column 2" size="150"/><header text="Column 3" size="200"/></headers></table></tch>': (
            [True, True, True],
            [
                HeaderDataItem(0, Qt.Orientation.Horizontal, 100, True, "Column 1"),
                HeaderDataItem(1, Qt.Orientation.Horizontal, 150, True, "Column 2"),
                HeaderDataItem(2, Qt.Orientation.Horizontal, 200, True, "Column 3"),
            ],
        ),
        '<?xml version="1.0"?><tch version="1"><table rows="1" columns="1"><headers><header text="Name" size="250"/></headers></table></tch>': (
            [True],
            [HeaderDataItem(0, Qt.Orientation.Horizontal, 250, True, "Name")],
        ),
        '<?xml version="1.0"?><tch version="1"><table rows="1" columns="2"><headers><header text="" size="100"/><header text="Valid Header" size="50"/></headers></table></tch>': (
            [True, True],
            [
                HeaderDataItem(0, Qt.Orientation.Horizontal, 100, True, ""),
                HeaderDataItem(1, Qt.Orientation.Horizontal, 50, True, "Valid Header"),
            ],
        ),
        '<?xml version="1.0"?><tch version="1"><table rows="1" columns="1"><headers><header text="Zero Size" size="0"/></headers></table></tch>': (
            [True],
            [HeaderDataItem(0, Qt.Orientation.Horizontal, 30, True, "Zero Size")],  # 0 becomes 30
        ),
        '<?xml version="1.0"?><tch version="1"><table rows="1" columns="2"><headers><header text="First" size="100"/><header text="Special chars: äöü €" size="120"/></headers></table></tch>': (
            [True, True],
            [
                HeaderDataItem(0, Qt.Orientation.Horizontal, 100, True, "First"),
                HeaderDataItem(1, Qt.Orientation.Horizontal, 120, True, "Special chars: äöü €"),
            ],
        ),
        '<?xml version="1.0"?><tch version="1"><table rows="1" columns="1"><headers><header text="Very long header text that contains many characters and should still be valid" size="300"/></headers></table></tch>': (
            [True],
            [
                HeaderDataItem(
                    0,
                    Qt.Orientation.Horizontal,
                    300,
                    True,
                    "Very long header text that contains many characters and should still be valid",
                )
            ],
        ),
        '<?xml version="1.0"?><tch version="1"><table rows="1" columns="1"><headers><header text="Large Size" size="9999"/></headers></table></tch>': (
            [True],
            [HeaderDataItem(0, Qt.Orientation.Horizontal, 9999, True, "Large Size")],
        ),
        '<?xml version="1.0"?><tch version="1"><table rows="1" columns="1"><headers><header text="Min Size 29" size="29"/></headers></table></tch>': (
            [True],
            [
                HeaderDataItem(0, Qt.Orientation.Horizontal, 30, True, "Min Size 29")
            ],  # 29 becomes 30
        ),
        '<?xml version="1.0"?><tch version="1"><table rows="1" columns="1"><headers><header text="Min Size 30" size="30"/></headers></table></tch>': (
            [True],
            [HeaderDataItem(0, Qt.Orientation.Horizontal, 30, True, "Min Size 30")],
        ),
        # Invalid cases - missing attributes (no HeaderDataItem created on failure)
        '<?xml version="1.0"?><tch version="1"><table rows="1" columns="1"><headers><header size="100"/></headers></table></tch>': (
            [False],
            [],
        ),
        '<?xml version="1.0"?><tch version="1"><table rows="1" columns="1"><headers><header text="No Size"/></headers></table></tch>': (
            [False],
            [],
        ),
        '<?xml version="1.0"?><tch version="1"><table rows="1" columns="1"><headers><header/></headers></table></tch>': (
            [False],
            [],
        ),
        # Invalid cases - wrong data types
        '<?xml version="1.0"?><tch version="1"><table rows="1" columns="1"><headers><header text="Invalid Size" size="not_a_number"/></headers></table></tch>': (
            [False],
            [],
        ),
        '<?xml version="1.0"?><tch version="1"><table rows="1" columns="1"><headers><header text="Float Size" size="100.5"/></headers></table></tch>': (
            [False],
            [],
        ),
        '<?xml version="1.0"?><tch version="1"><table rows="1" columns="1"><headers><header text="Negative" size="-50"/></headers></table></tch>': (
            [True],
            [HeaderDataItem(0, Qt.Orientation.Horizontal, 30, True, "Negative")],  # -50 becomes 30
        ),
        '<?xml version="1.0"?><tch version="1"><table rows="1" columns="1"><headers><header text="Empty Size" size=""/></headers></table></tch>': (
            [False],
            [],
        ),
        # Mixed valid/invalid - exceeding column count
        '<?xml version="1.0"?><tch version="1"><table rows="1" columns="2"><headers><header text="H1" size="100"/><header text="H2" size="100"/><header text="H3" size="100"/></headers></table></tch>': (
            [True, True, False],
            [
                HeaderDataItem(0, Qt.Orientation.Horizontal, 100, True, "H1"),
                HeaderDataItem(1, Qt.Orientation.Horizontal, 100, True, "H2"),
            ],
        ),
        '<?xml version="1.0"?><tch version="1"><table rows="1" columns="1"><headers><header text="H1" size="100"/><header text="H2" size="100"/></headers></table></tch>': (
            [True, False],
            [HeaderDataItem(0, Qt.Orientation.Horizontal, 100, True, "H1")],
        ),
        # Mixed valid/invalid - some headers have errors
        '<?xml version="1.0"?><tch version="1"><table rows="1" columns="3"><headers><header text="Valid" size="100"/><header text="Invalid" size="abc"/><header text="Valid2" size="150"/></headers></table></tch>': (
            [True, False, True],
            [
                HeaderDataItem(0, Qt.Orientation.Horizontal, 100, True, "Valid"),
                HeaderDataItem(2, Qt.Orientation.Horizontal, 150, True, "Valid2"),
            ],
        ),
        '<?xml version="1.0"?><tch version="1"><table rows="1" columns="3"><headers><header text="Valid" size="100"/><header text="No Size"/><header text="Valid2" size="150"/></headers></table></tch>': (
            [True, False, True],
            [
                HeaderDataItem(0, Qt.Orientation.Horizontal, 100, True, "Valid"),
                HeaderDataItem(2, Qt.Orientation.Horizontal, 150, True, "Valid2"),
            ],
        ),
        '<?xml version="1.0"?><tch version="1"><table rows="1" columns="2"><headers><header size="100"/><header text="Valid" size="150"/></headers></table></tch>': (
            [False, True],
            [HeaderDataItem(1, Qt.Orientation.Horizontal, 150, True, "Valid")],
        ),
        # Edge case - empty headers section
        '<?xml version="1.0"?><tch version="1"><table rows="1" columns="1"><headers></headers></table></tch>': (
            [],
            [],
        ),
    }


@pytest.fixture
def xml_table() -> dict[bytes, bool]:
    return {
        # Valid cases
        # Simple 1x1 table
        b'<?xml version="1.0"?><tch version="1"><table rows="1" columns="1">'
        b'<headers><header text="Column 1" size="100"/></headers>'
        b'<row><cell><element type="TextElement" file="test.html"/></cell></row>'
        b"</table></tch>": True,
        # 2x2 table
        b'<?xml version="1.0"?><tch version="1"><table rows="2" columns="2">'
        b'<headers><header text="Col1" size="100"/><header text="Col2" size="150"/></headers>'
        b'<row><cell><element type="TextElement" file="a.html"/></cell><cell><element type="TextElement" file="b.html"/></cell></row>'
        b'<row><cell><element type="TextElement" file="c.html"/></cell><cell><element type="TextElement" file="d.html"/></cell></row>'
        b"</table></tch>": True,
        # 3x3 table with multiple elements per cell
        b'<?xml version="1.0"?><tch version="1"><table rows="3" columns="3">'
        b'<headers><header text="A" size="80"/><header text="B" size="90"/><header text="C" size="100"/></headers>'
        b'<row><cell><element type="TextElement" file="1.html"/><element type="TextElement" file="2.html"/></cell><cell><element type="TextElement" file="3.html"/></cell><cell></cell></row>'
        b'<row><cell><element type="TextElement" file="4.html"/></cell><cell><element type="TextElement" file="5.html"/></cell><cell><element type="TextElement" file="6.html"/></cell></row>'
        b'<row><cell></cell><cell></cell><cell><element type="TextElement" file="7.html"/></cell></row>'
        b"</table></tch>": True,
        # Table with empty cells
        b'<?xml version="1.0"?><tch version="1"><table rows="2" columns="2">'
        b'<headers><header text="H1" size="100"/><header text="H2" size="100"/></headers>'
        b"<row><cell></cell><cell></cell></row>"
        b"<row><cell></cell><cell></cell></row>"
        b"</table></tch>": True,
        # Table with mixed element types
        b'<?xml version="1.0"?><tch version="1"><table rows="2" columns="2">'
        b'<headers><header text="Media" size="200"/><header text="Text" size="150"/></headers>'
        b'<row><cell><element type="PictureElement" file="img.jpg" width="800" height="600" rotation="0" adjusted="0"/></cell><cell><element type="TextElement" file="text.html"/></cell></row>'
        b'<row><cell><element type="AudioElement" file="audio.mp3" name="Sound" repeating="0" repeats="1" pause_length="0" start_time="0" end_time="0"/></cell><cell><element type="TextElement" file="desc.html"/></cell></row>'
        b"</table></tch>": True,
        # Large table 5x4
        b'<?xml version="1.0"?><tch version="1"><table rows="5" columns="4">'
        b'<headers><header text="Col1" size="100"/><header text="Col2" size="100"/><header text="Col3" size="100"/><header text="Col4" size="100"/></headers>'
        b'<row><cell><element type="TextElement" file="1.html"/></cell><cell></cell><cell></cell><cell></cell></row>'
        b'<row><cell></cell><cell><element type="TextElement" file="2.html"/></cell><cell></cell><cell></cell></row>'
        b'<row><cell></cell><cell></cell><cell><element type="TextElement" file="3.html"/></cell><cell></cell></row>'
        b'<row><cell></cell><cell></cell><cell></cell><cell><element type="TextElement" file="4.html"/></cell></row>'
        b'<row><cell><element type="TextElement" file="5.html"/></cell><cell><element type="TextElement" file="6.html"/></cell><cell><element type="TextElement" file="7.html"/></cell><cell><element type="TextElement" file="8.html"/></cell></row>'
        b"</table></tch>": True,
        # Invalid cases
        # Missing rows attribute
        b'<?xml version="1.0"?><tch version="1"><table columns="2">'
        b'<headers><header text="H1" size="100"/><header text="H2" size="100"/></headers>'
        b"<row><cell></cell><cell></cell></row>"
        b"</table></tch>": False,
        # Missing columns attribute
        b'<?xml version="1.0"?><tch version="1"><table rows="2">'
        b'<headers><header text="H1" size="100"/></headers>'
        b"<row><cell></cell></row>"
        b"<row><cell></cell></row>"
        b"</table></tch>": False,
        # Missing both rows and columns attributes
        b'<?xml version="1.0"?><tch version="1"><table>'
        b'<headers><header text="H1" size="100"/></headers>'
        b"<row><cell></cell></row>"
        b"</table></tch>": False,
        # Zero rows
        b'<?xml version="1.0"?><tch version="1"><table rows="0" columns="2">'
        b'<headers><header text="H1" size="100"/><header text="H2" size="100"/></headers>'
        b"</table></tch>": False,
        # Zero columns
        b'<?xml version="1.0"?><tch version="1"><table rows="2" columns="0">'
        b"<headers></headers>"
        b"<row></row><row></row>"
        b"</table></tch>": False,
        # Negative rows
        b'<?xml version="1.0"?><tch version="1"><table rows="-1" columns="2">'
        b'<headers><header text="H1" size="100"/><header text="H2" size="100"/></headers>'
        b"</table></tch>": False,
        # Negative columns
        b'<?xml version="1.0"?><tch version="1"><table rows="2" columns="-1">'
        b"<headers></headers>"
        b"<row></row><row></row>"
        b"</table></tch>": False,
        # Row count mismatch (declared 3, provided 2)
        b'<?xml version="1.0"?><tch version="1"><table rows="3" columns="2">'
        b'<headers><header text="H1" size="100"/><header text="H2" size="100"/></headers>'
        b"<row><cell></cell><cell></cell></row>"
        b"<row><cell></cell><cell></cell></row>"
        b"</table></tch>": True,
        # Row count mismatch (declared 1, provided 2)
        b'<?xml version="1.0"?><tch version="1"><table rows="1" columns="2">'
        b'<headers><header text="H1" size="100"/><header text="H2" size="100"/></headers>'
        b"<row><cell></cell><cell></cell></row>"
        b"<row><cell></cell><cell></cell></row>"
        b"</table></tch>": True,
        # Column count mismatch in row (declared 2, provided 3 cells)
        b'<?xml version="1.0"?><tch version="1"><table rows="1" columns="2">'
        b'<headers><header text="H1" size="100"/><header text="H2" size="100"/></headers>'
        b"<row><cell></cell><cell></cell><cell></cell></row>"
        b"</table></tch>": True,
        # Missing headers section
        b'<?xml version="1.0"?><tch version="1"><table rows="2" columns="2">'
        b"<row><cell></cell><cell></cell></row>"
        b"<row><cell></cell><cell></cell></row>"
        b"</table></tch>": True,
        # Header count mismatch (declared 3 columns, only 2 headers)
        b'<?xml version="1.0"?><tch version="1"><table rows="2" columns="3">'
        b'<headers><header text="H1" size="100"/><header text="H2" size="100"/></headers>'
        b"<row><cell></cell><cell></cell><cell></cell></row>"
        b"<row><cell></cell><cell></cell><cell></cell></row>"
        b"</table></tch>": True,
        # Non-numeric rows attribute
        b'<?xml version="1.0"?><tch version="1"><table rows="two" columns="2">'
        b'<headers><header text="H1" size="100"/><header text="H2" size="100"/></headers>'
        b"<row><cell></cell><cell></cell></row>"
        b"</table></tch>": False,
        # Non-numeric columns attribute
        b'<?xml version="1.0"?><tch version="1"><table rows="2" columns="three">'
        b'<headers><header text="H1" size="100"/></headers>'
        b"<row><cell></cell></row>"
        b"<row><cell></cell></row>"
        b"</table></tch>": False,
        # Float values for rows/columns
        b'<?xml version="1.0"?><tch version="1"><table rows="2.5" columns="2">'
        b'<headers><header text="H1" size="100"/><header text="H2" size="100"/></headers>'
        b"<row><cell></cell><cell></cell></row>"
        b"<row><cell></cell><cell></cell></row>"
        b"</table></tch>": False,
        # Missing table element entirely
        b'<?xml version="1.0"?><tch version="1">'
        b'<headers><header text="H1" size="100"/></headers>'
        b"</tch>": False,
        # Empty tch document
        b'<?xml version="1.0"?><tch version="1"></tch>': False,
        # Row with missing cells
        b'<?xml version="1.0"?><tch version="1"><table rows="2" columns="3">'
        b'<headers><header text="H1" size="100"/><header text="H2" size="100"/><header text="H3" size="100"/></headers>'
        b"<row><cell></cell><cell></cell><cell></cell></row>"
        b"<row><cell></cell></row>"
        b"</table></tch>": True,
    }


@pytest.fixture
def xml_metadata() -> dict[bytes, tuple[bool, FileMetaData]]:
    return {
        # Valid metadata - should succeed
        b'<?xml version="1.0"?><tch version="1"><file_id>550e8400-e29b-41d4-a716-446655440000</file_id><creation_date>2026-01-15T10:30:00</creation_date><changed_date>2026-08-20T14:45:00</changed_date></tch>': (
            True,
            {
                "file_id": uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
                "creation_date": QDateTime.fromString("2026-01-15T10:30:00", Qt.DateFormat.ISODate),
                "changed_date": QDateTime.fromString("2026-08-20T14:45:00", Qt.DateFormat.ISODate),
            },
        ),
        # Version too high - should fail
        b'<?xml version="1.0"?><tch version="999"><file_id>550e8400-e29b-41d4-a716-446655440000</file_id><creation_date>2026-01-15T10:30:00</creation_date><changed_date>2026-08-20T14:45:00</changed_date></tch>': (
            False,
            None,
        ),
        # Invalid UUID format - should fail with ValueError
        b'<?xml version="1.0"?><tch version="1"><file_id>invalid-uuid-format</file_id><creation_date>2026-01-15T10:30:00</creation_date><changed_date>2026-08-20T14:45:00</changed_date></tch>': (
            False,
            None,
        ),
        # Invalid creation_date - should succeed but correct the date to currentDateTime
        b'<?xml version="1.0"?><tch version="1"><file_id>550e8400-e29b-41d4-a716-446655440000</file_id><creation_date>invalid-date</creation_date><changed_date>2026-08-20T14:45:00</changed_date></tch>': (
            True,
            {
                "file_id": uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
                "creation_date": QDateTime.currentDateTime(),  # Will be corrected
                "changed_date": QDateTime.fromString("2026-08-20T14:45:00", Qt.DateFormat.ISODate),
            },
        ),
        # Invalid changed_date - should succeed but correct the date to currentDateTime
        b'<?xml version="1.0"?><tch version="1"><file_id>550e8400-e29b-41d4-a716-446655440000</file_id><creation_date>2026-01-15T10:30:00</creation_date><changed_date>not-a-date</changed_date></tch>': (
            True,
            {
                "file_id": uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
                "creation_date": QDateTime.fromString("2026-01-15T10:30:00", Qt.DateFormat.ISODate),
                "changed_date": QDateTime.currentDateTime(),  # Will be corrected
            },
        ),
        # Missing file_id - should fail (all() check fails)
        b'<?xml version="1.0"?><tch version="1"><creation_date>2026-01-15T10:30:00</creation_date><changed_date>2026-08-20T14:45:00</changed_date></tch>': (
            False,
            None,
        ),
        # Missing version - should fail (all() check fails)
        b'<?xml version="1.0"?><tch><file_id>550e8400-e29b-41d4-a716-446655440000</file_id><creation_date>2026-01-15T10:30:00</creation_date><changed_date>2026-08-20T14:45:00</changed_date></tch>': (
            False,
            None,
        ),
        # Empty tch element - should fail
        b'<?xml version="1.0"?><tch></tch>': (False, None),
        # Wrong root element - should fail validation
        b'<?xml version="1.0"?><wrong version="1"><file_id>550e8400-e29b-41d4-a716-446655440000</file_id><creation_date>2026-01-15T10:30:00</creation_date><changed_date>2026-08-20T14:45:00</changed_date></wrong>': (
            False,
            None,
        ),
    }


class TestXmlParsing:
    def test_picturemodel(self, qapp, test_picture_factory, xml_picturemodel, mock_settings):
        """Test element parsing of PictureElement"""

        for xml, result in xml_picturemodel.items():
            test_resobj = MockResourceObject(test_picture_factory(), "nice_pic.png")
            reader = QXmlStreamReader(xml)
            if reader.readNextStartElement():
                assert reader.name() == "element"
                model = PictureElementDefinitions.model_from_xml(reader.attributes(), test_resobj)
                assert all([model]) == result

    def test_audiomodel(self, qapp, xml_audiomodel):
        """Test element xml parsing for AudioElement"""
        for xml, result in xml_audiomodel.items():
            test_resobj = MockResourceObject(QBuffer(), "nice_sound.mp3")
            reader = QXmlStreamReader(xml)
            if reader.readNextStartElement():
                assert reader.name() == "element"
                model = AudioElementDefinitions.model_from_xml(reader.attributes(), test_resobj)
                assert all([model]) == result

    def test_lesson_parsing(self, qapp, xml_lesson_model):
        for xml, result in xml_lesson_model.items():
            reader = QXmlStreamReader(xml)
            if reader.readNextStartElement():
                assert reader.name() == "lesson"
                model = Lesson.read(reader, True)
                assert all([model]) == result

    def test_metadata_reading(self, xml_metadata):
        for xml, result in xml_metadata.items():
            success, metadata_obj = result
            buffer = QBuffer()
            buffer.setData(xml)
            print(buffer.data())
            tchpath = MockTchPath(metadata_io=buffer)
            logger = MockIOLogger()
            reader = XmlReader(tchpath, logger)
            try:
                assert reader.start_reading()
                assert reader.read_metadata() == success
                assert all([reader.metadata]) == all([metadata_obj])
            except AssertionError as e:
                pprint(logger.messages)
                raise e

    def test_lesson_reading(self, xml_lesson):
        for xml, result in xml_lesson.items():
            success, lesson_obj = result
            buffer = QBuffer()
            buffer.setData(xml)
            print(buffer.data())
            tchpath = MockTchPath(lesson_io=buffer)
            logger = MockIOLogger()
            reader = XmlReader(tchpath, logger)
            try:
                assert reader.start_reading()
                assert reader.read_lesson() == success
                if lesson_obj == "DEFAULT":
                    assert reader.lesson_model is not None
                    assert reader.lesson_model.course_id == 0
                    assert reader.lesson_model.duration == 0
                    assert reader.lesson_model.source_id == "0"
                    assert reader.lesson_model.comment == ""
                else:
                    assert reader.lesson_model == lesson_obj
            except AssertionError as e:
                pprint(logger.messages, width=500)
                raise e

    def test_header(self, xml_header):
        for xml, result in xml_header.items():
            successes, hitems = iter(result[0]), iter(result[1])
            reader = QXmlStreamReader(xml)
            xml_reader = XmlReader(MockTchPath(), MockIOLogger())
            tmodel: TableModel | None = None
            header = 0

            print(xml)
            while not reader.readNextStartElement():
                if reader.name() == "table":
                    tmodel = TableModel.new_from_xml(reader.attributes())

                if tmodel and reader.name() == "header":
                    try:
                        assert xml_reader.read_header(tmodel, header, reader.attributes()) == next(
                            successes
                        )
                        assert tmodel.headerData(
                            header, Qt.Orientation.Horizontal, Qt.ItemDataRole.EditRole
                        ) == next(hitems)
                        header += 1

                    except AssertionError as e:
                        pprint(xml_reader.logger.messages)
                        raise e

    def test_table(self, qapp, mock_settings, xml_table):
        for xml, result in xml_table.items():
            buffer = QBuffer()
            buffer.setData(xml)
            print(buffer.data())
            tchpath = MockTchPath(struct_io=buffer)
            reader = XmlReader(tchpath, MockIOLogger())
            assert reader.start_reading()
            try:
                assert reader.read_table() == result
            except AssertionError as e:
                pprint(reader.logger.messages)
                raise e
            buffer.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
