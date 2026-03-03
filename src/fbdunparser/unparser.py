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
    终极对齐版 FBD 还原器：
    1. 具备 STUnparser 同等的递归解包能力
    2. 解决 'not callable' 导致的诊断中断
    3. 支持多 POU 扫描与 Network 级语料收割
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
    # 🛡️ 核心防雷：深度解包与拍平 (对齐 STUnparser 的容错性)
    # ==========================================
    def _force_dict(self, obj: Any) -> Dict[str, Any]:
        """递归剥壳：不管嵌套了多少层 list，只取核心 dict"""
        if isinstance(obj, dict):
            return obj
        if isinstance(obj, list) and len(obj) > 0:
            return self._force_dict(obj[0])
        return {}

    def _flatten_ast(self, obj: Any) -> List[Dict[str, Any]]:
        """拍平压路机：将嵌套语句提取为一维列表"""
        flat_list = []
        if isinstance(obj, dict):
            flat_list.append(obj)
        elif isinstance(obj, list):
            for item in obj:
                flat_list.extend(self._flatten_ast(item))
        return flat_list

    # ==========================================
    # 🌟 入口：多 POU 扫描雷达
    # ==========================================
    def unparse(self, ast_root: Any) -> str:
        pou_nodes = self._find_pou_nodes(ast_root)
        if not pou_nodes:
            raise ValueError("[诊断: 找不到POU] AST 结构中没有 unit_type 节点。")

        valid_pou_xmls = []
        last_err = ""
        for pou in pou_nodes:
            try:
                xml = self.unparse_pou(pou)
                if xml:
                    valid_pou_xmls.append(xml)
            except Exception as e:
                last_err = str(e)
                continue

        if not valid_pou_xmls:
            raise ValueError(f"[诊断: 所有 POU 被过滤] 扫描了 {len(pou_nodes)} 个 POU，最后报错: {last_err}")

        return valid_pou_xmls[0]

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

    # ==========================================
    # 🏗️ POU 解析与 Network 收割
    # ==========================================
    def unparse_pou(self, pou_node: Dict[str, Any]) -> str:
        pou_node = self._force_dict(pou_node)
        pou_name = pou_node.get("name", "GeneratedPOU")

        # 核心改进：深度拍平 body，防止 [[{...}]] 导致判断为空
        raw_body = pou_node.get("body", [])
        flat_body = self._flatten_ast(raw_body)

        if not flat_body:
            raise ValueError(f"[诊断: Body为空] POU '{pou_name}' 没有任何可执行语句。")

        networks_xml = []
        for stmt in flat_body:
            try:
                # 即使某行语句崩了，也跳过它继续处理后面的
                net = self.unparse_network(stmt)
                if net:
                    networks_xml.append(net)
            except Exception:
                continue

        if not networks_xml:
            raise ValueError(f"[诊断: 语句全被过滤] POU '{pou_name}' 内无合法数据流语句。")

        networks_str = "\n".join(networks_xml)
        return self.render("project", pou_name=pou_name, networks_str=networks_str)

    def unparse_network(self, stmt_node: Any) -> str:
        stmt_node = self._force_dict(stmt_node)
        if not stmt_node: return ""

        self.elements_xml = []
        self.current_y += 80
        stmt_type = stmt_node.get("stmt_type")

        if stmt_type == "assign":
            val_node = self._force_dict(stmt_node.get("value"))
            target_node = self._force_dict(stmt_node.get("target"))

            right_out_id = self._parse_expr(val_node)
            target_name = target_node.get("name", "UNKNOWN")
            self._build_data_sink(target_name, right_out_id)

        elif stmt_type == "if":
            if not self._parse_if_to_sel(stmt_node):
                return ""

        elif stmt_type == "call":
            func_name = stmt_node.get("func_name", "FUNC")
            args = stmt_node.get("args", [])
            flat_args = self._flatten_ast(args)

            inputs = []
            for i, arg in enumerate(flat_args):
                arg_out_id = self._parse_expr(arg)
                inputs.append({"name": f"IN{i + 1}", "y": 20 + i * 20, "ref_out_id": arg_out_id})
                self.current_y += 25

            global_id = self.get_id()
            out_pin_id = self.get_id()
            block_xml = self.render("block", global_id=global_id, out_id=out_pin_id,
                                    type_name=func_name, height=max(40, len(inputs) * 20),
                                    width=60, x=400, y=self.current_y - 20, out_y=20, inputs=inputs)
            self.elements_xml.append(block_xml)
        else:
            return ""

        if not self.elements_xml: return ""
        self.network_order += 1
        return self.render("network", order=self.network_order, elements_str="\n".join(self.elements_xml))

    # ==========================================
    # 🧬 表达式解析 (带自动剥壳)
    # ==========================================
    def _parse_expr(self, expr: Any) -> str:
        expr = self._force_dict(expr)
        if not expr: return "0"

        expr_type = expr.get("expr_type")
        if not expr_type: return "0"

        if expr_type in ("var", "literal"):
            name = expr.get("name", expr.get("value", "0"))
            global_id, out_id = self.get_id(), self.get_id()
            self.elements_xml.append(
                self.render("data_source", global_id=global_id, out_id=out_id, y=self.current_y, name=name))
            return out_id

        elif expr_type == "binop":
            op = expr.get("op", "+").upper()
            l_id = self._parse_expr(expr.get("left"))
            self.current_y += 30
            r_id = self._parse_expr(expr.get("right"))

            gid, oid = self.get_id(), self.get_id()
            inputs = [{"name": "IN1", "y": 20, "ref_out_id": l_id}, {"name": "IN2", "y": 40, "ref_out_id": r_id}]
            self.elements_xml.append(
                self.render("block", global_id=gid, out_id=oid, type_name=op, height=60, width=40, x=500,
                            y=self.current_y - 40, out_y=30, inputs=inputs))
            return oid

        elif expr_type == "call":
            # 嵌套调用递归处理
            args = self._flatten_ast(expr.get("args", []))
            inputs = []
            for i, arg in enumerate(args):
                inputs.append({"name": f"IN{i + 1}", "y": 20 + i * 20, "ref_out_id": self._parse_expr(arg)})

            gid, oid = self.get_id(), self.get_id()
            self.elements_xml.append(
                self.render("block", global_id=gid, out_id=oid, type_name=expr.get("func_name", "F"), height=60,
                            width=60, x=600, y=self.current_y, out_y=20, inputs=inputs))
            return oid

        return "0"

    def _parse_if_to_sel(self, stmt: Dict) -> bool:
        # (保持原有的 SEL 转换逻辑，但内部增加 _force_dict 保护)
        try:
            then_body = self._flatten_ast(stmt.get("then_body", []))
            else_body = self._flatten_ast(stmt.get("else_body", []))
            if len(then_body) == 1 and len(else_body) == 1:
                t_stmt, e_stmt = then_body[0], else_body[0]
                if t_stmt.get("stmt_type") == "assign" and e_stmt.get("stmt_type") == "assign":
                    t_target = self._force_dict(t_stmt.get("target")).get("name")
                    e_target = self._force_dict(e_stmt.get("target")).get("name")
                    if t_target == e_target and t_target:
                        g_id = self._parse_expr(stmt.get("cond"))
                        in1_id = self._parse_expr(t_stmt.get("value"))
                        in0_id = self._parse_expr(e_stmt.get("value"))

                        gid, oid = self.get_id(), self.get_id()
                        inputs = [{"name": "G", "y": 20, "ref_out_id": g_id},
                                  {"name": "IN0", "y": 40, "ref_out_id": in0_id},
                                  {"name": "IN1", "y": 60, "ref_out_id": in1_id}]
                        self.elements_xml.append(
                            self.render("block", global_id=gid, out_id=oid, type_name="SEL", height=80, width=40, x=500,
                                        y=self.current_y, out_y=30, inputs=inputs))
                        self._build_data_sink(t_target, oid)
                        return True
        except:
            pass
        return False

    def _build_data_sink(self, target_name: str, connected_out_id: str):
        self.elements_xml.append(
            self.render("data_sink", global_id=self.get_id(), y=self.current_y, connected_out_id=connected_out_id,
                        name=target_name))