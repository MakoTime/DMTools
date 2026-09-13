import sys

from application.startup import ApplicationLauncher


def main():
    return ApplicationLauncher(sys.argv).run()


if __name__ == "__main__":
	sys.exit(main())
