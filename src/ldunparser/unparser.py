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
            target = stmt.get("target", {})
            value = stmt.get("value", {})

            # 1. 纯变量赋值 (A := B) -> 触点 + 线圈
            if target.get("expr_type") == "var" and value.get("expr_type") == "var":
                return self._parse_ld_assignment(stmt)

            # 2. 数学运算 (A := B + C) 或 函数赋值 (A := FUNC(B)) -> 数据源 + Block + 数据池
            elif target.get("expr_type") == "var" and value.get("expr_type") in ["binop", "call"]:
                return self._parse_ld_complex_assign(stmt)

            # 🌟 优雅重构 1：直接把详细的“案发现场”打包进 Exception
            raise ValueError(
                f"[LD诊断] 暂不支持过于复杂的嵌套赋值结构 -> "
                f"左侧节点类型: '{target.get('expr_type')}', 右侧节点类型: '{value.get('expr_type')}'"
            )

        elif stmt_type == "call":
            return self._parse_ld_call(stmt)

        # 🌟 优雅重构 2：直接抛出不支持的具体语句类型
        raise ValueError(f"[LD诊断] 暂不支持的控制流或语句类型: '{stmt_type}'")

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

    # ==========================================
    # 🌟 新增：处理数学运算和函数赋值的渲染器
    # ==========================================
    def _parse_ld_complex_assign(self, stmt: dict) -> str:
        target = stmt.get("target", {})
        value = stmt.get("value", {})
        target_name = target.get("name", "UNKNOWN_TARGET")

        y_pos = self.current_y
        elements = []

        # 分配核心骨架 ID
        left_rail_obj = self.get_id()
        left_rail_out = self.get_id()
        right_rail_obj = self.get_id()
        block_obj = self.get_id()
        eno_out = self.get_id()
        sink_obj = self.get_id()

        # 1. 生成左电源线
        elements.append(self.render("left_rail", id=left_rail_obj, out_id=left_rail_out, y=y_pos))

        inputs = []

        # 闭包辅助函数：快速生成数据源 (DataSource)
        def add_data_source(name, pin_name, py):
            src_obj = self.get_id()
            src_out = self.get_id()
            elements.append(self.render("data_source", id=src_obj, name=name, out_id=src_out, x=100, y=y_pos + py))
            inputs.append({"name": pin_name, "y": py, "ref_out_id": src_out})

        # 闭包辅助函数：解析叶子节点的值
        def get_expr_name(node):
            if node.get("expr_type") == "var":
                return node.get("name")
            elif node.get("expr_type") == "literal":
                return str(node.get("value"))
            raise ValueError(f"遇到了嵌套表达式: {node.get('expr_type')}")

        try:
            # 2A. 如果是加减乘除算术运算 (binop)
            if value.get("expr_type") == "binop":
                op_map = {"+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV", "MOD": "MOD"}
                block_type = op_map.get(value.get("op", "+").upper(), "ADD")

                # 为算式的左边和右边生成 DataSource 并连接到 IN1, IN2
                add_data_source(get_expr_name(value.get("left", {})), "IN1", 40)
                add_data_source(get_expr_name(value.get("right", {})), "IN2", 80)

            # 2B. 如果是函数调用赋值 A := MYFUNC(B, 1)
            elif value.get("expr_type") == "call":
                block_type = value.get("func_name", "FUNC")
                args = value.get("args", [])
                py = 40
                for i, arg in enumerate(args):
                    add_data_source(get_expr_name(arg), f"IN{i + 1}", py)
                    py += 40
        except ValueError as e:
            # 把底层的具体死因（比如遇到了 literal 或多层嵌套）向上透传
            raise ValueError(f"[LD诊断] 表达式解析失败，暂不支持该语法树结构 -> 详细原因: {str(e)}")

        # 3. 生成运算块 (Block)，分配输出引脚 OUT
        out_out = self.get_id()
        outputs = [{"name": "OUT", "y": 40, "out_id": out_out}]

        elements.append(self.render("block",
                                    id=block_obj,
                                    type_name=block_type,
                                    instance_name=f"INST_{block_type}",
                                    x=300, y=y_pos,
                                    en_connected_out_id=left_rail_out,
                                    eno_out_id=eno_out,
                                    inputs=inputs,
                                    outputs=outputs))

        # 4. 生成数据池 (DataSink)，承接 Block 的 OUT 结果并赋值给 target_name
        elements.append(self.render("data_sink",
                                    id=sink_obj,
                                    name=target_name,
                                    in_connected_out_id=out_out,
                                    x=700, y=y_pos + 40))

        # 5. 生成右电源线
        elements.append(self.render("right_rail", id=right_rail_obj, connected_out_id=eno_out, y=y_pos))

        # 动态计算高度
        self.current_y += max(120, len(inputs) * 40 + 60)
        self.network_order += 1

        return self.render("network", order=self.network_order, elements_str="\n".join(elements))
