from importlib.metadata import version

from ._core import hello

__version__ = version("oncepy")

__all__ = ["__version__", "hello"]
