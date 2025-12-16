from PyQt6 import QtWidgets, QtCore, QtGui
from tcha.settings import Settings
from ui.StyledWidget import fromStyle

class MainView(QtWidgets.QMainWindow):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setUI()
        if Settings.qsettings().value("Application/debug", False, bool):
            self.setWindowTitle("Teachart Indev (Debug)")
        else:
            self.setWindowTitle("Teachart Indev")
        self.setStyleSheet(fromStyle("Common"))

    def setUI(self):
        self.setObjectName("MainWindow")
        self.resize(1100, 700)
        self.setMinimumSize(QtCore.QSize(1100, 0))
        self.central_widget = QtWidgets.QWidget(self)
        self.central_widget.setEnabled(True)
        self.central_widget.setObjectName("centralwidget")
        self.central_layout = QtWidgets.QVBoxLayout(self.central_widget)
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_layout.setSpacing(0)
        self.central_layout.setObjectName("centralLayout")

        self.tab_widget = QtWidgets.QTabWidget(self.central_widget)
        font = QtGui.QFont()
        font.setFamily("Segoe UI Variable Small Semilig")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        
        self.tab_widget.setFont(font)
        # self.tab_widget.setStyleSheet(fromStyle("TabBar"))
        self.tab_widget.setTabShape(QtWidgets.QTabWidget.TabShape.Rounded)
        self.tab_widget.setElideMode(QtCore.Qt.TextElideMode.ElideNone)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setObjectName("tabWidget")

        self.central_layout.addWidget(self.tab_widget)
        self.setCentralWidget(self.central_widget)

        self.statusbar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.statusbar)