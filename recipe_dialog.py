# recipe_dialog.py
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QPushButton, QTabWidget, QLabel,
                             QMessageBox, QHeaderView, QWidget, QApplication)
from PyQt5.QtCore import Qt
import database
import bom_logic


class RecipeDetailDialog(QDialog):
    def __init__(self, parent_name, parent_window=None):
        # 【防闪退核心】：传入 None 切断父子窗口连带销毁，确保内存安全
        super().__init__(None)

        self.parent_name = parent_name
        self.main_window = parent_window
        self.setWindowTitle(f"配方详情管理 - {parent_name}")
        self.resize(750, 550)  # 适当调整弹窗大小
        self.init_ui()
        self.load_direct_recipe()
        self.load_exploded_recipe()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        header_layout = QHBoxLayout()
        header = QLabel(f"📄 产品名称：{self.parent_name}")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(header)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        self.tabs = QTabWidget()

        self.tab_direct = QWidget()
        direct_layout = QVBoxLayout()
        direct_layout.setContentsMargins(10, 15, 10, 10)

        self.table_direct = QTableWidget()
        self.table_direct.setColumnCount(3)
        self.table_direct.setHorizontalHeaderLabels(["组成成分 (子件)", "单耗 (kg/吨)", "操作"])

        # 【核心修改】：固定弹窗内的操作列宽度
        header_d = self.table_direct.horizontalHeader()
        header_d.setSectionResizeMode(0, QHeaderView.Stretch)
        header_d.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header_d.setSectionResizeMode(2, QHeaderView.Fixed)
        self.table_direct.setColumnWidth(2, 80)  # 删除按钮小，80px足够

        self.table_direct.setAlternatingRowColors(True)
        btn_save_all = QPushButton("💾 保存所有单耗修改")
        btn_save_all.setStyleSheet(
            "background-color: #3498db; color: white; padding: 10px; font-weight: bold; border-radius: 5px;")
        btn_save_all.clicked.connect(self.save_modifications)
        direct_layout.addWidget(self.table_direct)
        direct_layout.addWidget(btn_save_all)
        self.tab_direct.setLayout(direct_layout)

        # Tab 2 穿透拆解部分保持现状...
        self.tab_exploded = QWidget()
        exploded_layout = QVBoxLayout()
        self.table_exploded = QTableWidget()
        self.table_exploded.setColumnCount(2)
        self.table_exploded.setHorizontalHeaderLabels(["最底层原始原材料", "总需求量 (kg)"])
        self.table_exploded.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_exploded.setEditTriggers(QAbstractItemView.NoEditTriggers)
        exploded_layout.addWidget(self.table_exploded)
        self.tab_exploded.setLayout(exploded_layout)

        self.tabs.addTab(self.tab_direct, "1. 原始配方组成")
        self.tabs.addTab(self.tab_exploded, "2. 穿透拆解对比")
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def load_direct_recipe(self):
        data = database.get_recipe_by_parent(self.parent_name)
        self.table_direct.setRowCount(len(data))

        for i, (child, qty) in enumerate(data):
            item_child = QTableWidgetItem(child)
            item_child.setFlags(item_child.flags() ^ Qt.ItemIsEditable)
            self.table_direct.setItem(i, 0, item_child)

            item_qty = QTableWidgetItem(str(qty))
            item_qty.setTextAlignment(Qt.AlignCenter)
            self.table_direct.setItem(i, 1, item_qty)

            # --- 删除按钮精致化 ---
            del_btn = QPushButton("删除")
            del_btn.setFixedSize(55, 22)  # 更紧凑的大小
            del_btn.setStyleSheet("""
                QPushButton { 
                    background-color: #e74c3c; color: white; border-radius: 11px; 
                    font-size: 8pt; border: none;
                }
                QPushButton:hover { background-color: #c0392b; }
            """)
            del_btn.clicked.connect(lambda _, ch=child: self.delete_item(ch))

            container = QWidget()
            h_layout = QHBoxLayout(container)
            h_layout.addWidget(del_btn)
            h_layout.setAlignment(Qt.AlignCenter)
            h_layout.setContentsMargins(0, 0, 0, 0)
            self.table_direct.setCellWidget(i, 2, container)

    def load_exploded_recipe(self):
        """执行穿透算法，刷新对比表"""
        try:
            # 以 1000kg 为基准进行穿透
            results = bom_logic.calculate_raw_materials(self.parent_name, 1000)
            self.table_exploded.setRowCount(len(results))
            for i, (mat, qty) in enumerate(sorted(results.items())):
                item_name = QTableWidgetItem(mat)
                item_qty = QTableWidgetItem(f"{qty:.4f}".rstrip('0').rstrip('.'))
                item_qty.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

                self.table_exploded.setItem(i, 0, item_name)
                self.table_exploded.setItem(i, 1, item_qty)
        except Exception:
            self.table_exploded.setRowCount(0)

    def save_modifications(self):
        """保存表格中对单耗数字的修改"""
        try:
            for i in range(self.table_direct.rowCount()):
                child = self.table_direct.item(i, 0).text()
                qty_text = self.table_direct.item(i, 1).text()
                qty = float(qty_text)
                if qty < 0: raise ValueError
                database.add_recipe(self.parent_name, child, qty)

            QMessageBox.information(self, "成功", "配方数据已更新，相关穿透结果已重算。")
            self.load_exploded_recipe()  # 刷新穿透结果
        except ValueError:
            QMessageBox.warning(self, "错误", "请在单耗列输入有效的正数！")

    def delete_item(self, child_name):
        """删除特定的配方组成行"""
        reply = QMessageBox.question(self, "确认删除",
                                     f"确定要从【{self.parent_name}】的配方中移除【{child_name}】吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            database.delete_recipe(self.parent_name, child_name)
            self.load_direct_recipe()  # 刷新当前列表
            self.load_exploded_recipe()  # 刷新穿透结果