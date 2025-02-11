from PyQt6.QtCore import QDir, QCoreApplication
from educ.core import HTCore, MainWindow
import sys
import os

def main() -> None:
    root = os.path.dirname(os.path.abspath(__file__)) 
    QDir.addSearchPath("icons", os.path.join(root, "resources/icons"))
    QDir.addSearchPath("stylesheet", os.path.join(root, "resources/stylesheets"))
    app = HTCore(sys.argv)
    vm = MainWindow()
    vm.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()