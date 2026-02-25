import random

from lark import Token

from strewriter.st_rewriter import STRewriter


def run_tests():
    # 固定随机种子，确保测试结果可复现
    random.seed(42)
    rewriter = STRewriter(rename_map={"oldVar": "newVar"})

    print("=== 测试 1: IDENT 变量重命名 ===")
    t1 = rewriter.IDENT(Token("IDENT", "oldVar"))  # 命中 rename_map
    t2 = rewriter.IDENT(Token("IDENT", "motorSpeed"))  # 未命中，且不是全大写 (触发 var_ 前缀)
    t3 = rewriter.IDENT(Token("IDENT", "MAX_LIMIT"))  # 全大写，保持原样
    print(f"oldVar     -> {t1}")
    print(f"motorSpeed -> {t2}")
    print(f"MAX_LIMIT  -> {t3}")
    print()

    print("=== 测试 2: assign_stmt 算术交换 ===")
    # 模拟 AST: A := B + 1
    assign_items = ["A", {"type": "bin_op", "op": "+", "left": "B", "right": "1"}]
    res_assign = rewriter.assign_stmt(assign_items)
    print("原表达式: B + 1")
    print("变换后  :", f"{res_assign['expr']['left']} {res_assign['expr']['op']} {res_assign['expr']['right']}")
    print()

    print("=== 测试 3: if_stmt 条件反转 ===")
    # 模拟 AST: IF (X>0) THEN {Do_A} ELSE {Do_B}
    if_items = ["X>0", "Do_A", "Do_B"]
    res_if = rewriter.if_stmt(if_items)
    print("原逻辑: IF X>0 THEN Do_A ELSE Do_B")
    print("变换后: IF", res_if["condition"], "THEN", res_if["then_branch"], "ELSE", res_if["else_branch"])
    print()

    print("=== 测试 4: body 指令重排 (依赖分析) ===")
    # 构造 3 条语句：
    # stmt1: A := 1         (写 A)
    # stmt2: B := 2         (写 B)
    # stmt3: C := A + B     (读 A, B， 写 C)
    # 理论上：stmt1 和 stmt2 互不依赖，可以交换顺序。但 stmt3 绝对不能跑到它们前面去！
    stmt1 = {"id": "A:=1", "reads": set(), "writes": {"A"}}
    stmt2 = {"id": "B:=2", "reads": set(), "writes": {"B"}}
    stmt3 = {"id": "C:=A+B", "reads": {"A", "B"}, "writes": {"C"}}

    body_items = [stmt1, stmt2, stmt3]
    print("原顺序:", [s["id"] for s in body_items])

    # 我们运行 5 次，看看它怎么排
    for i in range(5):
        shuffled = rewriter.body(body_items)
        print(f"打乱 {i + 1} :", [s["id"] for s in shuffled])


if __name__ == "__main__":
    run_tests()