import sys
import os
import sys

os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.join(
    os.path.dirname(sys.executable),
    "Lib/site-packages/PyQt5/Qt5/plugins/platforms"
)
from PyQt5.QtWidgets import QApplication
from ui_main import MainWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())