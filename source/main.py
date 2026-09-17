import os
import sys

from PyQt6.QtCore import QCoreApplication, QProcess
from styling.resources import common
from tcha.core import AppCore


def restart() -> None:
    QCoreApplication.quit()
    status = QProcess.startDetached(sys.executable)
    print(status)


def main() -> None:
    app = AppCore(sys.argv)
    app.restartInitiated.connect(restart)
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)
    app.show_startup_window()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
