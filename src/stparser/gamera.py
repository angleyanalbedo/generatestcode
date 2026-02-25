ST_GRAMMAR = r"""
    ?start: program_unit

    ?program_unit: fb_decl | function_decl | program_decl

    program_decl: PROGRAM IDENT var_block* body END_PROGRAM

    fb_decl: FUNCTION_BLOCK IDENT var_block* body END_FUNCTION_BLOCK

    function_decl: FUNCTION IDENT ":" type_def var_block* body END_FUNCTION


    var_block: var_block_head var_decl+ END_VAR
    
    ?var_block_head: (VAR | VAR_INPUT | VAR_OUTPUT | VAR_IN_OUT | VAR_TEMP | VAR_GLOBAL | VAR_EXTERNAL) [var_qualifier]
    ?var_qualifier: CONSTANT | RETAIN | PERSISTENT

    ?type_def: TYPE_NAME
             | IDENT
             | ARRAY "[" NUMBER ".." NUMBER "]" OF type_def
             | STRUCT var_decl+ END_STRUCT

    TYPE_NAME: TYPE 
              | STRING ["(" NUMBER ")"]


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
    # --- 词法定义 (带优先级与边界保护) ---
    PROGRAM.2:            /\bPROGRAM\b/i
    END_PROGRAM.2:        /\bEND_PROGRAM\b/i
    FUNCTION_BLOCK.2:     /\bFUNCTION_BLOCK\b/i
    END_FUNCTION_BLOCK.2: /\bEND_FUNCTION_BLOCK\b/i
    FUNCTION.2:           /\bFUNCTION\b/i
    END_FUNCTION.2:       /\bEND_FUNCTION\b/i
    
    VAR_INPUT.2:          /\bVAR_INPUT\b/i
    VAR_OUTPUT.2:         /\bVAR_OUTPUT\b/i
    VAR_IN_OUT.2:         /\bVAR_IN_OUT\b/i
    VAR_TEMP.2:           /\bVAR_TEMP\b/i
    VAR_GLOBAL.2:         /\bVAR_GLOBAL\b/i
    VAR_EXTERNAL.2:       /\bVAR_EXTERNAL\b/i
    VAR.2:                /\bVAR\b/i
    END_VAR.2:            /\bEND_VAR\b/i
    
    CONSTANT.2:           /\bCONSTANT\b/i
    RETAIN.2:             /\bRETAIN\b/i
    PERSISTENT.2:         /\bPERSISTENT\b/i
    
    IF.2:                 /\bIF\b/i
    THEN.2:               /\bTHEN\b/i
    ELSIF.2:              /\bELSIF\b/i
    ELSE.2:               /\bELSE\b/i
    END_IF.2:             /\bEND_IF\b/i
    
    CASE.2:               /\bCASE\b/i
    OF.2:                 /\bOF\b/i
    END_CASE.2:           /\bEND_CASE\b/i
    
    FOR.2:                /\bFOR\b/i
    TO.2:               /\bTO\b/i
    BY.2:               /\bBY\b/i
    DO.2:               /\bDO\b/i
    END_FOR.2:          /\bEND_FOR\b/i
    
    WHILE.2:            /\bWHILE\b/i
    END_WHILE.2:        /\bEND_WHILE\b/i
    
    RETURN.2:           /\bRETURN\b/i
    NOT.2:              /\bNOT\b/i
    AND.2:              /\bAND\b/i
    OR.2:               /\bOR\b/i
    
    ARRAY.2:            /\bARRAY\b/i
    STRUCT.2:           /\bSTRUCT\b/i
    END_STRUCT.2:       /\bEND_STRUCT\b/i
    STRING.2:           /\bSTRING\b/i

    IDENT.1: /[a-zA-Z_][a-zA-Z0-9_]*/

    TYPE.2: /\b(BOOL|INT|UINT|DINT|REAL|LREAL|TIME|WORD|DWORD|BYTE)\b/i
    
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