
import glob
import json
import os
import fiftyone as fo

os.environ["FIFTYONE_DATABASE_URI"] = "mongodb://localhost:27017"
base_dir = os.path.expanduser("~/Downloads/road-damage-DatasetNinja/ds0")
images_dir = os.path.join(base_dir, "img")
annotations_dir = os.path.join(base_dir, "ann")

# 创建标注字典
annotations = {}
for json_path in glob.glob(os.path.join(annotations_dir, "*.json")):
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    # 获取对应的图片路径
    img_filename = os.path.basename(json_path).replace('.json', '')
    img_path = os.path.join(images_dir, img_filename)
    
    # 提取图片尺寸
    height = data['size']['height']
    width = data['size']['width']
    
    # 转换标注
    boxes = []
    for obj in data['objects']:
        exterior = obj['points']['exterior']
        x1, y1 = exterior[0]
        x2, y2 = exterior[1]
        
        # 转换为相对坐标 [x, y, width, height]
        rel_x = x1 / width
        rel_y = y1 / height
        rel_w = (x2 - x1) / width
        rel_h = (y2 - y1) / height
        
        boxes.append({
            "label": obj['classTitle'],
            "bbox": [rel_x, rel_y, rel_w, rel_h]
        })
    
    annotations[img_path] = boxes

# 创建samples
samples = []
for filepath in glob.glob(os.path.join(images_dir, "*")):
    sample = fo.Sample(filepath=filepath)
    
    if filepath in annotations:
        detections = []
        for obj in annotations[filepath]:
            detections.append(
                fo.Detection(
                    label=obj["label"],
                    bounding_box=obj["bbox"]
                )
            )
        sample["ground_truth"] = fo.Detections(detections=detections)
    
    samples.append(sample)

# 创建数据集
dataset = fo.Dataset("road-damage-dataset")
dataset.add_samples(samples)