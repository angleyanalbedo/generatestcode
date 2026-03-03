from pathlib import Path

from st2xml.validtor.validtor import IEC61131Validator, ValidationException


def test_validator():
    """IEC 61131-10 验证器测试"""

    # 获取测试文件所在目录 (tests/)
    tests_dir = Path(__file__).parent

    # 项目根目录是 tests/ 的父目录
    project_root = tests_dir.parent

    # 文件路径配置（在 project_root/resource/xsd/ 下）
    xsd_path = project_root / "resource" / "xsd" / "IEC61131_10_Ed1_0.xsd"
    example_xml = project_root / "resource" / "xsd" / "IEC61131_10_Ed1_0_Example.xml"

    print(f"项目根目录: {project_root}")
    print(f"XSD 路径: {xsd_path}")
    print(f"XML 路径: {example_xml}")

    # 检查文件是否存在
    if not xsd_path.exists():
        raise FileNotFoundError(f"XSD 文件不存在: {xsd_path}")
    if not example_xml.exists():
        raise FileNotFoundError(f"XML 文件不存在: {example_xml}")

    # 1. 初始化验证器
    print(f"\n加载 XSD: {xsd_path.name}")
    validator = IEC61131Validator(xsd_path)
    print(f"Schema 版本: {validator.get_schema_info().get('schema_version', 'unknown')}")
    print("-" * 50)

    # 2. 验证示例文件
    print(f"\n验证示例文件: {example_xml.name}")
    is_valid, errors = validator.validate_file(example_xml)

    if not is_valid:
        print(f"❌ 验证失败，发现 {len(errors)} 个问题:")
        for err in errors:
            print(f"   {err}")
    else:
        print("✅ 示例文件验证通过")

    print("-" * 50)

    # 3. 验证自定义 XML 字符串
    print("\n验证自定义 XML 字符串...")
    xml_string = """<?xml version="1.0" encoding="UTF-8"?>
    <project xmlns="http://www.plcopen.org/xml/tc6_0200"
             xmlns:xsd="http://www.w3.org/2001/XMLSchema"
             xmlns:xhtml="http://www.w3.org/1999/xhtml">
        <fileHeader companyName="Example" productName="Test" 
                    productVersion="1.0" creationDateTime="2024-01-01T00:00:00Z"/>
        <contentHeader name="TestProject">
            <coordinateInfo>
                <fbd><scaling x="1" y="1"/></fbd>
                <ld><scaling x="1" y="1"/></ld>
                <sfc><scaling x="1" y="1"/></sfc>
            </coordinateInfo>
        </contentHeader>
        <types>
            <dataTypes/>
            <pous/>
        </types>
        <instances>
            <configurations/>
        </instances>
    </project>
    """

    is_valid, errors = validator.validate_string(xml_string)
    print(f"自定义 XML: {'✅ 通过' if is_valid else '❌ 失败'}")
    if errors:
        for err in errors[:3]:
            print(f"   {err}")

    print("-" * 50)

    # 4. 批量验证 project_root/resource/xsd/ 下所有 xml 文件
    print("\n批量验证...")
    xml_dir = project_root / "resource" / "xsd"
    xml_files = list(xml_dir.glob("*.xml"))

    if xml_files:
        print(f"发现 {len(xml_files)} 个 XML 文件:")
        for f in xml_files:
            print(f"   - {f.name}")

        results = validator.validate_batch(xml_files)
        print(f"\n批量验证结果: {results['passed']}/{results['total']} 通过")

        for detail in results["details"]:
            status = "✅" if detail["valid"] else "❌"
            print(f"{status} {detail['source']}")
            if not detail["valid"]:
                for err in detail["errors"][:2]:
                    print(f"      {err}")
    else:
        print("未找到 XML 文件")

    print("-" * 50)

    # 5. 严格模式测试
    print("\n严格模式测试...")
    try:
        validator.assert_valid(example_xml)
        print(f"✅ assert_valid: {example_xml.name} 验证通过")
    except ValidationException as e:
        print(f"❌ assert_valid 失败: {e}")


def test_single_file():
    """快速测试单个文件"""
    # 从 tests/ 目录找到项目根目录
    project_root = Path(__file__).parent.parent

    xsd_path = project_root / "resource" / "xsd" / "IEC61131_10_Ed1_0.xsd"
    example_xml = project_root / "resource" / "xsd" / "IEC61131_10_Ed1_0_Example.xml"

    print(f"XSD: {xsd_path}")
    print(f"XML: {example_xml}")

    validator = IEC61131Validator(xsd_path)
    is_valid, errors = validator.validate_file(example_xml)

    print(f"\n结果: {'✅ 有效' if is_valid else '❌ 无效'}")

    if errors:
        print(f"\n详细错误 ({len(errors)} 个):")
        for i, err in enumerate(errors, 1):
            print(f"{i}. [{err.severity.value}] 行{err.line}: {err.message}")
            if i >= 10:
                print(f"... 还有 {len(errors) - 10} 个错误")
                break

    return is_valid


if __name__ == "__main__":
    test_validator()
    # test_single_file()