"""
IEC 61131-10 XML 验证器
基于 lxml 的 XSD Schema 验证封装
"""

from pathlib import Path
from typing import Union, List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import logging

from lxml import etree


class ValidationSeverity(Enum):
    """验证错误严重级别"""
    ERROR = "error"
    WARNING = "warning"
    FATAL = "fatal"


@dataclass
class ValidationError:
    """验证错误信息"""
    message: str
    severity: ValidationSeverity
    line: Optional[int] = None
    column: Optional[int] = None
    domain: Optional[str] = None
    type_name: Optional[str] = None

    def __str__(self) -> str:
        location = f"第{self.line}行" if self.line else "未知位置"
        return f"[{self.severity.value.upper()}] {location}: {self.message}"


class IEC61131Validator:
    """
    IEC 61131-10 XML 验证器

    功能：
    - 加载 XSD Schema
    - 验证 XML 文件/字符串
    - 支持批量验证
    - 提供详细的错误报告
    """

    def __init__(self, xsd_path: Union[str, Path], use_cached: bool = True):
        """
        初始化验证器

        Args:
            xsd_path: XSD 文件路径
            use_cached: 是否缓存解析后的 Schema
        """
        self.xsd_path = Path(xsd_path)
        self._schema: Optional[etree.XMLSchema] = None
        self._use_cached = use_cached
        self._logger = logging.getLogger(__name__)

        if not self.xsd_path.exists():
            raise FileNotFoundError(f"XSD 文件不存在: {self.xsd_path}")

        self._load_schema()

    def _load_schema(self) -> None:
        """加载并解析 XSD Schema"""
        try:
            with open(self.xsd_path, 'rb') as f:
                xsd_content = f.read()

            xsd_doc = etree.fromstring(xsd_content)
            self._schema = etree.XMLSchema(xsd_doc)
            self._logger.info(f"成功加载 XSD: {self.xsd_path}")

        except etree.XMLSchemaParseError as e:
            raise ValueError(f"XSD 解析失败: {e}") from e
        except Exception as e:
            raise RuntimeError(f"加载 XSD 时发生错误: {e}") from e

    def _parse_xml(self, xml_source: Union[str, Path, bytes]) -> etree._Element:
        """
        解析 XML 源

        Args:
            xml_source: XML 文件路径、字符串或字节

        Returns:
            解析后的 Element
        """
        if isinstance(xml_source, (str, Path)) and Path(xml_source).exists():
            # 文件路径
            with open(xml_source, 'rb') as f:
                return etree.parse(f).getroot()
        elif isinstance(xml_source, (str, bytes)):
            # XML 字符串或字节
            if isinstance(xml_source, str):
                xml_source = xml_source.encode('utf-8')
            return etree.fromstring(xml_source)
        else:
            raise ValueError("不支持的 XML 源类型")

    def _create_error_from_log(self, error) -> ValidationError:
        """从 lxml 错误日志创建 ValidationError"""
        severity = ValidationSeverity.ERROR
        if error.level_name == "WARNING":
            severity = ValidationSeverity.WARNING
        elif error.level_name == "FATAL":
            severity = ValidationSeverity.FATAL

        return ValidationError(
            message=error.message,
            severity=severity,
            line=error.line,
            column=error.column,
            domain=error.domain_name,
            type_name=error.type_name
        )

    def validate(
            self,
            xml_source: Union[str, Path, bytes],
            raise_exception: bool = False
    ) -> tuple[bool, List[ValidationError]]:
        """
        验证单个 XML

        Args:
            xml_source: XML 文件路径、字符串或字节
            raise_exception: 验证失败时是否抛出异常

        Returns:
            (是否通过, 错误列表)
        """
        errors: List[ValidationError] = []

        try:
            xml_doc = self._parse_xml(xml_source)

            # 创建验证器上下文以捕获详细错误
            valid = self._schema.validate(xml_doc)

            if not valid:
                for error in self._schema.error_log:
                    errors.append(self._create_error_from_log(error))

        except etree.XMLSyntaxError as e:
            errors.append(ValidationError(
                message=f"XML 语法错误: {e}",
                severity=ValidationSeverity.FATAL,
                line=e.lineno,
                column=e.offset
            ))
            valid = False
        except Exception as e:
            errors.append(ValidationError(
                message=f"验证过程异常: {e}",
                severity=ValidationSeverity.FATAL
            ))
            valid = False

        if not valid and raise_exception and errors:
            raise ValidationException(errors)

        return valid, errors

    def validate_file(self, xml_path: Union[str, Path]) -> tuple[bool, List[ValidationError]]:
        """验证 XML 文件（便捷方法）"""
        return self.validate(xml_path)

    def validate_string(self, xml_string: str) -> tuple[bool, List[ValidationError]]:
        """验证 XML 字符串（便捷方法）"""
        return self.validate(xml_string)

    def validate_batch(
            self,
            xml_sources: List[Union[str, Path, bytes]],
            stop_on_first_error: bool = False
    ) -> Dict[str, Any]:
        """
        批量验证

        Args:
            xml_sources: XML 源列表
            stop_on_first_error: 遇到第一个错误时停止

        Returns:
            验证结果字典
        """
        results = {
            "total": len(xml_sources),
            "passed": 0,
            "failed": 0,
            "details": []
        }

        for idx, source in enumerate(xml_sources):
            source_name = str(source) if isinstance(source, (str, Path)) else f"source_{idx}"

            is_valid, errors = self.validate(source)

            detail = {
                "source": source_name,
                "valid": is_valid,
                "errors": errors
            }
            results["details"].append(detail)

            if is_valid:
                results["passed"] += 1
            else:
                results["failed"] += 1
                if stop_on_first_error:
                    break

        return results

    def assert_valid(self, xml_source: Union[str, Path, bytes]) -> None:
        """
        断言 XML 有效，无效时抛出异常

        Args:
            xml_source: XML 源

        Raises:
            ValidationException: 验证失败时
        """
        is_valid, errors = self.validate(xml_source, raise_exception=True)
        if not is_valid:
            raise ValidationException(errors)

    @property
    def schema(self) -> etree.XMLSchema:
        """获取底层 Schema 对象（高级用法）"""
        return self._schema

    def get_schema_info(self) -> Dict[str, Any]:
        """获取 Schema 信息"""
        return {
            "xsd_path": str(self.xsd_path),
            "schema_file": self.xsd_path.name,
            "schema_version": self._extract_version(),
        }

    def _extract_version(self) -> Optional[str]:
        """尝试从文件名提取版本"""
        # IEC61131_10_Ed1_0.xsd -> Ed1.0
        name = self.xsd_path.stem
        if "_Ed" in name:
            parts = name.split("_Ed")
            if len(parts) > 1:
                return f"Ed{parts[1].replace('_', '.')}"
        return None


class ValidationException(Exception):
    """验证异常"""

    def __init__(self, errors: List[ValidationError]):
        self.errors = errors
        self.error_count = len([e for e in errors if e.severity == ValidationSeverity.ERROR])
        self.warning_count = len([e for e in errors if e.severity == ValidationSeverity.WARNING])

        message = f"XML 验证失败: {self.error_count} 个错误, {self.warning_count} 个警告\n"
        message += "\n".join(str(e) for e in errors[:5])  # 显示前5个
        if len(errors) > 5:
            message += f"\n... 还有 {len(errors) - 5} 个错误"

        super().__init__(message)

    def get_errors(self, severity: Optional[ValidationSeverity] = None) -> List[ValidationError]:
        """获取指定级别的错误"""
        if severity is None:
            return self.errors
        return [e for e in self.errors if e.severity == severity]