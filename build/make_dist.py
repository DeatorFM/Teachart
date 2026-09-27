import PyInstaller.__main__ as pyinstall

pyinstall.run(
    [
        "source/main.py",
        "--onefile",
        "--windowed",
        "--name=teachart_1.0.0-b.1",
        "--icon=resources/icons/logo.ico",
        "--distpath=dist",
        "--collect-submodules=nativeelements",
        "--collect-submodules=styling.resources",
    ]
)
