from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QTabWidget, QFileDialog
)
from datetime import datetime
import pandas as pd

from db import Database
from calculator import BomCalculator


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.db = Database()
        self.calculator = BomCalculator(self.db)

        self.setWindowTitle("BOM穿透核算工具")
        self.resize(900, 600)

        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()

        self.tabs.addTab(self.tab1, "配方维护")
        self.tabs.addTab(self.tab2, "穿透计算")

        self.init_tab1()
        self.init_tab2()

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    # =====================
    # Tab1 配方维护
    # =====================
    def init_tab1(self):
        layout = QVBoxLayout()

        form = QHBoxLayout()
        self.parent_input = QLineEdit()
        self.child_input = QLineEdit()
        self.qty_input = QLineEdit()

        form.addWidget(QLabel("产品"))
        form.addWidget(self.parent_input)
        form.addWidget(QLabel("成分"))
        form.addWidget(self.child_input)
        form.addWidget(QLabel("用量"))
        form.addWidget(self.qty_input)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存/更新")
        del_btn = QPushButton("删除选中")

        save_btn.clicked.connect(self.save_recipe)
        del_btn.clicked.connect(self.delete_recipe)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(del_btn)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["产品", "成分", "用量"])

        layout.addLayout(form)
        layout.addLayout(btn_layout)
        layout.addWidget(self.table)

        self.tab1.setLayout(layout)
        self.refresh_table()

    def save_recipe(self):
        try:
            parent = self.parent_input.text().strip()
            child = self.child_input.text().strip()
            qty = float(self.qty_input.text())

            if not parent or not child:
                raise ValueError("输入不能为空")

            self.db.add_or_update(parent, child, qty)
            self.refresh_table()

        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))

    def delete_recipe(self):
        row = self.table.currentRow()
        if row < 0:
            return

        parent = self.table.item(row, 0).text()
        child = self.table.item(row, 1).text()

        self.db.delete(parent, child)
        self.refresh_table()

    def refresh_table(self):
        data = self.db.get_all()
        self.table.setRowCount(len(data))

        for i, row in enumerate(data):
            for j, val in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(val)))

    # =====================
    # Tab2 计算
    # =====================
    def init_tab2(self):
        layout = QVBoxLayout()

        top = QHBoxLayout()
        self.calc_item = QLineEdit()
        self.calc_qty = QLineEdit()

        run_btn = QPushButton("执行计算")
        run_btn.clicked.connect(self.run_calc)

        top.addWidget(QLabel("产品"))
        top.addWidget(self.calc_item)
        top.addWidget(QLabel("数量(kg)"))
        top.addWidget(self.calc_qty)
        top.addWidget(run_btn)

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(2)
        self.result_table.setHorizontalHeaderLabels(["原料", "总用量(kg)"])

        export_btn = QPushButton("导出Excel")
        export_btn.clicked.connect(self.export_excel)

        layout.addLayout(top)
        layout.addWidget(self.result_table)
        layout.addWidget(export_btn)

        self.tab2.setLayout(layout)

    def run_calc(self):
        try:
            item = self.calc_item.text().strip()
            qty = float(self.calc_qty.text())

            if not item:
                raise ValueError("请输入产品名称")

            result = self.calculator.explode(item, qty)

            self.result_table.setRowCount(len(result))

            for i, (k, v) in enumerate(result.items()):
                self.result_table.setItem(i, 0, QTableWidgetItem(k))
                self.result_table.setItem(i, 1, QTableWidgetItem(f"{v:.2f}"))

        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))

    def export_excel(self):
        try:
            rows = self.result_table.rowCount()
            data = []

            for i in range(rows):
                name = self.result_table.item(i, 0).text()
                qty = float(self.result_table.item(i, 1).text())
                data.append([name, qty])

            df = pd.DataFrame(data, columns=["原料", "总用量(kg)"])

            filename = f"bom结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            path, _ = QFileDialog.getSaveFileName(self, "保存文件", filename, "Excel (*.xlsx)")

            if path:
                df.to_excel(path, index=False)

        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))