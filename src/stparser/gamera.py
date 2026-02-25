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

    # --- 显式定义不区分大小写的关键字 (Terminals) ---
    PROGRAM: /PROGRAM/i
    END_PROGRAM: /END_PROGRAM/i
    FUNCTION_BLOCK: /FUNCTION_BLOCK/i
    END_FUNCTION_BLOCK: /END_FUNCTION_BLOCK/i
    FUNCTION: /FUNCTION/i
    END_FUNCTION: /END_FUNCTION/i

    VAR: /VAR(?![_a-zA-Z0-9])/i
    VAR_INPUT: /VAR_INPUT/i
    VAR_OUTPUT: /VAR_OUTPUT/i
    VAR_IN_OUT: /VAR_IN_OUT/i
    VAR_TEMP: /VAR_TEMP/i
    VAR_GLOBAL: /VAR_GLOBAL/i
    VAR_EXTERNAL: /VAR_EXTERNAL/i
    END_VAR: /END_VAR/i

    IF: /IF/i
    THEN: /THEN/i
    ELSIF: /ELSIF/i
    ELSE: /ELSE/i
    END_IF: /END_IF/i

    CASE: /CASE/i
    OF: /OF/i
    END_CASE: /END_CASE/i

    FOR: /FOR/i
    TO: /TO/i
    BY: /BY/i
    DO: /DO/i
    END_FOR: /END_FOR/i

    WHILE: /WHILE/i
    END_WHILE: /END_WHILE/i

    RETURN: /RETURN/i
    NOT: /NOT/i
    AND: /AND/i
    OR: /OR/i

    ARRAY: /ARRAY/i
    STRUCT: /STRUCT/i
    END_STRUCT: /END_STRUCT/i
    STRING: /STRING/i

    IDENT: /[a-zA-Z_]\w*/
    TYPE: /BOOL|INT|UINT|DINT|REAL|LREAL|TIME|WORD|DWORD|STRING|BYTE/i

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