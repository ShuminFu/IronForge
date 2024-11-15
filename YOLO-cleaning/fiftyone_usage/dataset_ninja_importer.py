import os
import json
import glob
import random

import fiftyone.utils.data as foud
import fiftyone.core.labels as fol
import fiftyone.core.metadata as fom
import fiftyone.core.config as foc

"""
This class is used to import datasets into fiftyone_usage with custom format fo labels,
which looks like this:
{
    "description": "",
    "tags": [],
    "size": {
        "height": 1079,
        "width": 1919
    },
    "objects": [
        {
            "id": 6569791,
            "classId": 8815,
            "description": "",
            "geometryType": "rectangle",
            "labelerLogin": "az@datasetninja.com",
            "createdAt": "2022-06-15T08:23:28.518Z",
            "updatedAt": "2022-06-15T08:23:28.518Z",
            "tags": [],
            "classTitle": "pothole",
            "points": {
                "exterior": [
                    [
                        264,
                        730
                    ],
                    [
                        705,
                        897
                    ]
                ],
                "interior": []
            }
        }
    ]
}

For more information about the format, please refer to the official documentation:
https://datasetninja.com/road-damage#download
"""


class RoadDamageDatasetImporter(foud.LabeledImageDatasetImporter):
    """道路损坏数据集导入器

    Args:
        dataset_dir: 数据集根目录，包含 img 和 ann 子目录
        shuffle (False): 是否随机打乱样本顺序
        seed (None): 随机种子
        max_samples (None): 最大导入样本数
    """

    def __init__(
            self,
            dataset_dir=None,
            shuffle=False,
            seed=None,
            max_samples=None,
    ):
        super().__init__(
            dataset_dir=dataset_dir,
            shuffle=shuffle,
            seed=seed,
            max_samples=max_samples,
        )

        self.img_dir = os.path.join(dataset_dir, "img")
        self.ann_dir = os.path.join(dataset_dir, "ann")

        # 获取所有图片路径
        self._image_paths = glob.glob(os.path.join(self.img_dir, "*"))
        if shuffle:
            random.seed(seed)
            random.shuffle(self._image_paths)
        if max_samples is not None:
            self._image_paths = self._image_paths[:max_samples]

        self._current_index = 0

    def __len__(self):
        """返回数据集总样本数"""
        return len(self._image_paths)

    def __next__(self):
        """返回下一个样本的信息"""
        if self._current_index >= len(self._image_paths):
            raise StopIteration

        image_path = self._image_paths[self._current_index]
        self._current_index += 1

        # 获取对应的标注文件
        img_filename = os.path.basename(image_path)
        json_path = os.path.join(self.ann_dir, img_filename + ".json")

        # 读取标注
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                data = json.load(f)

            # 获取图片尺寸
            height = data['size']['height']
            width = data['size']['width']

            # 创建图片元数据
            metadata = fom.ImageMetadata(width=width, height=height)

            # 转换标注框
            detections = []
            for obj in data['objects']:
                exterior = obj['points']['exterior']
                x1, y1 = exterior[0]
                x2, y2 = exterior[1]

                # 转换为相对坐标
                rel_x = x1 / width
                rel_y = y1 / height
                rel_w = (x2 - x1) / width
                rel_h = (y2 - y1) / height

                detections.append(
                    fol.Detection(
                        label=obj['classTitle'],
                        bounding_box=[rel_x, rel_y, rel_w, rel_h]
                    )
                )

            label = fol.Detections(detections=detections)
        else:
            metadata = None
            label = None

        return image_path, metadata, label

    @property
    def has_dataset_info(self):
        """是否提供数据集信息"""
        return True

    @property
    def has_image_metadata(self):
        """是否提供图片元数据"""
        return True

    @property
    def label_cls(self):
        """返回标签类型"""
        return fol.Detections

    def setup(self):
        """初始化设置"""
        if not os.path.exists(self.img_dir) or not os.path.exists(self.ann_dir):
            raise FileNotFoundError(
                f"请确保数据集目录存在: {self.img_dir} 和 {self.ann_dir}"
            )

    def get_dataset_info(self):
        """返回数据集信息"""
        return {
            "name": "road-damage-dataset",
            "description": "道路损坏检测数据集",
            "num_samples": len(self),
        }

    def close(self, *args):
        """清理工作"""
        pass
