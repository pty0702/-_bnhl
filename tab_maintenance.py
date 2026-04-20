# tab_maintenance.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QHeaderView, QAbstractItemView)
from PyQt5.QtCore import Qt, QTimer  # 关键新增：QTimer 用于防止闪退
import database
from recipe_dialog import RecipeDetailDialog


class TabMaintenance(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_all_data()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # --- 1. 批量录入区 ---
        batch_group_layout = QVBoxLayout()

        parent_head_layout = QHBoxLayout()
        self.input_parent = QLineEdit()
        self.input_parent.setPlaceholderText("请输入成品/半成品名称（配方主件）")
        self.input_parent.setStyleSheet("font-weight: bold; height: 30px; border: 1px solid #ccc;")

        parent_head_layout.addWidget(QLabel("当前录入主件:"))
        parent_head_layout.addWidget(self.input_parent)
        parent_head_layout.addStretch()

        self.input_table = QTableWidget()
        self.input_table.setColumnCount(2)
        self.input_table.setRowCount(5)
        self.input_table.setHorizontalHeaderLabels(["组成成分名称 (子件)", "单耗 (kg/吨)"])
        self.input_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.input_table.setFixedHeight(180)

        batch_btn_layout = QHBoxLayout()
        self.btn_add_row = QPushButton("+ 增加一行")
        self.btn_add_row.clicked.connect(lambda: self.input_table.insertRow(self.input_table.rowCount()))

        self.btn_batch_save = QPushButton("💾 批量保存/更新配方")
        self.btn_batch_save.setStyleSheet("""
            QPushButton { background-color: #2ecc71; color: white; font-weight: bold; padding: 6px 15px; border-radius: 4px; }
            QPushButton:hover { background-color: #27ae60; }
        """)
        self.btn_batch_save.clicked.connect(self.save_batch_recipes)

        batch_btn_layout.addWidget(self.btn_add_row)
        batch_btn_layout.addStretch()
        batch_btn_layout.addWidget(self.btn_batch_save)

        batch_group_layout.addLayout(parent_head_layout)
        batch_group_layout.addWidget(self.input_table)
        batch_group_layout.addLayout(batch_btn_layout)

        # --- 2. 数据库全量展示区（合并展示） ---
        display_group_layout = QVBoxLayout()
        hint_label = QLabel("--- 产品配方目录 (双击所在行查看/修改配方详情) ---")
        hint_label.setStyleSheet("color: #2980b9; font-weight: bold; margin-top: 10px;")
        display_group_layout.addWidget(hint_label)

        self.all_table = QTableWidget()
        self.all_table.setColumnCount(3)
        # 变更为只显示父件和统计信息
        self.all_table.setHorizontalHeaderLabels(["产品名称 (配方主件)", "包含原材料项数", "操作提示"])
        self.all_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.all_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.all_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # 绑定双击事件
        self.all_table.itemDoubleClicked.connect(self.handle_double_click)

        # 删除按钮（现在是一键删除整个产品的配方）
        del_btn_layout = QHBoxLayout()
        self.btn_delete = QPushButton("🗑️ 删除选中产品的【全部配方】")
        self.btn_delete.setStyleSheet("color: #c0392b;")
        self.btn_delete.clicked.connect(self.delete_whole_recipe)
        del_btn_layout.addStretch()
        del_btn_layout.addWidget(self.btn_delete)

        display_group_layout.addWidget(self.all_table)
        display_group_layout.addLayout(del_btn_layout)

        main_layout.addLayout(batch_group_layout, stretch=1)
        main_layout.addSpacing(10)
        main_layout.addLayout(display_group_layout, stretch=2)

        self.setLayout(main_layout)

    def load_all_data(self):
        """刷新主表格，使用去重后的汇总数据"""
        self.all_table.setRowCount(0)
        try:
            # 调用我们在 database.py 中新增的函数
            data = database.get_parent_summaries()
            for row_idx, (parent, count) in enumerate(data):
                self.all_table.insertRow(row_idx)

                # 第一列：产品名
                item_name = QTableWidgetItem(parent)
                item_name.setForeground(Qt.blue)
                # 第二列：数量统计
                item_count = QTableWidgetItem(f"{count} 项物料")
                item_count.setTextAlignment(Qt.AlignCenter)
                # 第三列：提示文字
                item_hint = QTableWidgetItem("🔍 双击展开详情")
                item_hint.setForeground(Qt.gray)
                item_hint.setTextAlignment(Qt.AlignCenter)

                self.all_table.setItem(row_idx, 0, item_name)
                self.all_table.setItem(row_idx, 1, item_count)
                self.all_table.setItem(row_idx, 2, item_hint)
        except Exception as e:
            print(f"加载数据失败: {e}")

    def save_batch_recipes(self):
        parent = self.input_parent.text().strip()
        if not parent:
            QMessageBox.warning(self, "输入错误", "请先输入'主件名称'！")
            return

        saved_count = 0
        try:
            for row in range(self.input_table.rowCount()):
                child_item = self.input_table.item(row, 0)
                qty_item = self.input_table.item(row, 1)

                if child_item and qty_item:
                    child = child_item.text().strip()
                    qty_str = qty_item.text().strip()

                    if child and qty_str:
                        qty = float(qty_str)
                        if qty < 0: continue
                        database.add_recipe(parent, child, qty)
                        saved_count += 1

            if saved_count > 0:
                QMessageBox.information(self, "成功", f"已成功保存 '{parent}' 的 {saved_count} 条配方！")
                self.load_all_data()
                self.input_table.clearContents()
            else:
                QMessageBox.warning(self, "提示", "未检测到有效的子件信息。")
        except ValueError:
            QMessageBox.warning(self, "输入错误", "单耗必须是数字！")
        except Exception as e:
            QMessageBox.critical(self, "数据库错误", str(e))

    def handle_double_click(self, item):
        """处理双击：通过 QTimer 异步打开弹窗，彻底解决 0xC0000409 崩溃"""
        if not item: return
        row = item.row()
        parent_name = self.all_table.item(row, 0).text()

        # 【核心修复】：延迟 10 毫秒执行，切断 C++ 调用栈，防止缓冲区溢出
        QTimer.singleShot(10, lambda: self.open_recipe_dialog(parent_name))

    def open_recipe_dialog(self, parent_name):
        """实际打开弹窗的方法"""
        dialog = RecipeDetailDialog(parent_name, self)
        dialog.exec_()

    def delete_whole_recipe(self):
        """物理删除选中的产品的【所有】配方记录"""
        selected_rows = self.all_table.selectedItems()
        if not selected_rows:
            QMessageBox.information(self, "提示", "请先选中表格中的某一个产品！")
            return

        row = selected_rows[0].row()
        parent = self.all_table.item(row, 0).text()

        reply = QMessageBox.question(self, "严重警告",
                                     f"确定要彻底删除【{parent}】的所有配方组成吗？\n此操作不可恢复！",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # 调用我们在 database.py 中新增的批量删除函数
            database.delete_all_by_parent(parent)
            self.load_all_data()