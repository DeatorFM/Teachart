import PyInstaller.__main__ as pyinstall

pyinstall.run(
    [
        "source/main.py",
        "--onefile",
        "--windowed",
        "--name=teachart",
        "--icon=resources/icons/logo.ico",
        "--distpath=dist",
        '--add-data="resources/icons:icons"',
    ]
)
