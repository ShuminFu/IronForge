import albumentations as A
import numpy as np
from typing import List, Dict

class AugmentationTransforms:
    """数据增强转换类"""
    
    @staticmethod
    def create_default_transform():
        """创建默认的数据增强pipeline"""
        return A.Compose([
            A.RandomBrightnessContrast(p=1)
        ], bbox_params=A.BboxParams(
            format='yolo',
            label_fields=['class_labels']
        ))
    
    @staticmethod
    def preprocess_bboxes(bboxes: List[List[float]]) -> np.ndarray:
        """预处理边界框"""
        EPSILON = 1e-6
        processed = np.array(bboxes)
        
        # 处理接近0和1的值
        processed[np.abs(processed) < EPSILON] = 0
        processed[np.abs(processed - 1) < EPSILON] = 1
        
        # 调整中心点坐标
        center_coords = processed[..., :2]
        dimensions = processed[..., 2:]
        
        min_centers = dimensions / 2
        max_centers = 1 - dimensions / 2
        center_coords = np.maximum(min_centers, np.minimum(max_centers, center_coords))
        
        processed[..., :2] = center_coords
        processed[..., 2:] = dimensions
        
        return processed 

    def get_transform_params(self) -> Dict:
        """获取转换参数记录"""
        return {
            'transforms': [{
                'name': t.__class__.__name__,
                'params': t.get_params()
            } for t in self.transform.transforms],
            'bbox_params': self.transform.processors['bboxes'].params.__dict__
        }