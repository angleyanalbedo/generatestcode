ST_GRAMMAR = r"""
    ?start: program_unit

    ?program_unit: fb_decl | function_decl | program_decl

    program_decl: PROGRAM IDENT var_block* body END_PROGRAM

    fb_decl: FUNCTION_BLOCK IDENT var_block* body END_FUNCTION_BLOCK

    function_decl: FUNCTION IDENT ":" type_def var_block* body END_FUNCTION

    var_block: (VAR | VAR_INPUT | VAR_OUTPUT | VAR_IN_OUT | VAR_TEMP | VAR_GLOBAL | VAR_EXTERNAL) var_decl+ END_VAR

    ?type_def: TYPE
             | IDENT
             | STRING ["(" NUMBER ")"]
             | ARRAY "[" NUMBER ".." NUMBER "]" OF type_def
             | STRUCT var_decl+ END_STRUCT

    var_decl: IDENT ":" type_def [":=" expr] ";"

    body: (stmt)*

    ?stmt: assign_stmt 
         | if_stmt 
         | case_stmt 
         | for_stmt 
         | while_stmt
         | func_call
         | RETURN ";" -> return_stmt 

    assign_stmt: IDENT ":=" expr ";"

    if_stmt: IF expr THEN body (ELSIF expr THEN body)* [ELSE body] END_IF ";"

    case_stmt: CASE expr OF (case_selection)+ [ELSE body] END_CASE ";"
    case_selection: case_list ":" body
    case_list: (case_value) ("," (case_value))*
    ?case_value: NUMBER | IDENT

    for_stmt: FOR IDENT ":=" expr TO expr [BY expr] DO body END_FOR ";"
    while_stmt: WHILE expr DO body END_WHILE ";"

    func_call: IDENT "(" [param_list] ")" ";"

    ?param_list: formal_param_list | informal_param_list
    informal_param_list: expr ("," expr)*
    formal_param_list: formal_param ("," formal_param)*
    formal_param: IDENT ":=" expr

    ?expr: term
         | expr "+" term   -> add
         | expr "-" term   -> sub
         | expr ">" term   -> gt
         | expr "<" term   -> lt
         | expr ">=" term  -> ge
         | expr "<=" term  -> le
         | expr "=" term   -> eq
         | expr "<>" term  -> ne
         | expr AND term -> and_op
         | expr OR term  -> or_op

    ?term: factor
         | term "*" factor -> mul
         | term "/" factor -> div

    ?factor: NUMBER        -> num
           | ST_LITERAL    -> literal
           | "-" factor    -> neg_op
           | IDENT         -> var
           | "(" expr ")"
           | NOT factor    -> not_op
           | IDENT "(" [param_list] ")" -> expr_func_call

    # --- 显式定义不区分大小写的关键字 (增加单词边界 \b 防止误切变量名) ---
    PROGRAM:            /\bPROGRAM\b/i
    END_PROGRAM:        /\bEND_PROGRAM\b/i
    FUNCTION_BLOCK:     /\bFUNCTION_BLOCK\b/i
    END_FUNCTION_BLOCK: /\bEND_FUNCTION_BLOCK\b/i
    FUNCTION:           /\bFUNCTION\b/i
    END_FUNCTION:       /\bEND_FUNCTION\b/i
    
    # 特别注意：VAR 系列必须精准匹配
    VAR_INPUT:          /\bVAR_INPUT\b/i
    VAR_OUTPUT:         /\bVAR_OUTPUT\b/i
    VAR_IN_OUT:         /\bVAR_IN_OUT\b/i
    VAR_TEMP:           /\bVAR_TEMP\b/i
    VAR_GLOBAL:         /\bVAR_GLOBAL\b/i
    VAR_EXTERNAL:       /\bVAR_EXTERNAL\b/i
    VAR:                /\bVAR\b/i
    END_VAR:            /\bEND_VAR\b/i
    
    IF:                 /\bIF\b/i
    THEN:               /\bTHEN\b/i
    ELSIF:              /\bELSIF\b/i
    ELSE:               /\bELSE\b/i
    END_IF:             /\bEND_IF\b/i
    
    CASE:               /\bCASE\b/i
    OF:                 /\bOF\b/i
    END_CASE:           /\bEND_CASE\b/i
    
    FOR:                /\bFOR\b/i
    TO:                 /\bTO\b/i
    BY:                 /\bBY\b/i
    DO:                 /\bDO\b/i
    END_FOR:            /\bEND_FOR\b/i
    
    WHILE:              /\bWHILE\b/i
    END_WHILE:          /\bEND_WHILE\b/i
    
    RETURN:             /\bRETURN\b/i
    NOT:                /\bNOT\b/i
    AND:                /\bAND\b/i
    OR:                 /\bOR\b/i
    
    ARRAY:              /\bARRAY\b/i
    STRUCT:             /\bSTRUCT\b/i
    END_STRUCT:         /\bEND_STRUCT\b/i
    STRING:             /\bSTRING\b/i

    # 降低 IDENT 优先级，确保关键字优先匹配
    IDENT.0: /[a-zA-Z_][a-zA-Z0-9_]*/
    # --- 数据类型 ---
    TYPE: /\b(BOOL|INT|UINT|DINT|REAL|LREAL|TIME|WORD|DWORD|STRING|BYTE)\b/i

    ST_LITERAL: /[a-zA-Z_0-9]+#[a-zA-Z_0-9\.\-]+/

    %import common.NUMBER
    %import common.WS
    %import common.CPP_COMMENT
    %import common.C_COMMENT
    %ignore WS
    %ignore CPP_COMMENT
    %ignore C_COMMENT

    ST_COMMENT: "(*" /(.|\n)*?/ "*)"
    %ignore ST_COMMENT
"""