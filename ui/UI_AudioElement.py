from PyQt6.QtWidgets import QWidget, QSizePolicy, QVBoxLayout, QHBoxLayout, QFrame, QLineEdit
from PyQt6.QtCore import QSize, Qt
from ui.UI_Commons import SwitchButton
from ui.StyledWidget import fromStyle

class AudioView:

    def setUi(self, agent: QWidget) -> None:
        agent.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)        
        # agent.setMinimumWidth(90)
        agent.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        agent.setStyleSheet(fromStyle("AudioElement"))
        print("Audio size", agent.width(), agent.height())

        self.main_layout = QVBoxLayout(agent)
        self.main_layout.setContentsMargins(0, 0, 0, -5)
        agent.setLayout(self.main_layout)

        self.main_frame = QFrame(agent)
        self.main_frame.setFrameShape(QFrame.Shape.Box)

        self.frame_layout = QHBoxLayout(self.main_frame)

        self.frame_layout.setContentsMargins(3, 3, 7, 3)

        self.main_frame.setLayout(self.frame_layout)

        self.swi_PlayPause = SwitchButton("resources/icons/ic_play.svg", "resources/icons/ic_pause.svg", self.main_frame)
        self.swi_PlayPause.setMaximumSize(QSize(23, 23))
        self.swi_PlayPause.setObjectName("swi_PlayPause")
        self.frame_layout.addWidget(self.swi_PlayPause)

        self.le_name = QLineEdit(self.main_frame)
        self.le_name.setObjectName("self.le_name")
        # self.le_name.setMinimumWidth(90)
        self.le_name.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # self.le_name.setMaximumWidth(300)
        self.frame_layout.addWidget(self.le_name)