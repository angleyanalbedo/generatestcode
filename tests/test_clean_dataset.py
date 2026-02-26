from src.stdatacleaner import STDataCleaner

def test_clean_dataset():
    cleaner = STDataCleaner(
        input_dir="../data/IEC_61131-3_ST",
        output_dir="../data/IEC_61131-3_ST_CLEAN",
        ext=".json"
    )
    cleaner.run()

def test_clean_dataset_demo():
    cleaner = STDataCleaner(
        input_dir="../data/st_dataset_distillation_by_qwen2.5",
        output_dir="../data/st_dataset_distillation_by_qwen2.5_CLEAN",
        ext=".json"
    )
    cleaner.run()