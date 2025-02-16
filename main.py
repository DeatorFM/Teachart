from PyQt6.QtCore import QDir
from tcha.core import AppCore, MainWindow
import sys
import os

def main() -> None:
    root = os.path.dirname(os.path.abspath(__file__)) 
    QDir.addSearchPath("icons", os.path.join(root, "resources/icons"))
    QDir.addSearchPath("stylesheet", os.path.join(root, "resources/stylesheets"))
    app = AppCore(sys.argv)
    vm = MainWindow()
    vm.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()