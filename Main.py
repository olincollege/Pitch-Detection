from PyQt5.QtWidgets import QApplication
import sys
from Model import KaraokeModel, AudioRecorder
from View import KaraokeView
from Controller import KaraokeController

def main() -> None:
    """
    Application entry point for the karaoke app.
    """
    app = QApplication(sys.argv)
    model = KaraokeModel()
    view = KaraokeView(model)
    controller = KaraokeController(model, view)
    controller.load_songs()
    view.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
