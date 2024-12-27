from PyQt6.QtCore import Qt, QDate, QTime, QObject, pyqtSignal, QModelIndex, QAbstractListModel, QT_TR_NOOP as tr
from dataclasses import dataclass, field
from typing import Generator
from enum import Enum
import sqlite3
import uuid
import os

COURSES_TABLE = [(0, "id", "BLOB"), (1, "name", "TEXT")]
LESSONS_TABLE = [(0, "id", "BLOB"), (1, "course", "BLOB"), (2, "time", "INTEGER"), (3, "date", "INTEGER"), (4, "file", "TEXT")]

def generate_id() -> int:
    return uuid.uuid4().int

class ValidationResult(Enum):
    OK = 0
    LESSONS_LIST_REBUILT = 1
    COURSES_LIST_REBUILT = 2
    DB_NOT_FOUND = 3

class Database(QObject):
    contentChanged = pyqtSignal()

    def __init__(self, path: str) -> None:
        super(Database, self).__init__()
        self.connection = sqlite3.connect(path, timeout=20)
        self.sqlc = self.connection.cursor()

@dataclass
class ScheduleItem:
    time: QTime 
    date: QDate
    file_: str
    course: int = field(default=0)
    ID: int = field(default_factory=generate_id)
    

class Scheduler(Database):
    def __init__(self, dbpath: str) -> None:
        super().__init__(dbpath)
        self.schedules = self.readSchedule()

    def readSchedule(self) -> list[ScheduleItem]:
        self.sqlc.execute("""SELECT * FROM Lessons""")
        abstable = []
        for ID, course, time, date, f in self.sqlc.fetchall():
            if os.path.exists(f):
                abstable.append(ScheduleItem(QTime.fromMSecsSinceStartOfDay(time), QDate.fromJulianDay(date), f, course, ID))
        return abstable

    def add_lesson(self, course: int, time: QTime, date: QDate, f: str, ID: int) -> None:
        self.schedules.append(ScheduleItem(time, date, f, course, ID))
        self.contentChanged.emit()

    def new_lesson(self, course: int, time: QTime, date: QDate, f: str) -> None:
        self.schedules.append(ScheduleItem(time, date, f, course))
        self.contentChanged.emit()

    def add_item(self, item: ScheduleItem) -> None:
        if item not in self:
            self.schedules.append(item)
            self.contentChanged.emit()
        else:
            self.update(item)            
                    
    def update(self, item: ScheduleItem) -> None:
        for schedule in self.schedules:
            if schedule.ID == item.ID:
                schedule.course = item.course
                schedule.date = item.date
                schedule.time = item.time
                schedule.file_ = item.file_


    def write_to_db(self) -> None:
        for lesson in self.schedules:
            self.sqlc.execute(f"""DELETE FROM Lessons WHERE id= '{lesson.ID}'""")
            self.sqlc.execute(f"""INSERT INTO Lessons VALUES ('{lesson.ID}', '{lesson.course}', '{lesson.time.msecsSinceStartOfDay()}', '{lesson.date.toJulianDay()}', '{lesson.file_}')""")
            self.connection.commit()
            self.connection.close()

    def return_items_of_date(self, date: QDate) -> Generator[ScheduleItem, None, None]:
        for item in self.schedules:
            if item.date == date:
                yield item

    def return_calendar_dates(self):
        dates = set()
        for lesson in self.schedules:
            dates.add(lesson.date)
        for date in dates:
            yield date

    def __contains__(self, item: ScheduleItem) -> bool:
        for schedule in self.schedules:
            if schedule.ID == item.ID:
                return True
        return False
    
    def __repr__(self) -> str:
        return str(self.schedules)

    def has_overlap(self, item: ScheduleItem) -> bool:
        for schedule in self.schedules:
            if schedule.ID == item.ID:
                return True
        return False

class DatabaseModel(QAbstractListModel):
    table_result = pyqtSignal(str)

    def __init__(self, path: str, parent=None) -> None:
        super().__init__(parent)
        self.connection = sqlite3.connect(path, timeout=20)
        self.sqlc = self.connection.cursor()
        self._valid = self.validate()
        self._validation_results = []

    def validate(self) -> bool:
        """Checks if database tables are existent and have all the necessary columns."""   
        altered = False     
        self.sqlc.execute("""SELECT name FROM sqlite_master WHERE type='table' AND name='Courses'""")
        table_list = self.sqlc.fetchall()
        if len(table_list) == 1:
            self.sqlc.execute("""PRAGMA table_info(Courses)""")
            columns = self.sqlc.fetchall()
            for i, column in enumerate(columns):
                cid, name, data_type, not_null, default_value, primary_key = column
                if (cid, name, data_type) == COURSES_TABLE[i]:
                    continue
                else:
                    self.delete_courses_table()
                    self.create_courses_table()
                    altered = True
        else:
            self.create_courses_table()
            altered = True
        
        self.sqlc.execute("""SELECT name FROM sqlite_master WHERE type='table' AND name='Lessons'""")
        table_list = self.sqlc.fetchall()
        if len(table_list) == 1:
            self.sqlc.execute("""PRAGMA table_info(Lessons)""")
            columns = self.sqlc.fetchall()
            for i, column in enumerate(columns):
                cid, name, data_type, not_null, default_value, primary_key = column
                if (cid, name, data_type) == LESSONS_TABLE[i]:
                    continue
                else:
                    self.delete_lessons_table()
                    self.create_lessons_table()
                    altered = True
        else:
            self.create_lessons_table()
            altered = True
        
        if altered:
            return False
        else:
            return True

    def create_courses_table(self) -> None:
        self.sqlc.execute("CREATE TABLE 'Courses' ('id' BLOB, 'name' TEXT)")
        self.connection.commit()

    def delete_courses_table(self) -> None:
        self.sqlc.execute("DROP TABLE IF EXISTS Courses")
        self.connection.commit()

    def create_lessons_table(self) -> None:
        self.sqlc.execute("CREATE TABLE 'Lessons' ('id' BLOB, 'course' BLOB, 'time' INTEGER, 'date' INTEGER, 'file' TEXT)")
        self.connection.commit()

    def delete_lessons_table(self) -> None:
        self.sqlc.execute("DROP TABLE IF EXISTS Lessons")
        self.connection.commit()

@dataclass(frozen=True)
class CourseItem:
    name: str
    ID: int = field(default_factory=generate_id)
    temporary: bool = field(default=False)
    
    @classmethod
    def no_course(cls):
        return cls("", 0, True)

    def set_temporary(self, temporary: bool) -> None:
        object.__setattr__(self, "temporary", temporary)

class Courses(DatabaseModel):
    def __init__(self, database: str, parent= None) -> None:
        super().__init__(database, parent)
        self.items = self.readCourses()

    def readCourses(self) -> list[CourseItem]:
        if self._valid:
            self.sqlc.execute("""SELECT * FROM Courses""")
            l = []
            l.append(CourseItem.no_course())
            for ID, course in self.sqlc.fetchall():
                l.append(CourseItem(course, int(ID)))
            return l
        else: 
            self.table_result.emit()
            self._valid = True
            self.readCourses()
            return []

    def show_table_validation_results(self) -> str:
        ...
    
    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self.items)
    
    def new(self, name: str) -> None:
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount()+1)
        self.items.append(CourseItem(name))
        self.endInsertRows()

    def add(self, item: CourseItem) -> None:
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount()+1)
        self.items.append(item)
        self.endInsertRows()

    def data(self, index: QModelIndex, role: int = ...):
        if role == Qt.ItemDataRole.DisplayRole and index.column() == 0:
            item = self.items[index.row()]
            name = item.name
            if item.ID == 0:
                return tr("No course")
            else:
                return name
        elif role == Qt.ItemDataRole.UserRole and index.column() == 0:
            item = self.items[index.row()]
            return item
    
    def data_from_id(self, ID: int) -> CourseItem:
        for item in self.items:
            if ID == item.ID:
                return item
        return self.items[0]
    
    def index_from_id(self, ID: int) -> int:
        for i, item in enumerate(self.items):
            if ID == item.ID:
                return i
        return -1
    
    def removeRows(self, row: int, count: int, parent: QModelIndex = ...) -> bool:
        self.beginRemoveRows(QModelIndex(), row, row+count-1 )
        try:
            if row == 0:
                raise IndexError
             
            for _ in range(count):
                self.items.pop(row)
            self.endRemoveRows()
            return True
        except IndexError:
            self.endRemoveRows()
            return False

    def remove(self, item: CourseItem) -> None:
        self.removeRows(self.index_from_id(item.ID), 1)        
            
    def write_to_db(self) -> None:
        for course in self.items:
            if course.ID != 0 or course.temporary == False:
                self.sqlc.execute(f"""DELETE FROM Courses WHERE id= '{course.ID}'""")
                self.sqlc.execute(f"""INSERT INTO Courses VALUES ('{course.ID}', '{course.name}')""")
                self.connection.commit()

    def names(self) -> list[str]:
        return [item.name for item in self.items]
    
    def __contains__(self, __x: CourseItem) -> bool:
        if __x in self.items:
            return True
        else:
            return False

    def __repr__(self) -> str:
        return str(self.items)