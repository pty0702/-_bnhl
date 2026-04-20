# tab_maintenance.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QHeaderView, QAbstractItemView)
import database


class TabMaintenance(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout()

        # --- 表单录入区 ---
        form_layout = QHBoxLayout()

        self.input_parent = QLineEdit()
        self.input_parent.setPlaceholderText("成品/半成品名称")

        self.input_child = QLineEdit()
        self.input_child.setPlaceholderText("组成成分名称")

        self.input_qty = QLineEdit()
        self.input_qty.setPlaceholderText("单耗(kg)")

        self.btn_save = QPushButton("保存/更新配方")
        self.btn_save.clicked.connect(self.save_recipe)

        form_layout.addWidget(QLabel("父件:"))
        form_layout.addWidget(self.input_parent)
        form_layout.addWidget(QLabel("子件:"))
        form_layout.addWidget(self.input_child)
        form_layout.addWidget(QLabel("单耗:"))
        form_layout.addWidget(self.input_qty)
        form_layout.addWidget(self.btn_save)

        # --- 数据展示区 ---
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["父件名称", "子件名称", "单耗 (kg)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 禁止直接在表格修改

        # --- 操作区 ---
        btn_layout = QHBoxLayout()
        self.btn_delete = QPushButton("删除选中配方")
        self.btn_delete.clicked.connect(self.delete_recipe)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_delete)

        layout.addLayout(form_layout)
        layout.addWidget(self.table)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_data(self):
        self.table.setRowCount(0)
        data = database.get_all_recipes()
        for row_idx, row_data in enumerate(data):
            self.table.insertRow(row_idx)
            for col_idx, value in enumerate(row_data):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

    def save_recipe(self):
        parent = self.input_parent.text().strip()
        child = self.input_child.text().strip()
        qty_str = self.input_qty.text().strip()

        if not parent or not child or not qty_str:
            QMessageBox.warning(self, "输入错误", "请将父件、子件和单耗填写完整！")
            return

        try:
            qty = float(qty_str)
            if qty <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "输入错误", "单耗必须为大于0的有效数字！")
            return

        try:
            database.add_recipe(parent, child, qty)
            self.load_data()
            self.input_child.clear()
            self.input_qty.clear()
            self.input_parent.setFocus()
        except Exception as e:
            QMessageBox.critical(self, "数据库错误", str(e))

    def delete_recipe(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            QMessageBox.information(self, "提示", "请先选中要删除的行！")
            return

        row = selected_rows[0].row()
        parent = self.table.item(row, 0).text()
        child = self.table.item(row, 1).text()

        reply = QMessageBox.question(self, "确认删除",
                                     f"确定要删除配方: {parent} -> {child} 吗？",
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            database.delete_recipe(parent, child)
            self.load_data()