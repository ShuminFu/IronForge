## 工具说明

### 1. 数据格式转换工具

- `xml_2_yolo.py`: XML标注格式转换为YOLO格式的工具
  - 支持批量转换XML标注文件到YOLO格式
  - 自动分割训练集(70%)和验证集(30%)
  - 生成YOLO训练所需的data.yaml配置文件
  - 使用方法: `python xml_2_yolo.py`

- `bbx_2_polygon.py`: YOLO边界框格式转换为多边形格式
  - 将YOLO的中心点+宽高格式转换为4点多边形格式
  - 使用方法: `python bbx_2_polygon.py <labels_dir>`

### 2. 图像处理工具

- `jpeg_compress.py`: 异步图像压缩工具
  - 支持批量压缩图片到指定大小
  - 保持图像质量的同时优化存储空间
  - 使用方法: `python jpeg_compress.py <input_dir> <output_dir>`

### 3. 标注工具

- `autolabel.py`: 使用YOLO模型进行自动标注
  - 支持批量处理图片并生成YOLO格式标注
  - 使用方法: `python autolabel.py <input_folder> <weights_path>`

- `image_prompter.py`: 基于Gradio的交互式图像标注工具
  - 提供Web界面进行图像标注
  - 使用方法: `python image_prompter.py`

