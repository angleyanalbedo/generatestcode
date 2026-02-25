import re

from lark import Lark, exceptions

from stparser.lark.gamera import ST_GRAMMAR
from stanalyzer.lark_analyzer import STSemanticAnalyzer
from stparser.unparser import logger

# ==========================================
# 解析器类
# ==========================================

class STParser:
    def __init__(self):
        self.parser = Lark(ST_GRAMMAR, parser='lalr', propagate_positions=True, maybe_placeholders=False,
                           g_regex_flags=re.IGNORECASE)

    @staticmethod
    def preprocess(code: str) -> str:
        """预处理：清理干扰字符，统一换行符"""
        if not code: return ""
        # 很多从网上爬的代码带有不可见的 BOM 头或者奇怪的缩进
        code = code.lstrip('\ufeff')
        return code.strip().replace('\r\n', '\n')

    def parse(self, code: str):
        """核心解析逻辑，包含精细化的错误诊断"""
        clean_code = self.preprocess(code)
        try:
            return self.parser.parse(clean_code)

        except exceptions.UnexpectedToken as e:
            msg = f"Unexpected token '{e.token}' at line {e.line}, column {e.column}. Expected one of: {e.expected}"
            logger.warning(f"AST Parsing Failed: {msg}")
            return None, msg

        except exceptions.UnexpectedCharacters as e:
            msg = f"Unexpected character at line {e.line}, column {e.column}.\nContext: {e.get_context(clean_code)}"
            logger.warning(f"AST Parsing Failed: {msg}")
            return None, msg

        except exceptions.LarkError as e:
            msg = f"General Parsing Error: {str(e)}"
            logger.error(msg)
            return None, msg

    def get_ast(self, code: str):
        """
        对外提供一键获取字典型 AST 的接口，屏蔽掉底层的 Tree 和 Transformer 逻辑。
        """
        result = self.parse(code)

        # 如果返回的是 tuple，说明 parse 阶段报错了
        if isinstance(result, tuple):
            return {"status": "error", "message": result[1]}

        if not result:
            return {"status": "error", "message": "Unknown parsing failure"}

        try:
            # 实例化你的分析器，把 Tree 洗成干净的 Dict
            analyzer = STSemanticAnalyzer()
            ast_dict = analyzer.transform(result)
            return {"status": "success", "ast": ast_dict}
        except Exception as e:
            logger.error(f"Semantic Transformation Error: {str(e)}")
            return {"status": "error", "message": f"Transformer Error: {str(e)}"}
