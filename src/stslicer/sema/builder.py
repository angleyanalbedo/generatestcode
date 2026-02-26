from __future__ import annotations
from typing import List

from .symbols import VarSymbol, FBSymbol, POUSymbolTable, ProjectSymbolTable
from ..ast.nodes import ProgramDecl, FBDecl


def is_fb_type(type_name: str) -> bool:
    """
    简单占位实现：后面你可以根据工程的 FB 类型列表来真正判断。
    现在默认所有全大写且以 "_FB" 结尾的是 FB 类型。
    """
    return type_name.isupper() and type_name.endswith("_FB")


def build_symbol_table(programs: List[ProgramDecl | FBDecl]) -> ProjectSymbolTable:
    proj = ProjectSymbolTable()

    for pou in programs:
        pou_tab = POUSymbolTable(name=pou.name, vars={}, fb_instances={})
        for v in pou.vars:
            if is_fb_type(v.type):
                fb_sym = FBSymbol(name=v.name, type=v.type)
                pou_tab.add_fb_instance(fb_sym)
            else:
                var_sym = VarSymbol(
                    name=v.name,
                    type=v.type,
                    storage=v.storage,
                    init_expr=v.init_expr,
                )
                # 这里暂时不区分 global / local，后面可以根据 storage 字段细分
                pou_tab.add_var(var_sym)

        proj.add_pou(pou_tab)

    return proj
