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

    def resolve(item, current_qty, path):
        # 防死循环检测
        if item in path:
            cycle_path = " -> ".join(path + [item])
            raise RecursionError(f"检测到BOM死循环/交叉引用，请检查配方数据！\n循环路径: {cycle_path}")

        if item not in bom:
            # 叶子节点（最底层原材料）
            results[item] = results.get(item, 0.0) + current_qty
            return

        # 记录当前路径
        path.append(item)
        # 遍历当前父件的子件
        for child, qty_per_unit in bom[item]:
            resolve(child, current_qty * qty_per_unit, path)
        # 回溯出栈
        path.pop()

    resolve(product, float(target_qty), [])
    return results