# FiftyOne 道路损坏数据集处理工具

这是一个使用 FiftyOne 处理道路损坏数据集的工具集，主要用于数据集的导入、可视化和转换。

## 功能特点

- 支持导入自定义格式的道路损坏数据集
- 提供数据集可视化界面
- 支持数据集随机分割（训练集/验证集）
- 支持导出为 YOLOv5 格式

## 文件说明

- `custom_importer.py`: 自定义数据集导入器
- `51flow.py`: 主要处理流程脚本


## 使用方法

1. 准备数据集
   数据集目录结构应如下：
   ```
   dataset_dir/
   ├── img/
   │   ├── image1.jpg
   │   ├── image2.jpg
   │   └── ...
   └── ann/
       ├── image1.jpg.json
       ├── image2.jpg.json
       └── ...
   ```

2. 运行处理脚本
   ```python
   python 51flow.py
   ```

## 处理流程

1. 导入数据集
2. 启动可视化界面
3. 随机分割数据集（75% 训练集，25% 验证集）
4. 导出为 YOLOv5 格式

## 配置说明

在 `51flow.py` 中可以修改以下参数：
- `base_dir`: 数据集根目录路径
- `shuffle`: 是否随机打乱数据
- `max_samples`: 最大导入样本数（None 表示导入全部）
- 训练集/验证集分割比例

## 注意事项

1. 确保数据集格式符合要求
2. 导出目录会自动创建 `train` 和 `val` 文件夹
3. 默认导出为 YOLOv5 格式，可根据需要修改 `dataset_type`

## 高级用法

如需自定义导入器的行为，可以修改 `custom_importer.py` 中的相关参数：
- `shuffle`: 是否随机打乱数据
- `seed`: 随机种子
- `max_samples`: 最大样本数限制
