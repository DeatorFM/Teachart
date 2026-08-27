import pytest
from PyQt6.QtWidgets import QDialog, QMainWindow
from tcha.dialogs import DialogManager


class TestMainWindow(QMainWindow):
    def __init__(self, id: int, parent=None):
        super().__init__()
        self._id = id

    @property
    def wid(self) -> int:
        return self._id


class TestDialogManager:
    @pytest.fixture
    def test_dmanager(self):
        dmanager = DialogManager()
        dmanager.define_custom_mapping("Single", QDialog)
        dmanager.define_custom_mapping("Multiple", TestMainWindow, True)
        assert dmanager.is_defined("Single")
        assert dmanager.is_defined("Multiple")
        yield dmanager

    def test_single_dialogs(self, qapp, test_dmanager):
        dialog = test_dmanager.open("Single")
        assert dialog == test_dmanager.open("Single")
        dialog.close()
        test_dmanager.mark_closed("Single")
        assert test_dmanager.get_dialog("Single") is None

    def test_multiple_windows(self, qapp, test_dmanager):
        window1 = test_dmanager.open("Multiple", 123456789)
        window2 = test_dmanager.open("Multiple", 987654321)
        assert window1 in test_dmanager.get_container("Multiple").values()
        assert window2 in test_dmanager.get_container("Multiple").values()
        assert test_dmanager.get_dialog("Multiple", 123456789) == window1
        assert test_dmanager.get_dialog("Multiple", 987654321) == window2

        window1.close()
        test_dmanager.mark_closed("Multiple", 123456789)
        assert window1 not in test_dmanager.get_container("Multiple").values()
        assert test_dmanager.get_dialog("Multiple", 123456789) is None
        window2.close()
        test_dmanager.mark_closed("Multiple", 987654321)
        assert window2 not in test_dmanager.get_container("Multiple").values()
        assert test_dmanager.get_dialog("Multiple", 987654321) is None

    def test_close_all(self, qapp, test_dmanager):
        dialog = test_dmanager.open("Single")
        window1 = test_dmanager.open("Multiple", 123456789)
        window2 = test_dmanager.open("Multiple", 987654321)
        assert test_dmanager.close_all()
        assert test_dmanager.get_dialog("Single") is None
        assert 123456789 not in test_dmanager.get_container("Multiple")
        assert 987654321 not in test_dmanager.get_container("Multiple")
