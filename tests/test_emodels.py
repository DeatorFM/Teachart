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

    def test_creation(self, qapp, test_picture): ...

class TestAudioModel:

    def test_creation(self, qapp): ...
