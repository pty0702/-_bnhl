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