from jinja2 import Environment, DictLoader

from src.fbdunparser import FBDXmlUnparser
from .LD_XML_TEMPLATES import LD_XML_TEMPLATES


class LDXmlUnparser(FBDXmlUnparser):
    """
    梯形图 (LD) 还原器，继承自 FBDXmlUnparser。
    将 ST 语句转化为触点、线圈及带使能 (EN/ENO) 的功能块。
    """

    def __init__(self):
        super().__init__()
        # 覆写模板引擎，加载 LD 专属模板
        self.env = Environment(loader=DictLoader(LD_XML_TEMPLATES), trim_blocks=True, lstrip_blocks=True)

    def unparse_network(self, stmt: dict) -> str:
        stmt_type = stmt.get("stmt_type")

        if stmt_type == "assign":
            return self._parse_ld_assignment(stmt)
        elif stmt_type == "call":
            return self._parse_ld_call(stmt)

        raise ValueError(f"[LD诊断] 暂不支持的语句类型: {stmt_type}")

    def _parse_ld_assignment(self, stmt: dict) -> str:
        """
        [左电源线] ---> [触点 B] ---> [线圈 A] ---> [右电源线]
        """
        target = stmt.get("target", {})
        value = stmt.get("value", {})

        if target.get("expr_type") != "var" or value.get("expr_type") != "var":
            raise ValueError("[LD诊断] 暂只支持纯变量之间的赋值映射为触点/线圈。")

        target_name = target.get("name", "UNKNOWN_TARGET")
        value_name = value.get("name", "UNKNOWN_VALUE")

        # 🌟 必须分配对象 ID 和 输出引脚 ID (XSD 严格要求)
        left_rail_obj = self.get_id()
        left_rail_out = self.get_id()

        contact_obj = self.get_id()
        contact_out = self.get_id()

        coil_obj = self.get_id()
        coil_out = self.get_id()

        right_rail_obj = self.get_id()

        elements = []
        y_pos = self.current_y

        # 生成左电源线
        elements.append(self.render("left_rail", id=left_rail_obj, out_id=left_rail_out, y=y_pos))

        # 生成触点 (输入连左电源线，产生输出 ID)
        elements.append(self.render("contact",
                                    id=contact_obj,
                                    name=value_name,
                                    x=100, y=y_pos,
                                    in_connected_out_id=left_rail_out,
                                    out_id=contact_out))

        # 生成线圈 (输入连触点，产生输出 ID)
        elements.append(self.render("coil",
                                    id=coil_obj,
                                    name=target_name,
                                    x=600, y=y_pos,
                                    in_connected_out_id=contact_out,
                                    out_id=coil_out))

        # 生成右电源线 (连线圈)
        elements.append(self.render("right_rail",
                                    id=right_rail_obj,
                                    y=y_pos,
                                    connected_out_id=coil_out))

        self.current_y += 100
        self.network_order += 1

        return self.render("network", order=self.network_order, elements_str="\n".join(elements))

    def _parse_ld_call(self, stmt: dict) -> str:
        """
        处理形如 MY_FUNC(IN1:=A, IN2:=B) 的调用。
        结构：左电源线 -> 多个触点(参数) -> Block(EN连左电源) -> 右电源线(连ENO)
        """
        func_name = stmt.get("func_name", "UNKNOWN_FUNC")
        args = stmt.get("args", [])

        left_rail_obj = self.get_id()
        left_rail_out = self.get_id()
        right_rail_obj = self.get_id()
        block_obj = self.get_id()
        eno_out_id = self.get_id()

        elements = []
        y_pos = self.current_y

        # 1. 生成左电源线
        elements.append(self.render("left_rail", id=left_rail_obj, out_id=left_rail_out, y=y_pos))

        inputs = []
        pin_y = 20

        # 2. 遍历函数的输入参数，把它们渲染为触点，再连入 Block 引脚
        for i, arg in enumerate(args):
            arg_name = "ARG"
            if isinstance(arg, dict):
                if arg.get("expr_type") == "var":
                    arg_name = arg.get("name")
                elif arg.get("expr_type") == "literal":
                    arg_name = str(arg.get("value"))

            contact_obj = self.get_id()
            contact_out = self.get_id()

            # 将参数渲染为触点，接在左电源线上
            elements.append(self.render("contact",
                                        id=contact_obj,
                                        name=arg_name,
                                        x=100, y=y_pos + pin_y,
                                        in_connected_out_id=left_rail_out,
                                        out_id=contact_out))

            # 注册为 Block 的输入引脚 (如 IN1, IN2)
            inputs.append({
                "name": f"IN{i + 1}",
                "y": pin_y,
                "ref_out_id": contact_out
            })
            pin_y += 30

        # 3. 生成 Block 节点 (EN 连电源，各个引脚连到刚才生成的触点)
        elements.append(self.render("block",
                                    id=block_obj,
                                    type_name=func_name,
                                    instance_name=f"INST_{func_name}",
                                    x=400, y=y_pos,
                                    en_connected_out_id=left_rail_out,
                                    eno_out_id=eno_out_id,
                                    inputs=inputs,
                                    outputs=[]))

        # 4. 生成右电源线 (接住 Block 的 ENO 输出)
        elements.append(self.render("right_rail",
                                    id=right_rail_obj,
                                    y=y_pos,
                                    connected_out_id=eno_out_id))

        # 根据参数数量动态计算下一个 Network 的 Y 轴高度
        self.current_y += max(120, pin_y + 40)
        self.network_order += 1

        return self.render("network", order=self.network_order, elements_str="\n".join(elements))