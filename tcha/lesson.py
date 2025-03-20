from PyQt6.QtCore import QDateTime, QTime, QDate, QXmlStreamWriter, QXmlStreamReader
from tcha.dbmodels import CourseItem
from dataclasses import dataclass, field

@dataclass
class Lesson:
    datetime: QDateTime
    course: CourseItem = field(default_factory=CourseItem.no_course)
    duration: int = field(default=0)
    comment: str = field(default="") 

    def set_datetime(self, datetime: QDateTime) -> None:
        self.datetime = datetime

    def set_course(self, course: CourseItem) -> None:
        self.course = course

    def set_duration(self, minutes: int) -> None:
        self.duration = minutes

    def set_comment(self, text: str) -> None:
        self.comment = text

    def xml(self, stream: QXmlStreamWriter) -> QXmlStreamWriter:
        """Writes an element with the lesson data to an QXmlStreamWriter."""
        stream.writeStartElement("lesson")
        stream.writeAttribute("course_name", self.course.name)
        stream.writeAttribute("course_id", str(self.course.ID))
        stream.writeAttribute("date", str(self.datetime.date().toJulianDay()))
        stream.writeAttribute("time", str(self.datetime.time().msecsSinceStartOfDay()))
        stream.writeAttribute("duration", str(self.duration))
        stream.writeCharacters(self.comment)
        stream.writeEndElement()
        return stream
    
    @classmethod
    def read(cls, reader: QXmlStreamReader) -> "Lesson":
        """Reads data from an XML DOM element and returns an instance of Lesson."""
        attrs = reader.attributes()
        datetime = QDateTime()
        datetime.setTime(QTime().addMSecs(int(attrs.value("time"))))
        datetime.setDate(QDate.fromJulianDay(int(attrs.value("date"))))
        course = CourseItem(attrs.value("course_name"), int(attrs.value("course_id")))
        duration = int(attrs.value("duration"))
        comment = reader.readElementText()
        return cls(datetime, course, duration, comment)