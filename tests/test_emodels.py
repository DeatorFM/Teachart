from pathlib import Path

import pytest
from nativeelements.audioelement import AudioElementDefinitions, AudioModel
from nativeelements.pictureelement import PictureElementDefinitions, PictureModel
from nativeelements.textelement import TextElementDefinitions, TextModel
from PyQt6.QtCore import QBuffer, QIODevice, Qt
from PyQt6.QtGui import QImage, QImageWriter, QPainter
from tcha.resmanager import ResourceObject, ResourceType, UniqueResourceObject


@pytest.fixture
def test_html():
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.ReadWrite)

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body>
        <h1>Test Document Title</h1>
        <p>This is a <b>bold</b> paragraph with <i>italic</i> and <u>underlined</u> text.</p>
        
        <h2>Subtitle with Formatting</h2>
        <p style="color: #FF0000;">This is red text.</p>
        <p style="font-size: 16pt;">This is larger text.</p>
        
        <h3>List Examples</h3>
        <ul>
            <li>First bullet point</li>
            <li>Second bullet point with <b>bold text</b></li>
            <li>Third bullet point</li>
        </ul>
        
        <ol>
            <li>First numbered item</li>
            <li>Second numbered item</li>
            <li>Third numbered item</li>
        </ol>
        
        <h3>Links and More</h3>
        <p>Here is a <a href="https://example.com">hyperlink</a> in the text.</p>
        
        <p style="font-family: 'Arial'; font-size: 12pt;">
            This paragraph has specific font family and size.
        </p>
        
        <blockquote>
            This is a blockquote with some quoted text.
        </blockquote>
        
        <p>Special characters: &amp; &lt; &gt; &quot; &copy;</p>
    </body>
    </html>
    """

    buffer.write(html_content.encode("utf-8"))
    buffer.seek(0)
    yield buffer
    buffer.close()


@pytest.fixture
def test_picture():
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


class MockFileResourceObject(UniqueResourceObject):
    def __init__(self, num: int, path: Path, data: QBuffer, rtype=ResourceType.NONE, parent=None):
        super().__init__(num, rtype, parent)
        self._data = data
        self._mock_path = path

    def qfile(self) -> QBuffer:
        if not self._data.isOpen():
            self._data.open(QBuffer.OpenModeFlag.ReadOnly)
        return self._data

    @property
    def path(self) -> Path:
        print("Returning path")
        return self._mock_path


class TestTextModel:
    @pytest.fixture
    def simple_test_model(self):
        resobj = UniqueResourceObject(1, ResourceType.TEXT)
        model = TextModel(resobj)
        yield model

    def test_creation(self, qapp, test_html):
        resobj1 = UniqueResourceObject(1, ResourceType.TEXT)
        _ = TextModel(resobj1)
        assert resobj1.member_count == 1

        resobj2 = MockFileResourceObject(2, Path("text2.html"), test_html, ResourceType.TEXT)
        model2 = TextModel(resobj2)
        assert resobj2.member_count == 1
        assert bool(model2.toHtml())

    def test_shcopy(self, qapp, simple_test_model):
        assert simple_test_model.shcopy().toHtml() == simple_test_model.toHtml()

    def test_presentable_item(self, qapp, simple_test_model):
        item = simple_test_model.presentable_item()
        assert item


class TestPictureModel:
    @pytest.fixture
    def test_model(self, qapp, test_picture):
        resobj = MockFileResourceObject(
            1, Path("Pictures/clown.png"), test_picture(), ResourceType.IMAGE
        )
        model = PictureModel(resobj)
        assert model.width == 200
        assert model.height == 200
        assert model.rotation == 0
        assert model.adjusted == False
        assert model.original_aspect_ratio == 1.0
        yield model

    def test_modifications(self, qapp, test_model):
        test_model.set_width(100)
        assert test_model.width == 100
        assert test_model.current_aspect_ratio == 2.0
        test_model.set_height(150)
        assert test_model.height == 150
        assert test_model.current_aspect_ratio == 150 / 100

        assert test_model.set_rotation(90)
        assert test_model.set_rotation(45) == False
        assert test_model.rotation == 90
        assert test_model.rotate_by(180)
        assert test_model.rotate_by(130) == False
        assert test_model.rotation == 270

        test_model.set_adjusted(True)
        assert test_model.adjusted

    def test_presentable_item(self, qapp, test_model):
        item = test_model.presentable_item()
        assert item


class TestAudioModel:
    @pytest.fixture
    def test_model(self, qapp):
        resobj = MockFileResourceObject(1, Path("Music/Mozart.mp3"), QBuffer(), ResourceType.AUDIO)
        print("Type of .path", type(resobj.path))
        model = AudioModel(resobj)
        assert resobj.member_count == 1
        assert model.is_repeating == False
        assert model.repeats == 1
        assert model.pause_length == 0
        assert model.start_time == 0
        assert model.end_time == 0
        assert model.text == "Mozart.mp3"
        yield model

    def test_modifications(self, qapp, test_model):
        test_model.set_repeating(True)
        assert test_model.is_repeating
        test_model.set_repeats(5)
        assert test_model.repeats == 5
        test_model.set_pause_length(20)
        assert test_model.pause_length == 20
        test_model.set_start_time(2000)
        assert test_model.start_time == 2000
        test_model.set_end_time(1200)
        assert test_model.end_time == 1200
        test_model.set_current_time(5300)
        assert test_model.current_time == 5300
        test_model.set_text("Audio File 1")
        assert test_model.text == "Audio File 1"

    def test_presentable_item(self, qapp, test_model):
        item = test_model.presentable_item()
        assert item is None
