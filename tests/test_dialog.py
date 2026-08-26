from PyQt6.QtWidgets import QApplication

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


from tcha.dialogs import DialogManager
from tcha.dbmodels import CourseModel, StudentModel, ScheduleModel

class TestDialogManager:

    def test_single_dialogs(self): ...

    def test_multi_dialogs(self): ...

    def test_close_all(self): ...