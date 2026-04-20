# tab_maintenance.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QHeaderView, QAbstractItemView, QApplication,
                             QComboBox, QCompleter, QMenu, QToolTip)
from PyQt5.QtCore import Qt, QStringListModel, QTimer
from PyQt5.QtGui import QCursor
import database
from recipe_dialog import RecipeDetailDialog


class TabMaintenance(QWidget):
    def __init__(self):
        super().__init__()
        self._current_dialog = None
        self.init_ui()
        self.load_all_data()
        self.update_completer()  # 初始化补全数据

    def init_ui(self):
        main_layout = QVBoxLayout()

        # --- 1. 录入区：带模糊搜索的下拉输入框 ---
        batch_group_layout = QVBoxLayout()
        parent_head_layout = QHBoxLayout()

        # 使用 QComboBox 并设置为可编辑，作为搜索/输入框
        self.input_parent = QComboBox()
        self.input_parent.setEditable(True)
        self.input_parent.setPlaceholderText("搜索已有产品或输入新产品名...")
        self.input_parent.lineEdit().setStyleSheet("font-weight: bold; height: 30px;")

        # 配置补全器
        self.completer = QCompleter(self)
        self.completer.setFilterMode(Qt.MatchContains)  # 模糊匹配
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.input_parent.setCompleter(self.completer)

        parent_head_layout.addWidget(QLabel("主件产品:"))
        parent_head_layout.addWidget(self.input_parent, 1)
        parent_head_layout.addStretch()

        # 子件录入表
        self.input_table = QTableWidget()
        self.input_table.setColumnCount(2)
        self.input_table.setRowCount(5)
        self.input_table.setHorizontalHeaderLabels(["组成成分(子件)", "单耗(kg/吨)"])
        self.input_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.input_table.setFixedHeight(150)

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

        # --- 2. 展示区：带关键字过滤功能 ---
        display_group_layout = QVBoxLayout()

        search_filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 输入关键字实时筛选下方列表...")
        self.search_input.textChanged.connect(self.filter_table)

        search_filter_layout.addWidget(self.search_input)

        self.all_table = QTableWidget()
        self.all_table.setColumnCount(3)
        self.all_table.setHorizontalHeaderLabels(["产品名称 (双击复制)", "材料项数", "操作"])
        self.all_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.all_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.all_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # 绑定双击复制功能
        self.all_table.cellDoubleClicked.connect(self.handle_cell_double_click)

        display_group_layout.addLayout(search_filter_layout)
        display_group_layout.addWidget(self.all_table)

        main_layout.addLayout(batch_group_layout, stretch=1)
        main_layout.addLayout(display_group_layout, stretch=2)
        self.setLayout(main_layout)

    def update_completer(self):
        """修复 AttributeError 的关键：重新实例化 Model 并设置给 Completer"""
        try:
            all_parents = database.get_unique_parents()
            # 更新下拉框列表
            self.input_parent.clear()
            self.input_parent.addItems(all_parents)
            self.input_parent.setCurrentText("")  # 初始清空

            # 更新补全器模型
            model = QStringListModel(all_parents)
            self.completer.setModel(model)
        except Exception as e:
            print(f"更新补全列表失败: {e}")

    def filter_table(self, text):
        """列表实时搜索过滤"""
        for i in range(self.all_table.rowCount()):
            item = self.all_table.item(i, 0)
            if item:
                self.all_table.setRowHidden(i, text.lower() not in item.text().lower())

    def load_all_data(self):
        """加载去重后的主产品列表"""
        self.all_table.setRowCount(0)
        try:
            data = database.get_parent_summaries()
            for row_idx, (parent, count) in enumerate(data):
                self.all_table.insertRow(row_idx)

                # 产品名称列
                name_item = QTableWidgetItem(parent)
                name_item.setForeground(Qt.blue)  # 蓝色提示可交互
                self.all_table.setItem(row_idx, 0, name_item)

                # 项数列
                self.all_table.setItem(row_idx, 1, QTableWidgetItem(f"{count} 项"))

                # 操作列：放置按钮
                btn_view = QPushButton("📝 查看 / 修改")
                btn_view.setStyleSheet("background-color: #3498db; color: white; border-radius: 3px;")
                # 使用 lambda 闭包锁定当前的 parent 值
                btn_view.clicked.connect(lambda checked, p=parent: self.open_dialog(p))
                self.all_table.setCellWidget(row_idx, 2, btn_view)
        except Exception as e:
            print(f"数据加载失败: {e}")

    def handle_cell_double_click(self, row, column):
        """双击第一列自动复制产品名 (绝对防崩溃版)"""
        if column == 0:
            item = self.all_table.item(row, 0)
            if item:
                text = item.text()
                QApplication.clipboard().setText(text)

                # 【修复核心】：去掉了所有复杂的参数，只保留“位置”和“文字”
                # 这是 Qt 官方最推荐、也是最不可能引起崩溃的调用方式
                QToolTip.showText(QCursor.pos(), f"已复制: {text}")

                # 顺便在控制台打印一下，方便确认
                print(f"成功复制到剪贴板: {text}")

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
                self.update_completer()  # 刷新搜索建议
                self.input_table.clearContents()
                QMessageBox.information(self, "成功", f"【{parent}】配方已保存")
        except ValueError:
            QMessageBox.warning(self, "错误", "单耗请输入数字")

    def open_dialog(self, parent_name):
        """点击按钮打开弹窗，且关闭后安全刷新"""
        self._current_dialog = RecipeDetailDialog(parent_name)
        self._current_dialog.exec_()
        self.load_all_data()  # 弹窗关闭后再刷新，绝对安全
        self.update_completer()