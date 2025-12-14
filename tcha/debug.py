from typing import Self
from PyQt6 import uic
from PyQt6.QtWidgets import QDialog, QHeaderView
from PyQt6.QtCore import Qt, QFile, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtXml import QDomDocument
 
from tcha.lesson import Lesson
from tcha.lfio import LessonFile
from tcha.resmanager import ResourceContainer

class FileView(QDialog):
    def __init__(self, parent = None):
        super().__init__(parent, Qt.WindowType.Tool)
        self.ui = uic.loadUi("ui/debug_file_info.ui", self)

    def setup_view(self, lf: LessonFile, lesson: Lesson, schedule_id: int | None) -> None:
        if lf.path:
            self.ui.lb_show_path.setText(lf.path)
        else:
            self.ui.lb_show_path.setText("No file")

        self.ui.lb_show_fileid.setText(lf.file_id.hex)
        self.ui.lb_show_version.setText(str(lf.version))

        if lesson.course_id != 0:
            self.ui.lb_show_course_name.setText(lesson.course_name)
        else:
            self.ui.lb_show_course_name.setText("No course")
        self.ui.lb_show_courseid.setText(str(lesson.course_id))
        
        if schedule_id != None:
            self.ui.lb_show_scheduleid.setText(str(schedule_id))
        else:
            self.ui.lb_show_scheduleid.setText("No schedule found")

        self.ui.lb_show_sourceid.setText(lesson.source_id)
        self.ui.lb_show_date.setText(f"Formatted: {lesson.datetime.date().toString("dd/MM/yyyy")}; Raw: {lesson.datetime.date().toJulianDay()}")
        self.ui.lb_show_time.setText(f"Formatted: {lesson.datetime.time().toString("hh:mm")}; Raw: {lesson.datetime.time().msecsSinceStartOfDay()}")
        self.ui.lb_show_duration.setText(f"{lesson.duration} min")


class XmlView(QDialog):
    def __init__(self, parent = None):
        super().__init__(parent, Qt.WindowType.Tool)
        self.ui = uic.loadUi("ui/debug_xml.ui", self)

    def setup_view(self, structure_xml: QFile, resource_xml: QFile) -> None:
        structure_def = QDomDocument()
        structure_def.setContent(structure_xml)
        resource_def = QDomDocument()
        resource_def.setContent(resource_xml)
        self.ui.tb_structure.setText(structure_def.toString(2))
        self.ui.tb_resources.setText(resource_def.toString(2))


class ResourceViewModel(QAbstractTableModel):
    def __init__(self, rescont: ResourceContainer, parent = None):
        super().__init__(parent)
        self._rescont = tuple(rescont.contents())

    def rowCount(self, parent = QModelIndex) -> int:
        if parent.isValid():
            return 0
        return len(self._rescont)
    
    
    def columnCount(self, parent = ...) -> int:
        return 4
    
    def data(self, index: QModelIndex, role = Qt.ItemDataRole.DisplayRole) -> str | None:
        # print(f"Getting data for {index.row()}|{index.column()}")
        if role == Qt.ItemDataRole.DisplayRole:
            resobj = self._rescont[index.row()]
            match index.column():
                case 0:
                    return resobj.type.name
                case 1:
                    return str(resobj.type_num)
                case 2:
                    return resobj.path if resobj.path else "Not an external resource"
                case 3:
                    return str(resobj.member_count)
        return None
            
    def headerData(self, section: int, orientation: Qt.Orientation, role = Qt.ItemDataRole.DisplayRole) -> str:
        if orientation == Qt.Orientation.Horizontal:
            if role == Qt.ItemDataRole.DisplayRole:
                match section:
                    case 0:
                        return "Type"
                    case 1:
                        return "Type Index"
                    case 2:
                        return "Path"
                    case 3:
                        return "Member Count"
            elif role == Qt.ItemDataRole.SizeHintRole:
                if section == 2: return 490
        return super().headerData(section, orientation, role)
        

class ResourceView(QDialog):
    def __init__(self, parent = None):
        super().__init__(parent, Qt.WindowType.Tool)
        self.ui = uic.loadUi("ui/debug_resources.ui", self)
        self.resize(830, 500)

    def setup_view(self, rescont: ResourceContainer) -> None:
        model = ResourceViewModel(rescont)
        self.ui.tv_robjects.setModel(model)
        self.tv_robjects.header().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)