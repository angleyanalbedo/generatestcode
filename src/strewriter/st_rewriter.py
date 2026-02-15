class STRewriter(Transformer):
    """
    通过修改语法树来生成新的合成数据
    """
    def IDENT(self, token):
        # 1. 自动重命名变量：把 Start 改为 Input_Signal_1
        # 这能生成大量语义相同但形式不同的数据
        return token.update(value=f"renamed_{token.value}")

    def if_stmt(self, items):
        # 2. 逻辑变换：比如把简单的 IF 随机转换为 CASE
        # 或者反转 IF 的条件
        pass

# 使用方法
# tree = parser.parse(original_code)
# new_tree = STRewriter().transform(tree)
# new_code = new_tree.pretty() # Lark 提供的漂亮格式化输出