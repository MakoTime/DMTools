__all__ = ["ApplicationLauncher", "ProjectController"]


def __getattr__(name):
	if name == "ProjectController":
		from .project_controller import ProjectController

		return ProjectController
	if name == "ApplicationLauncher":
		from .startup import ApplicationLauncher

		return ApplicationLauncher
	raise AttributeError(name)
