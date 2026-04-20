# main.py
import os
import sys
import PyQt5

# 【终极修复 Qt 插件路径】：自动扫描当前虚拟环境下所有可能的插件位置
try:
    pyqt_dir = os.path.dirname(PyQt5.__file__)
    possible_paths = [
        os.path.join(pyqt_dir, 'Qt5', 'plugins', 'platforms'),
        os.path.join(pyqt_dir, 'Qt', 'plugins', 'platforms'),
        os.path.join(pyqt_dir, 'plugins', 'platforms')
    ]
    for p in possible_paths:
        if os.path.exists(p):
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = p
            break
except Exception as e:
    print(f"插件路径寻找出现异常: {e}")

from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget
import database
from tab_maintenance import TabMaintenance
from tab_calculation import TabCalculation

# 全局现代风格 QSS
MODERN_STYLE = """
    QWidget { font-family: "Microsoft YaHei", "Segoe UI"; font-size: 10pt; color: #2c3e50; }

    QTabWidget::pane { border: 1px solid #bdc3c7; background: #ffffff; border-radius: 4px; top: -1px; }
    QTabBar::tab { background: #ecf0f1; border: 1px solid #bdc3c7; padding: 10px 25px; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
    QTabBar::tab:selected { background: #ffffff; border-bottom-color: #ffffff; font-weight: bold; color: #2980b9; }

    /* 输入框/下拉框通用样式 */
    QLineEdit, QComboBox { 
        border: 1px solid #bdc3c7; 
        border-radius: 4px; 
        padding: 4px 6px; 
        background: #ffffff; 
        min-height: 28px; 
    }
    QLineEdit:focus, QComboBox:focus { border: 1px solid #3498db; }

    /* 【Bug修复】：彻底消除所有可编辑下拉框内部的嵌套边框 */
    QComboBox QLineEdit {
        border: none;
        background: transparent;
        margin: 0px;
        padding: 0px;
    }

    QComboBox::drop-down { border: none; width: 25px; }
    QComboBox::down-arrow {
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 5px solid #7f8c8d;
        margin-right: 5px;
    }

    QPushButton { background-color: #f3f3f3; border: 1px solid #bdc3c7; border-radius: 4px; padding: 6px 15px; font-weight: bold; }
    QPushButton:hover { background-color: #e0e0e0; }

    QTableWidget { border: 1px solid #bdc3c7; background-color: #ffffff; alternate-background-color: #f9f9f9; gridline-color: #ecf0f1; }
    QHeaderView::section { background-color: #f1f4f6; border: none; border-right: 1px solid #bdc3c7; border-bottom: 1px solid #bdc3c7; padding: 6px; font-weight: bold; }

    QGroupBox { border: 1px solid #dcdde1; border-radius: 8px; margin-top: 15px; padding-top: 10px; font-weight: bold; }
    QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 10px; left: 10px; color: #2980b9; }
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("多级配方穿透核算系统 - 专业版")
        self.resize(1000, 750)

        database.init_db()

        self.tabs = QTabWidget()
        self.tab1 = TabMaintenance()
        self.tab2 = TabCalculation()

        self.tabs.addTab(self.tab1, "🛠️ 配方维护")
        self.tabs.addTab(self.tab2, "🧮 穿透核算")

        self.setCentralWidget(self.tabs)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(MODERN_STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())