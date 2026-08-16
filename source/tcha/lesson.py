from __future__ import annotations

from dataclasses import dataclass, field
from typing import Self

from PyQt6.QtCore import QDate, QDateTime, QTime, QXmlStreamReader, QXmlStreamWriter
from tcha.error import LFExceptions


@dataclass
class Lesson:
    source_id: str
    datetime: QDateTime = field(default_factory=QDateTime.currentDateTime)
    course_name: str = field(default=None)
    course_id: int = field(default=0)
    duration: int = field(default=0)
    comment: str = field(default="")

    def isvalid(self) -> bool:
        if len(self.source_id) > 1:
            return True
        return False

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
    def new(cls: Self, source_id: str) -> Self:
        return cls(source_id, QDateTime.currentDateTime())

    @classmethod
    def read(cls: Self, reader: QXmlStreamReader, strict=False, logger) -> Lesson:
        """Reads data from an XML DOM element and returns an instance of Lesson.
        If a value is invalid a ModelReadError is invoked."""
        attrs = reader.attributes()
        datetime = QDateTime()

        try:
            datetime.setDate(QDate.fromJulianDay(int(attrs.value("date"))))
            datetime.setTime(QTime.fromMSecsSinceStartOfDay(int(attrs.value("date"))))
            course_name = str(attrs.value("course_name"))
            course_id = int(attrs.value("course_id"))
            duration = int(attrs.value("duration"))
            comment = reader.readElementText()
            source_id = str(attrs.value("source_id"))
            return cls(source_id, datetime, course_name, course_id, duration, comment)

        except (ValueError, TypeError):
            raise LFExceptions.ModelReadError(False)

    def copy(self) -> Lesson:
        """Creates a deepcopy of the object"""
        return Lesson(
            self.source_id,
            QDateTime(self.datetime),
            self.course_name,
            self.course_id,
            self.duration,
            self.comment,
        )
