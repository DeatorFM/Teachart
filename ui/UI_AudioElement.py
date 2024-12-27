from PyQt6 import QtCore, QtWidgets
from ui.UI_Commons import SwitchButton
from ui.StyledWidget import fromStyle

class AudioView:

    def setUi(self, agent: QtWidgets.QWidget) -> None:
        # agent.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        agent.setFixedSize(150, 35)
        agent.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
        agent.setStyleSheet(fromStyle("AudioElement"))

        self.main_layout = QtWidgets.QVBoxLayout(agent)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        agent.setLayout(self.main_layout)

        self.main_frame = QtWidgets.QFrame(agent)
        self.main_frame.setFixedSize(150, 35)
        self.main_frame.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.main_frame.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)

        self.frame_layout = QtWidgets.QHBoxLayout(self.main_frame)

        self.frame_layout.setContentsMargins(3, 3, 7, 3)

        self.main_frame.setLayout(self.frame_layout)

        self.swi_PlayPause = SwitchButton("resources/icons/ic_play.svg", "resources/icons/ic_pause.svg", self.main_frame)
        self.swi_PlayPause.setMaximumSize(QtCore.QSize(23, 23))
        self.swi_PlayPause.setObjectName("swi_PlayPause")
        self.frame_layout.addWidget(self.swi_PlayPause)

        self.le_name = QtWidgets.QLineEdit(self.main_frame)
        self.le_name.setObjectName("self.le_name")
        self.frame_layout.addWidget(self.le_name)
