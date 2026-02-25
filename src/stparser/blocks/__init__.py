# st_slicer/blocks/__init__.py

from .types import FunctionalBlock

from .slice_ops import (
    compute_slice_nodes,
    cluster_slices,
    close_with_control_structures,
    nodes_to_sorted_ast_stmts,
    build_parent_map_from_ir2ast,
)

from .line_map import stmts_to_line_numbers

from .structure_common import (
    scan_matching_end_generic,
    scan_matching_end_if,
    scan_matching_end_for,
    scan_matching_end_case,
    scan_matching_end_while,
    scan_matching_end_repeat,
)

from .structure_if_case_loop import (
    scan_if_header_end,
    patch_if_structure,
    patch_case_structure,
)

from .splitters import (
    split_blocks_by_stage,
    normalize_block_sizes,
    normalize_and_split_blocks,
)

from .postprocess import (
    remove_empty_ifs_in_blocks,
    remove_empty_loops_in_blocks,
    remove_empty_cases_in_blocks,
    is_meaningful_block,
    dedup_blocks_by_code,
)

from .render import render_block_text

