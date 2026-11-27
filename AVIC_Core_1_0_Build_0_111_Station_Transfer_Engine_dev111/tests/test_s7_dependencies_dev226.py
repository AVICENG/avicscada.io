"""Optional Siemens S7 library availability and version guard tests."""
from __future__ import annotations

from importlib.metadata import version


def test_classic_s7_library_is_importable_when_extra_is_installed():
    import s7
    from s7 import Client

    assert callable(Client)
    assert version("python-snap7").split(".")[0] == "3"


def test_s7commplus_library_is_importable_when_extra_is_installed():
    import s7commplus
    from s7commplus import Client

    assert callable(Client)
    assert version("s7commplus").split(".")[0] == "0"
