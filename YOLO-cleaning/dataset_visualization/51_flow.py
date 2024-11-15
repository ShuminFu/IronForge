import os
import fiftyone as fo
from dataset_ninja_importer import RoadDamageDatasetImporter
import fiftyone.utils.random as four

# 创建导入器实例
base_dir = os.path.expanduser("~/Downloads/road-damage-DatasetNinja/ds0")
importer = RoadDamageDatasetImporter(
    dataset_dir=base_dir,
    shuffle=True,
    max_samples=None
)

# 导入数据集
dataset = fo.Dataset.from_importer(importer, name="road-damage-dataset")
session = fo.launch_app(dataset)
classes = dataset.distinct("ground_truth.detections.label")

four.random_split(dataset, {"val": 0.25, "train": 0.75})
train_view = dataset.match_tags("train")
val_view = dataset.match_tags("val")

val_view.export(
   export_dir="/home/shumin/Downloads/RDD_yolo",
   dataset_type=fo.types.YOLOv5Dataset,
   label_field="ground_truth",
   classes=classes,
    split="val"
)

train_view.export(
   export_dir="/home/shumin/Downloads/RDD_yolo",
   dataset_type=fo.types.YOLOv5Dataset,
   label_field="ground_truth",
   classes=classes,
   split="train"
)


if __name__ =="__main__":
    train_dataset = fo.Dataset.from_dir(
        dataset_dir="/home/shumin/Downloads/RDD_yolo5/dataset_augmented_v1",
        dataset_type=fo.types.YOLOv5Dataset,
        label_field="ground_truth",
        split="train",
        max_sampels=100
    )
    session = fo.launch_app(train_dataset)
    input("按回车键退出程序...")


