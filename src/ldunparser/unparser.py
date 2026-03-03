from jinja2 import Environment, DictLoader
from .LD_XML_TEMPLATES import LD_XML_TEMPLATES

# 假设 FBDXmlUnparser 已经在此文件中定义

class LDXmlUnparser():
    """
    梯形图 (LD) 还原器，继承自 FBDXmlUnparser。
    将 ST 语句转化为触点、线圈及带使能 (EN/ENO) 的功能块。
    """

    def __init__(self):
        super().__init__()
        # 覆写模板引擎，加载 LD 专属模板
        self.env = Environment(loader=DictLoader(LD_XML_TEMPLATES), trim_blocks=True, lstrip_blocks=True)

    # ==========================================
    # 🌟 重写核心渲染逻辑
    # ==========================================
    def unparse_network(self, stmt: dict) -> str:
        """
        覆盖父类方法。针对每条语句生成一个梯形图 Network。
        最经典的 LD 结构：LeftRail -> Contact -> Coil -> RightRail
        """
        stmt_type = stmt.get("stmt_type")

        # 我们以最常见的赋值语句 (A := B) 为例
        if stmt_type == "assign":
            return self._parse_ld_assignment(stmt)

        # 如果是函数调用，可以作为挂在电源线上的 Block 处理
        elif stmt_type == "call":
            return self._parse_ld_call(stmt)

        # 遇到暂不支持的结构（如 IF、FOR），抛出异常交由外层跳过
        raise ValueError(f"[LD诊断] 暂不支持的语句类型: {stmt_type}")

    def _parse_ld_assignment(self, stmt: dict) -> str:
        """
        将 A := B 转化为：
        [左电源线] ---> [常开触点 B] ---> [线圈 A] ---> [右电源线]
        """
        target = stmt.get("target", {})
        value = stmt.get("value", {})

        # 为了简化演示，假设两边都是简单变量 (var)
        if target.get("expr_type") != "var" or value.get("expr_type") != "var":
            raise ValueError("[LD诊断] 暂只支持纯变量之间的赋值映射为触点/线圈。")

        target_name = target.get("name", "UNKNOWN_TARGET")
        value_name = value.get("name", "UNKNOWN_VALUE")

        # 1. 分配 ID
        left_rail_id = self.get_id()
        contact_id = self.get_id()
        coil_id = self.get_id()
        right_rail_id = self.get_id()

        elements = []
        y_pos = self.current_y

        # 2. 生成左电源线
        elements.append(self.render("left_rail", id=left_rail_id, y=y_pos))

        # 3. 生成触点 (连接到左电源线)
        elements.append(self.render("contact",
                                    id=contact_id,
                                    name=value_name,
                                    x=100, y=y_pos,
                                    in_connected_id=left_rail_id))

        # 4. 生成线圈 (连接到触点)
        elements.append(self.render("coil",
                                    id=coil_id,
                                    name=target_name,
                                    x=600, y=y_pos,
                                    in_connected_id=contact_id))

        # 5. 生成右电源线 (连接到线圈)
        elements.append(self.render("right_rail",
                                    id=right_rail_id,
                                    y=y_pos,
                                    connected_id=coil_id))

        # 迭代 Y 坐标，准备画下一个 Network
        self.current_y += 100
        self.network_order += 1

        return self.render("network",
                           order=self.network_order,
                           elements_str="\n".join(elements))

    def _parse_ld_call(self, stmt: dict) -> str:
        """处理形如 MY_FUNC(IN:=A) 的调用（在 LD 中通常直接挂接块）"""
        # 这里你可以复用 FBD 的 block 模板，将其 EN 引脚连到 LeftRail
        pass