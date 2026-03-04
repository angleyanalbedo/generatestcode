import xml.etree.ElementTree as ET

# 注册命名空间，确保输出的 XML 干净，不带多余的 ns0: 前缀
NS = "www.iec.ch/public/TC65SC65BWG7TF10"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
ET.register_namespace("", NS)
ET.register_namespace("xsi", XSI)


class FbdToLdConverter:
    def __init__(self):
        # 使用一个独立的计数器生成 LD 特有的本地 ID，避免与原 XML ID 冲突
        self.ld_id_counter = 90000

    def _get_id(self) -> str:
        self.ld_id_counter += 1
        return str(self.ld_id_counter)

    def convert(self, fbd_xml_string: str) -> str:
        ns_map = {'ns': NS, 'xsi': XSI}
        root = ET.fromstring(fbd_xml_string)

        # 修改容器类型 FBD -> LD
        for body in root.findall(".//ns:BodyContent", ns_map):
            if body.attrib.get(f"{{{XSI}}}type") == "FBD":
                body.set(f"{{{XSI}}}type", "LD")

        # 遍历并处理所有 Network
        for network in root.findall(".//ns:Network", ns_map):
            self._transform_network(network, ns_map)

            # 🌟 修复点：将 FBD 的 Network 标签重命名为 LD 的 Rung 标签
            network.tag = f"{{{NS}}}Rung"

        return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")

    def _transform_network(self, network: ET.Element, ns_map: dict):
        # 1. 容器重命名：根据 XSD 第 107 行，LadderRung 在 LD 中名为 Rung
        network.tag = f"{{{NS}}}Rung"

        left_rail_id = self._get_id()
        left_rail_out_id = self._get_id()
        right_rail_id = self._get_id()

        # 2. 🌟 生成左电源线：必须继承 LdObjectBase (XSD 行 136)
        left_rail = ET.Element(f"{{{NS}}}LdObject", globalId=f"OBJ_{left_rail_id}")
        left_rail.set(f"{{{XSI}}}type", "LeftPowerRail")
        ET.SubElement(left_rail, f"{{{NS}}}RelPosition", x="10", y="50")

        cpo_left = ET.SubElement(left_rail, f"{{{NS}}}ConnectionPointOut", connectionPointOutId=left_rail_out_id)
        ET.SubElement(cpo_left, f"{{{NS}}}RelPosition", x="10", y="20")

        # 3. 🌟 生成右电源线：(XSD 行 136-137)
        right_rail = ET.Element(f"{{{NS}}}LdObject", globalId=f"OBJ_{right_rail_id}")
        right_rail.set(f"{{{XSI}}}type", "RightPowerRail")
        ET.SubElement(right_rail, f"{{{NS}}}RelPosition", x="1000", y="50")

        right_cpi = ET.SubElement(right_rail, f"{{{NS}}}ConnectionPointIn")
        ET.SubElement(right_cpi, f"{{{NS}}}RelPosition", x="0", y="20")

        coils_out_ids = []

        # 4. 遍历处理原本的 FbdObject
        for obj in network.findall(".//ns:FbdObject", ns_map):
            xsi_type = obj.attrib.get(f"{{{XSI}}}type")

            if xsi_type == "DataSource":
                # 🌟 XSD 行 139-140：Contact 必须叫 LdObject，且属性名为 operand
                obj.tag = f"{{{NS}}}LdObject"
                obj.set(f"{{{XSI}}}type", "Contact")
                obj.set("operand", obj.get("identifier", "VAR"))
                obj.attrib.pop("identifier", None)

                # 严格遵守顺序：RelPosition -> ConnectionPointIn -> ConnectionPointOut
                cpi = ET.Element(f"{{{NS}}}ConnectionPointIn")
                ET.SubElement(cpi, f"{{{NS}}}RelPosition", x="0", y="10")
                ET.SubElement(cpi, f"{{{NS}}}Connection", refConnectionPointOutId=left_rail_out_id)

                # FBD 的 DataSource 已经有 RelPosition(索引0) 和 ConnectionPointOut(索引1)
                # 插入到索引 1，确保符合 XSD 的顺序要求
                rel_pos = obj.find(f"{{{NS}}}RelPosition")
                insert_idx = list(obj).index(rel_pos) + 1 if rel_pos is not None else 0
                obj.insert(insert_idx, cpi)

            elif xsi_type == "DataSink":
                # 🌟 XSD 行 137-139：Coil 的属性名也是 operand
                obj.tag = f"{{{NS}}}LdObject"
                obj.set(f"{{{XSI}}}type", "Coil")
                obj.set("operand", obj.get("identifier", "VAR"))
                obj.attrib.pop("identifier", None)

                # Coil 需要在末尾追加 ConnectionPointOut
                cpo_id = self._get_id()
                cpo = ET.SubElement(obj, f"{{{NS}}}ConnectionPointOut", connectionPointOutId=cpo_id)
                ET.SubElement(cpo, f"{{{NS}}}RelPosition", x="20", y="10")
                coils_out_ids.append(cpo_id)

            elif xsi_type == "Block":
                # 🌟 XSD 行 107：LadderRung 允许内部直接存在 FbdObject，所以 Block 不需要改名
                in_vars = obj.find("ns:InputVariables", ns_map)
                if in_vars is None:
                    in_vars = ET.SubElement(obj, f"{{{NS}}}InputVariables")

                # XSD 行 125/132：引脚必须叫 InputVariable / OutputVariable，属性叫 parameterName
                en_var = ET.Element(f"{{{NS}}}InputVariable", parameterName="EN")
                en_cpi = ET.SubElement(en_var, f"{{{NS}}}ConnectionPointIn")
                ET.SubElement(en_cpi, f"{{{NS}}}RelPosition", x="0", y="0")
                ET.SubElement(en_cpi, f"{{{NS}}}Connection", refConnectionPointOutId=left_rail_out_id)
                in_vars.insert(0, en_var)

                out_vars = obj.find("ns:OutputVariables", ns_map)
                if out_vars is None:
                    out_vars = ET.SubElement(obj, f"{{{NS}}}OutputVariables")

                eno_var = ET.Element(f"{{{NS}}}OutputVariable", parameterName="ENO")
                eno_cpo = ET.SubElement(eno_var, f"{{{NS}}}ConnectionPointOut", connectionPointOutId=self._get_id())
                ET.SubElement(eno_cpo, f"{{{NS}}}RelPosition", x="0", y="0")
                out_vars.insert(0, eno_var)

        # 5. 所有线圈连接到右电源线
        for cpo_id in coils_out_ids:
            ET.SubElement(right_cpi, f"{{{NS}}}Connection", refConnectionPointOutId=cpo_id)

        # 6. 梯级头尾插入电源线
        network.insert(0, left_rail)
        network.append(right_rail)