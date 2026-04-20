# tab_maintenance.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QHeaderView, QAbstractItemView, QApplication, QToolTip)
from PyQt5.QtCore import Qt
import database

from PyQt5.QtGui import QCursor
class TabMaintenance(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_all_data()  # 加载数据库已有配方

    def init_ui(self):
        main_layout = QVBoxLayout()

        # --- 1. 批量录入区（上方） ---
        batch_group_layout = QVBoxLayout()

        # 父件名称行
        parent_head_layout = QHBoxLayout()
        self.input_parent = QLineEdit()
        self.input_parent.setPlaceholderText("请输入成品/半成品名称（父件）")
        self.input_parent.setStyleSheet("font-weight: bold; height: 30px;")
        parent_head_layout.addWidget(QLabel("当前编辑父件:"))
        parent_head_layout.addWidget(self.input_parent)
        parent_head_layout.addStretch()

        # 批量输入表格（子件 + 单耗）
        self.input_table = QTableWidget()
        self.input_table.setColumnCount(2)
        self.input_table.setRowCount(5)  # 默认显示5行，不够可以加
        self.input_table.setHorizontalHeaderLabels(["组成成分名称 (子件)", "单耗 (kg/吨)"])
        self.input_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.input_table.setFixedHeight(180)  # 固定高度，不占用过多空间

        # 批量操作按钮
        batch_btn_layout = QHBoxLayout()
        self.btn_add_row = QPushButton("+ 增加一行")
        self.btn_add_row.clicked.connect(lambda: self.input_table.insertRow(self.input_table.rowCount()))

        self.btn_batch_save = QPushButton("💾 批量保存/更新当前配方")
        self.btn_batch_save.setStyleSheet(
            "background-color: #2ecc71; color: white; font-weight: bold; padding: 5px 15px;")
        self.btn_batch_save.clicked.connect(self.save_batch_recipes)

        batch_btn_layout.addWidget(self.btn_add_row)
        batch_btn_layout.addStretch()
        batch_btn_layout.addWidget(self.btn_batch_save)

        batch_group_layout.addLayout(parent_head_layout)
        batch_group_layout.addWidget(self.input_table)
        batch_group_layout.addLayout(batch_btn_layout)

        # --- 2. 数据库全量展示区（下方） ---
        display_group_layout = QVBoxLayout()
        display_group_layout.addWidget(QLabel("--- 数据库已有全部配方清单 (双击单元格复制) ---"))

        self.all_table = QTableWidget()
        self.all_table.setColumnCount(3)
        self.all_table.setHorizontalHeaderLabels(["父件名称", "子件名称", "单耗 (kg/吨)"])
        self.all_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.all_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.all_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.all_table.itemDoubleClicked.connect(self.copy_cell_text)  # 绑定双击复制

        # 删除按钮
        del_btn_layout = QHBoxLayout()
        self.btn_delete = QPushButton("🗑️ 删除选中配方")
        self.btn_delete.clicked.connect(self.delete_recipe)
        del_btn_layout.addStretch()
        del_btn_layout.addWidget(self.btn_delete)

        display_group_layout.addWidget(self.all_table)
        display_group_layout.addLayout(del_btn_layout)

        # 组合主布局
        main_layout.addLayout(batch_group_layout, stretch=1)
        main_layout.addSpacing(20)
        main_layout.addLayout(display_group_layout, stretch=2)

        self.setLayout(main_layout)

    def load_all_data(self):
        """刷新下方展示表格"""
        self.all_table.setRowCount(0)
        data = database.get_all_recipes()
        for row_idx, row_data in enumerate(data):
            self.all_table.insertRow(row_idx)
            for col_idx, value in enumerate(row_data):
                self.all_table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

    def save_batch_recipes(self):
        """批量保存逻辑"""
        parent = self.input_parent.text().strip()
        if not parent:
            QMessageBox.warning(self, "输入错误", "请先输入'父件名称'！")
            return

        saved_count = 0
        try:
            for row in range(self.input_table.rowCount()):
                child_item = self.input_table.item(row, 0)
                qty_item = self.input_table.item(row, 1)

                # 只有当这一行的子件和单耗都有内容时才处理
                if child_item and qty_item:
                    child = child_item.text().strip()
                    qty_str = qty_item.text().strip()

                    if child and qty_str:
                        qty = float(qty_str)
                        if qty <= 0:
                            continue  # 忽略无效数值

                        database.add_recipe(parent, child, qty)
                        saved_count += 1

            if saved_count > 0:
                QMessageBox.information(self, "成功", f"已成功保存/更新 {parent} 的 {saved_count} 条子件记录！")
                self.load_all_data()  # 刷新全表
                # 清空输入区以便下次录入
                self.input_table.clearContents()
            else:
                QMessageBox.warning(self, "提示", "未检测到有效的子件信息，请检查输入表格。")

        except ValueError:
            QMessageBox.warning(self, "输入错误", "单耗必须是数字！")
        except Exception as e:
            QMessageBox.critical(self, "数据库错误", str(e))

    def delete_recipe(self):
        selected_rows = self.all_table.selectedItems()
        if not selected_rows:
            QMessageBox.information(self, "提示", "请先选中要删除的行！")
            return

        row = selected_rows[0].row()
        parent = self.all_table.item(row, 0).text()
        child = self.all_table.item(row, 1).text()

        reply = QMessageBox.question(self, "确认删除",
                                     f"确定要删除配方: {parent} -> {child} 吗？",
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            database.delete_recipe(parent, child)
            self.load_all_data()

    def copy_cell_text(self, item):
        """双击单元格复制内容到剪贴板 - 健壮版"""
        if item:
            try:
                # 1. 获取剪贴板对象
                clipboard = QApplication.clipboard()
                text_to_copy = item.text()
                clipboard.setText(text_to_copy)

                # 2. 简单的气泡提示 (改用更稳定的 QCursor)
                # 之前崩溃可能是因为 QApplication.desktop() 在某些系统上返回了空对象
                QToolTip.showText(QCursor.pos(), f"已复制: {text_to_copy}", self)

                print(f"成功复制: {text_to_copy}")  # 控制台打印，方便调试
            except Exception as e:
                print(f"复制失败: {str(e)}")