LD_XML_TEMPLATES = {
    # 根模板复用 FBD 的即可
    "project_root": """<?xml version="1.0" encoding="utf-8"?>
<Project xmlns="www.iec.ch/public/TC65SC65BWG7TF10" schemaVersion="1.0">
  <Types><GlobalNamespace>\n{{ pous_xml_content }}\n</GlobalNamespace></Types>
</Project>""",

    # 🌟 核心差异 1：xsi:type="LD"
    "pou_fragment": """      <{{ unit_type }} name="{{ name }}">
        <MainBody>
          <BodyContent xsi:type="LD">
{{ networks_str }}
          </BodyContent>
        </MainBody>
      </{{ unit_type }}>""",

    "network": """            <Network evaluationOrder="{{ order }}">
{{ elements_str }}
            </Network>""",

    # 🌟 核心差异 2：电源线、触点和线圈
    "left_rail": """              <LeftPowerRail localId="{{ id }}">
                <Position x="10" y="{{ y }}" />
                <ConnectionPointOut formalParameter="">
                  <RelPosition x="10" y="20" />
                </ConnectionPointOut>
              </LeftPowerRail>""",

    "right_rail": """              <RightPowerRail localId="{{ id }}">
                <Position x="800" y="{{ y }}" />
                <ConnectionPointIn>
                  <RelPosition x="0" y="20" />
                  <Connection refLocalId="{{ connected_id }}" />
                </ConnectionPointIn>
              </RightPowerRail>""",

    "contact": """              <Contact localId="{{ id }}" variable="{{ name }}">
                <Position x="{{ x }}" y="{{ y }}" />
                <ConnectionPointIn>
                  <RelPosition x="0" y="20" />
                  <Connection refLocalId="{{ in_connected_id }}" />
                </ConnectionPointIn>
                <ConnectionPointOut>
                  <RelPosition x="20" y="20" />
                </ConnectionPointOut>
              </Contact>""",

    "coil": """              <Coil localId="{{ id }}" variable="{{ name }}">
                <Position x="{{ x }}" y="{{ y }}" />
                <ConnectionPointIn>
                  <RelPosition x="0" y="20" />
                  <Connection refLocalId="{{ in_connected_id }}" />
                </ConnectionPointIn>
                <ConnectionPointOut>
                  <RelPosition x="20" y="20" />
                </ConnectionPointOut>
              </Coil>"""
}