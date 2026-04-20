# tab_maintenance.py (核心修复，请全部替换)
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QHeaderView, QAbstractItemView, QApplication)
from PyQt5.QtCore import Qt
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
        self.input_parent.setPlaceholderText("请输入要创建/修改的产品名称（主件）")
        self.input_parent.setStyleSheet("font-weight: bold; height: 30px;")

        parent_head_layout.addWidget(QLabel("主件产品:"))
        parent_head_layout.addWidget(self.input_parent)
        parent_head_layout.addStretch()

        self.input_table = QTableWidget()
        self.input_table.setColumnCount(2)
        self.input_table.setRowCount(5)
        self.input_table.setHorizontalHeaderLabels(["组成成分(子件)", "单耗(kg/吨)"])
        self.input_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.input_table.setFixedHeight(180)

        batch_btn_layout = QHBoxLayout()
        self.btn_add_row = QPushButton("+ 增加一行")
        self.btn_add_row.clicked.connect(lambda: self.input_table.insertRow(self.input_table.rowCount()))

        self.btn_batch_save = QPushButton("💾 批量保存配方")
        self.btn_batch_save.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; padding: 6px;")
        self.btn_batch_save.clicked.connect(self.save_batch_recipes)

        batch_btn_layout.addWidget(self.btn_add_row)
        batch_btn_layout.addStretch()
        batch_btn_layout.addWidget(self.btn_batch_save)

        batch_group_layout.addLayout(parent_head_layout)
        batch_group_layout.addWidget(self.input_table)
        batch_group_layout.addLayout(batch_btn_layout)

        # --- 2. 目录展示区 ---
        display_group_layout = QVBoxLayout()

        hint_layout = QHBoxLayout()
        hint_label = QLabel("--- 配方库目录 (点击右侧按钮查看明细，需要复制文字请使用 Ctrl+C) ---")
        hint_label.setStyleSheet("color: #2980b9; font-weight: bold;")

        self.btn_refresh = QPushButton("🔄 手动刷新列表")
        self.btn_refresh.clicked.connect(self.load_all_data)

        hint_layout.addWidget(hint_label)
        hint_layout.addStretch()
        hint_layout.addWidget(self.btn_refresh)

        display_group_layout.addLayout(hint_layout)

        self.all_table = QTableWidget()
        self.all_table.setColumnCount(3)
        self.all_table.setHorizontalHeaderLabels(["产品名称", "材料项数", "操作"])
        self.all_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.all_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.all_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        del_btn_layout = QHBoxLayout()
        self.btn_delete = QPushButton("🗑️ 彻底删除选中产品的所有配方")
        self.btn_delete.setStyleSheet("color: #c0392b; padding: 5px;")
        self.btn_delete.clicked.connect(self.delete_whole_recipe)
        del_btn_layout.addStretch()
        del_btn_layout.addWidget(self.btn_delete)

        display_group_layout.addWidget(self.all_table)
        display_group_layout.addLayout(del_btn_layout)

        main_layout.addLayout(batch_group_layout, stretch=1)
        main_layout.addLayout(display_group_layout, stretch=2)
        self.setLayout(main_layout)

    def load_all_data(self):
        self.all_table.setRowCount(0)
        try:
            data = database.get_parent_summaries()
            for row_idx, (parent, count) in enumerate(data):
                self.all_table.insertRow(row_idx)

                item_name = QTableWidgetItem(parent)
                item_name.setTextAlignment(Qt.AlignVCenter)
                self.all_table.setItem(row_idx, 0, item_name)

                item_count = QTableWidgetItem(f"{count} 个物料")
                item_count.setTextAlignment(Qt.AlignCenter)
                self.all_table.setItem(row_idx, 1, item_count)

                btn_view = QPushButton("📝 查看 / 修改")
                btn_view.setStyleSheet("""
                    QPushButton { background-color: #3498db; color: white; border-radius: 3px; padding: 4px; margin: 2px 20px;}
                    QPushButton:hover { background-color: #2980b9; }
                """)
                btn_view.clicked.connect(lambda checked, p=parent: self.open_dialog(p))

                self.all_table.setCellWidget(row_idx, 2, btn_view)

        except Exception as e:
            print("加载失败:", e)

    def save_batch_recipes(self):
        parent = self.input_parent.text().strip()
        if not parent: return QMessageBox.warning(self, "错误", "请输入主件名称")
        try:
            for row in range(self.input_table.rowCount()):
                ch_it, qty_it = self.input_table.item(row, 0), self.input_table.item(row, 1)
                if ch_it and qty_it and ch_it.text().strip() and qty_it.text().strip():
                    database.add_recipe(parent, ch_it.text().strip(), float(qty_it.text().strip()))
            self.load_all_data()
            self.input_table.clearContents()
        except ValueError:
            QMessageBox.warning(self, "错误", "单耗必须是数字！")

    # 【修复】：最核心的修改在这里！
    def open_dialog(self, parent_name):
        dialog = RecipeDetailDialog(parent_name)
        # exec_() 是阻塞的，程序会停在这里，直到你把弹窗关闭 (点击右上角 X)
        dialog.exec_()

        # 只有当你【关闭了弹窗】之后，代码才会继续往下走。
        # 此时按钮点击事件已经安全结束，可以放心大胆地刷新整个表格！
        self.load_all_data()

    def delete_whole_recipe(self):
        items = self.all_table.selectedItems()
        if not items: return
        parent = self.all_table.item(items[0].row(), 0).text()
        if QMessageBox.Yes == QMessageBox.question(self, "警告", f"删除【{parent}】的所有配方？"):
            database.delete_all_by_parent(parent)
            self.load_all_data()