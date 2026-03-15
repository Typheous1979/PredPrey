import sys
from ui.app import create_app
from ui.main_window import MainWindow
from params.defaults import build_default_registry
from core.events import EventBus


def main():
    params    = build_default_registry()
    event_bus = EventBus()

    app    = create_app(sys.argv)
    window = MainWindow(params, event_bus)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
