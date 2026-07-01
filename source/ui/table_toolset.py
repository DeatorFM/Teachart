from PyQt6.QtCore import QCoreApplication, QSize, Qt
from PyQt6.QtGui import QActionGroup, QIcon, QPixmap
from PyQt6.QtWidgets import QMenu, QSizePolicy, QToolBar, QToolButton

from ui.commons import SwitchAction

ToolBarStyleSheet = """
QToolButton::menu-indicator {image: none;}
"""


class TableToolsetView:
    def setUI(self, agent: QToolBar) -> None:
        agent.setObjectName("TableToolset")
        agent.setFixedHeight(50)
        agent.setIconSize(QSize(23, 23))
        agent.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        agent.setAllowedAreas(Qt.ToolBarArea.TopToolBarArea)

        self.cell_editor_actions = QActionGroup(agent)

        self.ac_add_element = agent.addAction("")
        self.cell_editor_actions.addAction(self.ac_add_element)

        sep = agent.addSeparator()
        self.cell_editor_actions.addAction(sep)

        self.menu_element = QMenu()
        self.ac_from_clipboard = self.menu_element.addAction("")
        self.ac_from_clipboard.setEnabled(False)
        self.ac_from_clipboard.setData("Clipboard")

        self.menu_element.addSeparator()

        agent.widgetForAction(self.ac_add_element).setMenu(self.menu_element)
        agent.widgetForAction(self.ac_add_element).setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup
        )

        icon1 = QIcon()
        icon1.addPixmap(
            QPixmap("resources/icons/ic_insertRowBottom.svg"),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.ac_new_row = agent.addAction(icon1, None)
        self.cell_editor_actions.addAction(self.ac_new_row)

        icon2 = QIcon()
        icon2.addPixmap(
            QPixmap("resources/icons/ic_insertColumnRight.svg"),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.ac_new_column = agent.addAction(icon2, None)
        self.cell_editor_actions.addAction(self.ac_new_column)

        agent.addSeparator()

        icon3 = QIcon()
        icon3.addPixmap(
            QPixmap("resources/icons/ic_deleterow.svg"),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.ac_delete_row = agent.addAction(icon3, None)
        self.cell_editor_actions.addAction(self.ac_delete_row)

        icon4 = QIcon()
        icon4.addPixmap(
            QPixmap("resources/icons/ic_deletecolumn.svg"),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.ac_delete_column = agent.addAction(icon4, None)
        self.cell_editor_actions.addAction(self.ac_delete_column)

        icon5 = QIcon()
        icon5.addPixmap(
            QPixmap("resources/icons/ic_notpinned.svg"),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        icon6 = QIcon()
        icon6.addPixmap(
            QPixmap("resources/icons/ic_pinned.svg"), QIcon.Mode.Normal, QIcon.State.Off
        )
        self.ac_lock_size = SwitchAction(icon5, icon6, agent)
        agent.addAction(self.ac_lock_size)
        self.cell_editor_actions.addAction(self.ac_lock_size)

        self.retranslateUi()

    def retranslateUi(self) -> None:
        _translate = QCoreApplication.translate
        self.ac_add_element.setText(_translate("TableToolset", "Add to cell ▼"))
        self.ac_FromClipboard.setText(_translate("TableToolset", "From Clipboard"))
