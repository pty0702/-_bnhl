# recipe_dialog.py
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QPushButton, QTabWidget, QLabel,
                             QMessageBox, QHeaderView, QWidget, QApplication)
from PyQt5.QtCore import Qt, QTimer
import database
import bom_logic


class RecipeDetailDialog(QDialog):
    def __init__(self, parent_name, parent_window=None):
        super().__init__(None)

        self.parent_name = parent_name
        self.main_window = parent_window
        self.setWindowTitle(f"配方详情管理 - {parent_name}")
        self.resize(750, 550)
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

        hint_label = QLabel("💡 提示：双击“单耗”数字可直接修改，点击【新增物料】可追加配方，最后统一保存。")
        hint_label.setStyleSheet("color: #7f8c8d; font-size: 9pt; margin-bottom: 5px;")

        self.table_direct = QTableWidget()
        self.table_direct.setColumnCount(3)
        self.table_direct.setHorizontalHeaderLabels(["组成成分 (子件)", "单耗 (kg/吨)", "操作"])

        header_d = self.table_direct.horizontalHeader()
        header_d.setSectionResizeMode(0, QHeaderView.Stretch)
        header_d.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header_d.setSectionResizeMode(2, QHeaderView.Fixed)
        self.table_direct.setColumnWidth(2, 80)
        self.table_direct.setAlternatingRowColors(True)

        btn_layout = QHBoxLayout()

        self.btn_add_row = QPushButton("➕ 增加新物料")
        self.btn_add_row.setCursor(Qt.PointingHandCursor)
        self.btn_add_row.setStyleSheet("""
            QPushButton { 
                background-color: #f39c12; color: white; padding: 10px 20px; 
                font-weight: bold; border-radius: 5px; font-size: 10pt;
            }
            QPushButton:hover { background-color: #e67e22; }
        """)
        self.btn_add_row.clicked.connect(self.add_empty_row)

        self.btn_save_all = QPushButton("💾 保存配方修改")
        self.btn_save_all.setCursor(Qt.PointingHandCursor)
        self.btn_save_all.setStyleSheet("""
            QPushButton { 
                background-color: #3498db; color: white; padding: 10px 30px; 
                font-weight: bold; border-radius: 5px; font-size: 10pt;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        self.btn_save_all.clicked.connect(self.save_modifications)

        btn_layout.addWidget(self.btn_add_row)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save_all)

        direct_layout.addWidget(hint_label)
        direct_layout.addWidget(self.table_direct)
        direct_layout.addSpacing(10)
        direct_layout.addLayout(btn_layout)
        self.tab_direct.setLayout(direct_layout)

        self.tab_exploded = QWidget()
        exploded_layout = QVBoxLayout()
        exploded_layout.setContentsMargins(10, 15, 10, 10)

        self.table_exploded = QTableWidget()
        self.table_exploded.setColumnCount(2)
        self.table_exploded.setHorizontalHeaderLabels(["最底层原始原材料", "总需求量 (kg)"])
        self.table_exploded.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_exploded.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_exploded.setAlternatingRowColors(True)

        exploded_layout.addWidget(QLabel("📊 基于 1000kg (1吨) 产量的全拆解消耗明细："))
        exploded_layout.addWidget(self.table_exploded)
        self.tab_exploded.setLayout(exploded_layout)

        self.tabs.addTab(self.tab_direct, "1. 原始配方组成")
        self.tabs.addTab(self.tab_exploded, "2. 穿透拆解对比")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def create_delete_button(self):
        del_btn = QPushButton("删除")
        del_btn.setFixedSize(55, 22)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet("""
            QPushButton { 
                background-color: #e74c3c; color: white; border-radius: 11px; 
                font-size: 8pt; border: none;
            }
            QPushButton:hover { background-color: #c0392b; }
        """)
        del_btn.clicked.connect(
            lambda checked, btn=del_btn: QTimer.singleShot(10, lambda: self.remove_dynamic_row_safe(btn)))

        container = QWidget()
        h_layout = QHBoxLayout(container)
        h_layout.addWidget(del_btn)
        h_layout.setAlignment(Qt.AlignCenter)
        h_layout.setContentsMargins(0, 0, 0, 0)
        return container

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

            self.table_direct.setCellWidget(i, 2, self.create_delete_button())

    def add_empty_row(self):
        row_count = self.table_direct.rowCount()
        self.table_direct.insertRow(row_count)

        # 【修复闪退2】：删除了不存在的 setPlaceholderText，恢复正常新建格子逻辑
        item_name = QTableWidgetItem("")
        self.table_direct.setItem(row_count, 0, item_name)

        item_qty = QTableWidgetItem("")
        item_qty.setTextAlignment(Qt.AlignCenter)
        self.table_direct.setItem(row_count, 1, item_qty)

        self.table_direct.setCellWidget(row_count, 2, self.create_delete_button())

        self.table_direct.scrollToBottom()
        self.table_direct.setCurrentCell(row_count, 0)

    def remove_dynamic_row_safe(self, button):
        for row in range(self.table_direct.rowCount()):
            widget = self.table_direct.cellWidget(row, 2)
            if widget and widget.layout().indexOf(button) != -1:
                child_item = self.table_direct.item(row, 0)
                child_name = child_item.text().strip() if child_item else ""

                if child_name:
                    reply = QMessageBox.question(self, "确认删除",
                                                 f"确定要从【{self.parent_name}】中移除【{child_name}】吗？",
                                                 QMessageBox.Yes | QMessageBox.No)
                    if reply == QMessageBox.Yes:
                        database.delete_recipe(self.parent_name, child_name)
                        self.table_direct.removeRow(row)
                        self.load_exploded_recipe()
                else:
                    self.table_direct.removeRow(row)
                break

    def load_exploded_recipe(self):
        try:
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
        try:
            saved_count = 0
            for i in range(self.table_direct.rowCount()):
                child_item = self.table_direct.item(i, 0)
                qty_item = self.table_direct.item(i, 1)

                if not child_item or not qty_item: continue

                child = child_item.text().strip()
                qty_text = qty_item.text().strip()

                if not child or not qty_text: continue

                qty = float(qty_text)
                if qty < 0: raise ValueError

                database.add_recipe(self.parent_name, child, qty)
                saved_count += 1

            QMessageBox.information(self, "成功", f"配方已成功保存 (共包含 {saved_count} 项)！\n相关穿透结果已重算。")
            self.load_direct_recipe()
            self.load_exploded_recipe()
        except ValueError:
            QMessageBox.warning(self, "错误", "请确保所有单耗都输入了有效的正数！")