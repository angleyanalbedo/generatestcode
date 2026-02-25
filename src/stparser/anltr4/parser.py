from ast import AST

from antlr4 import InputStream, CommonTokenStream
from antlr4.error.ErrorListener import ErrorListener

from utils import auto_repair
from stparser.anltr4.generated.IEC61131Lexer import IEC61131Lexer
from stparser.anltr4.generated.IEC61131Parser import IEC61131Parser
from stparser.anltr4.generated.IEC61131ParserVisitor import IEC61131ParserVisitor



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
# 2. 自定义 AST 构建器 (Visitor 模式)
# ---------------------------------------------------------
class STAstBuilder(IEC61131ParserVisitor):
    """
    继承 ANTLR 生成的 Visitor 类。
    在这里重写各种 visit 方法，将 Parse Tree 转换为你的自定义字典 AST。
    """

    def visitStart(self, ctx: IEC61131Parser.StartContext):
        # 假设 start 规则下有多个 statement
        statements = []
        if ctx.children:
            for child in ctx.children:
                # 递归访问子节点
                child_ast = self.visit(child)
                if child_ast:
                    statements.append(child_ast)

        return {
            "node_type": "Program",
            "body": statements
        }

    # 举例：处理赋值语句 (假设你的 g4 文件里有 assignment 规则)
    def visitAssignment(self, ctx: IEC61131Parser.Assignment_statementContext):
        return {
            "node_type": "Assignment",
            # .getText() 获取原始文本
            "left": ctx.variable().getText() if ctx.variable() else None,
            # 递归解析右侧表达式
            "right": self.visit(ctx.expression()) if ctx.expression() else None
        }

    # 如果某个节点没有被重写，默认会调用 visitChildren
    # 你可以根据你的 g4 文件中的规则名 (如 if_statement, for_loop 等)
    # 继续添加 visitIf_statement 等方法。


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

            # 4. (可选) 代码修复/重写演示
            # 如果你想在解析时自动补全某些符号，可以使用 TokenStreamRewriter
            # rewriter = TokenStreamRewriter(token_stream)
            # 例如: rewriter.insertAfter(tree.stop.tokenIndex, ";")
            # repaired_code = rewriter.getDefaultText()

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
