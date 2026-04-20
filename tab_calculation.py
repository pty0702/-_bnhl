# tab_calculation.py
import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QHeaderView,QApplication)
import pandas as pd
import bom_logic


class TabCalculation(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.current_results = {}  # 暂存计算结果用于导出

    def init_ui(self):
        layout = QVBoxLayout()

        # --- 控制区 ---
        control_layout = QHBoxLayout()
        self.input_product = QLineEdit()
        self.input_product.setPlaceholderText("计算产品名称")

        self.input_target_qty = QLineEdit()
        self.input_target_qty.setPlaceholderText("计划产量(kg)")

        self.btn_calc = QPushButton("执行穿透计算")
        self.btn_calc.clicked.connect(self.run_calculation)

        control_layout.addWidget(QLabel("目标成品:"))
        control_layout.addWidget(self.input_product)
        control_layout.addWidget(QLabel("计划产量(kg):"))
        control_layout.addWidget(self.input_target_qty)
        control_layout.addWidget(self.btn_calc)

        # --- 展示区 ---
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["最底层原材料名称", "总消耗量 (kg)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # --- 导出区 ---
        export_layout = QHBoxLayout()
        self.btn_export = QPushButton("导出Excel报告")
        self.btn_export.clicked.connect(self.export_excel)
        export_layout.addStretch()
        export_layout.addWidget(self.btn_export)

        layout.addLayout(control_layout)
        layout.addWidget(self.table)
        layout.addLayout(export_layout)
        self.setLayout(layout)
        # 【新增】设置表格为不可编辑（防止双击变成输入状态）
        from PyQt5.QtWidgets import QAbstractItemView
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # 【新增】绑定双击事件
        self.table.itemDoubleClicked.connect(self.copy_cell_text)

    # 【新增】复制逻辑方法
    # 首先确保在文件顶部的 import 中加入了 QCursor
    from PyQt5.QtGui import QCursor  # <--- 必须加上这个导入

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
    def run_calculation(self):
        product = self.input_product.text().strip()
        qty_str = self.input_target_qty.text().strip()

        if not product or not qty_str:
            QMessageBox.warning(self, "输入错误", "请输入需要计算的产品和产量！")
            return

        try:
            qty = float(qty_str)
            if qty <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "输入错误", "计划产量必须为大于0的数字！")
            return

        try:
            # 核心穿透计算
            self.current_results = bom_logic.calculate_raw_materials(product, qty)
            self.update_table()
        except ValueError as ve:
            QMessageBox.warning(self, "数据提示", str(ve))
        except RecursionError as re:
            QMessageBox.critical(self, "严重错误", str(re))
        except Exception as e:
            QMessageBox.critical(self, "未知错误", str(e))

    def update_table(self):
        self.table.setRowCount(0)
        # 按名称排序展示
        sorted_results = sorted(self.current_results.items(), key=lambda x: x[0])

        for row_idx, (material, total_qty) in enumerate(sorted_results):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(material))
            # 格式化为保留4位小数，去除多余的0
            self.table.setItem(row_idx, 1, QTableWidgetItem(f"{total_qty:.4f}".rstrip('0').rstrip('.')))

    def export_excel(self):
        if not self.current_results:
            QMessageBox.information(self, "提示", "当前没有可导出的计算结果。")
            return

        product = self.input_product.text().strip()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{product}_BOM需求表_{timestamp}.xlsx"

        try:
            # 转换为 DataFrame 并导出
            df = pd.DataFrame(list(self.current_results.items()), columns=['最底层原材料名称', '总消耗量 (kg)'])
            df.to_excel(filename, index=False, engine='openpyxl')
            QMessageBox.information(self, "导出成功", f"文件已保存为：\n{filename}\n(保存在当前软件目录下)")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出Excel时发生错误:\n{str(e)}")