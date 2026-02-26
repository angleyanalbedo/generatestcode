from antlr4 import InputStream, CommonTokenStream
from antlr4.error.ErrorListener import ErrorListener

from stparser.anltr4.ast.builder import STAstBuilder
from utils import auto_repair
from stparser.anltr4.generated.IEC61131Lexer import IEC61131Lexer
from stparser.anltr4.generated.IEC61131Parser import IEC61131Parser


# ---------------------------------------------------------
# 1. 自定义错误监听器 (用于让 parser 返回失败状态)
# ---------------------------------------------------------
class STErrorListener(ErrorListener):
    def __init__(self):
        super(STErrorListener, self).__init__()
        self.errors = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        # 收集所有的语法错误
        self.errors.append(f"Line {line}:{column} - {msg}")




# ---------------------------------------------------------
# 3. 封装的 STParser 主类 (适配你的 pytest)
# ---------------------------------------------------------
class STParser:
    def preprocess_st(self, code: str) -> str:
        # 在这里放入你的预处理逻辑（如转大写、去特殊注释等）
        code = auto_repair(code)
        return code

    def get_ast(self, code: str) -> dict:
        try:
            code = self.preprocess_st(code)

            input_stream = InputStream(code)
            lexer = IEC61131Lexer(input_stream)
            token_stream = CommonTokenStream(lexer)
            parser = IEC61131Parser(token_stream)

            # 替换默认的错误监听器，防止它只在控制台打印而不抛出异常
            parser.removeErrorListeners()
            error_listener = STErrorListener()
            parser.addErrorListener(error_listener)

            # 1. 生成 Parse Tree
            tree = parser.start()

            # 2. 检查是否有语法错误
            if error_listener.errors:
                return {
                    "status": "fail",
                    "message": "Syntax Errors:\n" + "\n".join(error_listener.errors)
                }

            # 3. 如果成功，使用 Visitor 提取 AST
            visitor = STAstBuilder()
            ast = visitor.visit(tree)


            return {
                "status": "success",
                "ast": ast
                # "repaired_code": repaired_code # 如果有 auto_repair 逻辑可以返回
            }

        except Exception as e:
            return {
                "status": "fail",
                "message": f"Parser Crash: {str(e)}"
            }
