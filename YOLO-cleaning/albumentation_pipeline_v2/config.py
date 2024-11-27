from dataclasses import dataclass
from pathlib import Path
import yaml
import os

@dataclass
class AugmentationConfig:
    def __init__(self, yaml_path: str, version: str, num_samples: int, create_new_dataset: bool, split: str):
        self.yaml_path = yaml_path
        self.version = version
        self.num_samples = num_samples
        self.create_new_dataset = create_new_dataset
        self.split = split
        
        # 添加yaml配置加载
        with open(yaml_path, 'r') as f:
            self.yaml_config = yaml.safe_load(f)
            
        # 获取原始数据集路径
        self.source_path = self.yaml_config.get('path', '')
        if not os.path.isabs(self.source_path):
            # 如果是相对路径，转换为绝对路径
            yaml_dir = os.path.dirname(os.path.abspath(yaml_path))
            self.source_path = os.path.join(yaml_dir, self.source_path)
            
        # 设置基础路径为yaml文件所在目录
        self.base_path = Path(os.path.dirname(os.path.abspath(yaml_path)))
        
        # 转换路径为Path对象以便统一处理
        self.source_path = Path(self.source_path)