from src.staugment import *

def test_argment_dataset():
    augmenter = DataAugmenter(
        input_dir="../data/IEC_61131-3_ST",
        output_dir="../data/IEC_61131-3_ST_CLEAN",
        ext=".json",
        num_variants=3
    )
    augmenter.run()