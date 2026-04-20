# recipe_dialog.py
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QPushButton, QTabWidget, QLabel, QMessageBox, QHeaderView, QWidget)
from PyQt5.QtCore import Qt
import database
import bom_logic


class RecipeDetailDialog(QDialog):
    # 【修复】：去掉了 parent_window 参数，彻底切断连带关系
    def __init__(self, parent_name):
        super().__init__(None)

        self.parent_name = parent_name
        self.setWindowTitle(f"配方明细：{parent_name} (基准：1吨)")
        self.resize(700, 500)
        self.init_ui()
        self.load_direct_recipe()
        self.load_exploded_recipe()

    def init_ui(self):
        layout = QVBoxLayout()
        header = QLabel(f"产品名称：{self.parent_name}")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 5px;")
        layout.addWidget(header)

        self.tabs = QTabWidget()

        self.tab_direct = QWidget()
        direct_layout = QVBoxLayout()
        self.table_direct = QTableWidget()
        self.table_direct.setColumnCount(3)
        self.table_direct.setHorizontalHeaderLabels(["组成成分", "单耗(kg/吨)", "操作"])
        self.table_direct.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        btn_save = QPushButton("💾 保存当前表格中的修改")
        btn_save.setStyleSheet("background-color: #3498db; color: white; padding: 8px; font-weight: bold;")
        btn_save.clicked.connect(self.save_modifications)

        direct_layout.addWidget(QLabel("提示：双击数字修改，然后点击保存。"))
        direct_layout.addWidget(self.table_direct)
        direct_layout.addWidget(btn_save)
        self.tab_direct.setLayout(direct_layout)

        self.tab_exploded = QWidget()
        exploded_layout = QVBoxLayout()
        self.table_exploded = QTableWidget()
        self.table_exploded.setColumnCount(2)
        self.table_exploded.setHorizontalHeaderLabels(["最底层原材料", "总消耗量(kg)"])
        self.table_exploded.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_exploded.setEditTriggers(QTableWidget.NoEditTriggers)

        exploded_layout.addWidget(QLabel("提示：基于生产 1吨(1000kg) 计算的最底层纯原料清单。"))
        exploded_layout.addWidget(self.table_exploded)
        self.tab_exploded.setLayout(exploded_layout)

        self.tabs.addTab(self.tab_direct, "1. 原始配方 (可修改/删除)")
        self.tabs.addTab(self.tab_exploded, "2. 穿透全拆解 (只读对比)")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def load_direct_recipe(self):
        data = database.get_recipe_by_parent(self.parent_name)
        self.table_direct.setRowCount(len(data))
        for i, (child, qty) in enumerate(data):
            item_child = QTableWidgetItem(child)
            item_child.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table_direct.setItem(i, 0, item_child)

            self.table_direct.setItem(i, 1, QTableWidgetItem(str(qty)))

            del_btn = QPushButton("删除")
            del_btn.setStyleSheet("background-color: #e74c3c; color: white;")
            del_btn.clicked.connect(lambda _, ch=child: self.delete_item(ch))
            self.table_direct.setCellWidget(i, 2, del_btn)

    def load_exploded_recipe(self):
        try:
            results = bom_logic.calculate_raw_materials(self.parent_name, 1000)
            self.table_exploded.setRowCount(len(results))
            for i, (mat, qty) in enumerate(sorted(results.items())):
                self.table_exploded.setItem(i, 0, QTableWidgetItem(mat))
                self.table_exploded.setItem(i, 1, QTableWidgetItem(f"{qty:.4f}"))
        except Exception as e:
            self.table_exploded.setRowCount(0)

    def save_modifications(self):
        try:
            for i in range(self.table_direct.rowCount()):
                child = self.table_direct.item(i, 0).text()
                qty = float(self.table_direct.item(i, 1).text())
                database.add_recipe(self.parent_name, child, qty)
            QMessageBox.information(self, "成功", "配方更新成功！")
            self.load_exploded_recipe()
            # 【修复】：删除了 self.main_window.load_all_data()
        except ValueError:
            QMessageBox.warning(self, "错误", "单耗必须是数字！")

    def delete_item(self, child_name):
        reply = QMessageBox.question(self, "确认", f"确定移除 {child_name} 吗？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            database.delete_recipe(self.parent_name, child_name)
            self.load_direct_recipe()
            self.load_exploded_recipe()
            # 【修复】：删除了 self.main_window.load_all_data()