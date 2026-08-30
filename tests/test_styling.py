from collections.abc import Generator

import pytest
from PyQt6.QtCore import QByteArray, QDataStream, QIODevice, Qt
from PyQt6.QtGui import QColor, QPalette


def generate_bytearray(data, name, struct, add_magic_header=True) -> QByteArray:
    bytearr = QByteArray()
    stream = QDataStream(bytearr, QIODevice.OpenModeFlag.WriteOnly)
    if add_magic_header:
        stream.writeBytes(b"tcha-qrc")
    stream.writeBytes(data)
    stream.writeBytes(name)
    stream.writeBytes(struct)

    return bytearr


@pytest.fixture
def test_resource_data() -> Generator[dict[bytes, tuple[bool, bool]], None, None]:
    from styling.resources import light

    d = {}
    d[
        generate_bytearray(
            light.qt_resource_data, light.qt_resource_name, light.qt_resource_struct
        ).data()
    ] = (True, True)
    d[
        generate_bytearray(
            light.qt_resource_data,
            b"",
            light.qt_resource_struct,
        ).data()
    ] = (True, False)

    d[
        generate_bytearray(
            light.qt_resource_data, light.qt_resource_name, light.qt_resource_struct, False
        ).data()
    ] = (False, False)

    yield d


@pytest.fixture
def test_palettes() -> list[dict]:

    test_cases = []

    input_dict = {
        "Text": [0, 0, 0, 255],
        "Base": [255, 255, 255, 255],
        "Window": [240, 240, 240, 255],
        "WindowText": [0, 0, 0, 255],
    }
    expected = QPalette()
    expected.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0, 255))
    expected.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255, 255))
    expected.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240, 255))
    expected.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0, 255))
    test_cases.append(
        {
            "input": input_dict,
            "apply_all": False,
            "expected_result": expected,
        }
    )

    input_dict = {
        "Text": [0, 0, 0, 255],
        "Light": [200, 200, 200, 255],  # Ignored when apply_all=False
        "Dark": [100, 100, 100, 255],  # Ignored
    }
    expected = QPalette()
    expected.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0, 255))
    test_cases.append(
        {
            "input": input_dict,
            "apply_all": False,
            "expected_result": expected,
        }
    )

    input_dict = {
        "Text": [0, 0, 0, 255],
        "Light": [220, 220, 220, 255],
        "Dark": [80, 80, 80, 255],
        "Mid": [160, 160, 160, 255],
    }
    expected = QPalette()
    expected.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0, 255))
    expected.setColor(QPalette.ColorRole.Light, QColor(220, 220, 220, 255))
    expected.setColor(QPalette.ColorRole.Dark, QColor(80, 80, 80, 255))
    expected.setColor(QPalette.ColorRole.Mid, QColor(160, 160, 160, 255))
    test_cases.append(
        {
            "input": input_dict,
            "apply_all": True,
            "expected_result": expected,
        }
    )

    input_dict = {
        "Text": [0, 0, 0, 255],
        "Disabled.Text": [128, 128, 128, 255],
    }
    expected = QPalette()
    expected.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0, 255))
    expected.setColor(
        QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(128, 128, 128, 255)
    )
    test_cases.append(
        {
            "input": input_dict,
            "apply_all": False,
            "expected_result": expected,
        }
    )

    return test_cases


@pytest.fixture
def test_svg_colors() -> dict[tuple[str, float], QColor]:
    return {
        # Basic colors (full opacity)
        ("#000000", 1.0): QColor(0, 0, 0, 255),  # Black
        ("#ffffff", 1.0): QColor(255, 255, 255, 255),  # White
        ("#ff0000", 1.0): QColor(255, 0, 0, 255),  # Red
        ("#00ff00", 1.0): QColor(0, 255, 0, 255),  # Green
        ("#0000ff", 1.0): QColor(0, 0, 255, 255),  # Blue
        # Common UI colors (full opacity)
        ("#808080", 1.0): QColor(128, 128, 128, 255),  # Gray
        ("#0078d7", 1.0): QColor(0, 120, 215, 255),  # Windows blue
        ("#2a82da", 1.0): QColor(42, 130, 218, 255),  # Dark theme blue
        # Named colors (full opacity)
        ("#00ffff", 1.0): QColor(Qt.GlobalColor.cyan),
        ("#ff00ff", 1.0): QColor(Qt.GlobalColor.magenta),
        ("#ffff00", 1.0): QColor(Qt.GlobalColor.yellow),
        # Custom palette colors (full opacity)
        ("#f0f0f0", 1.0): QColor(240, 240, 240, 255),  # Light gray background
        ("#1e1e1e", 1.0): QColor(30, 30, 30, 255),  # Dark background
        ("#f5f5f5", 1.0): QColor(245, 245, 245, 255),  # Alternate base
        # Edge cases (full opacity)
        ("#010203", 1.0): QColor(1, 2, 3, 255),  # Low values
        ("#fefdfc", 1.0): QColor(254, 253, 252, 255),  # High values
        # Semi-transparent colors
        ("#ff0000", 0.501960813999176): QColor(255, 0, 0, 128),  # Red at 50% opacity
        ("#00ff00", 0.250980406999588): QColor(0, 255, 0, 64),  # Green at 25% opacity
        ("#0000ff", 0.7529411911964417): QColor(0, 0, 255, 192),  # Blue at 75% opacity
        # RGB only (alpha defaults to 255)
        ("#6496c8", 1.0): QColor(100, 150, 200),  # Light blue
        ("#324b64", 1.0): QColor(50, 75, 100),  # Dark blue-gray
    }


from styling.theming import make_palette, restructure_resource_data
from styling.utils import Svg
from tcha.error import BinReadError


class TestTheming:
    def test_restructure_resource_data(self, test_resource_data):
        """Testing seperating the resource data in three parts found in the resources.bin file of a .taste-file."""
        for bytesobj, results in test_resource_data.items():
            result_func, result_completeness = results
            try:
                restructured = restructure_resource_data(bytesobj)
                assert all(restructured) == result_completeness
                assert result_func == True
            except BinReadError:
                assert result_func == False

    def test_palette_parsing(self, test_palettes):
        """Testing palette creation by parsing the dictionary structure from properties.json or native themes properties dictionary."""
        for case in test_palettes:
            assert case["expected_result"] == make_palette(case["input"], case["apply_all"])


class TestSvg:
    @pytest.fixture
    def test_svg(self) -> str:
        return '<svg width="24" height="24" viewBox="0 0 24 24"><path d="M8 6.82v10.36c0 .79.87 1.27 1.54.84l8.14-5.18a1 1 0 0 0 0-1.69L9.54 5.98A.998.998 0 0 0 8 6.82z" /></svg>'

    @pytest.fixture
    def test_svg_object(self, test_svg) -> Svg:
        element = Svg(test_svg)
        assert element.to_string().decode() == test_svg
        return element

    def test_svg_coloring(self, test_svg_object, test_svg_colors):
        for expected, qcolor in test_svg_colors.items():
            hexstr, opacity = expected
            print(hexstr, opacity)
            colored = test_svg_object.colored(qcolor)
            assert colored.tree.get("fill") == hexstr
            try:
                value = colored.tree.get("fill-opacity")
                print("got value", value)
                assert float(value) == opacity
            except TypeError:
                assert opacity == 1.0

    def test_svg_rotation(self, test_svg_object):
        rotations = [180, 380, 100, 25, -65, 90, 270, -90, None]
        for rotation in rotations:
            rotated = test_svg_object.rotated(rotation)
            if rotation is not None:
                assert rotation == rotated.rotation
            else:
                assert rotated.rotation == 0
