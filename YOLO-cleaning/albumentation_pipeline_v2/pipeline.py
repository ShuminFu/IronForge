from .config import AugmentationConfig
from .dataset import DatasetManager
from .transforms import AugmentationTransforms
from tqdm import tqdm
import os
from pathlib import Path
import shutil

class AugmentationPipeline:
    """数据增强主流程类"""
    
    def __init__(self, config: AugmentationConfig):
        self.config = config
        self.transform = AugmentationTransforms.create_default_transform()
        self.dataset = DatasetManager(config)
        
    def copy_other_splits(self):
        """复制非增强split的数据和标签到新数据集"""
        base_splits = ['train', 'val', 'test']
        # 只处理存在的且不是当前split的目录
        splits = [s for s in base_splits if (
            s != self.config.split and 
            os.path.exists(os.path.join(self.dataset.paths['images'], s))
        )]
        data_types = [('images', 'new_images'), ('labels', 'new_labels')]
        
        for split in splits:
            for src_key, dst_key in data_types:
                src_dir = os.path.join(self.dataset.paths[src_key], split)
                if not os.path.exists(src_dir):
                    continue
                    
                dst_dir = os.path.join(self.dataset.paths[dst_key], split)
                if os.path.exists(dst_dir):
                    shutil.rmtree(dst_dir)
                shutil.copytree(src_dir, dst_dir)
        
    def run(self):
        """执行数据增强流程"""
        print(f"\n=== 创建新数据集结构 ===")
        if self.config.create_new_dataset:
            print(f"新数据集路径: {self.dataset.paths['base']}")
        
        # 构建输入输出路径
        input_dir = os.path.join(self.config.source_path, 'images', self.config.split)
        output_base = os.path.join(os.path.dirname(self.config.source_path),
                                 f'dataset_{self.config.version}')
        output_dir = os.path.join(output_base, 'images', self.config.split)
        
        if not os.path.exists(input_dir):
            raise ValueError(f"输入目录不存在: {input_dir}")
            
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 准备数据集
        self.dataset.prepare()
        
        print("\n=== 开始处理图片 ===")
        for split in ['train', 'val'] if self.config.split == 'all' else [self.config.split]:
            print(f"\n处理 {split} 集:")
            image_path_key = f"images_{split}"
            if image_path_key not in self.dataset.paths:
                raise KeyError(f"找不到路径键 '{image_path_key}'。可用的路径键: {list(self.dataset.paths.keys())}")
            
            input_image_dir = self.dataset.paths[image_path_key]
            print(f"输入图片目录: {input_image_dir}")
            
            output_key = f'new_images_{split}'
            if output_key not in self.dataset.paths:
                raise KeyError(f"找不到输出路径键 '{output_key}'。可用的路径键: {list(self.dataset.paths.keys())}")
            
            output_image_dir = self.dataset.paths[output_key]
            print(f"输出图片目录: {output_image_dir}")
            
            self._process_images(split, input_image_dir, output_image_dir)
        
        # 保存增强记录
        self.dataset.save_augmentation_record(self.transform)
        print("\n=== 数据增强完成 ===")
        
        self.copy_other_splits()
        
    def _process_images(self, split, input_dir, output_dir):
        """处理指定split的所有图片
        
        Args:
            split (str): 数据集分割名称 ('train' 或 'val')
            input_dir (str): 输入图片目录路径
            output_dir (str): 输出图片目录路径
        """
        try:
            self.dataset.set_split(split)
            
            # 使用新的图片文件匹配方式
            input_path = Path(input_dir)
            image_paths = []
            image_extensions = [
                '*.jpg', '*.jpeg', '*.JPG', '*.JPEG',
                '*.png', '*.PNG',
                '*.bmp', '*.BMP',
                '*.tif', '*.tiff', '*.TIF', '*.TIFF'
            ]
            
            for ext in image_extensions:
                image_paths.extend(list(input_path.glob(ext)))
            
            if not image_paths:
                print(f"警告: {split} 集中没有找到图片")
                return
            
            for img_path in tqdm(image_paths, desc=f"正在进行数据增强： {split} 集图片"):
                try:
                    self._augment_single_image(img_path)
                except Exception as e:
                    print(f"\n警告: 处理图片 {img_path} 时出错: {str(e)}")
                    continue
        except Exception as e:
            print(f"\n错误: 处理 {split} 集时发生错误: {str(e)}")
            raise
        
    def _augment_single_image(self, image_path):
        """处理单张图片并保存到新路径
        
        Args:
            image_path (str): 原始图片的路径
        """
        # 读取图片
        image = self.dataset.read_image(image_path)
        
        # 读取标签
        labels = self.dataset.read_labels(image_path)
        if not labels:
            return
        
        # 预处理边界框
        bboxes = AugmentationTransforms.preprocess_bboxes(labels.bboxes)
        
        # 获取原始文件名（不含路径）
        original_filename = Path(image_path).name
        base_name = Path(original_filename).stem
        
        # 生成增强样本
        for i in range(self.config.num_samples):
            transformed = self.transform(
                image=image,
                bboxes=bboxes,
                class_labels=labels.classes
            )
            
            # 构造新的文件名：原始名称_aug_序号
            augmented_filename = f"{base_name}_aug_{i}"
            
            # 保存结果到新路径
            self.dataset.save_augmented_result(
                original_path=image_path,
                transformed=transformed,
                aug_index=i,
                augmented_filename=augmented_filename
            ) 