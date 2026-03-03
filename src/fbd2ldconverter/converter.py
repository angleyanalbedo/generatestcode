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
        # ElementTree 处理带 xmlns 的 XML 时，必须使用命名空间字典
        ns_map = {'ns': NS, 'xsi': XSI}

        root = ET.fromstring(fbd_xml_string)

        # 1. 修改容器类型 FBD -> LD
        for body in root.findall(".//ns:BodyContent", ns_map):
            if body.attrib.get(f"{{{XSI}}}type") == "FBD":
                body.set(f"{{{XSI}}}type", "LD")

        # 2. 遍历并处理所有 Network
        for network in root.findall(".//ns:Network", ns_map):
            self._transform_network(network, ns_map)

        # 补回 XML 声明头并输出
        return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")

    def _transform_network(self, network: ET.Element, ns_map: dict):
        # --- A. 准备左/右电源线 ---
        left_rail_id = self._get_id()
        right_rail_id = self._get_id()

        left_rail = ET.Element(f"{{{NS}}}LeftPowerRail", localId=left_rail_id)
        ET.SubElement(left_rail, f"{{{NS}}}Position", x="10", y="50")
        ET.SubElement(left_rail, f"{{{NS}}}ConnectionPointOut", formalParameter="")

        right_rail = ET.Element(f"{{{NS}}}RightPowerRail", localId=right_rail_id)
        ET.SubElement(right_rail, f"{{{NS}}}Position", x="1000", y="50")
        right_cpi = ET.SubElement(right_rail, f"{{{NS}}}ConnectionPointIn")

        coils_out_ids = []  # 记录需要连到右电源线的线圈 ID

        # --- B. 遍历并替换图元 ---
        for obj in network.findall(".//ns:FbdObject", ns_map):
            xsi_type = obj.attrib.get(f"{{{XSI}}}type")

            if xsi_type == "DataSource":
                # 1. DataSource -> Contact (触点)
                obj.tag = f"{{{NS}}}Contact"
                obj.set("variable", obj.get("identifier", "VAR"))
                obj.attrib.pop("identifier", None)
                obj.attrib.pop(f"{{{XSI}}}type", None)

                # FBD 的 DataSource 只有输出，LD 的 Contact 需要输入端连到左电源线
                cpi = ET.Element(f"{{{NS}}}ConnectionPointIn")
                ET.SubElement(cpi, f"{{{NS}}}RelPosition", x="0", y="10")
                ET.SubElement(cpi, f"{{{NS}}}Connection", refLocalId=left_rail_id)  # 默认直连左电源
                obj.insert(0, cpi)  # 插入到最前面

            elif xsi_type == "DataSink":
                # 2. DataSink -> Coil (线圈)
                obj.tag = f"{{{NS}}}Coil"
                obj.set("variable", obj.get("identifier", "VAR"))
                obj.attrib.pop("identifier", None)
                obj.attrib.pop(f"{{{XSI}}}type", None)

                # FBD 的 DataSink 只有输入，LD 的 Coil 需要输出端连到右电源线
                cpo_id = self._get_id()
                cpo = ET.SubElement(obj, f"{{{NS}}}ConnectionPointOut", localId=cpo_id)
                ET.SubElement(cpo, f"{{{NS}}}RelPosition", x="20", y="10")
                coils_out_ids.append(cpo_id)

            elif xsi_type == "Block":
                # 3. 功能块注入 EN/ENO 引脚
                obj.tag = f"{{{NS}}}Block"
                obj.attrib.pop(f"{{{XSI}}}type", None)

                # 注入 EN (使能输入)，默认连到左电源线
                in_vars = obj.find("ns:InputVariables", ns_map)
                if in_vars is None:
                    in_vars = ET.SubElement(obj, f"{{{NS}}}InputVariables")

                en_var = ET.Element(f"{{{NS}}}Variable", formalParameter="EN")
                en_cpi = ET.SubElement(en_var, f"{{{NS}}}ConnectionPointIn")
                ET.SubElement(en_cpi, f"{{{NS}}}Connection", refLocalId=left_rail_id)
                in_vars.insert(0, en_var)

                # 注入 ENO (使能输出)
                out_vars = obj.find("ns:OutputVariables", ns_map)
                if out_vars is None:
                    out_vars = ET.SubElement(obj, f"{{{NS}}}OutputVariables")

                eno_var = ET.Element(f"{{{NS}}}Variable", formalParameter="ENO")
                ET.SubElement(eno_var, f"{{{NS}}}ConnectionPointOut", localId=self._get_id())
                out_vars.insert(0, eno_var)

        # --- C. 缝合网络尾部 ---
        # 将所有线圈的输出引脚，连接到右电源线
        for cpo_id in coils_out_ids:
            ET.SubElement(right_cpi, f"{{{NS}}}Connection", refLocalId=cpo_id)

        # 把生成的电源线注入到 Network 头尾
        network.insert(0, left_rail)
        network.append(right_rail)