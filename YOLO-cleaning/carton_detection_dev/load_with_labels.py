import os
import numpy as np
import fiftyone as fo
from ultralytics import YOLO


def read_yolo_detections_file(filepath):
    detections = []
    if not os.path.exists(filepath):
        return np.array([])

    with open(filepath) as f:
        lines = [line.rstrip('\n').split(' ') for line in f]

    for line in lines:
        detection = [float(l) for l in line]
        detections.append(detection)
    return np.array(detections)


"""
YOLOv8 represents bounding boxes in a centered format with coordinates [center_x, center_y, width, height], 
whereas FiftyOne stores bounding boxes in [top-left-x, top-left-y, width, height] format. 
"""


def _uncenter_boxes(boxes):
    '''convert from center coords to corner coords'''
    boxes[:, 0] -= boxes[:, 2] / 2.
    boxes[:, 1] -= boxes[:, 3] / 2.


def _get_class_labels(predicted_classes, class_list):
    labels = (predicted_classes).astype(int)
    labels = [class_list[l] for l in labels]
    return labels


def convert_yolo_detections_to_fiftyone(
        yolo_detections,
        class_list
):
    detections = []
    if yolo_detections.size == 0:
        return fo.Detections(detections=detections)

    boxes = yolo_detections[:, 1:-1]
    _uncenter_boxes(boxes)

    confs = yolo_detections[:, -1]
    labels = _get_class_labels(yolo_detections[:, 0], class_list)

    for label, conf, box in zip(labels, confs, boxes):
        detections.append(
            fo.Detection(
                label=label,
                bounding_box=box.tolist(),
                confidence=conf
            )
        )

    return fo.Detections(detections=detections)


# def get_prediction_filepath(filepath, run_number=1):
#     run_num_string = ""
#     if run_number != 1:
#         run_num_string = str(run_number)
#     filename = filepath.split("/")[-1].split(".")[0]
#     return f"runs/detect/predict{run_num_string}/labels/{filename}.txt"
def get_prediction_filepath(filepath, run_number=1):
    run_num_string = ""
    if run_number != 1:
        run_num_string = str(run_number)
    filename = filepath.split("/")[-1].split(".")[0]
    return f"./runs/detect/predict{run_num_string}/labels/{filename}.txt"

def add_yolo_detections(
        samples,
        prediction_field,
        prediction_filepath,
        class_list
):
    prediction_filepaths = samples.values(prediction_filepath)
    yolo_detections = [read_yolo_detections_file(pf) for pf in prediction_filepaths]
    detections = [convert_yolo_detections_to_fiftyone(yd, class_list) for yd in yolo_detections]
    samples.set_values(prediction_field, detections)


dataset_dir = "../datasets/raw_images"

detection_model = YOLO("../1127_v11n.pt")
name = "carton"

dataset = fo.Dataset.from_images_dir(dataset_dir)
filepaths = dataset.values("filepath")
prediction_filepaths = [get_prediction_filepath(fp, run_number=2) for fp in filepaths]

dataset.set_values(
    "yolo_det_filepath",
    prediction_filepaths
)
# classes = dataset.distinct("prediction.detections.label")
classes = ['carton', 'column', 'forklift', 'pallet']
add_yolo_detections(
    dataset,
    "yolo11n",
    "yolo_det_filepath",
    classes
)

session = fo.launch_app(dataset)
# view = dataset.load_saved_view("carton or forklift")
# export_dir = "./filtered_images"
# view.export(
#     export_dir=export_dir,
#     dataset_type=fo.types.ImageDirectory
# )