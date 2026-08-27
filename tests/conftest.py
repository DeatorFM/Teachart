import pytest
from PyQt6.QtSql import QSqlDatabase
from PyQt6.QtWidgets import QApplication
from tcha.start import OpenFileModel


@pytest.fixture
def qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    yield app


@pytest.fixture
def test_db(qapp):
    """Create an in-memory test database with schema."""
    # Create a unique connection name for each test
    import uuid

    QUERIES = {
        "metadata": """
            CREATE TABLE metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """,
        "Courses": """
            CREATE TABLE Courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                duration INTEGER,
                temporary INTEGER DEFAULT 0 CHECK (temporary = 0 OR temporary = 1)
            )
            """,
        "Schedules": """
            CREATE TABLE Schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER,
                date INTEGER NOT NULL,
                time INTEGER NOT NULL,
                file_id TEXT NOT NULL,
                path TEXT NOT NULL,
                FOREIGN KEY (course_id) REFERENCES Courses(id) ON DELETE SET NULL
            )
            """,
        "Students": """
            CREATE TABLE Students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                course_id INTEGER,
                email TEXT,
                FOREIGN KEY (course_id) REFERENCES Courses(id) ON DELETE SET NULL
            )
            """,
    }

    conn_name = f"test_db_{uuid.uuid4().hex}"

    db = QSqlDatabase.addDatabase("QSQLITE", conn_name)
    db.setDatabaseName(":memory:")
    assert db.open(), "Failed to open test database"

    # Create tables
    for query_str in QUERIES.values():
        query = db.exec(query_str)
        assert not query.lastError().isValid(), (
            f"Failed to create table: {query.lastError().text()}"
        )

    # Insert metadata
    db.exec("""
        INSERT INTO metadata (key, value)
        VALUES ('source_id', 'test_source_id')
    """)

    db.exec("""
        INSERT INTO metadata (key, value)
        VALUES ('db_ver', '1')
    """)

    # Insert default "No course" entry
    db.exec("""
        INSERT OR IGNORE INTO Courses (id, name, duration, temporary) 
        VALUES (0, 'No course', 0, 0)
    """)

    yield db

    # Cleanup
    db.close()
    QSqlDatabase.removeDatabase(conn_name)


@pytest.fixture
def test_file_model():
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

    yield OpenFileModel(RECENT, PINNED)

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