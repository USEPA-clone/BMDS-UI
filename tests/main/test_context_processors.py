from bmds_ui.main.context_processors import desktop_versions


def test_desktop_versions():
    assert isinstance(desktop_versions(), dict)
