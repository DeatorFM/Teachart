import os
import sys
from pathlib import Path

from PyQt6.QtCore import QCoreApplication, QDir, QProcess
from styling.resources import common
from tcha.core import AppCore


def restart() -> None:
    QCoreApplication.quit()
    status = QProcess.startDetached(sys.executable, sys.argv)
    print(status)


def main() -> None:
    app = AppCore(sys.argv)
    app.restartRequested.connect(restart)
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)
    QDir.addSearchPath("icons", str(Path(root).parent / "resources" / "svg"))
    app.show_startup_window()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
