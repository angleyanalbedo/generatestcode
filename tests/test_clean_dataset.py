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
        input_dir="../data/train_data_merged",
        output_dir="../data/train_data_merged_CLEAN",
        ext=".json"
    )
    cleaner.run()