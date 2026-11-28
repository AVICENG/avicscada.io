from importlib.metadata import version

def test_xknx_runtime_dependency_is_installed_and_importable():
    from xknx import XKNX
    from xknx.io import ConnectionConfig

    assert callable(XKNX)
    assert callable(ConnectionConfig)
    installed = version("xknx")
    major = int(installed.split(".", 1)[0])
    assert major == 4
