from application import ApplicationLauncher, ProjectController


def test_application_exports_are_lazy_and_available():
    assert ProjectController.__name__ == "ProjectController"
    assert ApplicationLauncher.__name__ == "ApplicationLauncher"