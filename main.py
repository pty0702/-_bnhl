# main.py
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget
import database
from tab_maintenance import TabMaintenance
from tab_calculation import TabCalculation


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("多级配方(BOM)穿透核算工具 - 单机版")
        self.resize(800, 600)

        # 初始化数据库
        database.init_db()

        # 设置多标签页
        self.tabs = QTabWidget()

        self.tab1 = TabMaintenance()
        self.tab2 = TabCalculation()

        self.tabs.addTab(self.tab1, "配方基础数据维护")
        self.tabs.addTab(self.tab2, "穿透计算与报表导出")

        # 每次切换到Tab2时，可选：可以在此连接信号刷新数据，但目前逻辑已通过直接查库解耦

        self.setCentralWidget(self.tabs)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # 全局字体稍微放大一点，提升专业软件质感
    font = app.font()
    font.setPointSize(10)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())