from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtCore import QBuffer, QByteArray, QIODevice, Qt, QXmlStreamReader
from PyQt6.QtGui import QImage, QImageWriter, QPainter
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    yield app


from nativeelements.audioelement import AudioElementDefinitions
from nativeelements.pictureelement import PictureElementDefinitions


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

    def set_compressed_file(self) -> None:
        pass

    def add_member(self) -> None:
        pass


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


class TestXmlParsing:
    def test_picturemodel(self, qapp, test_picture_factory, xml_picturemodel, mock_settings):
        """Test element parsing of PictureElement"""

        for xml, result in xml_picturemodel.items():
            print(xml)
            test_resobj = MockResourceObject(test_picture_factory(), "nice_pic.png")
            reader = QXmlStreamReader(xml)
            if reader.readNextStartElement():
                assert reader.name() == "element"
                model = PictureElementDefinitions.model_from_xml(reader.attributes(), test_resobj)
                print(model)
                assert all([model]) == result


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
