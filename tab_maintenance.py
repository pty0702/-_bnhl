# tab_maintenance.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QHeaderView, QAbstractItemView, QApplication,
                             QComboBox, QCompleter, QToolTip, QGroupBox)
from PyQt5.QtCore import Qt, QStringListModel
from PyQt5.QtGui import QCursor
import database
from recipe_dialog import RecipeDetailDialog
from export_dialog import ExportRecipeDialog  # 导入新写的导出弹窗


class TabMaintenance(QWidget):
    def __init__(self):
        super().__init__()
        self._current_dialog = None
        self.init_ui()
        self.load_all_data()
        self.update_completer()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)  # 增加模块间距，呼吸感更好

        # ==================== 区域 1：批量录入区 ====================
        group_input = QGroupBox("📥 新增 / 更新配方")
        batch_group_layout = QVBoxLayout()

        parent_head_layout = QHBoxLayout()
        self.input_parent = QComboBox()
        self.input_parent.setEditable(True)
        self.input_parent.setPlaceholderText("搜索已有产品或输入新产品名...")
        self.input_parent.lineEdit().setStyleSheet("font-weight: bold; height: 32px; font-size: 11pt;")

        self.completer = QCompleter(self)
        self.completer.setFilterMode(Qt.MatchContains)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.input_parent.setCompleter(self.completer)

        parent_head_layout.addWidget(QLabel("主件产品名称:"))
        parent_head_layout.addWidget(self.input_parent, 1)

        self.input_table = QTableWidget()
        self.input_table.setColumnCount(2)
        self.input_table.setRowCount(5)
        self.input_table.setHorizontalHeaderLabels(["组成成分(子件)", "单耗(kg/吨)"])
        self.input_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.input_table.setFixedHeight(180)

        batch_btn_layout = QHBoxLayout()
        self.btn_add_row = QPushButton("➕ 增加一行")
        self.btn_add_row.clicked.connect(lambda: self.input_table.insertRow(self.input_table.rowCount()))

        self.btn_batch_save = QPushButton("💾 批量保存配方")
        self.btn_batch_save.setStyleSheet("background-color: #27ae60; color: white;")
        self.btn_batch_save.clicked.connect(self.save_batch_recipes)

        batch_btn_layout.addWidget(self.btn_add_row)
        batch_btn_layout.addStretch()
        batch_btn_layout.addWidget(self.btn_batch_save)

        batch_group_layout.addLayout(parent_head_layout)
        batch_group_layout.addSpacing(10)
        batch_group_layout.addWidget(self.input_table)
        batch_group_layout.addLayout(batch_btn_layout)
        group_input.setLayout(batch_group_layout)

        # ==================== 区域 2：配方库目录区 ====================
        group_display = QGroupBox("🗄️ 配方库总览")
        display_group_layout = QVBoxLayout()

        # 顶部工具栏：搜索 + 导出 + 刷新
        toolbar_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 输入关键字实时筛选下方列表...")
        self.search_input.setFixedWidth(300)
        self.search_input.textChanged.connect(self.filter_table)

        self.btn_export_all = QPushButton("📤 导出配方到 Excel")
        self.btn_export_all.setStyleSheet("background-color: #8e44ad; color: white;")
        self.btn_export_all.clicked.connect(self.open_export_dialog)

        self.btn_refresh = QPushButton("🔄 刷新")
        self.btn_refresh.clicked.connect(self.load_all_data)

        toolbar_layout.addWidget(self.search_input)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.btn_export_all)
        toolbar_layout.addWidget(self.btn_refresh)

        self.all_table = QTableWidget()
        self.all_table.setColumnCount(3)
        self.all_table.setHorizontalHeaderLabels(["产品名称 (双击复制)", "配方材料项数", "操作"])
        self.all_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.all_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.all_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.all_table.setAlternatingRowColors(True)  # 开启隔行变色
        self.all_table.cellDoubleClicked.connect(self.handle_cell_double_click)

        del_btn_layout = QHBoxLayout()
        self.btn_delete = QPushButton("🗑️ 彻底删除选中产品")
        self.btn_delete.setStyleSheet("background-color: #e74c3c; color: white;")
        self.btn_delete.clicked.connect(self.delete_whole_recipe)
        del_btn_layout.addStretch()
        del_btn_layout.addWidget(self.btn_delete)

        display_group_layout.addLayout(toolbar_layout)
        display_group_layout.addSpacing(10)
        display_group_layout.addWidget(self.all_table)
        display_group_layout.addLayout(del_btn_layout)
        group_display.setLayout(display_group_layout)

        # 组合到主界面
        main_layout.addWidget(group_input, 0)  # 0表示不拉伸
        main_layout.addWidget(group_display, 1)  # 1表示占据剩余拉伸空间
        self.setLayout(main_layout)

    def update_completer(self):
        try:
            all_parents = database.get_unique_parents()
            self.input_parent.clear()
            self.input_parent.addItems(all_parents)
            self.input_parent.setCurrentText("")
            model = QStringListModel(all_parents)
            self.completer.setModel(model)
        except Exception as e:
            print(f"更新补全列表失败: {e}")

    def filter_table(self, text):
        for i in range(self.all_table.rowCount()):
            item = self.all_table.item(i, 0)
            if item:
                self.all_table.setRowHidden(i, text.lower() not in item.text().lower())

    def load_all_data(self):
        self.all_table.setRowCount(0)
        try:
            data = database.get_parent_summaries()
            for row_idx, (parent, count) in enumerate(data):
                self.all_table.insertRow(row_idx)

                name_item = QTableWidgetItem(parent)
                name_item.setForeground(Qt.blue)
                self.all_table.setItem(row_idx, 0, name_item)

                count_item = QTableWidgetItem(f"{count} 项")
                count_item.setTextAlignment(Qt.AlignCenter)
                self.all_table.setItem(row_idx, 1, count_item)

                btn_view = QPushButton("📝 查看 / 修改")
                btn_view.setStyleSheet("background-color: #3498db; color: white; border-radius: 4px; max-width: 120px;")
                btn_view.clicked.connect(lambda checked, p=parent: self.open_dialog(p))

                # 让按钮居中显示更美观
                widget = QWidget()
                h_layout = QHBoxLayout(widget)
                h_layout.addWidget(btn_view)
                h_layout.setAlignment(Qt.AlignCenter)
                h_layout.setContentsMargins(0, 0, 0, 0)
                self.all_table.setCellWidget(row_idx, 2, widget)

        except Exception as e:
            print(f"数据加载失败: {e}")

    def handle_cell_double_click(self, row, column):
        if column == 0:
            item = self.all_table.item(row, 0)
            if item:
                text = item.text()
                QApplication.clipboard().setText(text)
                QToolTip.showText(QCursor.pos(), f"已复制: {text}")

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
                QMessageBox.information(self, "成功", f"【{parent}】配方已保存")
        except ValueError:
            QMessageBox.warning(self, "错误", "单耗请输入数字")

    def open_dialog(self, parent_name):
        self._current_dialog = RecipeDetailDialog(parent_name)
        self._current_dialog.exec_()
        self.load_all_data()
        self.update_completer()

    def open_export_dialog(self):
        """打开批量导出Excel弹窗"""
        dialog = ExportRecipeDialog(self)
        dialog.exec_()

    def delete_whole_recipe(self):
        items = self.all_table.selectedItems()
        if not items: return
        parent = self.all_table.item(items[0].row(), 0).text()
        if QMessageBox.Yes == QMessageBox.question(self, "警告", f"确认彻底删除【{parent}】的所有配方？"):
            database.delete_all_by_parent(parent)
            self.load_all_data()
            self.update_completer()