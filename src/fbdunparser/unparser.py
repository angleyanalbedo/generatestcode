from jinja2 import Environment, DictLoader
from typing import List, Dict, Any

# ==========================================
# 1. 严格基于 IEC 61131-10 的 Jinja2 模板
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
    全方位诊断雷达版 FBD 还原器
    """
    def __init__(self):
        self.id_counter = 0
        self.current_y = 50
        self.network_order = 0
        self.env = Environment(loader=DictLoader(XML_TEMPLATES), trim_blocks=True, lstrip_blocks=True)

    def get_id(self) -> str:
        self.id_counter += 1
        return str(self.id_counter)

    def render(self, template_name: str, **kwargs) -> str:
        return self.env.get_template(template_name).render(**kwargs)

    # ==========================================
    # 🛡️ 核心防雷：深度拍平压路机
    # ==========================================
    def _flatten_ast(self, obj: Any) -> List[Dict[str, Any]]:
        flat_list = []
        if isinstance(obj, dict):
            flat_list.append(obj)
        elif isinstance(obj, list):
            for item in obj:
                flat_list.extend(self._flatten_ast(item))
        return flat_list

    def _safe_dict(self, obj: Any) -> Dict[str, Any]:
        if isinstance(obj, dict):
            return obj
        if isinstance(obj, list):
            for item in obj:
                res = self._safe_dict(item)
                if res: return res
        return {}

    # ==========================================
    # 🌟 诊断版入口
    # ==========================================
    def unparse(self, ast_root: Any) -> str:
        pou_nodes = self._find_pou_nodes(ast_root)
        if not pou_nodes:
            # 🚨 诊断点 1：根本没找到 POU
            raise ValueError(f"[诊断: 找不到 POU (unit_type)] AST根节点结构: {str(ast_root)[:200]}...")
        return self.unparse_pou(pou_nodes[0])

    def _find_pou_nodes(self, node: Any) -> list:
        found = []
        if isinstance(node, dict):
            if "unit_type" in node:
                found.append(node)
            else:
                for val in node.values():
                    found.extend(self._find_pou_nodes(val))
        elif isinstance(node, list):
            for item in node:
                found.extend(self._find_pou_nodes(item))
        return found

    def unparse_pou(self, pou_node: Dict[str, Any]) -> str:
        pou_node = self._safe_dict(pou_node)
        pou_name = pou_node.get("name", "GeneratedPOU")

        raw_body = pou_node.get("body", [])
        flat_body = self._flatten_ast(raw_body)

        if not flat_body:
            # 🚨 诊断点 2：body 解析失败或为空
            raise ValueError(f"[诊断: Body为空] POU '{pou_name}' 的 body 解析出是空的。原始 body 数据: {str(raw_body)[:200]}")

        networks_xml = []
        for stmt in flat_body:
            # 遇到报错直接抛给上层测试脚本，不要拦截
            net = self.unparse_network(stmt)
            if net:
                networks_xml.append(net)

        if not networks_xml:
            raise ValueError(f"[诊断: 所有语句生成失败] POU '{pou_name}' 内没有生成任何合法的 Network。")

        networks_str = "\n".join(networks_xml)
        return self.render("project", pou_name=pou_name, networks_str=networks_str)

    # ==========================================
    # 3. 诊断版解析 Network
    # ==========================================
    def unparse_network(self, stmt_node: Any) -> str:
        stmt_node = self._safe_dict(stmt_node)
        if not stmt_node:
            raise ValueError(f"[诊断: 空语句节点] 传入了空字典或无法提取字典。节点: {stmt_node}")

        self.elements_xml = []
        self.current_y += 80
        stmt_type = stmt_node.get("stmt_type")

        if not stmt_type:
            # 🚨 诊断点 3：语句字典里居然没有 stmt_type
            raise ValueError(f"[诊断: 语句缺少 stmt_type] 节点内容: {str(stmt_node)[:150]}")

        if stmt_type == "assign":
            right_out_id = self._parse_expr(stmt_node.get("value"))
            target_dict = self._safe_dict(stmt_node.get("target"))
            target_name = target_dict.get("name", "UNKNOWN")
            self._build_data_sink(target_name, right_out_id)

        elif stmt_type == "if":
            self._parse_if_to_sel(stmt_node)

        elif stmt_type == "call":
            func_name = stmt_node.get("func_name", "UNKNOWN_FUNC")
            args = stmt_node.get("args", [])
            flat_args = self._flatten_ast(args) if isinstance(args, list) else [self._safe_dict(args)]

            inputs = []
            for i, arg in enumerate(flat_args):
                arg_out_id = self._parse_expr(arg)
                inputs.append({"name": f"IN{i + 1}", "y": 20 + i * 20, "ref_out_id": arg_out_id})
                self.current_y += 30

            global_id = self.get_id()
            out_pin_id = self.get_id()
            block_height = max(40, len(flat_args) * 20 + 20)

            block_xml = self.render("block", global_id=global_id, out_id=out_pin_id, type_name=func_name,
                                    height=block_height, width=60, x=400, y=self.current_y - 30, out_y=20,
                                    inputs=inputs)
            self.elements_xml.append(block_xml)

        else:
            # 🚨 诊断点 4：遇到了目前我们不支持的语句类型（比如 FOR, WHILE 等）
            raise ValueError(f"[诊断: 不支持的语句类型] 遇到了 '{stmt_type}'，由于无法映射为标准 FBD 数据流已被丢弃。节点: {str(stmt_node)[:150]}")

        if not self.elements_xml: return ""

        self.network_order += 1
        elements_str = "\n".join(self.elements_xml)
        return self.render("network", order=self.network_order, elements_str=elements_str)

    def _build_data_sink(self, target_name: str, connected_out_id: str):
        out_xml = self.render("data_sink", global_id=self.get_id(), y=self.current_y, connected_out_id=connected_out_id, name=target_name)
        self.elements_xml.append(out_xml)

    # ==========================================
    # 4. 诊断版解析表达式
    # ==========================================
    def _parse_expr(self, expr: Any) -> str:
        expr = self._safe_dict(expr)
        if not expr:
            raise ValueError(f"[诊断: 空表达式] 尝试解析一个空的或非法的表达式节点。")

        expr_type = expr.get("expr_type")
        current_node_y = self.current_y

        if not expr_type:
            # 🚨 诊断点 5：表达式缺少 expr_type
            raise ValueError(f"[诊断: 表达式缺少 expr_type] 节点内容: {str(expr)[:150]}")

        if expr_type in ("var", "literal"):
            name = expr.get("name", expr.get("value", ""))
            global_id = self.get_id()
            out_pin_id = self.get_id()
            in_xml = self.render("data_source", global_id=global_id, out_id=out_pin_id, y=current_node_y, name=name)
            self.elements_xml.append(in_xml)
            return out_pin_id

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
            flat_args = self._flatten_ast(args) if isinstance(args, list) else [self._safe_dict(args)]
            inputs = []
            for i, arg in enumerate(flat_args):
                arg_out_id = self._parse_expr(arg)
                inputs.append({"name": f"IN{i + 1}", "y": 20 + i * 20, "ref_out_id": arg_out_id})
                self.current_y += 30
            global_id = self.get_id()
            out_pin_id = self.get_id()
            block_height = max(40, len(flat_args) * 20 + 20)
            block_xml = self.render("block", global_id=global_id, out_id=out_pin_id, type_name=func_name,
                                    height=block_height, width=60, x=600, y=current_node_y, out_y=20, inputs=inputs)
            self.elements_xml.append(block_xml)
            return out_pin_id

        else:
            # 🚨 诊断点 6：遇到了不支持的表达式
            raise ValueError(f"[诊断: 不支持的表达式类型] '{expr_type}'。内容: {str(expr)[:150]}")


    def _parse_if_to_sel(self, stmt_node: Dict[str, Any]):
        cond = stmt_node.get("cond")
        then_body = stmt_node.get("then_body", [])
        else_body = stmt_node.get("else_body", [])

        if isinstance(then_body, list) and len(then_body) == 1 and isinstance(else_body, list) and len(else_body) == 1:
            then_stmt = self._safe_dict(then_body[0])
            else_stmt = self._safe_dict(else_body[0])

            if then_stmt.get("stmt_type") == "assign" and else_stmt.get("stmt_type") == "assign":
                t_name = self._safe_dict(then_stmt.get("target")).get("name")
                e_name = self._safe_dict(else_stmt.get("target")).get("name")

                if t_name == e_name and t_name:
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
                    self._build_data_sink(t_name, sel_out_pin_id)
                else:
                    raise ValueError(f"[诊断: IF转SEL失败] THEN 和 ELSE 赋值目标不一致或为空。THEN: '{t_name}', ELSE: '{e_name}'")
        else:
            # 🚨 诊断点 7：IF 结构太复杂，不符合我们简单的 SEL 转换要求
            raise ValueError(f"[诊断: IF语句过于复杂] 只有纯净的单条 if-else 赋值能转为 SEL 流图。")