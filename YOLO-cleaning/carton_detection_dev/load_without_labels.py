import fiftyone as fo
import fiftyone.zoo as foz
from fiftyone import ViewField as F
import numpy as np
import os
from tqdm import tqdm
from ultralytics import YOLO
import fiftyone as fo
import fiftyone.zoo as foz
from datetime import datetime

dataset_dir = "../carton_1125_8000"
dataset_type = fo.types.YOLOv5Dataset
detection_model = YOLO("../1025_v11n_1.pt")
name = "carton"

# dataset = fo.Dataset.from_dir(
#     dataset_dir=dataset_dir,
#     dataset_type=dataset_type,
#     name=name,
# )

dataset = fo.Dataset.from_images_dir(dataset_dir)

# Apply the model to the dataset
dataset.apply_model(detection_model, batch_size=64, num_workers=8)


def export_yolo_data(
        samples,
        export_dir,
        classes,
        label_field="prediction",
        split=None
):
    if type(split) == list:
        splits = split
        for split in splits:
            export_yolo_data(
                samples,
                export_dir,
                classes,
                label_field,
                split
            )
    else:
        if split is None:
            split_view = samples
            split = "val"
        else:
            split_view = samples.match_tags(split)

        split_view.export(
            export_dir=export_dir,
            dataset_type=fo.types.YOLOv5Dataset,
            label_field=label_field,
            classes=classes,
            split=split
        )


classes = dataset.distinct("prediction.detections.label")
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
yolo_dir = f"../carton_1125_8000_{timestamp}"
export_yolo_data(dataset, yolo_dir, classes)

# Launch the App to visualize the results
session = fo.launch_app(dataset)
input("按回车键退出程序...")
