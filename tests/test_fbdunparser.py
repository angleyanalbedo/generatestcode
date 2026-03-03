from src.fbdunparser.unparser import FBDXmlUnparser
from src.xmlvalidtor import IEC61131Validator
import xml.dom.minidom
import xml.dom.minidom
from pathlib import Path


def test_fbdunparser():
    # 模拟从 STAstBuilder 解析出来的 AST 字典
    sample_ast = {
        "unit_type": "PROGRAM",
        "name": "Main",
        "body": [
            {
                "stmt_type": "assign",
                "target": {"expr_type": "var", "name": "Y"},
                "value": {
                    "expr_type": "binop",
                    "op": "AND",
                    "left": {"expr_type": "var", "name": "A"},
                    "right": {
                        "expr_type": "unaryop",
                        "op": "NOT",
                        "operand": {"expr_type": "var", "name": "B"}
                    }
                }
            },
            {
                "stmt_type": "if",
                "cond": {"expr_type": "var", "name": "C"},
                "then_body": [
                    {"stmt_type": "assign", "target": {"expr_type": "var", "name": "Z"},
                     "value": {"expr_type": "literal", "value": "10"}}
                ],
                "else_body": [
                    {"stmt_type": "assign", "target": {"expr_type": "var", "name": "Z"},
                     "value": {"expr_type": "literal", "value": "20"}}
                ]
            }
        ]
    }

    # 1. 运行转换器
    unparser = FBDXmlUnparser()
    xml_output = unparser.unparse_pou(sample_ast)

    # 2. XSD 校验
    tests_dir = Path(__file__).parent
    project_root = tests_dir.parent
    xsd_path = project_root / "resource" / "xsd" / "IEC61131_10_Ed1_0.xsd"

    # 假设你已经有了 IEC61131Validator 类
    validator = IEC61131Validator(xsd_path)
    is_valid, errors = validator.validate_string(xml_output)

    # ==========================================
    # 3. 输出美化 (Beautification)
    # ==========================================
    print("\n" + "=" * 60)
    print("🚀 FBD XML Unparser 转换测试")
    print("=" * 60)

    # 打印校验结果
    if is_valid:
        print("✅ XSD 校验状态 : [ PASSED ] 完美符合 IEC 61131-10 标准！")
    else:
        print("❌ XSD 校验状态 : [ FAILED ]")
        print("\n🚨 发现以下错误详情:")
        for i, error in enumerate(errors, 1):
            print(f"   {i}. {error}")

    print("-" * 60)
    print("📄 生成的 PLCopen XML (FBD 格式):")
    print("-" * 60)

    # # 尝试使用 minidom 对 XML 进行美化缩进打印
    # try:
    #     parsed_xml = xml.dom.minidom.parseString(xml_output)
    #     # 去除生成过程中产生的多余空行，使输出更紧凑
    #     pretty_xml = '\n'.join([line for line in parsed_xml.toprettyxml(indent="  ").split('\n') if line.strip()])
    #     print(pretty_xml)
    # except Exception as e:
    #     print(f"⚠️ XML 美化失败，打印原始输出 (错误: {e}):\n")
    #     print(xml_output.strip())

    print("=" * 60 + "\n")