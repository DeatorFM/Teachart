import os
import re
import sys
from pathlib import Path


def compress_qss(qss_content: str) -> str:
    """Compresses stylesheet by removing any unnecessary whitespaces and line breaks etc."""
    qss = re.sub(r"/\*.*?\*/", "", qss_content, flags=re.DOTALL)
    qss = re.sub(r"//.*?$", "", qss, flags=re.MULTILINE)

    qss = re.sub(r"[\n\r\t]+", " ", qss)
    qss = re.sub(r" +", " ", qss)

    qss = re.sub(r" *\{ *", "{", qss)
    qss = re.sub(r" *\} *", "}", qss)
    qss = re.sub(r" *; *", ";", qss)
    qss = re.sub(r" *, *", ",", qss)
    qss = re.sub(r" *> *", ">", qss)
    qss = re.sub(r" *\+ *", "+", qss)
    qss = re.sub(r" *~ *", "~", qss)

    qss = re.sub(r" *: *", ":", qss)

    qss = qss.strip()

    return qss


def qss_to_py(name: str, input_qss: Path) -> None:
    from source.styling.stylesheets import STYLESHEETS

    # Read and compress the QSS file
    qss_content = input_qss.read_text(encoding="utf-8")
    compressed = compress_qss(qss_content)

    # Update the dictionary
    STYLESHEETS[name] = compressed

    # Write to stylesheets.py
    stylesheets_file = Path() / "source" / "styling" / "stylesheets.py"

    py_content = "# Auto-generated - Do not edit manually\n\n"
    py_content += "STYLESHEETS = {\n"

    for theme_name, qss in STYLESHEETS.items():
        # Escape backslashes and single quotes
        escaped_qss = qss.replace("\\", "\\\\").replace("'", "\\'")
        py_content += f"    '{theme_name}': '{escaped_qss}',\n"

    py_content += "}\n"

    stylesheets_file.write_text(py_content, encoding="utf-8")


def main():
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    sys.path.insert(0, str(project_root))

    if len(sys.argv) == 3:
        name = sys.argv[1]
        path = Path(sys.argv[2])

        if path.exists():
            print(f"Updating stylesheet of native theme '{name}' and integrate in .py-file.")
            qss_to_py(name, path)
            return
        else:
            print(f"File '{path}' doesn't exist")
            return

    print("Not enough or too many arguments")


if __name__ == "__main__":
    main()
