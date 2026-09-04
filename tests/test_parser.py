import pytest

from tcha.utils import _parser, _test_parser, LaunchConfig
from argparse import ArgumentError, ArgumentTypeError

@pytest.fixture
def argument_cases() -> dict[tuple[str], LaunchConfig | ArgumentError | ArgumentTypeError]:
    pass

class TestParser:
    def test_launch_parser(argument_cases):
        pass
