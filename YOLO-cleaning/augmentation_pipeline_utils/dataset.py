from pathlib import Path
import cv2
import yaml
import shutil
from typing import Dict, List, Tuple, Optional
import numpy as np
from datetime import datetime
import json
from .config import AugmentationConfig
import os
from dataclasses import dataclass


@dataclass
class Labels:
    classes: List[int]
    bboxes: List[List[float]]


class DatasetManager:
    """数据集管理类"""

    IMAGE_EXTENSIONS = [
        '*.jpg', '*.jpeg', '*.JPG', '*.JPEG',
        '*.png', '*.PNG', '*.bmp', '*.BMP',
        '*.tif', '*.tiff', '*.TIF', '*.TIFF'
    ]

    def __init__(self, config: AugmentationConfig):
        self.config = config
        self.current_split = None
        self.yaml_config = self._load_yaml_config()
        self.paths = self._setup_paths()

        # 设置增强记录文件路径
        self.augmentation_record_path = self.paths['base'] / f"augmentation_record_{self.config.version}.json"

    def _load_yaml_config(self) -> Dict:
        """加载YAML配置文件"""
        with open(self.config.yaml_path, 'r') as f:
            return yaml.safe_load(f)

    def _setup_paths(self) -> Dict[str, Path]:
        """设置数据集路径"""
        paths = self._setup_original_paths()  # 首先设置原始数据集路径

        if self.config.create_new_dataset:
            # 添加新数据集的输出路径
            new_base = self.config.base_path / f"dataset_{self.config.version}"
            paths.update({
                'new_base': new_base,
                'new_images': new_base / 'images',
                'new_labels': new_base / 'labels',
                'new_yaml': new_base / 'dataset.yaml',
                'new_images_train': new_base / 'images' / 'train',
                'new_images_val': new_base / 'images' / 'val',
                'new_labels_train': new_base / 'labels' / 'train',
                'new_labels_val': new_base / 'labels' / 'val'
            })

        return paths

    def prepare(self):
        """准备数据集结构"""
        if self.config.create_new_dataset:
            self._create_directories()
            self._copy_dataset_structure()

    def get_image_paths(self) -> List[Path]:
        """获取需要处理的图片路径列表"""
        image_files = []
        input_dir = self.paths['images_input']
        for ext in self.IMAGE_EXTENSIONS:
            image_files.extend(list(input_dir.glob(ext)))
        return image_files

    def read_image(self, image_path: Path) -> np.ndarray:
        """读取图片"""
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"无法读取图片: {image_path}")
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    def save_augmented_result(self, original_path, transformed, aug_index, augmented_filename):
        """保存增强后的图片和标签
        
        Args:
            original_path (str): 原始图片路径
            transformed (dict): 增强后的图片和标签数据
            aug_index (int): 增强序号
            augmented_filename (str): 新的文件名（不含扩展名）
        """
        # 使用预设的路径
        output_image_path = self.paths[f'new_images_{self.current_split}'] / f"{augmented_filename}.jpg"
        output_label_path = self.paths[f'new_labels_{self.current_split}'] / f"{augmented_filename}.txt"
        
        # 保存增强后的图片
        cv2.imwrite(str(output_image_path), cv2.cvtColor(transformed['image'], cv2.COLOR_RGB2BGR))
        
        # 保存对应的标签
        with open(output_label_path, 'w') as f:
            for class_label, bbox in zip(transformed['class_labels'], transformed['bboxes']):
                line = f"{class_label} {' '.join(map(str, bbox))}\n"
                f.write(line)

    def _setup_new_dataset_paths(self) -> Dict[str, Path]:
        """创建新的数据集路径结构"""
        new_base = self.config.base_path / f"dataset_{self.config.version}"

        paths = {
            'base': new_base,
            'images': new_base / 'images',
            'labels': new_base / 'labels',
            'yaml': new_base / 'dataset.yaml'
        }

        # 添加train和val子目录
        for split in ['train', 'val']:
            paths[f'images_{split}'] = paths['images'] / split
            paths[f'labels_{split}'] = paths['labels'] / split

        return paths

    def _setup_original_paths(self) -> Dict[str, Path]:
        """设置原始数据集的路径"""
        base = self.config.base_path
        split = self.config.split

        return {
            'base': base,
            'images': base / 'images',
            'labels': base / 'labels',
            'images_train': base / 'images' / 'train',
            'images_val': base / 'images' / 'val',
            'labels_train': base / 'labels' / 'train',
            'labels_val': base / 'labels' / 'val',
        }

    def _create_directories(self):
        """创建必要的目录结构"""
        for path in self.paths.values():
            if isinstance(path, Path) and not path.suffix:
                os.makedirs(path, exist_ok=True)

    def _copy_dataset_structure(self):
        """复制数据集结构和标签"""
        # 复制yaml配置
        new_config = self.yaml_config.copy()
        new_config['train'] = './images/train/'
        new_config['val'] = './images/val/'
        new_config['path'] = str(self.paths['base'])

        with open(self.paths['new_yaml'], 'w') as f:
            yaml.dump(new_config, f, default_flow_style=False)

    def read_labels(self, image_path: Path) -> Optional[Labels]:
        """读取标签文件"""
        label_path = (self.paths['labels'] / image_path.relative_to(self.paths['images'])).with_suffix('.txt')
        raw_labels = self._read_yolo_label(label_path)

        if not raw_labels:
            return None

        classes = []
        bboxes = []
        for label in raw_labels:
            classes.append(int(label[0]))
            bbox = label[1:]
            if self._ensure_valid_bbox(bbox):
                bboxes.append(bbox)

        return Labels(classes=classes, bboxes=bboxes) if bboxes else None

    def _save_labels(self, stem: str, bboxes: List[List[float]],
                     class_labels: List[int], output_dir: Path):
        """保存标签文件"""
        output_label_path = output_dir / f"{stem}.txt"
        with open(output_label_path, 'w') as f:
            for bbox, class_label in zip(bboxes, class_labels):
                line = f"{class_label} {' '.join(map(str, bbox))}\n"
                f.write(line)

    def _read_yolo_label(self, label_path: Path) -> List[List[float]]:
        """读取YOLO格式标签文件"""
        raw_labels = []
        with open(label_path, 'r') as f:
            for line in f:
                raw_labels.append(list(map(float, line.split())))
        return raw_labels

    def _ensure_valid_bbox(self, bbox: List[float]) -> bool:
        """确保边界框格式有效"""
        return len(bbox) == 4 and all(0 <= coord <= 1 for coord in bbox)

    def set_split(self, split: str):
        """设置当前数据集分割
        
        Args:
            split (str): 数据集分割名称 ('train' 或 'val')
        """
        if split not in ['train', 'val']:
            raise ValueError(f"无效的数据集分割名称: {split}")
        self.current_split = split

    def save_augmentation_record(self, transform):
        """保存数据增强记录
        
        Args:
            transform: 使用的数据增强转换器
        """
        if not hasattr(self, 'augmentation_record_path'):
            self.augmentation_record_path = self.paths['new_base'] / f"augmentation_record_{self.config.version}.json"

        transform_params = {
            'transforms': [{
                'name': t.__class__.__name__,
                'params': t.get_params()
            } for t in transform.transforms],
            'bbox_params': transform.processors['bboxes'].params.__dict__
        }

        record = {
            'version': self.config.version,
            'num_samples': self.config.num_samples,
            'augmentation_config': transform_params,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # 确保父目录存在
        self.augmentation_record_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.augmentation_record_path, 'w', encoding='utf-8') as f:
            json.dump(record, f, indent=4, ensure_ascii=False)
