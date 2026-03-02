import oncepy
from oncepy import hello


def test_hello_returns_expected_message() -> None:
    assert hello() == "Hello from oncepy!"


def test_version_is_exposed() -> None:
    assert oncepy.__version__
