from PyQt6.QtCore import QDateTime, QTime, QDate, QXmlStreamWriter, QXmlStreamReader
from dataclasses import dataclass, field

@dataclass
class Lesson:
    datetime: QDateTime
    course_name: str
    course_id: int = field(default=0)
    duration: int = field(default=0)
    comment: str = field(default="")
    source_id: str = field(default='0')

    def set_datetime(self, datetime: QDateTime) -> None:
        self.datetime = datetime

    def set_course(self, name: str, id: int) -> None:
        self.course_name = name
        self.course_id = id

    def set_duration(self, minutes: int) -> None:
        self.duration = minutes

    def set_comment(self, text: str) -> None:
        self.comment = text

    def xml(self, stream: QXmlStreamWriter) -> QXmlStreamWriter:
        """Writes an element with the lesson data to an QXmlStreamWriter."""
        stream.writeStartElement("lesson")
        stream.writeAttribute("course_name", self.course_name)
        stream.writeAttribute("course_id", str(self.course_id))
        stream.writeAttribute("date", str(self.datetime.date().toJulianDay()))
        stream.writeAttribute("time", str(self.datetime.time().msecsSinceStartOfDay()))
        stream.writeAttribute("duration", str(self.duration))
        stream.writeAttribute("source_id", self.source_id)
        stream.writeCharacters(self.comment)
        stream.writeEndElement()
        return stream
    
    @classmethod
    def read(cls, reader: QXmlStreamReader) -> "Lesson":
        """Reads data from an XML DOM element and returns an instance of Lesson."""
        attrs = reader.attributes()
        datetime = QDateTime()
        time = QTime()
        time = time.addMSecs(int(attrs.value("time")))
        datetime.setDate(QDate.fromJulianDay(int(attrs.value("date"))))
        datetime.setTime(time)
        course_name = attrs.value("course_name")
        course_id = int(attrs.value("course_id"))
        duration = int(attrs.value("duration"))
        comment = reader.readElementText()
        source_id = attrs.value("source_id")
        return cls(datetime, course_name, course_id, duration, comment, source_id)