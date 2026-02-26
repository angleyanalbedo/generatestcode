
# st_slicer/pdg_cache.py
from __future__ import annotations
import pickle
from pathlib import Path
from stslicer.pdg import ProgramDependenceGraph   # 你的 PDG 类

CACHE_VER = 1      # 以后 PDG 结构变了就 +1，老缓存自动失效

def pdg_cache_path(st_file: Path, pou_name: str) -> Path:
    """缓存文件路径：原文件同目录，名字加后缀"""
    return st_file.with_suffix(f".{pou_name}.pdgcache{CACHE_VER}.pickle")

def save_pdg(pdg: ProgramDependenceGraph, st_file: Path, pou_name: str) -> None:
    """把 PDG 落盘"""
    cache = pdg_cache_path(st_file, pou_name)
    with cache.open("wb") as f:
        pickle.dump(pdg, f, protocol=pickle.HIGHEST_PROTOCOL)

def load_pdg(st_file: Path, pou_name: str) -> ProgramDependenceGraph | None:
    """有缓存就返回 PDG，否则 None"""
    cache = pdg_cache_path(st_file, pou_name)
    if not cache.exists():
        return None
    try:
        with cache.open("rb") as f:
            return pickle.load(f)
    except Exception:          # 损坏/版本不兼容
        cache.unlink(missing_ok=True)
        return None