from PyQt6.QtCore import pyqtSlot, Qt, QSettings, QLocale, QDateTime, QDate, QTime, QModelIndex, QVariant, QSortFilterProxyModel, pyqtSignal, QT_TR_NOOP as tr
from PyQt6.QtSql import QSqlTableModel, QSqlDatabase, QSqlError, QSqlRelationalTableModel, QSqlRelation, QSqlQuery, QSqlRecord

from dataclasses import dataclass, field
from typing import Self

        
@dataclass(frozen=True)
class CourseItem:
    id: int
    name: str
    duration: int = field(default=0)
    temporary: bool = field(default=False)
    source_id: str = field(default='0')

    @classmethod
    def no_course(cls: Self, source_id: str) -> Self:
        return cls(0, tr("No course"), 0, True, source_id)
    
    @classmethod
    def from_record(cls: Self, record: QSqlRecord) -> Self:
        return cls(
            record.value("id"),
            record.value("name"),
            record.value("duration"),
            bool(record.value("temporary"))
        )
    
@dataclass
class StudentItem:
    id: int
    name: str
    course_id: int | None
    email: str | None

    @classmethod
    def from_record(cls: Self, record: QSqlRecord) -> Self:
        return cls(
            record.value("id"),
            record.value("name"),
            record.value("course_id"),
            record.value("email")
        )

class CourseModel(QSqlTableModel):
    courseDataChanged = pyqtSignal()

    def __init__(self, db: QSqlDatabase, parent = None):
        super().__init__(parent, db)
        self.setTable("Courses")
        ok = self.select()
        self.setEditStrategy(QSqlTableModel.EditStrategy.OnManualSubmit)

    def add_course(self, name: str, duration: int, temporary=False) -> None:
        record = self.record()    
        record.setValue("name", name)
        record.setValue("duration", duration)
        record.setValue("temporary", int(temporary))

        if self.insertRecord(0, record):
            if self.submitAll(): 
                self.select()
                self.courseDataChanged.emit()
            print(self.data(self.index(0, 1)))
        else:
            print("Insert Failed")
            print(f"Database Error: {self.database().lastError().text()}")
            print(f"Model Error: {self.lastError().text()}")

    def remove_by_id(self, id: int) -> None:
        for row in range(self.rowCount()):
            record = self.record(row)
            if record.value("id") == id:
                if self.removeRow(row):
                    if self.submitAll():
                        self.select()
                    return
                
    def index_for_id(self, course_id: int) -> QModelIndex:
        """Returns the index for the record with student_id."""
        for row in range(self.rowCount()):
            record = self.record(row)
            if record.value("id") == course_id:
                return self.index(row, 0)
        return QModelIndex()
    
    def source_id(self) -> str:
        query =  QSqlQuery(self.database())
        query.prepare("SELECT value FROM metadata WHERE key = 'source_id'")
        if query.exec() and query.next():
            return query.value(0)
        return '0'

    def has_id(self, id: int) -> bool:
        for row in range(self.rowCount()):
            record = self.record(row)
            if record.value("id") == id:
                return True
        return False
    
    def getRow(self, row: int) -> CourseItem:
        record = self.record(row)
        return CourseItem(
            int(record.value("id")),
            record.value("name"),
            int(record.value("duration")),
            bool(record.value("temporary")),
            self.source_id()
        )
                       
    def data(self, idx: QModelIndex, role = Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if idx.row() == 0:
                if idx.column() == 1:
                    return tr("All students")
                else:
                    return 
            if idx.column() == 2:
                value = super().data(idx, role)
                return "{}{}".format(value, tr(" min"))

        if role == Qt.ItemDataRole.UserRole:
            record = self.record(idx.row())
            return CourseItem(int(record.value("id")), record.value("name"), int(record.value("duration")), bool(record.value("temporary")), self.source_id())
        return super().data(idx, role)
      
    def cleanup(self) -> None:
        query = QSqlQuery(self.database())
        query.prepare("DELETE FROM Courses WHERE temporary = 1")
        query.exec()
    
    def __contains__(self, value: CourseItem | str) -> bool:
        if isinstance(value, CourseItem):
            query = self.database().exec()
            query.prepare("SELECT EXISTS (SELECT 1 FROM Courses WHERE id = ? AND name = ?)")
            query.addBindValue(value.id)
            query.addBindValue(value.name)
            if query.exec() and query.next():
                return bool(query.value(0))
        elif isinstance(value, str):
            query = self.database().exec()
            query.prepare("SELECT EXISTS (SELECT 1 FROM Courses WHERE name = ?)")
            query.addBindValue(value)
            if query.exec() and query.next():
                return bool(query.value(0))
        return False

class ScheduleModel(QSqlRelationalTableModel):
    def __init__(self, db: QSqlDatabase, parent = None):
        super().__init__(parent, db)
        self.setTable("Schedules")
        self.setRelation(1, QSqlRelation("Courses", "id", "name"))
        self.setJoinMode(QSqlRelationalTableModel.JoinMode.LeftJoin)
        self.setEditStrategy(QSqlRelationalTableModel.EditStrategy.OnRowChange)
        self.select()

    def on_course_data_changed(self) -> None:
        relation_model = self.relationModel(1)
        if relation_model:
            relation_model.select()
        self.select()

    def add_schedule(self, course_id: int, datetime: QDateTime, file_id: str, path: str) -> bool:
        record = self.record()
        record.setValue(1, course_id)
        record.setValue("date", datetime.date().toJulianDay())
        record.setValue("time", datetime.time().msecsSinceStartOfDay())
        record.setValue("file_id", file_id)
        record.setValue("path", path)

        if self.insertRecord(0, record):
            if self.submitAll():
                return self.select()
            return False
        else:
            return False

    def remove_by_id(self, id: int) -> None:
        for row in range(self.rowCount()):
            record = self.record(row)
            if record.value("id") == id:
                if self.removeRow(row):
                    self.submitAll()

    def index_for_id(self, schedule_id: int) -> QModelIndex:
        """Returns the index for the record with schedule id."""
        for row in range(self.rowCount()):
            record = self.record(row)
            if record.value("id") == schedule_id:
                return self.index(row, 0)
        return QModelIndex()
    
    def index_for_file_id(self, file_id: str) -> QModelIndex:
        """Returns the index for the first record with file id."""
        for row in range(self.rowCount()):
            record = self.record(row)
            print("Checking file id: ", record.value("file_id"), "with", file_id)
            if record.value("file_id") == file_id:
                return self.index(row, 0)
        return QModelIndex()
    
    def course_id(self, index: QModelIndex) -> int:
        """Returns the course id of the index as a numeric value."""
        query = QSqlQuery(self.database())
        query.prepare("SELECT course_id FROM Schedules WHERE id = ?")
        query.addBindValue(super().data(self.index(index.row(), 0), Qt.ItemDataRole.DisplayRole))
        if query.exec() and query.next():
            print("Return course id")
            return query.value(0)
        return 0
    
    def has_file(self, file_id: str) -> bool:
        query = self.database().exec()
        query.prepare("SELECT EXISTS (SELECT 1 FROM Schedules WHERE file_id = ?)")
        query.addBindValue(file_id)
        if query.exec() and query.next():
            return bool(query.value(0))
    
    def update_schedule(self, schedule_id: int, course_id: int, datetime: QDateTime, path: str) -> bool:
        row = self.index_for_id(schedule_id).row()
        if row > -1:
            ok = True
            ok &= self.setData(self.index(row, 1), course_id, Qt.ItemDataRole.EditRole)
            ok &= self.setData(self.index(row, 2), datetime.date().toJulianDay())
            ok &= self.setData(self.index(row, 3), datetime.time().msecsSinceStartOfDay())
            ok &= self.setData(self.index(row, 5), path)
            self.submitAll()
            self.select()
            return ok
        return False

    def schedules_for_month(self, month: QDate) -> list[QDate]:
        month.setDate(month.year(), month.month(), 1)
        last_day = month.addDays(month.daysInMonth() - 1)

        try:
            schedules = []
            query = self.database().exec("SELECT date FROM Schedules WHERE date >= ? AND date <= ?")
            query.addBindValue(month.toJulianDay())
            query.addBindValue(last_day.toJulianDay())
            query.exec()

            while query.next():
                schedules.append(QDate.fromJulianDay(query.value("date")))
            return schedules

        except QSqlError:
            return []
        
    def date_schedule_count(self, date: QDate) -> int:
        """Returns the count of schedules for a specific date."""
        query = self.database().exec()
        query.prepare("SELECT COUNT(*) FROM Schedules WHERE date = ?")
        query.addBindValue(date.toJulianDay())
        if query.exec() and query.next():
            return query.value(0)
        return 0
        
    def removeRows(self, row, count, parent = ...):
        self.beginRemoveRows(parent, row, row + count)
        ok = super().removeRows(row, count, parent)
        self.endRemoveRows()
        return ok

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if section == 1:
                return tr("Course")
            elif section == 2:
                return tr("Date")
            elif section == 3:
                return tr("Time")
            elif section == 5:
                return tr("File")
        return super().headerData(section, orientation, role)
    
    def data(self, item: QModelIndex, role = Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if item.column() == 2:
                locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedKingdom)
                julian_day = self.record(item.row()).value("date")
                qdate = QDate.fromJulianDay(julian_day)
                return locale.toString(qdate, QLocale.FormatType.ShortFormat)
            elif item.column() == 3:
                msecs = self.record(item.row()).value("time")
                qtime = QTime.fromMSecsSinceStartOfDay(msecs)
                return qtime.toString("HH:mm")
        elif role == Qt.ItemDataRole.EditRole:
            if item.column() == 2:
                julian_day = super().data(item, role)
                return julian_day
            elif item.column() == 3:
                msecs = super().data(item, role)
                return msecs
        return super().data(item, role)
    
class StudentModel(QSqlRelationalTableModel):
    valueChanged = pyqtSignal(QModelIndex, QVariant, QVariant)
    
    def __init__(self, db: QSqlDatabase, parent = None):
        super().__init__(parent, db)
        self.setTable("Students")
        self.setRelation(2, QSqlRelation("Courses", "id", "name"))
        self.setJoinMode(QSqlRelationalTableModel.JoinMode.LeftJoin)
        self.setEditStrategy(QSqlRelationalTableModel.EditStrategy.OnRowChange)
        self.select()

        self.dataChanged.connect(self.on_value_change)

    def on_course_data_changed(self) -> None:
        relation_model = self.relationModel(2)
        if relation_model:
            relation_model.select()
        self.select()

    def index_for_id(self, student_id: int, column=0) -> QModelIndex:
        for row in range(self.rowCount()):
            record = self.record(row)
            if record.value("id") == student_id:
                return self.index(row, column)
        return QModelIndex()

    def add_student(self, name: str, course_id: int | None, email: str | None) -> bool:
        record = self.record()
        record.setValue(1, name)
        record.setValue(2, course_id)
        record.setValue(3, email)

        if self.insertRecord(0, record):
            if self.submitAll():
                return self.select()
            return False
        else:
            return False
    
    def setRow(self, item: QModelIndex, value: StudentItem) -> bool:
        if isinstance(value, StudentItem):
            ok = self.setData(self.index(item.row(), 1), value.name)
            ok &= self.setData(self.index(item.row(), 2), value.course_id)
            ok &= self.setData(self.index(item.row(), 3), value.email)
            ok = ok & self.submitAll()
            if ok:
                self.selectRow(item.row())
                leftIndex = self.index(item.row(), 0)
                rightIndex = self.index(item.row(), self.columnCount() - 1)
                self.dataChanged.emit(leftIndex, rightIndex, [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.UserRole])
                return ok
        return False
    
    def getRow(self, item: QModelIndex) -> StudentItem:
        record = self.record(item.row())
        return StudentItem.from_record(record)  
    
    def course_id(self, index: QModelIndex) -> int:
        query = QSqlQuery(self.database())
        query.prepare("SELECT course_id FROM Students WHERE id = ?")
        query.addBindValue(super().data(self.index(index.row(), 0), Qt.ItemDataRole.DisplayRole))
        if query.exec() and query.next():
            print("Return course id")
            return query.value(0)
        return 0

    def on_value_change(self, topLeft: QModelIndex, bottomRight: QModelIndex, roles: list) -> None:
        print("Value has been changed")
        self.submit()
        if topLeft.isValid() and bottomRight.isValid():
            print("Is valid")
            new_value = self.data(self.createIndex(topLeft.row(), 2), Qt.ItemDataRole.EditRole)
            print("New id: ", new_value)
   
    def headerData(self, section, orientation, role = ...):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if section == 1:
                return "Name"
            elif section == 2:
                return "Course"
            elif section == 3:
                return "E-Mail"
        return super().headerData(section, orientation, role)

    
class FilteredCourseModel(QSortFilterProxyModel):
    courseDataChanged = pyqtSignal()

    def __init__(self, source_model: CourseModel, parent = None):
        super().__init__(parent)
        self.setSourceModel(source_model)
        self._search_str = ""

    def index_for_id(self, id: int) -> QModelIndex:
        source_idx = self.sourceModel().index_for_id(id)
        if source_idx.isValid():
            return self.mapFromSource(source_idx)
        return QModelIndex()
    
    def has_id(self, id: int) -> bool:
        return self.sourceModel().has_id(id)
    
    def course_id(self) -> str:
        return self.sourceModel().course_id()

    @pyqtSlot(str)
    def set_search_filter(self, search_str: str) -> None:
        self.beginFilterChange()
        self._search_str = search_str
        self.invalidateFilter()

    def getRow(self, row: int) -> CourseItem:
        source_idx = self.mapToSource(self.index(row, 0))
        return self.sourceModel().getRow(source_idx.row())
    
    def source_id(self) -> str:
        return self.sourceModel().source_id()
    
    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex):
        if source_parent.isValid():
            return True

        if not self._search_str:
            return True
        
        source_index = self.sourceModel().index(source_row, 0)
        course: CourseItem = self.sourceModel().data(source_index, Qt.ItemDataRole.UserRole)
        print(course.source_id)
        search = self._search_str.lower()

        if search in course.name.lower():
            return True
        
        query = QSqlQuery(self.sourceModel().database())
        query.prepare("""
            SELECT EXISTS (
                SELECT 1 FROM Students 
                WHERE course_id = ? AND (
                    name LIKE ? OR  
                    name LIKE ? OR  
                    name LIKE ? OR
                    name = ?
                )
            )
        """)

        query.addBindValue(course.id)
        query.addBindValue(f"{self._search_str}%")    
        query.addBindValue(f"%{self._search_str}")    
        query.addBindValue(f"%{self._search_str}%")   
        query.addBindValue(self._search_str)  
        
        if query.exec() and query.next():
            return bool(query.value(0))
            
        return False
    
class FilteredStudentModel(QSortFilterProxyModel): 
    def __init__(self, source_model: StudentModel, parent = None):
        super().__init__(parent)
        self.setSourceModel(source_model)
        self._excluded_student_ids: list[int] = []
        self._exclusive_course_id: int | None = None
        self._hide_assigned = False
        self._search_str: str = ""

    def exclusive_course_id(self) -> int:
        return self._exclusive_course_id
        
    def add_excluded_student_id(self, student_id: int) -> None:
        self.beginFilterChange()
        self._excluded_student_ids.append(student_id)
        print("Currently filtered student ids: ", self._excluded_student_ids)
        self.invalidateFilter()

    def remove_excluded_student_id(self, student_id: int) -> bool:
        self.beginFilterChange()
        try:
            self._excluded_student_ids.remove(student_id)
            self.invalidateFilter()
            return True
        except ValueError:
            self.invalidateFilter()
            return False
        
    def set_exclusive_course_id(self, course_id: int | None) -> None:
        self.beginFilterChange()
        self._exclusive_course_id = course_id
        self.invalidateFilter()

    def set_exclude_assigned_students(self, exclude: bool) -> None:
        self.beginFilterChange()
        self._hide_assigned = exclude
        self.invalidateFilter()
        
    def getRow(self, index: QModelIndex) -> StudentItem:
        return self.sourceModel().getRow(self.mapToSource(index))

    @pyqtSlot(str)
    def set_search_filter(self, search_str: str) -> None:
        self.beginFilterChange()
        self._search_str = search_str
        self.invalidateFilter()
    
    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        if self._exclusive_course_id:
            if not self.sourceModel().course_id(self.sourceModel().index(source_row, 2)) == self._exclusive_course_id:
                return False
            
        elif self._hide_assigned:
            if self.sourceModel().course_id(self.sourceModel().index(source_row, 2)):
                return False

        if self._excluded_student_ids:
            student_id = self.sourceModel().record(source_row).value("id")
            if student_id in self._excluded_student_ids:
                return False

        if self._search_str:
            source_index = self.sourceModel().index(source_row, 0)
            student: StudentItem = self.sourceModel().getRow(source_index)
            search = self._search_str.lower()
            course_name = self.sourceModel().data(self.sourceModel().index(source_row, 2)).lower()

            if search in student.name.lower():
                return True
            if isinstance(course_name, str) and search in course_name.lower():
                return True
            if search in student.email:
                return True
            return False
            
        return True
    
class FilteredScheduleModel(QSortFilterProxyModel):
    def __init__(self, source_model: ScheduleModel, parent = None):
        super().__init__(parent)
        self.setSourceModel(source_model)
        self.setSortRole(Qt.ItemDataRole.EditRole)

        self._exclusive_course_id: int | None = None
        self._exclusive_date: QDate | None = None

    def schedules_for_month(self, month: QDate) -> list[QDate]:
        return self.sourceModel().schedules_for_month(month)
    
    def date_schedule_count(self, date: QDate) -> int:
        return self.sourceModel().date_schedule_count(date)

    def set_exclusive_course_id(self, course_id: int | None) -> None:
        self.beginFilterChange()
        self._exclusive_course_id = course_id
        self.invalidateFilter()

    def set_exclusive_date(self, date: QDate | None) -> None:
        self.beginFilterChange()
        self._exclusive_date = date
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        if self._exclusive_course_id:
            if not self.sourceModel().course_id(self.sourceModel().index(source_row, 2)) == self._exclusive_course_id:
                return False
            
        if self._exclusive_date:
            source_index = self.sourceModel().index(source_row, 2)
            date = self.sourceModel().data(source_index, Qt.ItemDataRole.EditRole)
            if date == self._exclusive_date.toJulianDay():
                return True
            return False
        
        return True
