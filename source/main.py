import os
import sys

from styling.resources import common
from tcha.core import AppCore


def main() -> None:
    app = AppCore(sys.argv)
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)
    app.show_startup_window()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
