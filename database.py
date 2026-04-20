# database.py
import sqlite3
import os

DB_NAME = "bom_data.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            parent_item TEXT,
            child_item TEXT,
            qty_per_unit REAL,
            PRIMARY KEY (parent_item, child_item)
        )
    ''')
    conn.commit()
    conn.close()


def add_recipe(parent, child, qty):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('REPLACE INTO recipes (parent_item, child_item, qty_per_unit) VALUES (?, ?, ?)',
                   (parent, child, float(qty)))
    conn.commit()
    conn.close()


def get_all_recipes():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT parent_item, child_item, qty_per_unit FROM recipes")
    data = cursor.fetchall()
    conn.close()
    return data


# ====== 下面这两个是实现“去重展示”和“弹窗管理”的核心函数 ======
def get_parent_summaries():
    """获取去重后的产品列表，并统计它直接包含几项材料"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT parent_item, COUNT(child_item) FROM recipes GROUP BY parent_item")
    data = cursor.fetchall()
    conn.close()
    return data


def get_recipe_by_parent(parent):
    """供弹窗使用：获取某个产品具体用到的材料明细"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT child_item, qty_per_unit FROM recipes WHERE parent_item=?", (parent,))
    data = cursor.fetchall()
    conn.close()
    return data


def delete_recipe(parent, child):
    """物理删除某一条具体配方"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM recipes WHERE parent_item=? AND child_item=?", (parent, child))
    conn.commit()
    conn.close()


def delete_all_by_parent(parent):
    """物理删除某个产品的【所有】配方"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM recipes WHERE parent_item=?", (parent,))
    conn.commit()
    conn.close()
# database.py 增加此函数
def get_unique_parents():
    """获取所有已录入的产品名称清单（去重）"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT parent_item FROM recipes")
    # 将结果转为简单的列表
    data = [row[0] for row in cursor.fetchall()]
    conn.close()
    return data