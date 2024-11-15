# FiftyOne 用例教程

这是一个使用 FiftyOne 处理数据集的工具集，提供多种数据集导入和处理方式。

## 功能特点

- 支持多种数据集导入方式：
  - Dataset Ninja 格式导入器
  - Ultralytics YOLO 格式导入器
  - 手动构建数据集
- 提供数据集可视化界面
- 支持数据集随机分割（训练集/验证集）
- 支持导出为 YOLOv5 格式

## 文件说明

- `dataset_ninja_importer.py`: Dataset Ninja 格式数据集导入器
- `ultralytics_importer.py`: Ultralytics YOLO 格式数据集导入器
- `load_datasets_manually.py`: 手动构建数据集示例
- `51flow.py`: 完整的数据处理流程示例

## 使用方法

### 1. 使用 Dataset Ninja 导入器

```python
from dataset_ninja_importer import RoadDamageDatasetImporter
import fiftyone as fo

dataset = fo.Dataset.from_importer(
    RoadDamageDatasetImporter(dataset_dir="path/to/dataset"),
    name="road-damage-dataset"
)
```

### 2. 使用 Ultralytics YOLO 导入器

```python
from ultralytics_importer import UltralyticsDataset
import fiftyone as fo

dataset = fo.Dataset.from_dir(
    dataset_dir="path/to/dataset",
    dataset_type=UltralyticsDataset,
    split="train"
)
```

### 3. 手动添加样本，构建数据集

```python
import fiftyone as fo
import glob
import json
import os

# 准备数据
images_dir = "path/to/images"
annotations_dir = "path/to/annotations"

# 创建samples
samples = []
for filepath in glob.glob(os.path.join(images_dir, "*")):
    sample = fo.Sample(filepath=filepath)
    
    # 获取对应的标注文件
    img_filename = os.path.basename(filepath)
    json_path = os.path.join(annotations_dir, img_filename + ".json")
    
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            ann_data = json.load(f)
            # 处理标注数据...
            detections = []
            # 添加检测框...
            sample["ground_truth"] = fo.Detections(detections=detections)
    
    samples.append(sample)

# 创建数据集
dataset = fo.Dataset("road-damage-dataset")
dataset.add_samples(samples)
```

## 数据集格式要求

### Dataset Ninja 格式
```
dataset_dir/
├── img/
│   ├── image1.jpg
│   └── ...
└── ann/
    ├── image1.jpg.json
    └── ...
```

### Ultralytics YOLO 格式
```
dataset_dir/
├── images/
│   ├── train/
│   └── val/
└── labels/
    ├── train/
    └── val/
```

## 主要处理流程

1. 数据集导入
2. 数据集可视化
3. 数据集分割
4. 格式转换与导出

## 高级配置

### Dataset Ninja 导入器参数
- `dataset_dir`: 数据集根目录
- `shuffle`: 是否随机打乱
- `seed`: 随机种子
- `max_samples`: 最大样本数

### Ultralytics 导入器参数
- `dataset_dir`: 数据集目录
- `split`: 数据集分割（train/val）
- `classes_file`: 类别映射文件路径
- `shuffle`: 是否随机打乱
- `max_samples`: 最大样本数

## 注意事项

1. 确保数据集格式符合要求
2. 导入前检查文件路径正确性
3. 大数据集建议使用 `max_samples` 参数进行测试
4. 确保 MongoDB 服务正常运行

## 示例用法

完整的处理流程示例可参考 `51flow.py`：
```python
import fiftyone as fo
from dataset_ninja_importer import RoadDamageDatasetImporter

# 导入数据集
dataset = fo.Dataset.from_importer(importer, name="road-damage-dataset")

# 数据集分割
dataset.split_collection(splits={"train": 0.8, "val": 0.2})

# 导出为 YOLO 格式
dataset.export(
    export_dir="output_dir",
    dataset_type=fo.types.YOLOv5Dataset,
    split="train"
)
```
