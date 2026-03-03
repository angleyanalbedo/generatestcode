from jinja2 import Environment, DictLoader
from typing import List, Dict, Any

# ==========================================
# 1. 定义 Jinja2 模板字典
# ==========================================
XML_TEMPLATES = {
    "pou": """<?xml version="1.0" encoding="utf-8"?>
<project xmlns="{{ namespace }}" 
         xmlns:xhtml="http://www.w3.org/1999/xhtml" 
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
         xsi:schemaLocation="{{ namespace }} IEC61131_10_Ed1_0.xsd">
  <fileHeader companyName="SyntheticDataGen" productName="LLM_AST_Unparser" productVersion="1.0" creationDateTime="2024-01-01T00:00:00"/>
  <contentHeader name="LLM_Synthetic_Project">
    <coordinateInfo>
      <fbd>
        <scaling x="1" y="1"/>
      </fbd>
    </coordinateInfo>
  </contentHeader>
  <types>
    <pous>
      <pou name="{{ pou_name }}" pouType="{{ pou_type }}">
        <interface>
          <localVars>
          </localVars>
        </interface>
        <body>
          <FBD>
{{ networks_str }}
          </FBD>
        </body>
      </pou>
    </pous>
  </types>
</project>""",

    "network": """            <network>
{{ elements_str }}
            </network>""",

    "in_variable": """              <inVariable localId="{{ local_id }}" height="20" width="40">
                <position x="100" y="{{ y }}" />
                <connectionPointOut>
                  <relPosition x="40" y="10" />
                </connectionPointOut>
                <expression>{{ name }}</expression>
              </inVariable>""",

    "out_variable": """              <outVariable localId="{{ local_id }}" height="20" width="40">
                <position x="800" y="{{ y }}" />
                <connectionPointIn>
                  <relPosition x="0" y="10" />
                  <connection refLocalId="{{ connected_id }}" />
                </connectionPointIn>
                <expression>{{ name }}</expression>
              </outVariable>""",

    "block": """              <block localId="{{ local_id }}" typeName="{{ type_name }}" height="{{ height }}" width="{{ width }}">
                <position x="{{ x }}" y="{{ y }}" />
                <inputVariables>
{% for pin in inputs %}
                  <variable formalParameter="{{ pin.name }}">
                    <connectionPointIn>
                      <relPosition x="0" y="{{ pin.y }}" />
                      <connection refLocalId="{{ pin.ref_id }}" />
                    </connectionPointIn>
                  </variable>
{% endfor %}
                </inputVariables>
                <inOutVariables/>
                <outputVariables>
                  <variable formalParameter="OUT">
                    <connectionPointOut>
                      <relPosition x="{{ width }}" y="{{ out_y }}" />
                    </connectionPointOut>
                  </variable>
                </outputVariables>
              </block>"""
}


class FBDXmlUnparser:
    """
    ST AST 到 PLCopen XML (FBD) 的还原器 (基于 Jinja2 模板渲染)
    """

    def __init__(self):
        self.local_id_counter = 0
        self.current_y = 50

        # 初始化 Jinja2 环境
        self.env = Environment(loader=DictLoader(XML_TEMPLATES), trim_blocks=True, lstrip_blocks=True)

    def get_id(self) -> int:
        self.local_id_counter += 1
        return self.local_id_counter

    def render(self, template_name: str, **kwargs) -> str:
        """辅助方法：渲染指定的模板"""
        template = self.env.get_template(template_name)
        return template.render(**kwargs)

    # ==========================================
    # 2. 生成完整的 POU 结构
    # ==========================================
    def unparse_pou(self, pou_node: Dict[str, Any]) -> str:
        if not pou_node or "unit_type" not in pou_node:
            return ""

        pou_name = pou_node.get("name", "GeneratedPOU")
        pou_type = pou_node.get("unit_type", "program").lower()

        body_ast = pou_node.get("body", [])
        if not isinstance(body_ast, list):
            body_ast = [body_ast]

        networks_xml = filter(None, [self.unparse_network(stmt) for stmt in body_ast])
        networks_str = "\n".join(networks_xml)

        # 这里使用 XSD 文件中定义的目标命名空间 targetNamespace 
        namespace = "www.iec.ch/public/TC65SC65BWG7TF10"

        return self.render("pou",
                           namespace=namespace,
                           pou_name=pou_name,
                           pou_type=pou_type,
                           networks_str=networks_str)

    # ==========================================
    # 3. 解析 Network
    # ==========================================
    def unparse_network(self, stmt_node: Dict[str, Any]) -> str:
        if not isinstance(stmt_node, dict): return ""
        self.elements_xml = []
        stmt_type = stmt_node.get("stmt_type")
        self.current_y += 80

        if stmt_type == "assign":
            right_expr = stmt_node.get("value")
            right_out_id = self._parse_expr(right_expr)
            target_name = stmt_node.get("target", {}).get("name", "UNKNOWN")
            self._build_out_variable(target_name, right_out_id)

        elif stmt_type == "if":
            self._parse_if_to_sel(stmt_node)
        else:
            return ""

        if not self.elements_xml: return ""

        elements_str = "\n".join(self.elements_xml)
        return self.render("network", elements_str=elements_str)

    def _build_out_variable(self, target_name: str, connected_id: int):
        out_xml = self.render("out_variable",
                              local_id=self.get_id(),
                              y=self.current_y,
                              connected_id=connected_id,
                              name=target_name)
        self.elements_xml.append(out_xml)

    # ==========================================
    # 4. 解析表达式 (复用通用 Block 模板)
    # ==========================================
    def _parse_expr(self, expr: Dict[str, Any]) -> int:
        if not expr: return 0
        if isinstance(expr, str): return 0
        expr_type = expr.get("expr_type")
        current_node_y = self.current_y

        # 处理变量/常量
        if expr_type in ("var", "literal"):
            var_id = self.get_id()
            name = expr.get("name", expr.get("value", ""))
            in_xml = self.render("in_variable", local_id=var_id, y=current_node_y, name=name)
            self.elements_xml.append(in_xml)
            return var_id

        # 处理一元操作 (NOT 等)
        elif expr_type == "unaryop":
            op = expr.get("op", "").upper()
            operand_id = self._parse_expr(expr.get("operand"))
            block_id = self.get_id()
            inputs = [{"name": "IN", "y": 20, "ref_id": operand_id}]

            block_xml = self.render("block", local_id=block_id, type_name=op, height=40, width=40,
                                    x=300, y=current_node_y, out_y=20, inputs=inputs)
            self.elements_xml.append(block_xml)
            return block_id

        # 处理二元操作 (+, -, AND, OR 等)
        elif expr_type == "binop":
            op = expr.get("op", "").upper()
            left_id = self._parse_expr(expr.get("left"))
            self.current_y += 40
            right_id = self._parse_expr(expr.get("right"))
            block_id = self.get_id()

            inputs = [
                {"name": "IN1", "y": 20, "ref_id": left_id},
                {"name": "IN2", "y": 40, "ref_id": right_id}
            ]
            block_xml = self.render("block", local_id=block_id, type_name=op, height=60, width=40,
                                    x=500, y=current_node_y, out_y=30, inputs=inputs)
            self.elements_xml.append(block_xml)
            return block_id

        # 处理函数调用
        elif expr_type == "call":
            func_name = expr.get("func_name", "UNKNOWN_FUNC")
            args = expr.get("args", [])

            inputs = []
            for i, arg in enumerate(args):
                arg_id = self._parse_expr(arg)
                inputs.append({"name": f"IN{i + 1}", "y": 20 + i * 20, "ref_id": arg_id})
                self.current_y += 30

            block_id = self.get_id()
            block_height = max(40, len(args) * 20 + 20)
            block_xml = self.render("block", local_id=block_id, type_name=func_name, height=block_height, width=60,
                                    x=600, y=current_node_y, out_y=20, inputs=inputs)
            self.elements_xml.append(block_xml)
            return block_id

        return 0

    # ==========================================
    # 5. IF 转换为 SEL 选择器
    # ==========================================
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
                    g_id = self._parse_expr(cond)
                    self.current_y += 30
                    in1_id = self._parse_expr(then_stmt.get("value"))
                    self.current_y += 30
                    in0_id = self._parse_expr(else_stmt.get("value"))

                    sel_block_id = self.get_id()
                    inputs = [
                        {"name": "G", "y": 20, "ref_id": g_id},
                        {"name": "IN0", "y": 40, "ref_id": in0_id},
                        {"name": "IN1", "y": 60, "ref_id": in1_id}
                    ]
                    sel_xml = self.render("block", local_id=sel_block_id, type_name="SEL", height=80, width=40,
                                          x=500, y=self.current_y - 60, out_y=30, inputs=inputs)
                    self.elements_xml.append(sel_xml)
                    self._build_out_variable(target_then, sel_block_id)