from antlr4 import InputStream, CommonTokenStream

from ..generated.IEC61131Lexer import IEC61131Lexer
from ..generated.IEC61131Parser import IEC61131Parser
from .preprocess import preprocess_st


def parse_st_code(code: str):
    #做预处理
    code = preprocess_st(code)
    """
    把 ST 源码字符串解析成 ANTLR 的 parse tree。
    """
    input_stream = InputStream(code)
    lexer = IEC61131Lexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = IEC61131Parser(token_stream)
    tree = parser.start()  # 对应 IEC61131Parser.g4 里的 start 规则
    return tree
