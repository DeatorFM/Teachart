import pytest
from PyQt6.QtCore import QBuffer

from tcha.resmanager import FileResourceObject, UniqueResourceObject, ResourceType
from nativeelements.textelement import TextModel, TextElementDefinitions
from nativeelements.pictureelement import PictureModel, PictureElementDefinitions
from nativeelements.audioelement import AudioModel, AudioElementDefinitions

@pytest.fixture
def test_html():
    buffer = QBuffer()
    # Add proper html
    yield buffer

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

class MockFileResourceObject(FileResourceObject):
    def __init__(self, num: int, path: Path, data: QBuffer, rtype=ResourceType.NONE, parent=None):
        super().__init__(num, path, rtype, parent)
        self._data = data

    def qfile(self) -> QBuffer:
        if not self._data.isOpen():
            self._data.open(QBuffer.OpenModeFlag.ReadOnly)
        return self._data

class TestTextModel:
    @pytest.fixture
    def simple_test_model(self):
        resobj = UniqueResourceObject(1, ResourceType.TEXT)
        model = TextModel(resobj)
        yield model

    def test_creation(self, qapp, test_html):
        resobj1 = UniqueResourceObject(1, ResourceType.TEXT)
        model1 = TextModel(resobj1)
        assert resobj1.member_count == 1

        resobj2 = MockFileResourceObject(2, Path("text2.html"), test_html ResourceType.TEXT)
        model2 = TextModel(resobj2)
        assert resobj2.member_count == 1
        assert bool(model2.toHtml())

    def test_shcopy(self, qapp, simple_test_model):
        assert simple_test_model.shcopy() == simple_test_model


class TestPictureModel:

    @pytest.fixture
    def test_model(self, qapp, test_picture):
        resobj = MockFileResourceObject(1, Path("Pictures/clown.png"), test_picture, ResourceType.IMAGE)
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



class TestAudioModel:

    @pytest.fixture
    def test_model(self, qapp):
        resobj = MockFileResourceObject(1, Path("Music/Mozart.mp3"), QBuffer(), ResourceType.AUDIO)
        model = AudioModel(resobj)
        assert resobj.member_count == 1
        assert model.is_repeating == False
        assert model.repeats == 1
        assert model.pause_length == 0
        assert model.start_time == 0
        assert model.end_time == 0
        assert model.text == "Mozart.mp3"
        yield model

    def test_modifications(self, qapp): ...
