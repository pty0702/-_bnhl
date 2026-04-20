# database.py
import sqlite3
import os

DB_NAME = "bom_data.db"

def init_db():
    """初始化数据库并建表"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # 使用复合主键保证配方唯一性
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
    """添加或更新配方"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        REPLACE INTO recipes (parent_item, child_item, qty_per_unit)
        VALUES (?, ?, ?)
    ''', (parent, child, float(qty)))
    conn.commit()
    conn.close()

def get_all_recipes():
    """获取所有配方数据"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT parent_item, child_item, qty_per_unit FROM recipes")
    data = cursor.fetchall()
    conn.close()
    return data

def delete_recipe(parent, child):
    """物理删除指定配方"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM recipes WHERE parent_item=? AND child_item=?", (parent, child))
    conn.commit()
    conn.close()
def get_recipe_by_parent(parent):
    """获取某个父件的直接配方组成"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT child_item, qty_per_unit FROM recipes WHERE parent_item=?", (parent,))
    data = cursor.fetchall()
    conn.close()
    return data
# 追加到 database.py 底部

def get_parent_summaries():
    """获取所有产品的汇总信息（去重，并统计包含的原材料数量）"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # 使用 GROUP BY 进行分组去重
    cursor.execute("SELECT parent_item, COUNT(child_item) FROM recipes GROUP BY parent_item")
    data = cursor.fetchall()
    conn.close()
    return data

def delete_all_by_parent(parent):
    """删除某个产品的所有配方记录"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM recipes WHERE parent_item=?", (parent,))
    conn.commit()
    conn.close()