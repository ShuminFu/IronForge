import os
import fiftyone as fo
from custom_importer import RoadDamageDatasetImporter
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


four.random_split(dataset, {"val": 0.25, "train": 0.75})
train_view = dataset.match_tags("train")
val_view = dataset.match_tags("val")

val_view.export(
   export_dir="val",
   dataset_type=fo.types.YOLOv5Dataset,
   label_field="ground_truth",
   #classes=classes
)

train_view.export(
   export_dir="train",
   dataset_type=fo.types.YOLOv5Dataset,
   label_field="ground_truth",
   #classes=classes
)


