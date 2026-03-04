LD_XML_TEMPLATES = {
    # 根模板保持不变
    "project_root": """<?xml version="1.0" encoding="utf-8"?>
<Project xmlns="www.iec.ch/public/TC65SC65BWG7TF10" 
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
         schemaVersion="1.0">
  <FileHeader companyName="SyntheticDataGen" productName="LLM_AST_Unparser" productVersion="1.0"/>
  <ContentHeader name="LLM_Synthetic_Project" creationDateTime="2024-01-01T00:00:00">
    <CoordinateInfo><FbdScaling x="1" y="1"/></CoordinateInfo>
  </ContentHeader>
  <Types>
    <GlobalNamespace>
{{ pous_xml_content }}
    </GlobalNamespace>
  </Types>
  <Instances/>
</Project>""",

    # 容器声明为 LD
    "pou_fragment": """      <{{ unit_type }} name="{{ name }}">
        <MainBody>
          <BodyContent xsi:type="LD">
{{ networks_str }}
          </BodyContent>
        </MainBody>
      </{{ unit_type }}>""",

    # 🌟 核心差异 1：LD 的网络容器必须叫 Rung
    "network": """            <Rung evaluationOrder="{{ order }}">
{{ elements_str }}
            </Rung>""",

    # 🌟 核心差异 2：电源线必须是 LdObject 且使用 RelPosition 和 globalId
    "left_rail": """              <LdObject xsi:type="LeftPowerRail" globalId="OBJ_{{ id }}">
                <RelPosition x="10" y="{{ y }}" />
                <ConnectionPointOut connectionPointOutId="{{ out_id }}">
                  <RelPosition x="10" y="20" />
                </ConnectionPointOut>
              </LdObject>""",

    "right_rail": """              <LdObject xsi:type="RightPowerRail" globalId="OBJ_{{ id }}">
                <RelPosition x="1000" y="{{ y }}" />
                <ConnectionPointIn>
                  <RelPosition x="0" y="20" />
                  <Connection refConnectionPointOutId="{{ connected_out_id }}" />
                </ConnectionPointIn>
              </LdObject>""",

    # 🌟 核心差异 3：触点必须是 LdObject，变量名必须叫 operand，且严格保证标签顺序
    "contact": """              <LdObject xsi:type="Contact" globalId="OBJ_{{ id }}" operand="{{ name }}">
                <RelPosition x="{{ x }}" y="{{ y }}" />
                <ConnectionPointIn>
                  <RelPosition x="0" y="20" />
                  <Connection refConnectionPointOutId="{{ in_connected_out_id }}" />
                </ConnectionPointIn>
                <ConnectionPointOut connectionPointOutId="{{ out_id }}">
                  <RelPosition x="20" y="20" />
                </ConnectionPointOut>
              </LdObject>""",

    # 🌟 核心差异 4：线圈同理，必须叫 operand
    "coil": """              <LdObject xsi:type="Coil" globalId="OBJ_{{ id }}" operand="{{ name }}">
                <RelPosition x="{{ x }}" y="{{ y }}" />
                <ConnectionPointIn>
                  <RelPosition x="0" y="20" />
                  <Connection refConnectionPointOutId="{{ in_connected_out_id }}" />
                </ConnectionPointIn>
                <ConnectionPointOut connectionPointOutId="{{ out_id }}">
                  <RelPosition x="20" y="20" />
                </ConnectionPointOut>
              </LdObject>""",
    # 🌟 修复后的 block 模板：标签必须是 FbdObject
    "block": """              <FbdObject xsi:type="Block" typeName="{{ type_name }}" instanceName="{{ instance_name }}" globalId="OBJ_{{ id }}">
                <RelPosition x="{{ x }}" y="{{ y }}" />
                <InputVariables>
                  <InputVariable parameterName="EN">
                    <ConnectionPointIn>
                      <RelPosition x="0" y="0" />
                      <Connection refConnectionPointOutId="{{ en_connected_out_id }}" />
                    </ConnectionPointIn>
                  </InputVariable>
{% for pin in inputs %}
                  <InputVariable parameterName="{{ pin.name }}">
                    <ConnectionPointIn>
                      <RelPosition x="0" y="{{ pin.y }}" />
{% if pin.ref_out_id %}
                      <Connection refConnectionPointOutId="{{ pin.ref_out_id }}" />
{% endif %}
                    </ConnectionPointIn>
                  </InputVariable>
{% endfor %}
                </InputVariables>
                <OutputVariables>
                  <OutputVariable parameterName="ENO">
                    <ConnectionPointOut connectionPointOutId="{{ eno_out_id }}">
                      <RelPosition x="0" y="0" />
                    </ConnectionPointOut>
                  </OutputVariable>
{% for pin in outputs %}
                  <OutputVariable parameterName="{{ pin.name }}">
                    <ConnectionPointOut connectionPointOutId="{{ pin.out_id }}">
                      <RelPosition x="0" y="{{ pin.y }}" />
                    </ConnectionPointOut>
                  </OutputVariable>
{% endfor %}
                </OutputVariables>
              </FbdObject>""",
# 🌟 核心差异 5：用于给功能块传递非布尔值的数据源和数据池
    "data_source": """              <FbdObject xsi:type="DataSource" globalId="OBJ_{{ id }}" identifier="{{ name }}">
                <RelPosition x="{{ x }}" y="{{ y }}" />
                <ConnectionPointOut connectionPointOutId="{{ out_id }}">
                  <RelPosition x="20" y="10" />
                </ConnectionPointOut>
              </FbdObject>""",

    "data_sink": """              <FbdObject xsi:type="DataSink" globalId="OBJ_{{ id }}" identifier="{{ name }}">
                <RelPosition x="{{ x }}" y="{{ y }}" />
                <ConnectionPointIn>
                  <RelPosition x="0" y="10" />
                  <Connection refConnectionPointOutId="{{ in_connected_out_id }}" />
                </ConnectionPointIn>
              </FbdObject>"""
}