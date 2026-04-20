# recipe_dialog.py
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QPushButton, QTabWidget, QLabel, QMessageBox, QHeaderView)
import database
import bom_logic


class RecipeDetailDialog(QDialog):
    def __init__(self, parent_name, main_window):
        super().__init__()
        self.parent_name = parent_name
        self.main_window = main_window  # 用于刷新主表
        self.setWindowTitle(f"配方详情：{parent_name} (基准：1吨)")
        self.resize(700, 500)
        self.init_ui()
        self.load_direct_recipe()
        self.load_exploded_recipe()

    def init_ui(self):
        layout = QVBoxLayout()

        header = QLabel(f"产品名称：{self.parent_name}")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header)

        self.tabs = QTabWidget()

        # --- 标签页1：原始配方（可编辑） ---
        self.tab_direct = QWidget()
        direct_layout = QVBoxLayout()

        self.table_direct = QTableWidget()
        self.table_direct.setColumnCount(3)
        self.table_direct.setHorizontalHeaderLabels(["组成成分(子件)", "单耗(kg/吨)", "操作"])
        self.table_direct.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        btn_save_all = QPushButton("保存所有修改")
        btn_save_all.setStyleSheet("background-color: #3498db; color: white; padding: 8px;")
        btn_save_all.clicked.connect(self.save_modifications)

        direct_layout.addWidget(QLabel("提示：直接修改数值后点击保存，或点击删除按钮。"))
        direct_layout.addWidget(self.table_direct)
        direct_layout.addWidget(btn_save_all)
        self.tab_direct.setLayout(direct_layout)

        # --- 标签页2：穿透结果（只读） ---
        self.tab_exploded = QWidget()
        exploded_layout = QVBoxLayout()
        self.table_exploded = QTableWidget()
        self.table_exploded.setColumnCount(2)
        self.table_exploded.setHorizontalHeaderLabels(["最底层原材料", "总需求量(kg)"])
        self.table_exploded.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_exploded.setEditTriggers(QTableWidget.NoEditTriggers)

        exploded_layout.addWidget(QLabel("提示：这里显示的是穿透所有中间件后的最终原材料清单。"))
        exploded_layout.addWidget(self.table_exploded)
        self.tab_exploded.setLayout(exploded_layout)

        self.tabs.addTab(self.tab_direct, "1. 原始配方 (可修改)")
        self.tabs.addTab(self.tab_exploded, "2. 穿透全拆解 (只读对比)")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def load_direct_recipe(self):
        """加载直接子件数据"""
        data = database.get_recipe_by_parent(self.parent_name)
        self.table_direct.setRowCount(len(data))
        for i, (child, qty) in enumerate(data):
            self.table_direct.setItem(i, 0, QTableWidgetItem(child))
            self.table_direct.item(i, 0).setFlags(self.table_direct.item(i, 0).flags() ^ 1)  # 禁用子件名编辑
            self.table_direct.setItem(i, 1, QTableWidgetItem(str(qty)))

            # 删除按钮
            del_btn = QPushButton("删除")
            del_btn.setStyleSheet("background-color: #e74c3c; color: white; max-width: 60px;")
            del_btn.clicked.connect(lambda ch=child: self.delete_item(ch))
            self.table_direct.setCellWidget(i, 2, del_btn)

    def load_exploded_recipe(self):
        """加载全拆解数据（基于1000kg）"""
        try:
            results = bom_logic.calculate_raw_materials(self.parent_name, 1000)
            self.table_exploded.setRowCount(len(results))
            for i, (mat, qty) in enumerate(sorted(results.items())):
                self.table_exploded.setItem(i, 0, QTableWidgetItem(mat))
                self.table_exploded.setItem(i, 1, QTableWidgetItem(f"{qty:.4f}".rstrip('0').rstrip('.')))
        except Exception:
            self.table_exploded.setRowCount(0)

    def save_modifications(self):
        """保存表格中修改过的单耗"""
        try:
            for i in range(self.table_direct.rowCount()):
                child = self.table_direct.item(i, 0).text()
                qty = float(self.table_direct.item(i, 1).text())
                database.add_recipe(self.parent_name, child, qty)
            QMessageBox.information(self, "成功", "配方已更新！")
            self.load_exploded_recipe()  # 刷新拆解视图
            self.main_window.load_all_data()  # 刷新主界面
        except ValueError:
            QMessageBox.warning(self, "错误", "请输入有效的数字单耗！")

    def delete_item(self, child_name):
        reply = QMessageBox.question(self, "确认", f"确定从配方中移除 {child_name} 吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            database.delete_recipe(self.parent_name, child_name)
            self.load_direct_recipe()
            self.load_exploded_recipe()
            self.main_window.load_all_data()