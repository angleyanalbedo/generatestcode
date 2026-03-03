from jinja2 import Environment, DictLoader
from typing import List, Dict, Any

# ==========================================
# 1. 严格基于 IEC61131-10 的 Jinja2 模板
# ==========================================
XML_TEMPLATES = {
    "project": """<?xml version="1.0" encoding="utf-8"?>
<Project xmlns="www.iec.ch/public/TC65SC65BWG7TF10" 
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
         schemaVersion="1.0">
  <FileHeader companyName="SyntheticDataGen" productName="LLM_AST_Unparser" productVersion="1.0"/>
  <ContentHeader name="LLM_Synthetic_Project" creationDateTime="2024-01-01T00:00:00">
    <CoordinateInfo>
      <FbdScaling x="1" y="1"/>
    </CoordinateInfo>
  </ContentHeader>
  <Types>
    <GlobalNamespace>
      <Program name="{{ pou_name }}">
        <MainBody>
          <BodyContent xsi:type="FBD">
{{ networks_str }}
          </BodyContent>
        </MainBody>
      </Program>
    </GlobalNamespace>
  </Types>
  <Instances/>
</Project>""",

    "network": """            <Network evaluationOrder="{{ order }}">
{{ elements_str }}
            </Network>""",

    # 修复 3: 将所有图元转为 FbdObject 并指定 xsi:type
    "data_source": """              <FbdObject xsi:type="DataSource" identifier="{{ name }}" globalId="OBJ_{{ global_id }}">
                <RelPosition x="100" y="{{ y }}" />
                <ConnectionPointOut connectionPointOutId="{{ out_id }}">
                  <RelPosition x="40" y="10" />
                </ConnectionPointOut>
              </FbdObject>""",

    "data_sink": """              <FbdObject xsi:type="DataSink" identifier="{{ name }}" globalId="OBJ_{{ global_id }}">
                <RelPosition x="800" y="{{ y }}" />
                <ConnectionPointIn>
                  <RelPosition x="0" y="10" />
                  <Connection refConnectionPointOutId="{{ connected_out_id }}" />
                </ConnectionPointIn>
              </FbdObject>""",

    "block": """              <FbdObject xsi:type="Block" typeName="{{ type_name }}" globalId="OBJ_{{ global_id }}">
                <RelPosition x="{{ x }}" y="{{ y }}" />
                <InputVariables>
{% for pin in inputs %}
                  <InputVariable parameterName="{{ pin.name }}">
                    <ConnectionPointIn>
                      <RelPosition x="0" y="{{ pin.y }}" />
                      <Connection refConnectionPointOutId="{{ pin.ref_out_id }}" />
                    </ConnectionPointIn>
                  </InputVariable>
{% endfor %}
                </InputVariables>
                <OutputVariables>
                  <OutputVariable parameterName="OUT">
                    <ConnectionPointOut connectionPointOutId="{{ out_id }}">
                      <RelPosition x="{{ width }}" y="{{ out_y }}" />
                    </ConnectionPointOut>
                  </OutputVariable>
                </OutputVariables>
              </FbdObject>"""
}


class FBDXmlUnparser:
    """
    严格基于 IEC61131_10_Ed1_0.xsd 的 FBD 还原器
    """

    def __init__(self):
        self.id_counter = 0
        self.current_y = 50
        self.network_order = 0
        self.env = Environment(loader=DictLoader(XML_TEMPLATES), trim_blocks=True, lstrip_blocks=True)

    def get_id(self) -> str:
        """生成全局唯一的数字 ID，用于 globalId 和 connectionPointOutId"""
        self.id_counter += 1
        return str(self.id_counter)

    def render(self, template_name: str, **kwargs) -> str:
        template = self.env.get_template(template_name)
        return template.render(**kwargs)

    # ==========================================
    # 2. 生成 Project 根结构
    # ==========================================
    def unparse_pou(self, pou_node: Dict[str, Any]) -> str:
        if not pou_node or "unit_type" not in pou_node:
            return ""

        pou_name = pou_node.get("name", "GeneratedPOU")

        body_ast = pou_node.get("body", [])
        if not isinstance(body_ast, list):
            body_ast = [body_ast]

        # 遍历解析生成 Network 列表
        networks_xml = []
        for stmt in body_ast:
            net = self.unparse_network(stmt)
            if net:
                networks_xml.append(net)

        networks_str = "\n".join(networks_xml)

        return self.render("project", pou_name=pou_name, networks_str=networks_str)

    # ==========================================
    # 3. 解析 Network
    # ==========================================
    def unparse_network(self, stmt_node: Dict[str, Any]) -> str:
        if not isinstance(stmt_node, dict): return ""
        self.elements_xml = []
        self.current_y += 80
        stmt_type = stmt_node.get("stmt_type")

        if stmt_type == "assign":
            right_expr = stmt_node.get("value")
            # 注意：新版解析表达式返回的是输出引脚的 ID (out_id)，而不是模块本身的 ID
            right_out_id = self._parse_expr(right_expr)
            target_name = stmt_node.get("target", {}).get("name", "UNKNOWN")
            self._build_data_sink(target_name, right_out_id)

        elif stmt_type == "if":
            self._parse_if_to_sel(stmt_node)
        else:
            return ""

        if not self.elements_xml: return ""

        self.network_order += 1
        elements_str = "\n".join(self.elements_xml)
        return self.render("network", order=self.network_order, elements_str=elements_str)

    def _build_data_sink(self, target_name: str, connected_out_id: str):
        """对应 XSD 中的 DataSink (原 outVariable)"""
        out_xml = self.render("data_sink",
                              global_id=self.get_id(),
                              y=self.current_y,
                              connected_out_id=connected_out_id,
                              name=target_name)
        self.elements_xml.append(out_xml)

    # ==========================================
    # 4. 解析表达式 -> 必须返回引脚的 ConnectionPointOutId
    # ==========================================
    def _parse_expr(self, expr: Dict[str, Any]) -> str:
        if not expr: return "0"
        if isinstance(expr, str): return "0"

        expr_type = expr.get("expr_type")
        current_node_y = self.current_y

        if expr_type in ("var", "literal"):
            name = expr.get("name", expr.get("value", ""))
            global_id = self.get_id()
            out_pin_id = self.get_id()  # 必须给输出引脚分配独立ID

            in_xml = self.render("data_source",
                                 global_id=global_id,
                                 out_id=out_pin_id,
                                 y=current_node_y,
                                 name=name)
            self.elements_xml.append(in_xml)
            return out_pin_id  # 返回引脚ID供下一步连线

        elif expr_type == "unaryop":
            op = expr.get("op", "").upper()
            operand_out_id = self._parse_expr(expr.get("operand"))

            global_id = self.get_id()
            out_pin_id = self.get_id()
            inputs = [{"name": "IN", "y": 20, "ref_out_id": operand_out_id}]

            block_xml = self.render("block", global_id=global_id, out_id=out_pin_id, type_name=op,
                                    height=40, width=40, x=300, y=current_node_y, out_y=20, inputs=inputs)
            self.elements_xml.append(block_xml)
            return out_pin_id

        elif expr_type == "binop":
            op = expr.get("op", "").upper()
            left_out_id = self._parse_expr(expr.get("left"))
            self.current_y += 40
            right_out_id = self._parse_expr(expr.get("right"))

            global_id = self.get_id()
            out_pin_id = self.get_id()
            inputs = [
                {"name": "IN1", "y": 20, "ref_out_id": left_out_id},
                {"name": "IN2", "y": 40, "ref_out_id": right_out_id}
            ]
            block_xml = self.render("block", global_id=global_id, out_id=out_pin_id, type_name=op,
                                    height=60, width=40, x=500, y=current_node_y, out_y=30, inputs=inputs)
            self.elements_xml.append(block_xml)
            return out_pin_id

        elif expr_type == "call":
            func_name = expr.get("func_name", "UNKNOWN_FUNC")
            args = expr.get("args", [])

            inputs = []
            for i, arg in enumerate(args):
                arg_out_id = self._parse_expr(arg)
                inputs.append({"name": f"IN{i + 1}", "y": 20 + i * 20, "ref_out_id": arg_out_id})
                self.current_y += 30

            global_id = self.get_id()
            out_pin_id = self.get_id()
            block_height = max(40, len(args) * 20 + 20)

            block_xml = self.render("block", global_id=global_id, out_id=out_pin_id, type_name=func_name,
                                    height=block_height, width=60, x=600, y=current_node_y, out_y=20, inputs=inputs)
            self.elements_xml.append(block_xml)
            return out_pin_id

        return "0"

    def _parse_if_to_sel(self, stmt_node: Dict[str, Any]):
        cond = stmt_node.get("cond")
        then_body = stmt_node.get("then_body", [])
        else_body = stmt_node.get("else_body", [])

        if len(then_body) == 1 and len(else_body) == 1:
            then_stmt = then_body[0]
            else_stmt = else_body[0]

            if then_stmt.get("stmt_type") == "assign" and else_stmt.get("stmt_type") == "assign":
                target_then = then_stmt.get("target", {}).get("name")
                target_else = else_stmt.get("target", {}).get("name")

                if target_then == target_else and target_then:
                    g_out_id = self._parse_expr(cond)
                    self.current_y += 30
                    in1_out_id = self._parse_expr(then_stmt.get("value"))
                    self.current_y += 30
                    in0_out_id = self._parse_expr(else_stmt.get("value"))

                    global_id = self.get_id()
                    sel_out_pin_id = self.get_id()

                    inputs = [
                        {"name": "G", "y": 20, "ref_out_id": g_out_id},
                        {"name": "IN0", "y": 40, "ref_out_id": in0_out_id},
                        {"name": "IN1", "y": 60, "ref_out_id": in1_out_id}
                    ]
                    sel_xml = self.render("block", global_id=global_id, out_id=sel_out_pin_id, type_name="SEL",
                                          height=80, width=40, x=500, y=self.current_y - 60, out_y=30, inputs=inputs)

                    self.elements_xml.append(sel_xml)
                    self._build_data_sink(target_then, sel_out_pin_id)