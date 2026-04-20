# export_dialog.py
import datetime
import re
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QListWidget, QListWidgetItem, QMessageBox, QLabel, QFileDialog)
from PyQt5.QtCore import Qt
import pandas as pd
import database
import bom_logic


class ExportRecipeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("批量导出配方穿透报表")
        self.resize(400, 500)
        self.init_ui()
        self.load_products()

    def init_ui(self):
        layout = QVBoxLayout()

        # 提示文字
        header = QLabel("请勾选需要导出的产品：\n(每个产品将生成一个独立的Excel Sheet，基准为1吨)")
        header.setStyleSheet("color: #34495e; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)

        # 列表框
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("QListWidget { border: 1px solid #bdc3c7; border-radius: 5px; padding: 5px; }")
        layout.addWidget(self.list_widget)

        # 全选/反选控制区
        ctrl_layout = QHBoxLayout()
        btn_select_all = QPushButton("☑️ 全选")
        btn_select_all.clicked.connect(self.select_all)
        btn_clear_all = QPushButton("☐ 清空")
        btn_clear_all.clicked.connect(self.clear_all)
        ctrl_layout.addWidget(btn_select_all)
        ctrl_layout.addWidget(btn_clear_all)
        ctrl_layout.addStretch()
        layout.addLayout(ctrl_layout)

        # 导出操作区
        btn_export = QPushButton("📊 立即导出所选配方")
        btn_export.setStyleSheet("""
            QPushButton { background-color: #27ae60; color: white; font-size: 14px; font-weight: bold; padding: 10px; border-radius: 5px; margin-top: 10px;}
            QPushButton:hover { background-color: #2ecc71; }
        """)
        btn_export.clicked.connect(self.export_to_excel)
        layout.addWidget(btn_export)

        self.setLayout(layout)

    def load_products(self):
        """加载所有产品并生成复选框"""
        products = database.get_unique_parents()
        for prod in products:
            item = QListWidgetItem(prod)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)  # 默认不勾选
            self.list_widget.addItem(item)

    def select_all(self):
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Checked)

    def clear_all(self):
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Unchecked)

    def sanitize_sheet_name(self, name):
        """Excel Sheet名不能包含特殊字符，且最长31个字符"""
        safe_name = re.sub(r'[\\/*?:\[\]]', '_', name)
        return safe_name[:31]

    def export_to_excel(self):
        # 收集被勾选的产品
        selected_products = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                selected_products.append(item.text())

        if not selected_products:
            QMessageBox.warning(self, "提示", "请至少勾选一个要导出的产品！")
            return

        # 让用户选择保存路径
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        default_name = f"多级配方穿透报表_{timestamp}.xlsx"
        filepath, _ = QFileDialog.getSaveFileName(self, "保存Excel文件", default_name, "Excel Files (*.xlsx)")

        if not filepath:
            return  # 用户取消了保存

        try:
            # 批量穿透计算并写入多Sheet
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                for prod in selected_products:
                    # 统一按照 1吨(1000kg) 计算底层原料
                    results = bom_logic.calculate_raw_materials(prod, 1000)

                    if results:
                        # 排序并转为 DataFrame
                        sorted_res = sorted(results.items(), key=lambda x: x[0])
                        df = pd.DataFrame(sorted_res, columns=['最底层原材料', '总消耗量 (kg/吨)'])
                    else:
                        # 防止空配方报错
                        df = pd.DataFrame([["(无底层数据)", 0]], columns=['最底层原材料', '总消耗量 (kg/吨)'])

                    sheet_name = self.sanitize_sheet_name(prod)
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

            QMessageBox.information(self, "导出成功", f"成功导出 {len(selected_products)} 个产品的配方到：\n{filepath}")
            self.accept()  # 关闭弹窗

        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"生成Excel时出错，可能文件被占用：\n{e}")