# tab_calculation.py
import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QHeaderView, QAbstractItemView, QApplication,
                             QComboBox, QCompleter)
from PyQt5.QtCore import Qt, QStringListModel
import pandas as pd
import bom_logic
import database


class TabCalculation(QWidget):
    def __init__(self):
        super().__init__()
        self.current_results = {}
        self.init_ui()
        self.update_completer()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # --- 控制区 ---
        control_layout = QHBoxLayout()

        self.input_product = QComboBox()
        self.input_product.setEditable(True)
        self.input_product.setPlaceholderText("选择或搜索要计算的产品...")
        # 【Bug已修复】：删除了上一版这里的 setStyleSheet，让它乖乖继承 main.py 的全局无边框设定
        self.input_product.lineEdit().setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.completer = QCompleter(self)
        self.completer.setFilterMode(Qt.MatchContains)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.input_product.setCompleter(self.completer)

        self.input_target_qty = QLineEdit()
        self.input_target_qty.setText("1000")
        self.input_target_qty.setFixedWidth(100)

        self.btn_calc = QPushButton("⚙️ 执行穿透计算")
        self.btn_calc.setStyleSheet("background-color: #f39c12; color: white; font-weight: bold; padding: 6px 15px;")
        self.btn_calc.clicked.connect(self.run_calculation)

        control_layout.addWidget(QLabel("目标成品:"))
        control_layout.addWidget(self.input_product, 1)
        control_layout.addWidget(QLabel("计划产量(kg):"))
        control_layout.addWidget(self.input_target_qty)
        control_layout.addWidget(self.btn_calc)

        # --- 中间过滤区 ---
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 输入关键字过滤下方计算出的原材料...")
        self.search_input.textChanged.connect(self.filter_table)
        filter_layout.addWidget(self.search_input)

        # --- 展示区 ---
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["最底层原材料名称 (双击复制)", "总消耗量 (kg)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.cellDoubleClicked.connect(self.handle_cell_double_click)

        # --- 导出区 ---
        export_layout = QHBoxLayout()
        self.btn_export = QPushButton("📊 导出Excel报告")
        self.btn_export.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 8px 20px;")
        self.btn_export.clicked.connect(self.export_excel)
        export_layout.addStretch()
        export_layout.addWidget(self.btn_export)

        layout.addLayout(control_layout)
        layout.addLayout(filter_layout)
        layout.addWidget(self.table)
        layout.addLayout(export_layout)
        self.setLayout(layout)

    def update_completer(self):
        try:
            all_parents = database.get_unique_parents()
            self.input_product.clear()
            self.input_product.addItems(all_parents)
            self.input_product.setCurrentText("")
            model = QStringListModel(all_parents)
            self.completer.setModel(model)
        except Exception as e:
            print(f"下拉列表初始化失败: {e}")

    def filter_table(self, text):
        for i in range(self.table.rowCount()):
            item = self.table.item(i, 0)
            if item:
                self.table.setRowHidden(i, text.lower() not in item.text().lower())

    def handle_cell_double_click(self, row, column):
        item = self.table.item(row, column)
        if item:
            text = item.text()
            QApplication.clipboard().setText(text)
            print(f"已复制: {text}")

    def run_calculation(self):
        product = self.input_product.currentText().strip()
        qty_str = self.input_target_qty.text().strip()

        if not product or not qty_str:
            QMessageBox.warning(self, "提示", "请输入需要计算的产品和产量！")
            return

        try:
            qty = float(qty_str)
            if qty <= 0: raise ValueError
        except ValueError:
            QMessageBox.warning(self, "输入错误", "计划产量必须为大于0的数字！")
            return

        try:
            self.current_results = bom_logic.calculate_raw_materials(product, qty)
            self.update_table()
            self.search_input.clear()
            self.update_completer()
            self.input_product.setCurrentText(product)
        except ValueError as ve:
            QMessageBox.warning(self, "数据提示", str(ve))
        except RecursionError as re:
            QMessageBox.critical(self, "严重错误", str(re))
        except Exception as e:
            QMessageBox.critical(self, "未知错误", str(e))

    def update_table(self):
        self.table.setRowCount(0)
        sorted_results = sorted(self.current_results.items(), key=lambda x: x[0])

        for row_idx, (material, total_qty) in enumerate(sorted_results):
            self.table.insertRow(row_idx)
            item_mat = QTableWidgetItem(material)
            item_qty = QTableWidgetItem(f"{total_qty:.4f}".rstrip('0').rstrip('.'))
            item_qty.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self.table.setItem(row_idx, 0, item_mat)
            self.table.setItem(row_idx, 1, item_qty)

    def export_excel(self):
        if not self.current_results:
            QMessageBox.information(self, "提示", "当前没有可导出的计算结果。")
            return

        product = self.input_product.currentText().strip()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{product}_BOM需求表_{timestamp}.xlsx"

        try:
            df = pd.DataFrame(list(self.current_results.items()), columns=['最底层原材料名称', '总消耗量 (kg)'])
            df.to_excel(filename, index=False, engine='openpyxl')
            QMessageBox.information(self, "导出成功", f"文件已保存为：\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出出错:\n{str(e)}")