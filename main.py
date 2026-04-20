# main.py
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget
import database
from tab_maintenance import TabMaintenance
from tab_calculation import TabCalculation
import os
import sys
import PyQt5

# 【核心修复代码】强行定位 Qt 插件路径
# 这段代码会自动寻找你当前环境里 PyQt5 存放插件的真实位置
dirname = os.path.dirname(PyQt5.__file__)
plugin_path = os.path.join(dirname, 'Qt5', 'plugins', 'platforms')

if os.path.exists(plugin_path):
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
else:
    # 兼容某些版本的路径差异
    plugin_path = os.path.join(dirname, 'Qt', 'plugins', 'platforms')
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
# 定义全局现代风格 CSS (QSS)
MODERN_STYLE = """
    /* 全局字体和颜色 */
    QWidget { font-family: "Microsoft YaHei", "Segoe UI", sans-serif; font-size: 10pt; color: #2c3e50; }

    /* 选项卡美化 */
    QTabWidget::pane { border: 1px solid #bdc3c7; background: #ffffff; border-radius: 4px; top: -1px; }
    QTabBar::tab { background: #ecf0f1; border: 1px solid #bdc3c7; border-bottom-color: #bdc3c7; padding: 8px 20px; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
    QTabBar::tab:selected { background: #ffffff; border-bottom-color: #ffffff; font-weight: bold; color: #2980b9; }
    QTabBar::tab:hover:!selected { background: #e0e6ed; }

    /* 按钮美化 (默认灰色系，特定按钮在代码里单独设色) */
    QPushButton { background-color: #ecf0f1; border: 1px solid #bdc3c7; border-radius: 4px; padding: 6px 12px; font-weight: bold; }
    QPushButton:hover { background-color: #d0d6dc; border-color: #95a5a6; }
    QPushButton:pressed { background-color: #bdc3c7; }

    /* 输入框和下拉框美化 */
    QLineEdit, QComboBox { border: 1px solid #bdc3c7; border-radius: 4px; padding: 5px; background: #ffffff; }
    QLineEdit:focus, QComboBox:focus { border: 2px solid #3498db; }
    QComboBox::drop-down { border: none; width: 20px; }

    /* 表格美化 */
    QTableWidget { border: 1px solid #bdc3c7; border-radius: 4px; background-color: #ffffff; alternate-background-color: #f9f9f9; selection-background-color: #ebf5fb; selection-color: #2c3e50; }
    QHeaderView::section { background-color: #f1f4f6; border: none; border-right: 1px solid #bdc3c7; border-bottom: 1px solid #bdc3c7; padding: 6px; font-weight: bold; color: #34495e; }

    /* 区域框 (GroupBox) 美化 */
    QGroupBox { border: 1px solid #bdc3c7; border-radius: 6px; margin-top: 15px; padding-top: 15px; }
    QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 10px; left: 10px; color: #2980b9; font-weight: bold; }
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("多级配方(BOM)穿透核算系统 - 专业版")
        self.resize(950, 700)  # 稍微放大窗口以适应更好的排版

        database.init_db()

        self.tabs = QTabWidget()
        self.tab1 = TabMaintenance()
        self.tab2 = TabCalculation()

        self.tabs.addTab(self.tab1, "🛠️ 配方库管理与维护")
        self.tabs.addTab(self.tab2, "🧮 穿透核算与单品分析")

        self.setCentralWidget(self.tabs)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # 注入全局样式表
    app.setStyleSheet(MODERN_STYLE)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())