# ==========================================
# 工业级 IEC 61131-3 EBNF 语法定义 (完全体)
# ==========================================
ST_GRAMMAR = r"""
    ?start: program_unit

    ?program_unit: fb_decl | function_decl | program_decl

    program_decl: "PROGRAM" IDENT var_block* body "END_PROGRAM"

    fb_decl: "FUNCTION_BLOCK" IDENT var_block* body "END_FUNCTION_BLOCK"
    function_decl: "FUNCTION" IDENT ":" type_def var_block* body "END_FUNCTION"

    var_block: ("VAR" | "VAR_INPUT" | "VAR_OUTPUT" | "VAR_IN_OUT" | "VAR_TEMP") var_decl+ "END_VAR"

    // --- 升级：支持复杂的变量类型定义 (ARRAY, STRUCT) ---
    ?type_def: TYPE
             | IDENT
             | "STRING" ["(" NUMBER ")"]
             | "ARRAY" "[" NUMBER ".." NUMBER "]" "OF" type_def
             | "STRUCT" var_decl+ "END_STRUCT"

    var_decl: IDENT ":" type_def [":=" expr] ";"
    // --------------------------------------------------

    body: (stmt)*

    ?stmt: assign_stmt 
         | if_stmt 
         | case_stmt 
         | for_stmt 
         | while_stmt
         | func_call
         | "RETURN" ";" -> return_stmt  // 新增：支持 RETURN 语句

    assign_stmt: IDENT ":=" expr ";"

    if_stmt: "IF" expr "THEN" body ("ELSIF" expr "THEN" body)* ["ELSE" body] "END_IF" ";"

    case_stmt: "CASE" expr "OF" (case_selection)+ ["ELSE" body] "END_CASE" ";"
    case_selection: case_list ":" body
    case_list: (NUMBER | IDENT) ("," (NUMBER | IDENT))*

    for_stmt: "FOR" IDENT ":=" expr "TO" expr ["BY" expr] "DO" body "END_FOR" ";"
    while_stmt: "WHILE" expr "DO" body "END_WHILE" ";"

    // --- 升级：支持标准的带 := 的功能块传参 ---
    func_call: IDENT "(" [param_list] ")" ";"

    ?param_list: formal_param_list | informal_param_list
    informal_param_list: expr ("," expr)*
    formal_param_list: formal_param ("," formal_param)*
    formal_param: IDENT ":=" expr
    // ------------------------------------------

    // --- 升级：支持 <=, >= 等运算符 ---
    ?expr: term
         | expr "+" term   -> add
         | expr "-" term   -> sub
         | expr ">" term   -> gt
         | expr "<" term   -> lt
         | expr ">=" term  -> ge
         | expr "<=" term  -> le
         | expr "=" term   -> eq
         | expr "<>" term  -> ne
         | expr "AND" term -> and_op
         | expr "OR" term  -> or_op

    ?term: factor
         | term "*" factor -> mul
         | term "/" factor -> div

    // --- 升级：支持函数调用、工业字面量 (T#1s) 和负数 ---
    ?factor: NUMBER        -> num
           | ST_LITERAL    -> literal
           | "-" factor    -> neg_op
           | IDENT         -> var
           | "(" expr ")"
           | "NOT" factor  -> not_op
           | IDENT "(" [param_list] ")" -> expr_func_call
    // ----------------------------------------------------

    IDENT: /[a-zA-Z_]\w*/
    TYPE: "BOOL" | "INT" | "UINT" | "DINT" | "REAL" | "LREAL" | "TIME" | "WORD" | "DWORD" | "STRING" | "BYTE"

    // 匹配工业专有字面量，如 T#10ms, 16#FFFF
    ST_LITERAL: /[a-zA-Z_0-9]+#[a-zA-Z_0-9\.\-]+/

    %import common.NUMBER
    %import common.WS
    %import common.CPP_COMMENT
    %import common.C_COMMENT
    %ignore WS
    %ignore CPP_COMMENT
    %ignore C_COMMENT

    // 匹配 IEC 61131-3 专有块注释 (* ... *)
    ST_COMMENT: "(*" /(.|\n)*?/ "*)"
    %ignore ST_COMMENT
"""