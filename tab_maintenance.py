# tab_maintenance.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QHeaderView, QAbstractItemView, QApplication,
                             QComboBox, QCompleter, QToolTip, QGroupBox)
from PyQt5.QtCore import Qt, QStringListModel, QTimer
from PyQt5.QtGui import QCursor
import database
from recipe_dialog import RecipeDetailDialog
from export_dialog import ExportRecipeDialog


class TabMaintenance(QWidget):
    def __init__(self):
        super().__init__()
        self._current_dialog = None
        self._last_loaded_parent = None
        self.init_ui()
        self.load_all_data()
        self.update_completer()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 10, 15, 15)
        main_layout.setSpacing(10)

        # ==================== 1. 录入区 ====================
        group_input = QGroupBox("📥 新增 / 更新配方")
        batch_group_layout = QVBoxLayout()

        parent_head_layout = QHBoxLayout()
        self.input_parent = QComboBox()
        self.input_parent.setEditable(True)
        self.input_parent.setPlaceholderText("选择或输入主产品名称...")

        self.completer = QCompleter(self)
        self.completer.setFilterMode(Qt.MatchContains)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.input_parent.setCompleter(self.completer)

        self.completer.activated.connect(self.load_existing_recipe)
        self.input_parent.lineEdit().editingFinished.connect(self.check_and_load_recipe)

        parent_head_layout.addWidget(QLabel("主件产品名称:"))
        parent_head_layout.addWidget(self.input_parent, 1)

        hint_label = QLabel(
            "💡 提示：输入已有产品将自动载入现有配方。在此可直接修改单耗或追加新物料，保存即生效 (如需删除物料请到下方操作)。")
        hint_label.setStyleSheet("color: #7f8c8d; font-size: 9pt;")

        self.input_table = QTableWidget()
        self.input_table.setColumnCount(2)
        self.input_table.setRowCount(6)
        self.input_table.setHorizontalHeaderLabels(["组成成分(子件)", "单耗(kg/吨)"])
        self.input_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.input_table.setFixedHeight(235)

        batch_btn_layout = QHBoxLayout()
        self.btn_add_row = QPushButton("➕ 增加行")
        self.btn_add_row.clicked.connect(lambda: self.input_table.insertRow(self.input_table.rowCount()))

        self.btn_batch_save = QPushButton("💾 批量保存/更新配方")
        self.btn_batch_save.setStyleSheet("background-color: #27ae60; color: white;")
        self.btn_batch_save.clicked.connect(self.save_batch_recipes)

        batch_btn_layout.addWidget(self.btn_add_row)
        batch_btn_layout.addStretch()
        batch_btn_layout.addWidget(self.btn_batch_save)

        batch_group_layout.addLayout(parent_head_layout)
        batch_group_layout.addWidget(hint_label)
        batch_group_layout.addWidget(self.input_table)
        batch_group_layout.addLayout(batch_btn_layout)
        group_input.setLayout(batch_group_layout)

        # ==================== 2. 目录区 ====================
        group_display = QGroupBox("🗄️ 已录入配方库")
        display_group_layout = QVBoxLayout()

        toolbar_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 输入关键字搜索产品...")
        self.search_input.setFixedWidth(280)
        self.search_input.textChanged.connect(self.filter_table)

        self.btn_export_all = QPushButton("📤 批量导出 Excel")
        self.btn_export_all.setStyleSheet("background-color: #8e44ad; color: white;")
        self.btn_export_all.clicked.connect(self.open_export_dialog)

        toolbar_layout.addWidget(self.search_input)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.btn_export_all)

        self.all_table = QTableWidget()
        self.all_table.setColumnCount(3)
        self.all_table.setHorizontalHeaderLabels(["产品名称", "材料项数", "管理操作"])

        header = self.all_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        self.all_table.setColumnWidth(2, 110)

        self.all_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.all_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.all_table.setAlternatingRowColors(True)
        self.all_table.cellDoubleClicked.connect(self.handle_cell_double_click)

        # 【核心修复】：加回主界面的右下角删除按钮
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()  # 靠右对齐

        self.btn_delete_product = QPushButton("🗑️ 删除选中产品及配方")
        self.btn_delete_product.setCursor(Qt.PointingHandCursor)
        self.btn_delete_product.setStyleSheet("""
            QPushButton { 
                background-color: #e74c3c; color: white; padding: 8px 15px; 
                font-weight: bold; border-radius: 4px;
            }
            QPushButton:hover { background-color: #c0392b; }
        """)
        self.btn_delete_product.clicked.connect(self.delete_whole_recipe)
        bottom_layout.addWidget(self.btn_delete_product)

        display_group_layout.addLayout(toolbar_layout)
        display_group_layout.addWidget(self.all_table)
        display_group_layout.addLayout(bottom_layout)  # 把删除按钮放在表格的正下方
        group_display.setLayout(display_group_layout)

        main_layout.addWidget(group_input)
        main_layout.addWidget(group_display)
        self.setLayout(main_layout)

    def check_and_load_recipe(self):
        parent_name = self.input_parent.currentText().strip()
        self.load_existing_recipe(parent_name)

    def load_existing_recipe(self, parent_name):
        if not parent_name: return
        if getattr(self, '_last_loaded_parent', None) == parent_name: return

        data = database.get_recipe_by_parent(parent_name)
        if data:
            self.input_table.clearContents()
            self.input_table.setRowCount(max(6, len(data) + 2))

            for i, (child, qty) in enumerate(data):
                self.input_table.setItem(i, 0, QTableWidgetItem(child))
                self.input_table.setItem(i, 1, QTableWidgetItem(str(qty)))

            self._last_loaded_parent = parent_name
        else:
            self._last_loaded_parent = parent_name

    def load_all_data(self):
        self.all_table.setRowCount(0)
        try:
            data = database.get_parent_summaries()
            for row_idx, (parent, count) in enumerate(data):
                self.all_table.insertRow(row_idx)
                name_item = QTableWidgetItem(parent)
                name_item.setForeground(Qt.blue)
                self.all_table.setItem(row_idx, 0, name_item)
                self.all_table.setItem(row_idx, 1, QTableWidgetItem(f"{count} 项"))

                btn_view = QPushButton("查看/修改")
                btn_view.setFixedSize(85, 28)
                btn_view.setCursor(Qt.PointingHandCursor)
                btn_view.setStyleSheet("""
                    QPushButton { 
                        background-color: #3498db; color: white; 
                        border-radius: 14px; font-size: 9pt; border: none; padding-bottom: 2px;
                    }
                    QPushButton:hover { background-color: #2980b9; }
                """)

                btn_view.clicked.connect(lambda checked, p=parent: QTimer.singleShot(10, lambda: self.open_dialog(p)))

                container = QWidget()
                h_layout = QHBoxLayout(container)
                h_layout.addWidget(btn_view)
                h_layout.setAlignment(Qt.AlignCenter)
                h_layout.setContentsMargins(0, 0, 0, 0)
                self.all_table.setCellWidget(row_idx, 2, container)
        except Exception as e:
            print(f"加载失败: {e}")

    def update_completer(self):
        try:
            all_parents = database.get_unique_parents()
            self.input_parent.clear()
            self.input_parent.addItems(all_parents)
            self.input_parent.setCurrentText("")
            model = QStringListModel(all_parents)
            self.completer.setModel(model)
        except:
            pass

    def filter_table(self, text):
        for i in range(self.all_table.rowCount()):
            item = self.all_table.item(i, 0)
            if item: self.all_table.setRowHidden(i, text.lower() not in item.text().lower())

    def save_batch_recipes(self):
        parent = self.input_parent.currentText().strip()
        if not parent: return QMessageBox.warning(self, "提示", "请输入主件名称")
        try:
            saved = 0
            for row in range(self.input_table.rowCount()):
                ch = self.input_table.item(row, 0)
                qt = self.input_table.item(row, 1)
                if ch and qt and ch.text().strip() and qt.text().strip():
                    database.add_recipe(parent, ch.text().strip(), float(qt.text().strip()))
                    saved += 1
            if saved > 0:
                self.load_all_data()
                self.update_completer()
                self.input_table.clearContents()
                self._last_loaded_parent = None
                QMessageBox.information(self, "成功", f"【{parent}】配方已保存")
        except:
            QMessageBox.warning(self, "错误", "数据格式有误")

    def open_dialog(self, parent_name):
        self._current_dialog = RecipeDetailDialog(parent_name)
        self._current_dialog.exec_()
        self.load_all_data()
        self.update_completer()

    def open_export_dialog(self):
        ExportRecipeDialog(self).exec_()

    def handle_cell_double_click(self, row, column):
        if column == 0:
            text = self.all_table.item(row, 0).text()
            QApplication.clipboard().setText(text)
            QToolTip.showText(QCursor.pos(), f"已复制: {text}")

    def delete_whole_recipe(self):
        """【修复】：确保必须先选中表格中的某一行才能删除"""
        items = self.all_table.selectedItems()
        if not items:
            QMessageBox.information(self, "提示", "请先在上方表格中选中某一个产品。")
            return

        parent = self.all_table.item(items[0].row(), 0).text()
        if QMessageBox.Yes == QMessageBox.question(self, "危险警告",
                                                   f"确认彻底删除【{parent}】及其所有配方？\n此操作不可恢复！",
                                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No):
            database.delete_all_by_parent(parent)
            self.load_all_data()
            self.update_completer()
            # 删除后清空顶部缓存，防止串台
            self._last_loaded_parent = None