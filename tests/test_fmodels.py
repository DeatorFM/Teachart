from pathlib import Path

import pytest
from PyQt6.QtWidgets import QApplication

RECENT = [
    "D:/Documents/Math/algebra_basics.tch",
    "D:/Documents/Science/physics_101.tch",
    "D:/Documents/History/world_war_2.tch",
    "D:/Documents/Math/calculus_intro.tch",
    "D:/Documents/English/shakespeare.tch",
    "D:/Documents/Science/chemistry_lab.tch",
    "D:/Documents/Geography/continents.tch",
    "D:/Documents/Math/geometry_shapes.tch",
]

PINNED = [
    "D:/Documents/Math/algebra_basics.tch",
    "D:/Documents/Science/physics_101.tch",
    "D:/Documents/Art/painting_techniques.tch",
    "D:/Documents/Music/music_theory.tch",
    "D:/Documents/Math/calculus_intro.tch",
    "D:/Documents/Programming/python_basics.tch",
]


from tcha.start import OpenFileModel


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    yield app


class TestFileModelFunctions:
    @pytest.fixture
    def open_file_model(self):
        return OpenFileModel([], [])

    @pytest.fixture
    def mock_model(self):
        return OpenFileModel(RECENT, PINNED)

    def test_append_file(self, open_file_model):
        initial_count = open_file_model.rowCount()
        assert (
            open_file_model.append_file("D:/Documents/Introduction to Peruan history.tch", False)
            is True
        )
        assert open_file_model.append_file("D:/Documents/password.txt", False) is False

        new_count = open_file_model.rowCount()
        assert new_count > initial_count

        open_file_model.append_file("D:/Documents/Introduction to Peruan history.tch", False)

        assert open_file_model.rowCount() == new_count

    def test_get_item(self, open_file_model):
        open_file_model.append_file("D:/Documents/Math/algebra_basics.tch", False)
        item = open_file_model.get_item(0)
        assert item.path == Path("D:/Documents/Math/algebra_basics.tch")
        assert item.recent is True
        assert item.pinned is False

        open_file_model.setData(open_file_model.index(0, 1), True)
        new_item = open_file_model.get_item(0)
        assert new_item.pinned is True

    def test_exported_list(self, mock_model):
        assert set(mock_model.export_recent()) == set(RECENT)
        assert set(mock_model.export_pinned()) == set(PINNED)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
