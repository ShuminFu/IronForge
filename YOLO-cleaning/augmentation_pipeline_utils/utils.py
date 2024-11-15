from pathlib import Path
from typing import List
import cv2
import numpy as np

def read_yolo_label(label_path: Path) -> List[List[float]]:
    """读取YOLO格式的标注文件"""
    if not label_path.exists():
        return []
        
    labels = []
    with open(label_path, 'r') as f:
        for line in f:
            data = list(map(float, line.strip().split()))
            labels.append(data)
    return labels

def ensure_valid_bbox(bbox: List[float]) -> bool:
    """验证边界框是否有效"""
    return all(0.0 <= x <= 1.0 for x in bbox) 