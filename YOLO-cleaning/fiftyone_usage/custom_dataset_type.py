import os
import fiftyone as fo
import fiftyone.utils.data as foud
import fiftyone.core.metadata as fom
import fiftyone.core.labels as fol
import random

class UltralyticsYOLODatasetImporter(foud.LabeledImageDatasetImporter):
    """
    用于导入Ultralytics YOLO格式数据集的导入器。
    """
    def __init__(
        self,
        dataset_dir=None,
        split=None,
        shuffle=False,
        seed=None,
        max_samples=None,
        classes_file=None,
    ):
        super().__init__(
            dataset_dir=dataset_dir,
            shuffle=shuffle,
            seed=seed,
            max_samples=max_samples,
        )
        self.split = split
        self._current_index = 0
        
        # 设置图片和标签目录
        self.images_dir = os.path.join(dataset_dir, split, "images") if split else os.path.join(dataset_dir, "images")
        self.labels_dir = os.path.join(dataset_dir, split, "labels") if split else os.path.join(dataset_dir, "labels")
        
        # 初始化路径列表
        self._image_paths = []
        self._label_paths = []
        
        # 加载类别映射
        self.classes_map = {}
        if classes_file:
            self._load_classes(classes_file)
        else:
            # 尝试从数据集目录下的data.yaml或classes.txt加载
            yaml_path = os.path.join(dataset_dir, "data.yaml")
            txt_path = os.path.join(dataset_dir, "classes.txt")
            if os.path.exists(yaml_path):
                self._load_yaml_classes(yaml_path)
            elif os.path.exists(txt_path):
                self._load_txt_classes(txt_path)

    def _load_classes(self, classes_file):
        """加载类别映射文件"""
        if classes_file.endswith('.yaml'):
            self._load_yaml_classes(classes_file)
        else:
            self._load_txt_classes(classes_file)

    def _load_yaml_classes(self, yaml_path):
        """从YAML文件加载类别映射"""
        import yaml
        try:
            with open(yaml_path, 'r') as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict) and 'names' in data:
                    self.classes_map = {i: name for i, name in enumerate(data['names'])}
        except Exception as e:
            print(f"警告: 无法加载类别文件 {yaml_path}: {e}")

    def _load_txt_classes(self, txt_path):
        """从txt文件加载类别映射"""
        try:
            with open(txt_path, 'r') as f:
                classes = [line.strip() for line in f.readlines()]
                self.classes_map = {i: name for i, name in enumerate(classes)}
        except Exception as e:
            print(f"警告: 无法加载类别文件 {txt_path}: {e}")

    @property
    def label_cls(self):
        """返回标签类型"""
        return fol.Detections

    @property
    def has_dataset_info(self):
        return True

    @property
    def has_image_metadata(self):
        """是否提供图片元数据"""
        return True

    def get_dataset_info(self):
        return {
            "name": f"Ultralytics YOLO Dataset - {self.split}",
            "type": "detection",
            "num_samples": len(self._image_paths) if self._image_paths else 0,
        }

    def setup(self):
        """初始化设置"""
        if not os.path.exists(self.images_dir):
            raise ValueError(f"图片目录不存在: {self.images_dir}")
        if not os.path.exists(self.labels_dir):
            raise ValueError(f"标签目录不存在: {self.labels_dir}")

        # 获取所有图片和对应的标签文件
        for filename in os.listdir(self.images_dir):
            if filename.endswith((".jpg", ".jpeg", ".png")):
                image_path = os.path.join(self.images_dir, filename)
                label_path = os.path.join(
                    self.labels_dir, os.path.splitext(filename)[0] + ".txt"
                )

                if os.path.exists(label_path):
                    self._image_paths.append(image_path)
                    self._label_paths.append(label_path)
                else:
                    print(f"警告: 未找到图片 {filename} 对应的标签文件")

        if self.shuffle:
            random.seed(self.seed)
            indices = list(range(len(self._image_paths)))
            random.shuffle(indices)
            self._image_paths = [self._image_paths[i] for i in indices]
            self._label_paths = [self._label_paths[i] for i in indices]

        if self.max_samples is not None:
            self._image_paths = self._image_paths[:self.max_samples]
            self._label_paths = self._label_paths[:self.max_samples]

    def __len__(self):
        return len(self._image_paths)

    def __next__(self):
        """返回下一个样本的信息"""
        if self._current_index >= len(self._image_paths):
            raise StopIteration

        image_path = self._image_paths[self._current_index]
        self._current_index += 1

        # 获取对应的标注文件
        img_filename = os.path.splitext(os.path.basename(image_path))[0]
        label_path = os.path.join(self.labels_dir, img_filename + ".txt")

        # 创建图片元数据 - 确保返回正确的图像格式
        try:
            metadata = fom.ImageMetadata.build_for(image_path)
            if not metadata.mime_type.startswith('image/'):
                raise ValueError(f"Invalid image format for {image_path}")
        except Exception as e:
            print(f"Error loading image metadata for {image_path}: {e}")
            return None
        
        # 读取标注
        if os.path.exists(label_path):
            detections = []
            with open(label_path, 'r') as f:
                for line in f:
                    try:
                        class_id, x_center, y_center, width, height = map(float, line.strip().split())
                        class_id = int(class_id)
                        
                        # 使用类别映射获取标签名称，如果没有映射则使用类别ID
                        label_name = self.classes_map.get(class_id, str(class_id))
                        
                        detections.append(
                            fol.Detection(
                                label=label_name,  # 使用映射后的类别名称
                                bounding_box=[
                                    x_center - width/2,
                                    y_center - height/2,
                                    width,
                                    height
                                ]
                            )
                        )
                    except Exception as e:
                        print(f"Error parsing label file {label_path}: {e}")
                        continue

            label = fol.Detections(detections=detections)
        else:
            label = None

        return image_path, metadata, label


class UltralyticsDataset(fo.types.LabeledImageDataset):
    def get_dataset_importer_cls(self):
        return UltralyticsYOLODatasetImporter

    def get_dataset_exporter_cls(self):
        return fo.types.LabeledImageDatasetExporter


if __name__ == "__main__":
    # 初始化 FiftyOne 数据集
    fo.list_datasets()
    dataset_dir = "/home/shumin/Downloads/RDD2020"
    train_dataset = fo.Dataset.from_dir(
        dataset_dir=dataset_dir,
        dataset_type=UltralyticsDataset,
        split="train",
        name="train_dataset"  # 给数据集一个名字
    )

    valid_dataset = fo.Dataset.from_dir(
        dataset_dir=dataset_dir,
        dataset_type=UltralyticsDataset,
        split="valid",
        name="valid_dataset"
    )
    # 打印数据集信息
    print(f"训练集样本数: {len(train_dataset)}")
    print(f"验证集样本数: {len(valid_dataset)}")

    # 查看一些基本统计信息
    print("\n训练集信息:")
    print(train_dataset.stats())

    # 可视化几个样本
    session = fo.launch_app(train_dataset)

    # 也可以合并数据集
    merged_dataset = train_dataset.clone()  # 克隆训练集
    merged_dataset.merge_samples(valid_dataset)
    print(f"\n合并后的数据集大小: {len(merged_dataset)}")

    # 保存数据集
    train_dataset.persistent = True  # 持久化保存
    valid_dataset.persistent = True

    # 导出数据集(如果需要)
    # train_dataset.export(
    #     export_dir="exported_dataset",
    #     dataset_type=fo.types.YOLOv5Dataset,
    # )

