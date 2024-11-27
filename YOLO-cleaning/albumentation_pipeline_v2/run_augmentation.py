from albumentation_pipeline_v2.config import AugmentationConfig
from albumentation_pipeline_v2.pipeline import AugmentationPipeline

def main():
    config = AugmentationConfig(
        yaml_path="/home/shumin/Downloads/RDD_yolo5/dataset.yaml",
        version="augmented_v0",
        num_samples=3,
        create_new_dataset=True,
        split='train'
    )
    
    pipeline = AugmentationPipeline(config)
    pipeline.run()

if __name__ == "__main__":
    main() 