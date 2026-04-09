import importlib
from types import ModuleType


def test_import_voidcode_exposes_version() -> None:
    voidcode = importlib.import_module("voidcode")

    assert isinstance(voidcode, ModuleType)
    version = getattr(voidcode, "__version__", None)

    assert version == "0.1.0"
