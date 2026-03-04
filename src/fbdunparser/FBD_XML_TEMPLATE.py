# ==========================================
# 1. 严格基于 IEC 61131-10 的 Jinja2 模板
# ==========================================
XML_TEMPLATES = {
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

    # 🌟 POU 单体片段模板 (支持自适应标签)
    "pou_fragment": """      <{{ unit_type }} name="{{ name }}">
            <MainBody>
              <BodyContent xsi:type="FBD">
    {{ networks_str }}
              </BodyContent>
            </MainBody>
          </{{ unit_type }}>""",

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
