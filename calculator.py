from collections import defaultdict


class BomCalculator:
    def __init__(self, db):
        self.db = db

    def explode(self, item, qty, path=None):
        """
        递归拆解BOM，返回最底层原料汇总
        """
        if path is None:
            path = set()

        if item in path:
            raise Exception(f"检测到循环依赖: {' -> '.join(path)} -> {item}")

        path.add(item)

        result = defaultdict(float)
        children = self.db.get_children(item)

        # 叶子节点（底层原料）
        if not children:
            result[item] += qty
            return result

        for child, per_unit in children:
            need_qty = qty * per_unit

            if self.db.is_parent(child):
                sub = self.explode(child, need_qty, path.copy())
                for k, v in sub.items():
                    result[k] += v
            else:
                result[child] += need_qty

        return result