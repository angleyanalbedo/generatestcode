class FBDXmlUnparser:
    def __init__(self):
        self.local_id_counter = 0

    def get_id(self) -> int:
        self.local_id_counter += 1
        return self.local_id_counter

    def unparse_network(self, stmt_node) -> str:
        """
        将一条 ST 赋值语句转换为一个 PLCopen XML Network (FBD 格式)
        例如: Y := A AND B;
        """
        if stmt_node.get("stmt_type") != "assign":
            return ""  # 这里演示最核心的 assignment

        self.elements_xml = []

        # 1. 解析右值表达式 (构建运算块和输入变量)
        right_expr = stmt_node.get("value")
        # 返回该表达式输出引脚的 localId
        right_out_id = self._parse_expr(right_expr)

        # 2. 解析左值 (构建输出变量)
        target_name = stmt_node.get("target", {}).get("name", "UNKNOWN")
        out_var_id = self.get_id()
        in_pin_id = self.get_id()  # 输出变量也有一个输入引脚

        out_var_xml = f"""
            <outVariable localId="{out_var_id}" height="20" width="40">
              <position x="800" y="100" />
              <connectionPointIn>
                <relPosition x="0" y="10" />
                <connection refLocalId="{right_out_id}" />
              </connectionPointIn>
              <expression>{target_name}</expression>
            </outVariable>"""
        self.elements_xml.append(out_var_xml)

        # 3. 组装整个 Network
        network_xml = f"""
        <network>
          <FBD>
            {"".join(self.elements_xml)}
          </FBD>
        </network>"""
        return network_xml

    def _parse_expr(self, expr) -> int:
        """
        递归解析表达式，生成对应的 XML 元素，并返回当前元素的 localId 以供上一级连接
        """
        if not expr: return 0
        expr_type = expr.get("expr_type")

        # 处理变量 (叶子节点)
        if expr_type == "var" or expr_type == "literal":
            var_id = self.get_id()
            name = expr.get("name", expr.get("value", ""))

            var_xml = f"""
            <inVariable localId="{var_id}" height="20" width="40">
              <position x="100" y="100" />
              <connectionPointOut>
                <relPosition x="40" y="10" />
              </connectionPointOut>
              <expression>{name}</expression>
            </inVariable>"""
            self.elements_xml.append(var_xml)
            return var_id

        # 处理二元操作 (如 AND, OR, +, -)
        elif expr_type == "binop":
            op = expr.get("op", "").upper()

            # 递归解析左右子节点，获取它们的输出 ID
            left_id = self._parse_expr(expr.get("left"))
            right_id = self._parse_expr(expr.get("right"))

            block_id = self.get_id()

            # FBD Block 通常有两个输入 IN1, IN2，和一个输出 OUT
            block_xml = f"""
            <block localId="{block_id}" typeName="{op}" height="40" width="40">
              <position x="400" y="100" />
              <inputVariables>
                <variable formalParameter="IN1">
                  <connectionPointIn>
                    <relPosition x="0" y="10" />
                    <connection refLocalId="{left_id}" />
                  </connectionPointIn>
                </variable>
                <variable formalParameter="IN2">
                  <connectionPointIn>
                    <relPosition x="0" y="30" />
                    <connection refLocalId="{right_id}" />
                  </connectionPointIn>
                </variable>
              </inputVariables>
              <inOutVariables/>
              <outputVariables>
                <variable formalParameter="OUT">
                  <connectionPointOut>
                    <relPosition x="40" y="20" />
                  </connectionPointOut>
                </variable>
              </outputVariables>
            </block>"""
            self.elements_xml.append(block_xml)
            return block_id

        return 0