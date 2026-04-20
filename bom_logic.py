# bom_logic.py
from database import get_all_recipes

def get_bom_dict():
    """将数据库数据转化为字典，格式: {父件: [(子件, 单耗), ...]}"""
    recipes = get_all_recipes()
    bom = {}
    for parent, child, qty in recipes:
        if parent not in bom:
            bom[parent] = []
        bom[parent].append((child, qty))
    return bom

def calculate_raw_materials(product, target_qty):
    """
    递归穿透计算最底层原材料
    返回: {原材料名称: 总消耗量}
    抛出: ValueError (找不到产品), RecursionError (死循环)
    """
    bom = get_bom_dict()
    results = {}

    if product not in bom:
        raise ValueError(f"数据库中不存在产品/半成品：'{product}'，或该产品本身即为最底层原材料。")

    # bom_logic.py 局部修改

    def resolve(item, current_qty, path):
        # 防死循环检测
        if item in path:
            cycle_path = " -> ".join(path + [item])
            raise RecursionError(f"检测到BOM死循环！\n循环路径: {cycle_path}")

        if item not in bom:
            # 叶子节点（最底层原材料）
            results[item] = results.get(item, 0.0) + current_qty
            return

        path.append(item)
        for child, qty_per_1000 in bom[item]:
            # 核心逻辑变更：
            # 因为 qty_per_1000 的单位是 kg/吨 (即 kg/1000kg)
            # 所以 1kg 父件消耗的子件 = qty_per_1000 / 1000
            real_qty_per_unit = qty_per_1000 / 1000.0

            # 递归计算：当前父件需求量(kg) * 每kg父件消耗的子件(kg)
            resolve(child, current_qty * real_qty_per_unit, path)
        path.pop()

    resolve(product, float(target_qty), [])
    return results