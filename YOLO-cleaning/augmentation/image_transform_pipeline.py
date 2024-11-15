import os
import cv2
import yaml
import shutil
import albumentations as A
from pathlib import Path
from tqdm import tqdm
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import numpy as np
import json

image_extensions = [
    '*.jpg', '*.jpeg', '*.JPG', '*.JPEG',
    '*.png', '*.PNG',
    '*.bmp', '*.BMP',
    '*.tif', '*.tiff', '*.TIF', '*.TIFF'
]


def load_yaml_config(yaml_path: str) -> Dict:
    """
    加载yaml配置文件
    
    Args:
        yaml_path: yaml文件路径
    Returns:
        配置字典
    """
    with open(yaml_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def create_new_dataset_structure(
        yaml_path: str,
        version: str
) -> Dict[str, Path]:
    """
    创建新的数据集结构
    
    Args:
        yaml_path: 原始yaml文件路径
        version: 版本标识
    Returns:
        新的路径配置字典
    """
    base_path = Path(yaml_path).parent
    new_base = base_path / f"dataset_{version}"

    # 创建主要目录
    new_paths = {
        'base': new_base,
        'images': new_base / 'images',
        'labels': new_base / 'labels',
        'yaml': new_base / 'dataset.yaml'
    }

    # 创建train和val子目录
    for split in ['train', 'val']:
        new_paths[f'images_{split}'] = new_paths['images'] / split
        new_paths[f'labels_{split}'] = new_paths['labels'] / split

    # 创建目录结构
    for path in new_paths.values():
        if isinstance(path, Path) and not path.suffix:  # 不为文件的路径才创建目录
            os.makedirs(path, exist_ok=True)

    return new_paths


def copy_dataset_structure(
        yaml_path: str,
        new_paths: Dict[str, Path],
        copy_labels: bool = True
) -> None:
    """
    复制数据集结构和标签
    """
    config = load_yaml_config(yaml_path)
    base_path = Path(yaml_path).parent

    # 复制标签文件
    if copy_labels:
        for split in ['train', 'val']:
            label_src = base_path / 'labels' / split
            label_dst = new_paths[f'labels_{split}']
            if label_src.exists():
                for label_file in label_src.glob('*.txt'):
                    shutil.copy2(label_file, label_dst)

    # 创建新的yaml文件
    new_config = config.copy()
    new_config['train'] = './images/train/'
    new_config['val'] = './images/val/'
    new_config['path'] = str(new_paths['base'])

    with open(new_paths['yaml'], 'w') as f:
        yaml.dump(new_config, f, default_flow_style=False)


def read_yolo_label(label_path: Path) -> List[List[float]]:
    """
    读取YOLO格式的标注文件
    
    Args:
        label_path: 标注文件路径
    Returns:
        标注列表 [class_id, x_center, y_center, width, height]
    """
    if not label_path.exists():
        return []

    labels = []
    with open(label_path, 'r') as f:
        for line in f:
            data = list(map(float, line.strip().split()))
            labels.append(data)
    return labels


def yolo_to_albumentations(
        bbox: List[float],
        img_width: int,
        img_height: int
) -> List[float]:
    """
    将YOLO格式的bbox转换为albumentations格式
    YOLO: [x_center, y_center, width, height] (normalized)
    Albumentations: [x_min, y_min, x_max, y_max] (normalized)
    """
    x_center, y_center, width, height = bbox[1:]
    x_min = x_center - width / 2
    y_min = y_center - height / 2
    x_max = x_center + width / 2
    y_max = y_center + height / 2

    return [x_min, y_min, x_max, y_max]


def preprocess_bboxes(bboxes):
    """预处理bbox，处理浮点数精度问题和边界框坐标"""
    EPSILON = 1e-6
    processed = np.array(bboxes)

    # 将接近0的值设为0
    processed[np.abs(processed) < EPSILON] = 0
    # 将接近1的值设为1
    processed[np.abs(processed - 1) < EPSILON] = 1

    # 调整中心点，确保x_min和y_min不会为负
    center_coords = processed[..., :2]  # 获取中心点坐标
    dimensions = processed[..., 2:]  # 获取宽高

    # 计算最小允许的中心点坐标，防止边界框超出图像
    min_centers = dimensions / 2
    # 计算最大允许的中心点坐标
    max_centers = 1 - dimensions / 2

    # 将中心点限制在合理范围内
    center_coords = np.maximum(min_centers, np.minimum(max_centers, center_coords))

    # 重新组合结果
    processed[..., :2] = center_coords
    processed[..., 2:] = dimensions

    return processed


def create_augmentation_record(
        base_path: Path,
        transform_params: Dict,
        version: str,
        split: str,
        num_samples: int
) -> None:
    """
    创建数据增强记录文件，直接覆盖现有记录
    
    Args:
        base_path: 数据集根目录
        transform_params: 数据增强参数
        version: 数据集版本
        split: 处理的数据集分割
        num_samples: 每张图片增强的数量
    """
    record = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'version': version,
        'split': split,
        'num_samples': num_samples,
        'transform_params': transform_params
    }

    record_path = base_path / 'augmentation_record.json'

    with open(record_path, 'w') as f:
        json.dump(record, f, indent=4)


def augment_images(
        yaml_path: str,
        split: str = 'train',
        num_samples: int = 5,
        create_new_dataset: bool = False,
        version: Optional[str] = None
):
    """
    根据yaml配置对指定split的图片进行数据增强
    
    Args:
        yaml_path: 数据集yaml配置文件路径
        split: 数据集分割，可选 'train'、'val' 或 'all'
        num_samples: 每张图片增强的数量
        create_new_dataset: 是否创建新的数据集结构
        version: 新数据集版本标识，如果为None则使用时间戳
    """
    if split not in ['train', 'val', 'all']:
        raise ValueError("split must be one of 'train', 'val', or 'all'")

    # 设置版本标识
    if create_new_dataset:
        if version is None:
            version = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_paths = create_new_dataset_structure(yaml_path, version)
        copy_dataset_structure(yaml_path, new_paths)
        print(f"\n=== 创建新数据集结构 ===")
        print(f"新数据集路径: {new_paths['base']}")

    # 获取处理路径
    config = load_yaml_config(yaml_path)
    base_path = Path(yaml_path).parent
    splits = ['train', 'val'] if split == 'all' else [split]

    # 创建数据增强pipeline
    transform = A.Compose([
        A.RandomBrightnessContrast(p=1)
    ], bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels']))

    transform_params = {
        'transforms': [{
            'name': t.__class__.__name__,
            'params': t.get_params()
        } for t in transform.transforms],
        'bbox_params': transform.processors['bboxes'].params.__dict__
    }

    create_augmentation_record(
        base_path=base_path if not create_new_dataset else new_paths['base'],
        transform_params=transform_params,
        version=version if create_new_dataset else 'original',
        split=split,
        num_samples=num_samples
    )

    print("\n=== 开始处理图片 ===")

    # 处理每个数据集
    for split_name in ['train', 'val']:
        input_dir = base_path / config[split_name].lstrip('./')
        label_dir = base_path / 'labels' / split_name

        if create_new_dataset:
            output_dir = new_paths[f'images_{split_name}']
            output_label_dir = new_paths[f'labels_{split_name}']
            # 首先收集所有需要复制的文件
            image_files_to_copy = []
            for ext in image_extensions:
                image_files_to_copy.extend(list(input_dir.glob(ext)))

            # 使用tqdm显示复制进度
            print(f"\n复制原始文件到 {split_name} 集:")
            for img_path in tqdm(image_files_to_copy, desc=f"复制{split_name}集文件"):
                shutil.copy2(img_path, output_dir)
                label_path = label_dir / f"{img_path.stem}.txt"
                if label_path.exists():
                    shutil.copy2(label_path, output_label_dir)

            # 只对指定的split进行增强
            if split_name not in splits:
                continue
        else:
            # 如果不创建新数据集，则使用_augmented后缀的目录
            output_dir = input_dir.parent / f"{split_name}_augmented"
            output_label_dir = label_dir.parent / f"{split_name}_augmented"
            os.makedirs(output_dir, exist_ok=True)
            os.makedirs(output_label_dir, exist_ok=True)

        print(f"\n处理 {split_name} 集:")
        print(f"输入图片目录: {input_dir}")
        print(f"输入标签目录: {label_dir}")
        print(f"输出图片目录: {output_dir}")
        print(f"输出标签目录: {output_label_dir}")

        # 获取所有支持格式的图片文件
        image_files = []
        for ext in image_extensions:
            image_files.extend(list(input_dir.glob(ext)))

        for img_path in tqdm(image_files, desc=f"增强{split_name}集"):
            # 读取图片
            image = cv2.imread(str(img_path))
            if image is None:
                print(f"警告: 无法读取图片 {img_path}")
                continue

            height, width = image.shape[:2]
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # 读取对应的标签文件
            label_path = label_dir / f"{img_path.stem}.txt"
            labels = read_yolo_label(label_path)

            if not labels:
                continue

            # 准备数据增强的标注格式
            bboxes = []
            class_labels = []
            for label in labels:
                class_labels.append(int(label[0]))
                bbox = label[1:]  # 裁剪边界框坐标
                if all(0.0 <= x <= 1.0 for x in bbox):  # 确保所有坐标都在有效范围内
                    bboxes.append(bbox)
                else:
                    continue  # 跳过无效的边界框

            if not bboxes:  # 如果没有有效的边界框，跳过这张图片
                continue

            # 对每张图片生成多个增强版本
            for i in range(num_samples):
                # 应用数据增强
                bboxes = preprocess_bboxes(bboxes)
                transformed = transform(
                    image=image,
                    bboxes=bboxes,
                    class_labels=class_labels
                )

                aug_image = cv2.cvtColor(transformed['image'], cv2.COLOR_RGB2BGR)
                aug_bboxes = transformed['bboxes']
                aug_labels = transformed['class_labels']

                # 保存增强后的图片
                output_filename = f"{img_path.stem}_aug_{i + 1}.jpg"
                output_path = output_dir / output_filename
                cv2.imwrite(str(output_path), aug_image)

                # 保存增强后的标签
                output_label_path = output_label_dir / f"{img_path.stem}_aug_{i + 1}.txt"
                with open(output_label_path, 'w') as f:
                    for bbox, class_label in zip(aug_bboxes, aug_labels):
                        # 写入YOLO格式：class_id x_center y_center width height
                        line = f"{class_label} {' '.join(map(str, bbox))}\n"
                        f.write(line)


if __name__ == "__main__":
    yaml_path = "/home/shumin/Downloads/RDD_yolo5/dataset.yaml"

    # 执行数据增强
    augment_images(
        yaml_path=yaml_path,
        split='train',
        num_samples=3,
        create_new_dataset=True,  # 创建新的数据集结构
        version='augmented_v1_1080p'  # 可选，不指定则使用时间戳
    )
