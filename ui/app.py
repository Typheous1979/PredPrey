import sys
from PyQt6.QtWidgets import QApplication


def create_app(argv=None) -> QApplication:
    if argv is None:
        argv = sys.argv
    app = QApplication(argv)
    app.setApplicationName("PredPrey Simulator")
    app.setStyle("Fusion")
    return app
