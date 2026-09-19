from argparse import ArgumentError, ArgumentTypeError
from pathlib import Path

import pytest
from tcha.utils import LaunchConfig, parse_args


@pytest.fixture
def argument_cases() -> dict[tuple[str], LaunchConfig | None]:
    return {
        (): LaunchConfig(None, False, 0, False, False, {}),
        ("lesson.tch",): LaunchConfig(Path("lesson.tch"), False, 0, False, False, {}),
        ("--clean",): LaunchConfig(None, False, 0, True, False, {}),
        ("--debug",): LaunchConfig(None, True, 0, False, False, {}),
        ("--debug", "10"): LaunchConfig(None, True, 10, False, False, {}),
        ("lesson.tch", "--clean", "--debug", "50"): LaunchConfig(
            Path("lesson.tch"), True, 50, True, False, {}
        ),
        ("--test",): LaunchConfig(None, False, 0, False, False, {}),
        ("--test", "source_id=B473DE34A"): LaunchConfig(
            None,
            False,
            0,
            False,
            True,
            {"source_id": "B473DE34A"},
        ),
        ("--test", "db=custom.tdb"): LaunchConfig(
            None,
            False,
            0,
            False,
            True,
            {"db": Path("custom.tdb")},
        ),
        ("--test", "theme=native:dark", "confetti=true"): LaunchConfig(
            None,
            False,
            0,
            False,
            True,
            {"theme": "native:dark", "confetti": True},
        ),
        ("--debug", "15"): None,
        ("--debug", "verbose"): None,
    }


class TestParser:
    def test_launch_parser(self, argument_cases):
        for key, result in argument_cases.items():
            try:
                assert result == parse_args(key, exit_on_error=False)
            except (ArgumentError, ArgumentTypeError):
                assert result is None
