from PyQt6.QtCore import QDir, QCoreApplication, QProcess, QSettings
from tcha.core import AppCore, MainWindow
import sys
import os

def restart() -> None:
    QCoreApplication.quit()
    status = QProcess.startDetached(sys.executable, sys.argv)
    print(status)

def main() -> None:
    app = AppCore(sys.argv)
    root = os.path.dirname(os.path.abspath(__file__)) 
    QDir.addSearchPath("icons", os.path.join(root, "resources/icons"))
    QDir.addSearchPath("stylesheet", os.path.join(root, "resources/stylesheets"))
    vm = MainWindow(app.db())
    vm.restartRequested.connect(restart)
    vm.show()
    sys.exit(app.exec())
     
if __name__ == "__main__":
    main()